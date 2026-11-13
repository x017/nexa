"""Native shared library loader for nexa (GIL-releasing ctypes.CDLL).

The loader also guards against *stale* libraries: after a ``git pull``/branch
switch the ``_native/libnexa_cui.so`` built by the previous checkout is still
there, but it lacks the symbols the Python side now calls, and every new widget
fails with ``undefined symbol: cui_..._ex``.  Two cheap checks keep that from
happening:

* a build stamp next to the library records the CUI version plus a fingerprint
  of every C source, so an out-of-date library is recompiled on import;
* a handful of sentinel symbols are resolved from the loaded library, which
  catches builds made by older releases (or prebuilt wheels) even when the
  stamp is missing or cannot be trusted.
"""

from __future__ import annotations

import ctypes
import os
import platform
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

_LIB: Optional[ctypes.CDLL] = None
_LIB_PATH: Optional[Path] = None

# Symbols introduced by different CUI generations.  Every one of them must
# resolve, otherwise the library predates the matching nexa release.
_SENTINEL_SYMBOLS: tuple[str, ...] = (
    "cui_month_calendar_ex",  # CUI 1.2  (text/media/files/planning)
    "cui_pipeline_ex",        # CUI 1.3  (dev tools)
    "cui_dot_display_ex",     # CUI 1.4  (instruments)
    "cui_terminal_ex",
)


def _lib_filename() -> str:
    s = platform.system().lower()
    if s == "windows":
        return "nexa_cui.dll"
    if s == "darwin":
        return "libnexa_cui.dylib"
    return "libnexa_cui.so"


def missing_symbols(path: Path) -> list[str]:
    """Sentinel symbols that ``path`` does not export (empty when it loads fine).

    Note that ``dlopen`` caches by path: after a rebuild in the same process a
    second ``CDLL(path)`` returns the *old* image, so this is only used before
    the library is actually loaded (see ``_load_rebuilt``).
    """
    try:
        lib = ctypes.CDLL(str(path))
    except OSError:
        return []
    return [name for name in _SENTINEL_SYMBOLS if not hasattr(lib, name)]


def stale_reason(path: Path, csrc_dir: Optional[Path]) -> Optional[str]:
    """Why ``path`` must be rebuilt, or ``None`` when it can be used as-is."""
    if csrc_dir is None:
        return None  # installed wheel without sources: trust the shipped binary
    from .build import cui_version, read_stamp, stamp_matches

    record = read_stamp(path)
    if record is not None and stamp_matches(path, csrc_dir):
        return _option_mismatch(record, csrc_dir)
    if record is None:
        # built before stamps existed (or by another tool): rebuild once and
        # stamp it, so the next import is free
        return "no build stamp (built by an older nexa)"
    version = cui_version(csrc_dir)
    if version and record.get("cui_version") != version:
        return f"built against CUI {record.get('cui_version') or '?'}, sources are {version}"
    return "C sources changed since it was built"


def _option_mismatch(record: dict, csrc_dir: Path) -> Optional[str]:
    """Rebuild when the library was built without a capability nexa now expects.

    Only shaping is treated this strictly: a build without it cannot join
    Persian/Arabic letters, which looks like a rendering bug rather than a
    missing feature. Other options (fonts, gl, sw, app) are left to the user.
    """
    from .build import default_options

    options = record.get("options") or {}
    if not options:
        return None
    if options.get("minimal"):
        return None  # an explicitly minimal build: the user chose the size trade-off
    want = bool(default_options().get("text_shaping"))
    if want and options.get("text_shaping") is False:
        return "built without text shaping (Persian/Arabic letters would not join)"
    return None


def _unique_copy(path: Path) -> Path:
    """Copy ``path`` to a never-before-loaded name so ``dlopen`` maps the new bytes."""
    if platform.system().lower() == "windows":
        target = path.with_name(f"{path.stem}-{int(time.time() * 1000)}{path.suffix}")
    else:
        cache = Path(tempfile.gettempdir()) / "nexa-native"
        cache.mkdir(parents=True, exist_ok=True)
        cutoff = time.time() - 7 * 24.0 * 3600.0
        for old in cache.glob(f"*-*-*{path.suffix}"):  # best-effort pruning
            try:
                if old.stat().st_mtime < cutoff:
                    old.unlink()
            except OSError:
                pass
        target = cache / f"{path.stem}-{os.getpid()}-{int(time.time() * 1000)}{path.suffix}"
    shutil.copy2(path, target)
    return target


