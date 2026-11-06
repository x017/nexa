"""Images, carousels, before/after comparison, card stacks, waveforms, now playing, counters & tickers."""

from __future__ import annotations

import ctypes
from ctypes import c_float, c_int
from pathlib import Path
from typing import Optional, Sequence, Tuple, Union

from .._cdefs import (
    CuiCardStackOpts,
    CuiCarouselOpts,
    CuiCompareOpts,
    CuiCounterOpts,
    CuiImageOpts,
    CuiNowPlaying,
    CuiNowPlayingOpts,
    CuiTickerItem,
    CuiTickerOpts,
    CuiWaveformOpts,
    encode_opt,
    encode_str,
    to_c_color,
    to_c_size,
)
from ..scopes import CardStackScope, CarouselScope
from ..types import (
    ColorLike,
    FontRole,
    NowPlaying,
    PlayerFlags,
    SizeLike,
    TickerItem,
)


class MediaMixin:
    __slots__ = ()

    # ---- Images & Textures ----

    def image_create(self, width: int, height: int, rgba: Union[bytes, bytearray, memoryview]) -> int:
        mv = memoryview(rgba)
        expected = int(width) * int(height) * 4
        if mv.nbytes < expected:
            raise ValueError(f"RGBA buffer too small: got {mv.nbytes}, need {expected}")
        if mv.readonly:
            buf = (ctypes.c_uint8 * mv.nbytes).from_buffer_copy(mv)
        else:
            buf = (ctypes.c_uint8 * mv.nbytes).from_buffer(mv)
        tex = int(self._lib.cui_image_create(self._ctx, int(width), int(height), buf))
        if tex == 0:
            raise RuntimeError("Failed to create image texture (no renderer attached?)")
        return tex

    def image_load(self, path: Union[str, Path]) -> Tuple[int, int, int]:
        """Load PNG/JPEG from ``path``; returns ``(texture_id, width, height)``."""
        cw, ch = c_int(0), c_int(0)
        tex = int(self._lib.cui_image_load(
            self._ctx, str(path).encode("utf-8"), ctypes.byref(cw), ctypes.byref(ch)
        ))
        if tex == 0:
            raise OSError(f"Failed to load image: {path}")
        return tex, int(cw.value), int(ch.value)

    def image_destroy(self, texture: int) -> None:
        if texture:
            self._lib.cui_image_destroy(self._ctx, int(texture))

    def image(
        self,
        texture: int,
        *,
        width: SizeLike = None,
        height: SizeLike = None,
        radius: float = 0.0,
        tint: ColorLike = None,
    ) -> None:
        keep = self._frame_keepalive
        opts = CuiImageOpts()
        opts.width = to_c_size(width)
        opts.height = to_c_size(height)
        opts.radius = float(radius)
        opts.tint = to_c_color(tint)
        keep.append(opts)
        self._lib.cui_image_ex(self._ctx, int(texture), ctypes.byref(opts))

    # ---- Carousel, Compare & Card Stack ----

    def carousel(
        self,
        id: str,
        count: int,
        index: int,
        *,
        height: float = 220.0,
        auto_advance: float = 0.0,
        gap: float = 0.0,
        no_arrows: bool = False,
        no_dots: bool = False,
        loop: bool = False,
    ) -> CarouselScope:
        keep = self._frame_keepalive
        c_idx = c_int(int(index))
        opts = CuiCarouselOpts()
        opts.height = float(height)
        opts.auto_advance = float(auto_advance)
        opts.gap = float(gap)
        opts.no_arrows = bool(no_arrows)
        opts.no_dots = bool(no_dots)
        opts.loop = bool(loop)
        keep.extend((c_idx, opts))
        changed = bool(self._lib.cui_carousel_begin(
            self._ctx, encode_str(id, keep), int(count), ctypes.byref(c_idx), ctypes.byref(opts)
        ))
        return CarouselScope(self, c_idx, changed)

    def image_compare(
        self,
        id: str,
        before_tex: int,
        after_tex: int,
        pos: float = 0.5,
        *,
        width: SizeLike = None,
        height: float = 240.0,
        before_label: Optional[str] = None,
        after_label: Optional[str] = None,
        aspect: float = 0.0,
    ) -> float:
        keep = self._frame_keepalive
        c_pos = c_float(float(pos))
        opts = CuiCompareOpts()
        opts.width = to_c_size(width)
        opts.height = float(height)
        opts.before_label = encode_opt(before_label, keep)
        opts.after_label = encode_opt(after_label, keep)
        opts.aspect = float(aspect)
        keep.append(opts)
        changed = bool(self._lib.cui_image_compare_ex(
            self._ctx, encode_str(id, keep), int(before_tex), int(after_tex),
            ctypes.byref(c_pos), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return float(c_pos.value)

    def card_stack(
        self,
        id: str,
        count: int,
        *,
        width: SizeLike = None,
        height: float = 220.0,
        visible: int = 3,
    ) -> CardStackScope:
        keep = self._frame_keepalive
        opts = CuiCardStackOpts()
        opts.width = to_c_size(width)
        opts.height = float(height)
        opts.visible = int(visible)
        keep.append(opts)
        self._lib.cui_card_stack_begin(self._ctx, encode_str(id, keep), int(count), ctypes.byref(opts))
        return CardStackScope(self)

    # ---- Audio / Media & Tickers ----

    def waveform(
        self,
        id: str,
        peaks: Sequence[float],
        progress: Optional[float] = None,
        *,
        width: SizeLike = None,
        height: float = 0.0,
        bar: float = 0.0,
        gap: float = 0.0,
        color: ColorLike = None,
    ) -> float:
        keep = self._frame_keepalive
        n = len(peaks)
        c_peaks = (c_float * n)(*(float(p) for p in peaks))
        c_prog = c_float(float(progress)) if progress is not None else None
        opts = CuiWaveformOpts()
        opts.width = to_c_size(width)
        opts.height = float(height)
        opts.bar = float(bar)
        opts.gap = float(gap)
        opts.color = to_c_color(color)
        keep.extend((c_peaks, opts))
        if c_prog is not None:
            keep.append(c_prog)
        changed = bool(self._lib.cui_waveform_ex(
            self._ctx, encode_str(id, keep), c_peaks, n,
            ctypes.byref(c_prog) if c_prog is not None else None, ctypes.byref(opts)
        ))
        self._record_change(changed)
        return float(c_prog.value) if c_prog is not None else 0.0

    def now_playing(
        self,
        id: str,
        track: NowPlaying,
        *,
        width: SizeLike = None,
        compact: bool = False,
    ) -> Tuple[NowPlaying, PlayerFlags]:
        keep = self._frame_keepalive
        c_np = CuiNowPlaying()
        c_np.title = encode_str(track.title, keep)
        c_np.artist = encode_opt(track.artist, keep)
        c_np.art = int(track.art)
        c_np.art_color = to_c_color(track.art_color)
        c_np.position = float(track.position)
        c_np.duration = float(track.duration)
        c_np.playing = bool(track.playing)
        opts = CuiNowPlayingOpts()
        opts.width = to_c_size(width)
        opts.compact = bool(compact)
        keep.extend((c_np, opts))
        flags = PlayerFlags(int(self._lib.cui_now_playing_ex(
            self._ctx, encode_str(id, keep), ctypes.byref(c_np), ctypes.byref(opts)
        )))
        self._record_change(bool(flags))
        updated = NowPlaying(
            track.title, track.artist, float(c_np.position), float(c_np.duration),
            bool(c_np.playing), track.art, track.art_color
        )
        return updated, flags

    def counter(
        self,
        id: str,
        value: float,
        *,
        format: Optional[str] = None,
        size: float = 0.0,
        font: Union[FontRole, int] = FontRole.BODY,
        color: ColorLike = None,
        group_thousands: bool = True,
    ) -> None:
        keep = self._frame_keepalive
        opts = CuiCounterOpts()
        opts.format = encode_opt(format, keep)
        opts.size = float(size)
        opts.font = int(font)
        opts.color = to_c_color(color)
        opts.group_thousands = bool(group_thousands)
        keep.append(opts)
        self._lib.cui_counter_ex(
            self._ctx, encode_str(id, keep), float(value), ctypes.byref(opts)
        )

    def ticker(
        self,
        id: str,
        items: Sequence[TickerItem],
        *,
        speed: float = 0.0,
        height: float = 0.0,
    ) -> None:
        keep = self._frame_keepalive
        n = len(items)
        arr = (CuiTickerItem * n)()
        for i, it in enumerate(items):
            arr[i].label = encode_str(it.label, keep)
            arr[i].value = encode_str(it.value, keep)
            arr[i].delta = float(it.delta)
            arr[i].lower_is_better = bool(it.lower_is_better)
        opts = CuiTickerOpts(0, float(speed), float(height))
        keep.extend((arr, opts))
        self._lib.cui_ticker_ex(self._ctx, encode_str(id, keep), arr, n, ctypes.byref(opts))
