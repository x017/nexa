"""PyInstaller hook for nexa — bundles only the tiny C99 shared library."""

from PyInstaller.utils.hooks import collect_dynamic_libs

binaries = collect_dynamic_libs("nexa")
excludedimports = ["nexa.build"]
