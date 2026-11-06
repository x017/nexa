"""Setuptools build integration for yapps.

Compiles the pure-C99 shared library ``libyapps_cui`` (.so/.dylib/.dll) during
package build and marks wheels as Python-ABI-independent (``py3-none-<plat>``)
since yapps binds through ctypes without linking against libpython.
"""

from __future__ import annotations

import sys
from pathlib import Path
from setuptools import setup
from setuptools.command.build_py import build_py as _build_py

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))


class build_py(_build_py):
    def run(self) -> None:
        from yapps.build import build_native, shared_lib_filename

        csrc = ROOT / "csrc"
        # Build into build_lib/yapps/_native AND into src/yapps/_native for editable installs
        src_native = ROOT / "src" / "yapps" / "_native" / shared_lib_filename()
        build_native(csrc_dir=csrc, output_path=src_native)
        super().run()
        out_native = Path(self.build_lib) / "yapps" / "_native" / shared_lib_filename()
        out_native.parent.mkdir(parents=True, exist_ok=True)
        if src_native.resolve() != out_native.resolve():
            import shutil
            shutil.copy2(src_native, out_native)


cmdclass = {"build_py": build_py}

try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

    class bdist_wheel(_bdist_wheel):
        def finalize_options(self) -> None:
            super().finalize_options()
            self.root_is_pure = False

        def get_tag(self):
            _, _, plat = super().get_tag()
            return "py3", "none", plat

    cmdclass["bdist_wheel"] = bdist_wheel
except ImportError:
    pass


if __name__ == "__main__":
    setup(cmdclass=cmdclass)