def _rebuild(path: Path, csrc_dir: Path, reason: str) -> Path:
    from .build import build_native

    print(
        f"nexa: native library {path.name} is out of date ({reason}); rebuilding…",
        file=sys.stderr,
        flush=True,
    )
    build_native(csrc_dir=csrc_dir, output_path=path)
    return path


def locate_library(*, auto_build: bool = True) -> Path:
    """Locate ``libnexa_cui`` in env override, frozen bundle, package dir, or dev checkout."""
    env_override = os.environ.get("NEXA_LIB_PATH")
    if env_override:
        p = Path(env_override).expanduser().resolve()
        if not p.is_file():
            raise FileNotFoundError(f"NEXA_LIB_PATH points to missing file: {p}")
        missing = missing_symbols(p)
        if missing:
            raise RuntimeError(
                f"NEXA_LIB_PATH={p} is out of date: it does not export {missing[0]}. "
                "Rebuild it with `python -m nexa.build -o <path>`."
            )
        return p

    fname = _lib_filename()
    candidates = []

    # PyInstaller / cx_Freeze / Nuitka bundle directories
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        mp = Path(meipass)
        candidates.extend([mp / "nexa" / "_native" / fname, mp / fname])

    pkg_dir = Path(__file__).resolve().parent
    candidates.append(pkg_dir / "_native" / fname)

    csrc = None
    if auto_build:
        from .build import find_repo_csrc

        csrc = find_repo_csrc(pkg_dir)

    for cand in candidates:
        if not cand.is_file():
            continue
        if not auto_build:
            return cand
        reason = stale_reason(cand, csrc)
        if reason is None or csrc is None:
            return cand
        try:
            return _rebuild(cand, csrc, reason)
        except Exception as exc:  # no compiler, read-only dir, ...
            if missing_symbols(cand):
                raise RuntimeError(
                    f"{cand} is out of date ({reason}) and could not be rebuilt: {exc}\n"
                    "Install a C compiler and run `python -m nexa.build`."
                ) from exc
            return cand

    if auto_build and csrc is not None:
        from .build import build_native

        return build_native(csrc_dir=csrc, output_path=pkg_dir / "_native" / fname)

    raise FileNotFoundError(
        f"Could not find compiled {fname}. Run `python -m nexa.build` or reinstall nexa."
    )


def get_cdll() -> ctypes.CDLL:
    """Return the singleton GIL-releasing ``ctypes.CDLL`` handle (configured once)."""
    global _LIB, _LIB_PATH
    if _LIB is None:
        path = locate_library(auto_build=True)
        lib = ctypes.CDLL(str(path), use_errno=True)
        missing = [name for name in _SENTINEL_SYMBOLS if not hasattr(lib, name)]
        if missing:
            # the stamp lied (or a wheel ships an old binary): rebuild once, then
            # load the fresh image through a unique path
            from .build import build_native, find_repo_csrc

            csrc = find_repo_csrc(Path(__file__).resolve().parent)
            if csrc is None:
                raise RuntimeError(
                    f"{path} does not export {missing[0]} — it was built by an older nexa. "
                    "Reinstall nexa or run `python -m nexa.build`."
                )
            print(
                f"nexa: {path.name} does not export {missing[0]}; rebuilding…",
                file=sys.stderr,
                flush=True,
            )
            build_native(csrc_dir=csrc, output_path=path)
            path = _unique_copy(path)
            lib = ctypes.CDLL(str(path), use_errno=True)
        from ._cdefs import bind_prototypes

        bind_prototypes(lib)
        _LIB_PATH = path
        _LIB = lib
    return _LIB


def get_library_path() -> Path:
    if _LIB_PATH is None:
        get_cdll()
    assert _LIB_PATH is not None
    return _LIB_PATH
