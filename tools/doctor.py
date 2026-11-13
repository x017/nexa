#!/usr/bin/env python3
"""Check a nexa checkout for the environment problems that break a build.

    python tools/doctor.py          # human readable
    python tools/doctor.py --json   # machine readable (CI / bug reports)

Everything here has actually bitten someone: a root-owned build directory that
makes setuptools fail with ``Cannot update time stamp of directory
'src/nexa_ui.egg-info'`` (it calls ``os.utime`` on that directory and gets
EACCES), a dangling symlink left by an interrupted build, a stale compiled
library that a wheel install no longer overwrites, a missing C compiler.

Exit status is 0 when nothing failed (warnings are fine) and 1 otherwise.
Nothing here writes to the tree — this is diagnosis only.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".venv", "venv", "build", "dist", "__pycache__", "node_modules",
             ".pytest_cache", ".mypy_cache", ".ruff_cache", ".eggs"}
OK, WARN, FAIL = "ok", "warn", "fail"


class Report:
    def __init__(self) -> None:
        self.rows: list[dict[str, str]] = []

    def add(self, level: str, title: str, detail: str = "", fix: str = "") -> None:
        self.rows.append({"level": level, "title": title, "detail": detail, "fix": fix})

    @property
    def failed(self) -> bool:
        return any(r["level"] == FAIL for r in self.rows)

    def render(self) -> str:
        icons = {OK: "\u2713", WARN: "!", FAIL: "\u2717"}
        lines = []
        for r in self.rows:
            lines.append(f" {icons[r['level']]} {r['title']}")
            if r["detail"]:
                lines.append(f"     {r['detail']}")
            if r["fix"]:
                lines.append(f"     fix: {r['fix']}")
        return "\n".join(lines)


def load_build_module(root: Path = ROOT):
    """Import ``src/nexa/build.py`` without importing the package.

    ``import nexa`` may start a native rebuild, which is exactly what a doctor
    must not do.
    """
    path = root / "src" / "nexa" / "build.py"
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("_nexa_build_doctor", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:  # noqa: BLE001 - a broken build.py is reported elsewhere
        return None
    return module


def rel(path: Path, root: Path) -> str:
    """Path relative to ``root`` for display; absolute when it lives elsewhere."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def walk(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        base = Path(dirpath)
        yield base, dirnames, filenames


def check_writable(rep: Report, root: Path = ROOT) -> None:
    """Root-owned / unwritable paths: the cause of setuptools' 'time stamp' error."""
    euid = os.geteuid() if hasattr(os, "geteuid") else None
    bad_dirs: list[Path] = []
    bad_files: list[Path] = []
    for base, dirnames, filenames in walk(root):
        for name in dirnames + filenames:
            path = base / name
            if path.is_symlink():
                continue  # handled by check_symlinks
            try:
                st = path.stat()
                if not os.access(path, os.W_OK):
                    (bad_dirs if path.is_dir() else bad_files).append(path)
                elif euid and st.st_uid != euid and path.is_dir():
                    bad_dirs.append(path)
            except OSError:
                continue
    if not bad_dirs and not bad_files:
        rep.add(OK, "every path in the checkout is writable by this user")
        return
    sample = ", ".join(rel(p, root) for p in (bad_dirs + bad_files)[:4])
    more = "" if len(bad_dirs) + len(bad_files) <= 4 else f" (+{len(bad_dirs) + len(bad_files) - 4} more)"
    rep.add(
        FAIL,
        f"{len(bad_dirs) + len(bad_files)} path(s) are not writable by you: {sample}{more}",
        "setuptools calls os.utime() on the egg-info directory, so a root-owned or "
        "read-only build directory fails with \"Cannot update time stamp of directory "
        "'src/nexa_ui.egg-info'\"",
        'sudo chown -R "$(id -u):$(id -g)" .   # or: sudo rm -rf src/*.egg-info build dist',
    )


def check_symlinks(rep: Report, root: Path = ROOT) -> None:
    broken = []
    for base, dirnames, filenames in walk(root):
        for name in dirnames + filenames:
            path = base / name
            if path.is_symlink() and not path.exists():
                broken.append(path)
    if broken:
        rep.add(
            FAIL,
            f"{len(broken)} broken symlink(s): " + ", ".join(rel(p, root) for p in broken[:4]),
            "a dangling link is indistinguishable from a missing directory to setuptools",
            "rm the link(s), then `make clean`",
        )
    else:
        rep.add(OK, "no broken symlinks")


