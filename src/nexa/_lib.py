"""Native shared library loader for nexa (GIL-releasing ctypes.CDLL)."""

from __future__ import annotations

import ctypes
import os
import platform
import sys
from pathlib import Path
from typing import Optional

_LIB: Optional[ctypes.CDLL] = None
_LIB_PATH: Optional[Path] = None


def _lib_filename() -> str:
    s = platform.system().lower()
    if s == "windows":
        return "nexa_cui.dll"
    if s == "darwin":
        return "libnexa_cui.dylib"
    return "libnexa_cui.so"


def locate_library(*, auto_build: bool = True) -> Path:
    """Locate ``libnexa_cui`` in env override, frozen bundle, package dir, or dev checkout."""
    env_override = os.environ.get("NEXA_LIB_PATH")
    if env_override:
        p = Path(env_override).expanduser().resolve()
        if p.is_file():
            return p
        raise FileNotFoundError(f"NEXA_LIB_PATH points to missing file: {p}")

    fname = _lib_filename()
    candidates = []

    # PyInstaller / cx_Freeze / Nuitka bundle directories
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        mp = Path(meipass)
        candidates.extend([mp / "nexa" / "_native" / fname, mp / fname])

    pkg_dir = Path(__file__).resolve().parent
    candidates.append(pkg_dir / "_native" / fname)

    for cand in candidates:
        if cand.is_file():
            return cand

    if auto_build:
        from .build import build_native, find_repo_csrc

        csrc = find_repo_csrc(pkg_dir)
        if csrc is not None:
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
