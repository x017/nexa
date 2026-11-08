"""Setuptools build integration for nexa-ui (`import nexa`).

Compiles the zero-dependency C99 shared library ``libnexa_cui`` (.so/.dylib/.dll)
into ``nexa/_native/`` during wheel/install builds and tags binary wheels as
Python-ABI-independent (``py3-none-<plat>``) since nexa binds through ``ctypes``
without linking against ``libpython``.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from setuptools import Distribution, find_packages, setup
from setuptools.command.build_py import build_py as _build_py

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))


class BinaryDistribution(Distribution):
    """Ensure wheels place ``nexa/`` directly at ``platlib`` root (no ``.data/purelib``)."""

    def has_ext_modules(self) -> bool:
        return True


class build_py(_build_py):
    def run(self) -> None:
        super().run()
        from nexa.build import build_native, shared_lib_filename

        csrc = ROOT / "csrc"
        fname = shared_lib_filename()
        out_native = Path(self.build_lib) / "nexa" / "_native" / fname
        out_native.parent.mkdir(parents=True, exist_ok=True)
        build_native(csrc_dir=csrc, output_path=out_native)

        # PEP 660 editable install (`pip install -e .`) also expects the binary in `src/nexa/_native/`
        if getattr(self, "editable_mode", False):
            src_native = ROOT / "src" / "nexa" / "_native" / fname
            src_native.parent.mkdir(parents=True, exist_ok=True)
            if src_native.resolve() != out_native.resolve():
                shutil.copy2(out_native, src_native)


cmdclass: dict[str, type] = {"build_py": build_py}

try:
    from setuptools.command.develop import develop as _develop

    class develop(_develop):
        def run(self) -> None:
            from nexa.build import build_native, shared_lib_filename

            src_native = ROOT / "src" / "nexa" / "_native" / shared_lib_filename()
            build_native(csrc_dir=ROOT / "csrc", output_path=src_native)
            super().run()

    cmdclass["develop"] = develop
except ImportError:
    pass

try:
    try:
        from setuptools.command.bdist_wheel import bdist_wheel as _bdist_wheel
    except ImportError:
        from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

    class bdist_wheel(_bdist_wheel):
        def finalize_options(self) -> None:
            self.root_is_pure = False
            super().finalize_options()
            self.root_is_pure = False

        def get_tag(self) -> tuple[str, str, str]:
            _, _, plat = super().get_tag()
            env_plat = os.environ.get("NEXA_WHEEL_PLAT", "").strip()
            if env_plat:
                plat = env_plat
            return "py3", "none", plat

    cmdclass["bdist_wheel"] = bdist_wheel
except ImportError:
    pass


if __name__ == "__main__":
    setup(
        distclass=BinaryDistribution,
        cmdclass=cmdclass,
        package_dir={"": "src"},
        packages=find_packages("src"),
        package_data={
            "nexa": [
                "py.typed",
                "_native/*.so",
                "_native/*.dylib",
                "_native/*.dll",
            ],
        },
    )
