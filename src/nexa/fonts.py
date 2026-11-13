"""Font discovery helpers — install a brand font, a system font, or an RTL font.

CUI itself only loads TrueType/OpenType bytes or a file path; finding a font by
*family name* on the host is this module's job::

    import nexa as ui
    from nexa import fonts

    path = fonts.find_system_font("DejaVu Sans")       # /usr/share/fonts/.../DejaVuSans.ttf
    rtl = fonts.find_rtl_font()                        # Vazirmatn, Noto Naskh Arabic, …

    with ui.SoftwareRenderer() as sw, ui.UI(width=800, height=600, renderer=sw) as ctx:
        ctx.use_font(path_or_bytes, fallbacks=[rtl])    # BODY + MEDIUM + DISPLAY
        ctx.use_rtl_font()                              # falls back to whatever is installed

Persian/Arabic also needs glyph shaping, which is compiled in by default; a
library built with ``--no-rtl`` (or by an older nexa) lacks it and is rebuilt on
import — check :func:`supports_text_shaping`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

FONT_SUFFIXES = (".ttf", ".otf", ".ttc")

#: Families commonly installed for Persian/Arabic, most preferred first.
RTL_FAMILIES: Tuple[str, ...] = (
    "Vazirmatn",
    "Vazir",
    "Sahel",
    "Noto Naskh Arabic",
    "Noto Sans Arabic",
    "Noto Kufi Arabic",
    "Iranian Sans",
    "IRANSans",
    "Shabnam",
    "Tahoma",
    "DejaVu Sans",
)

_STYLE_HINTS = {
    "regular": ("regular", "book", "normal"),
    "bold": ("bold", "semibold", "demi", "black", "heavy"),
    "italic": ("italic", "oblique"),
}


def _default_dirs() -> Tuple[Path, ...]:
    if sys.platform == "win32":
        windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
        local = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return (windir / "Fonts", local / "Microsoft" / "Windows" / "Fonts")
    if sys.platform == "darwin":
        return (
            Path("/System/Library/Fonts"),
            Path("/System/Library/Fonts/Supplemental"),
            Path("/Library/Fonts"),
            Path.home() / "Library" / "Fonts",
        )
    return (
        Path("/usr/share/fonts"),
        Path("/usr/local/share/fonts"),
        Path.home() / ".local" / "share" / "fonts",
        Path.home() / ".fonts",
    )


def system_font_dirs() -> Tuple[Path, ...]:
    """Every directory this platform keeps fonts in (existing ones only)."""
    dirs = [Path(p) for p in (os.environ.get("NEXA_FONT_DIRS") or "").split(os.pathsep) if p]
    dirs.extend(_default_dirs())
    seen = set()
    out = []
    for directory in dirs:
        key = str(directory)
        if key in seen or not directory.is_dir():
            continue
        seen.add(key)
        out.append(directory)
    return tuple(out)


def list_system_fonts(dirs: Optional[Iterable[Path]] = None, *, limit: int = 0) -> list[Path]:
    """Font files installed on this machine (sorted, optionally truncated)."""
    found: list[Path] = []
    for directory in dirs if dirs is not None else system_font_dirs():
        try:
            for path in sorted(Path(directory).rglob("*")):
                if path.suffix.lower() in FONT_SUFFIXES and path.is_file():
                    found.append(path)
                    if limit and len(found) >= limit:
                        return found
        except OSError:  # pragma: no cover - unreadable directory
            continue
    return found


def _normalize(text: str) -> str:
    return "".join(ch for ch in text.lower() if ch.isalnum())


def _style_rank(stem: str, *, bold: bool, italic: bool) -> int:
    """Lower is better: prefer an exact style match, then a regular weight."""
    low = _normalize(stem)
    wants_bold = bold
    wants_italic = italic
    rank = 0
    if any(hint in low for hint in _STYLE_HINTS["bold"]) != wants_bold:
        rank += 2
    if any(hint in low for hint in _STYLE_HINTS["italic"]) != wants_italic:
        rank += 1
    return rank


def find_system_font(
    family: str,
    *,
    bold: bool = False,
    italic: bool = False,
    dirs: Optional[Iterable[Path]] = None,
) -> Optional[Path]:
    """The best installed file for a family name, e.g. ``"DejaVu Sans"``.

    Looks through the platform font directories and, when fontconfig is
    installed, asks ``fc-match`` so aliases and user-installed fonts resolve
    too.  Returns ``None`` when nothing matches.
    """
    wanted = _normalize(family)
    if not wanted:
        return None
    exact = shutil.which("fc-match")
    if exact and dirs is None:
        try:
            style = ":style=" + "+".join(
                name for name, on in (("Bold", bold), ("Italic", italic)) if on
            ) if (bold or italic) else ""
            result = subprocess.run(
                [exact, "-f", "%{file}", f"{family}{style}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            candidate = Path(result.stdout.strip()) if result.returncode == 0 else None
            if candidate and candidate.is_file() and candidate.suffix.lower() in FONT_SUFFIXES:
                if wanted in _normalize(candidate.stem):
                    return candidate
        except (OSError, subprocess.SubprocessError):  # pragma: no cover - no fontconfig daemon
            pass

    candidates: list[Tuple[int, int, Path]] = []
    for path in list_system_fonts(dirs):
        stem = _normalize(path.stem)
        if wanted not in stem:
            continue
        # prefer the shortest stem: "DejaVuSans" beats "DejaVuSansCondensedBold"
        candidates.append((_style_rank(path.stem, bold=bold, italic=italic), len(path.stem), path))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[0][2]


def find_rtl_font(
    *families: str,
    bold: bool = False,
    dirs: Optional[Iterable[Path]] = None,
) -> Optional[Path]:
    """The first installed font from :data:`RTL_FAMILIES` (or ``families``)."""
    for family in families or RTL_FAMILIES:
        path = find_system_font(family, bold=bold, dirs=dirs)
        if path is not None:
            return path
    return None


def supports_text_shaping() -> bool:
    """Whether this build shapes Arabic/Persian/Indic scripts (the default build does)."""
    from .render import build_features
    from .types import BuildFeatures

    return bool(BuildFeatures.TEXT_SHAPING & build_features())


__all__ = [
    "FONT_SUFFIXES",
    "RTL_FAMILIES",
    "system_font_dirs",
    "list_system_fonts",
    "find_system_font",
    "find_rtl_font",
    "supports_text_shaping",
]
