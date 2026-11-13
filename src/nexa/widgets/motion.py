"""Spring animations, spotlight cards, and text motion effects."""

from __future__ import annotations

import ctypes
from typing import Sequence, Union

from .._cdefs import (
    CuiGradientTextOpts,
    CuiSpotlightOpts,
    CuiTextFxOpts,
    encode_str,
    encode_str_array,
    to_c_color,
    to_c_size,
)
from ..scopes import SimpleScope
from ..types import ColorLike, FontRole, SizeLike


def _build_text_fx_opts(
    keep: list,
    *,
    font: Union[FontRole, int] = FontRole.BODY,
    size: float = 0.0,
    color: ColorLike = None,
    fg: ColorLike = None,
    width: SizeLike = None,
    nowrap: bool = False,
    speed: float = 0.0,
    delay: float = 0.0,
    caret: bool = False,
) -> CuiTextFxOpts:
    if fg is not None:
        color = fg
    opts = CuiTextFxOpts()
    opts.font = int(font)
    opts.size = float(size)
    opts.color = to_c_color(color)
    opts.width = to_c_size(width)
    opts.nowrap = bool(nowrap)
    opts.speed = float(speed)
    opts.delay = float(delay)
    opts.caret = bool(caret)
    keep.append(opts)
    return opts


class MotionMixin:
    __slots__ = ()

    def shimmer_text(self, text: str, **kwargs) -> None:
        keep = self._frame_keepalive
        opts = _build_text_fx_opts(keep, **kwargs)
        self._lib.cui_shimmer_text_ex(self._ctx, encode_str(text, keep), ctypes.byref(opts))

    def typewriter(self, id: str, text: str, **kwargs) -> bool:
        keep = self._frame_keepalive
        opts = _build_text_fx_opts(keep, **kwargs)
        return bool(self._lib.cui_typewriter_ex(
            self._ctx, encode_str(id, keep), encode_str(text, keep), ctypes.byref(opts)
        ))

    def text_reveal(self, id: str, text: str, **kwargs) -> None:
        keep = self._frame_keepalive
        opts = _build_text_fx_opts(keep, **kwargs)
        self._lib.cui_text_reveal_ex(
            self._ctx, encode_str(id, keep), encode_str(text, keep), ctypes.byref(opts)
        )

    def word_rotate(
        self, id: str, words: Sequence[str], interval: float = 2.2, **kwargs
    ) -> None:
        keep = self._frame_keepalive
        arr, n = encode_str_array(words, keep)
        opts = _build_text_fx_opts(keep, **kwargs)
        self._lib.cui_word_rotate_ex(
            self._ctx, encode_str(id, keep), arr, n, float(interval), ctypes.byref(opts)
        )

    def number_roll(self, id: str, formatted_text: str, **kwargs) -> None:
        keep = self._frame_keepalive
        opts = _build_text_fx_opts(keep, **kwargs)
        self._lib.cui_number_roll_ex(
            self._ctx, encode_str(id, keep), encode_str(formatted_text, keep), ctypes.byref(opts)
        )

    def gradient_text(
        self,
        text: str,
        *,
        from_color: ColorLike = None,
        to_color: ColorLike = None,
        font: Union[FontRole, int] = FontRole.BODY,
        size: float = 0.0,
        animate: bool = False,
        width: SizeLike = None,
    ) -> None:
        keep = self._frame_keepalive
        opts = CuiGradientTextOpts()
        opts.font = int(font)
        opts.size = float(size)
        opts.from_color = to_c_color(from_color)
        opts.to = to_c_color(to_color)
        opts.animate = bool(animate)
        opts.width = to_c_size(width)
        keep.append(opts)
        self._lib.cui_gradient_text_ex(self._ctx, encode_str(text, keep), ctypes.byref(opts))

    def spotlight(
        self,
        id: str,
        *,
        width: SizeLike = None,
        height: SizeLike = None,
        pad: float = 0.0,
        gap: float = 0.0,
        color: ColorLike = None,
        fg: ColorLike = None,
        beam: bool = False,
    ) -> SimpleScope:
        if fg is not None:
            color = fg
        keep = self._frame_keepalive
        opts = CuiSpotlightOpts()
        opts.width = to_c_size(width)
        opts.height = to_c_size(height)
        opts.pad = float(pad)
        opts.gap = float(gap)
        opts.color = to_c_color(color)
        opts.beam = bool(beam)
        keep.append(opts)
        self._lib.cui_spotlight_begin(self._ctx, encode_str(id, keep), ctypes.byref(opts))
        return SimpleScope(self._ctx, self._lib.cui_spotlight_end)

    def animate(self, key: Union[str, int], target: float) -> float:
        cid = int(key) if isinstance(key, int) else self.make_id(key)
        return float(self._lib.cui_animate(self._ctx, cid, float(target)))

    def animate_spring(
        self, key: Union[str, int], target: float, duration: float = 0.35, bounce: float = 0.2
    ) -> float:
        cid = int(key) if isinstance(key, int) else self.make_id(key)
        return float(self._lib.cui_animate_spring(
            self._ctx, cid, float(target), float(duration), float(bounce)
        ))
