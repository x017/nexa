"""Typography, text widgets, inline icons, and TrueType/OpenType font loading."""

from __future__ import annotations

import ctypes
from ctypes import c_float
from pathlib import Path
from typing import Union

from .._cdefs import CuiTextOpts, encode_str, to_c_color, to_c_size, to_packed_color
from ..types import Color, ColorLike, FontRole, SizeLike, TextAlign, TextMetrics


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
        self._lib.yapps_icon(
            self._ctx, encode_str(glyph, self._frame_keepalive), float(size), to_packed_color(color)
        )

    def measure_text(
        self, content: str, *, font: Union[FontRole, int] = FontRole.BODY, size: float = 13.0
    ) -> TextMetrics:
        raw = content.encode("utf-8")
        out = (c_float * 5)()
        self._lib.yapps_measure_text(self._ctx, int(font), float(size), raw, len(raw), out)
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