def check_python(rep: Report, root: Path = ROOT) -> None:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info < (3, 9):
        rep.add(FAIL, f"Python {version} is too old", "nexa-ui requires >= 3.9",
                "use Python 3.9+ (uv python install 3.12)")
    else:
        where = sys.executable
        in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
        rep.add(OK, f"Python {version} at {where}", "virtualenv" if in_venv else "not a virtualenv (uv/pip will make one)")


def check_compiler(rep: Report, root: Path = ROOT) -> None:
    if not (root / "csrc").is_dir():
        rep.add(OK, "wheel install: no csrc/, nothing to compile")
        return
    candidates = ["cc", "gcc", "clang", "cl", "clang-cl"]
    found = next((c for c in candidates if shutil.which(c)), None)
    if found:
        rep.add(OK, f"C compiler: {found} ({platform.system()})")
    else:
        rep.add(FAIL, "no C compiler found", "a source checkout compiles libnexa_cui on first import",
                "install gcc/clang (Linux), Xcode CLI tools (macOS) or MSVC build tools (Windows)")


def check_native(rep: Report, root: Path = ROOT) -> None:
    build = load_build_module(root)
    native = root / "src" / "nexa" / "_native"
    libs = sorted(p for p in native.glob("libnexa_cui.*") if p.suffix in {".so", ".dylib", ".dll"})
    if not libs:
        rep.add(OK, "no compiled library yet", "builds automatically on first `import nexa` (or `make native`)")
        return
    lib = libs[0]
    if build is None:
        rep.add(WARN, f"library present: {rel(lib, root)}", "could not read src/nexa/build.py to verify the stamp")
        return
    stamp = build.read_stamp(lib)
    if not stamp:
        rep.add(WARN, f"{rel(lib, root)} has no build stamp",
                "built by an older nexa; it will be recompiled on import",
                "make native")
        return
    # Mirror the loader's own rebuild rule (nexa/_lib.py) rather than comparing
    # every option: --lto, --debug and the backend are legitimately different and
    # do not make a library stale.
    problems = []
    options = stamp.get("options") or {}
    if not options:
        problems.append("no options recorded in the stamp")
    elif options.get("minimal"):
        problems.append("built with --minimal, so text shaping is off (chosen trade-off)")
    elif options.get("text_shaping") is False:
        problems.append("built without text shaping (Persian/Arabic letters would not join)")
    csrc = root / "csrc"
    if csrc.is_dir() and stamp.get("fingerprint") != build.source_fingerprint(csrc):
        problems.append("csrc/ sources changed since it was compiled")
    if problems:
        # `--minimal` is a deliberate choice: report it, but it will not rebuild.
        level = OK if options.get("minimal") else WARN
        rep.add(level, f"{rel(lib, root)}: " + "; ".join(problems),
                "recompiled automatically on the next import" if level == WARN else "respected by the loader",
                "make native" if level == WARN else "")
    else:
        rep.add(OK, f"{rel(lib, root)} is up to date (CUI {stamp.get('cui_version')})")


def check_env_override(rep: Report, root: Path = ROOT) -> None:
    override = os.environ.get("NEXA_LIB_PATH")
    if not override:
        return
    if Path(override).is_file():
        rep.add(OK, f"NEXA_LIB_PATH={override}")
    else:
        rep.add(FAIL, f"NEXA_LIB_PATH={override} does not exist",
                "the loader refuses to start with a missing override",
                "unset NEXA_LIB_PATH or point it at a built library")


def check_leftovers(rep: Report, root: Path = ROOT) -> None:
    leftovers = sorted(p for p in root.rglob("*.egg-info") if p.is_dir())
    if leftovers:
        rep.add(WARN, f"{len(leftovers)} egg-info director{'y' if len(leftovers) == 1 else 'ies'} in the tree",
                ", ".join(rel(p, root) for p in leftovers[:4]),
                "harmless when writable; `make clean` removes them")


def run_checks(root: Path = ROOT) -> Report:
    """Run every check against ``root`` (a checkout); returns the findings."""
    rep = Report()
    for check in (check_python, check_compiler, check_writable, check_symlinks,
                  check_native, check_env_override, check_leftovers):
        try:
            check(rep, root)
        except Exception as exc:  # noqa: BLE001 - a doctor must never crash
            rep.add(WARN, f"{check.__name__} could not run", repr(exc))
    return rep


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="machine readable output")
    args = parser.parse_args(argv)

    rep = run_checks()
    if args.json:
        print(json.dumps({"root": str(ROOT), "rows": rep.rows, "failed": rep.failed}, indent=2))
    else:
        print(f"nexa doctor — {ROOT}\n")
        print(rep.render())
        print(f"\n{'problems found' if rep.failed else 'no problems found'}"
              f" · {sum(r['level'] == WARN for r in rep.rows)} warning(s)")
    return 1 if rep.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
