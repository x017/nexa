"""Typography, text widgets, inline icons, and TrueType/OpenType font loading."""

from __future__ import annotations

import ctypes
from ctypes import c_float
from pathlib import Path
from typing import Optional, Sequence, Union

from .._cdefs import (
    CuiTerminalOpts,
    CuiTerminalResult,
    CuiTextOpts,
    encode_opt,
    encode_str,
    to_c_color,
    to_c_size,
    to_packed_color,
)
from ..types import (
    Color,
    ColorLike,
    FontRole,
    SizeLike,
    TerminalBuffer,
    TerminalResult,
    TextAlign,
    TextDirection,
    TextMetrics,
)


class TextMixin:
    __slots__ = ()

    def text(
        self,
        content: str,
        *,
        font: Union[FontRole, int] = FontRole.BODY,
        size: float = 0.0,
        color: ColorLike = None,
        align: TextAlign = TextAlign.LEFT,
        nowrap: bool = False,
        tabular: bool = False,
        selectable: bool = False,
        width: SizeLike = None,
        line_height: float = 0.0,
        direction: TextDirection = TextDirection.INHERIT,
    ) -> None:
        keep = self._frame_keepalive
        opts = CuiTextOpts()
        opts.font = int(font)
        opts.size = float(size)
        opts.color = to_c_color(color)
        opts.align = int(align)
        opts.nowrap = bool(nowrap)
        opts.tabular = bool(tabular)
        opts.selectable = bool(selectable)
        opts.width = to_c_size(width)
        opts.line_height = float(line_height)
        opts.direction = int(direction)
        keep.append(opts)
        self._lib.cui_text_ex(self._ctx, encode_str(content, keep), ctypes.byref(opts))

    def heading(self, content: str, level: int = 2) -> None:
        self._lib.cui_heading(self._ctx, encode_str(content, self._frame_keepalive), int(level))

    def label(self, content: str) -> None:
        self._lib.cui_label(self._ctx, encode_str(content, self._frame_keepalive))

    def secondary(self, content: str) -> None:
        self._lib.cui_secondary(self._ctx, encode_str(content, self._frame_keepalive))

    def muted(self, content: str) -> None:
        self._lib.cui_muted(self._ctx, encode_str(content, self._frame_keepalive))

    def code(self, content: str) -> None:
        self._lib.cui_code(self._ctx, encode_str(content, self._frame_keepalive))

    def kbd(self, keys: str) -> None:
        self._lib.cui_kbd(self._ctx, encode_str(keys, self._frame_keepalive))

    def link(self, content: str) -> bool:
        clicked = bool(self._lib.cui_link(self._ctx, encode_str(content, self._frame_keepalive)))
        self._record_change(clicked)
        return clicked

    def icon(self, glyph: str, size: float = 16.0, color: ColorLike = Color.FOREGROUND) -> None:
        self._lib.nexa_icon(
            self._ctx, encode_str(glyph, self._frame_keepalive), float(size), to_packed_color(color)
        )

    def measure_text(
        self, content: str, *, font: Union[FontRole, int] = FontRole.BODY, size: float = 13.0
    ) -> TextMetrics:
        raw = content.encode("utf-8")
        out = (c_float * 5)()
        self._lib.nexa_measure_text(self._ctx, int(font), float(size), raw, len(raw), out)
        return TextMetrics(float(out[0]), float(out[1]), float(out[2]), float(out[3]), float(out[4]))

    def font_load_file(self, path: Union[str, Path]) -> int:
        fid = int(self._lib.cui_font_load_file(self._ctx, str(path).encode("utf-8")))
        if fid < 0:
            raise OSError(f"Failed to load font file: {path}")
        return fid

    def font_load_memory(self, data: Union[bytes, bytearray, memoryview]) -> int:
        raw = bytes(data)
        buf = ctypes.create_string_buffer(raw, len(raw))
        fid = int(self._lib.cui_font_load_memory(self._ctx, buf, len(raw), True))
        if fid < 0:
            raise ValueError("Failed to load TrueType/OpenType font from memory")
        return fid

    def font_set_role(self, role: FontRole, font_id: int) -> None:
        self._lib.cui_font_set_role(self._ctx, int(role), int(font_id))

    def font_add_fallback(self, font_id: int, fallback_font_id: int) -> None:
        self._lib.cui_font_add_fallback(self._ctx, int(font_id), int(fallback_font_id))

    # ---- Whole-UI typography (CUI 1.2+) ----

    def load_font(
        self,
        source: Union[str, Path, bytes, bytearray, memoryview],
        *,
        fallbacks: Sequence[Union[str, Path, int]] = (),
    ) -> int:
        """Load a ``.ttf``/``.otf`` from a path or from bytes and return its font id.

        ``fallbacks`` are font paths (or ids already loaded) consulted for glyphs
        the font is missing — the usual way to combine a Latin UI font with a
        Persian/Arabic or CJK one.
        """
        if isinstance(source, (bytes, bytearray, memoryview)):
            font_id = self.font_load_memory(source)
        else:
            font_id = self.font_load_file(source)
        for fallback in fallbacks:
            other = fallback if isinstance(fallback, int) else self.font_load_file(fallback)
            self.font_add_fallback(font_id, int(other))
        return font_id

    def use_font(
        self,
        source: Union[str, Path, bytes, bytearray, memoryview, None] = None,
        *,
        family: Optional[str] = None,
        roles: Sequence[FontRole] = (FontRole.BODY, FontRole.MEDIUM, FontRole.DISPLAY),
        fallbacks: Sequence[Union[str, Path, int]] = (),
    ) -> int:
        """Make one font the face of the whole UI and return its font id.

        Accepts a path, raw bytes, or ``family="Segoe UI"`` to look the file up
        among the installed system fonts.  ``roles`` decides which of the five
        built-in roles it replaces; leave ``MONO`` and ``ICONS`` out so code and
        icons keep their own faces::

            ctx.use_font("assets/PlusJakartaSans-Regular.ttf",
                         fallbacks=[fonts.find_rtl_font()])
            ctx.use_font(family="DejaVu Sans")

        Persian/Arabic also needs a shaping build; see
        :func:`nexa.fonts.supports_text_shaping`.
        """
        if source is None:
            if family is None:
                raise ValueError("pass a font path/bytes or family='System Font Name'")
            from ..fonts import find_system_font

            found = find_system_font(family)
            if found is None:
                raise FileNotFoundError(f"no installed font matches family {family!r}")
            source = found
        font_id = self.load_font(source, fallbacks=fallbacks)
        for role in roles:
            self.font_set_role(role, font_id)
        return font_id

    def use_system_font(
        self,
        family: str,
        *,
        roles: Sequence[FontRole] = (FontRole.BODY, FontRole.MEDIUM, FontRole.DISPLAY),
        fallbacks: Sequence[Union[str, Path, int]] = (),
    ) -> int:
        """``use_font(family=…)`` as a one-liner; raises when the font is not installed."""
        return self.use_font(family=family, roles=roles, fallbacks=fallbacks)

    def use_rtl_font(
        self,
        family: Optional[str] = None,
        *,
        roles: Sequence[FontRole] = (FontRole.BODY, FontRole.MEDIUM, FontRole.DISPLAY),
        fallbacks: Sequence[Union[str, Path, int]] = (),
    ) -> int:
        """Install a Persian/Arabic-capable font for the whole UI.

        Without ``family`` the first installed font from
        :data:`nexa.fonts.RTL_FAMILIES` is used (Vazirmatn, Noto Naskh Arabic,
        Tahoma, …).  Pair it with ``direction=ui.TextDirection.RTL`` on a
        container, and build with ``--rtl`` so the glyphs are shaped.
        """
        from ..fonts import find_rtl_font, find_system_font

        found = find_system_font(family) if family else find_rtl_font()
        if found is None:
            raise FileNotFoundError(
                "no Persian/Arabic font found; install Vazirmatn or Noto Naskh Arabic, "
                "or pass the .ttf path to use_font()"
            )
        return self.use_font(found, roles=roles, fallbacks=fallbacks)

    # ---- Terminal (CUI 1.3) ----

    def terminal(
        self,
        id: str,
        buffer: TerminalBuffer,
        *,
        width: SizeLike = None,
        height: float = 320.0,
        size: float = 13.0,
        prompt: Optional[str] = None,
        no_input: bool = False,
    ) -> TerminalResult:
        """Output over an input line, with ANSI colors, history and Ctrl+C/Ctrl+L.

        Write to the ``TerminalBuffer`` you own; this draws it and returns the
        submitted command (``result.command[0]``) or an interrupt.
        """
        keep = self._frame_keepalive
        opts = CuiTerminalOpts()
        opts.width = to_c_size(width)
        opts.height = float(height)
        opts.size = float(size)
        opts.prompt = encode_opt(prompt, keep)
        opts.no_input = bool(no_input)
        out = CuiTerminalResult()
        keep.extend((opts, out))
        self._lib.nexa_terminal_ex(self._ctx, encode_str(id, keep), ctypes.byref(buffer._buf),
                                   ctypes.byref(opts), ctypes.byref(out))
        res = TerminalResult(
            command=out.command.decode("utf-8", errors="replace") if out.command else None,
            interrupt=bool(out.interrupt),
        )
        self._record_change(bool(res))
        return res
