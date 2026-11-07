"""PyInstaller hook registration for small standalone nexa binaries."""

from __future__ import annotations

import os


def get_hook_dirs() -> list[str]:
    return [os.path.dirname(os.path.abspath(__file__))]
