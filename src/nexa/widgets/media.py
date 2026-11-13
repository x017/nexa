"""Images, carousels, before/after comparison, card stacks, waveforms, now playing, counters & tickers."""

from __future__ import annotations

import ctypes
import os
import tempfile
from ctypes import c_bool, c_float, c_int, c_uint8
from pathlib import Path
from typing import Optional, Sequence, Tuple, Union

from .._cdefs import (
    CuiCardStackOpts,
    CuiCropperOpts,
    CuiImageView,
    CuiImageViewerOpts,
    CuiCarouselOpts,
    CuiCompareOpts,
    CuiRect,
    CuiCounterOpts,
    CuiImageOpts,
    CuiNowPlaying,
    CuiNowPlayingOpts,
    CuiResultCardOpts,
    CuiTickerItem,
    CuiTickerOpts,
    CuiVoiceNote,
    CuiVoiceNoteOpts,
    CuiVoiceSessionOpts,
    CuiVoiceWaveOpts,
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
    ImageView,
    NowPlaying,
    PlayerFlags,
    Rect,
    SizeLike,
    TickerItem,
    Tone,
    VoiceNoteResult,
    VoiceState,
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

    def image_load_bytes(
        self,
        data: Union[bytes, bytearray, memoryview],
        *,
        suffix: str = ".png",
    ) -> Tuple[int, int, int]:
        """Decode PNG/JPEG from in-memory ``data``; returns ``(texture_id, width, height)``."""
        fd, tmp_name = tempfile.mkstemp(suffix=suffix)
        try:
            with os.fdopen(fd, "wb") as fp:
                fp.write(data)
            return self.image_load(tmp_name)
        finally:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass

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

    def image_viewer(
        self,
        id: str,
        texture: int,
        image_width: int,
        image_height: int,
        view: ImageView,
        *,
        width: SizeLike = None,
        height: SizeLike = None,
        max_zoom: float = 8.0,
        no_toolbar: bool = False,
        checkerboard: bool = True,
    ) -> ImageView:
        """Zoomable, pannable picture with a toolbar; returns the updated :class:`ImageView`."""
        keep = self._frame_keepalive
        opts = CuiImageViewerOpts()
        opts.width = to_c_size(width)
        opts.height = to_c_size(height)
        opts.max_zoom = float(max_zoom)
        opts.no_toolbar = bool(no_toolbar)
        opts.checkerboard = bool(checkerboard)
        c_view = CuiImageView()
        c_view.zoom = float(view.zoom)
        c_view.cx = float(view.cx)
        c_view.cy = float(view.cy)
        keep.extend((opts, c_view))
        changed = bool(self._lib.cui_image_viewer_ex(
            self._ctx, encode_str(id, keep), int(texture), int(image_width), int(image_height),
            ctypes.byref(c_view), ctypes.byref(opts),
        ))
        self._record_change(changed)
        return ImageView(float(c_view.zoom), float(c_view.cx), float(c_view.cy))

    def cropper(
        self,
        id: str,
        texture: int,
        image_width: int,
        image_height: int,
        crop: Rect,
        *,
        width: SizeLike = None,
        height: SizeLike = None,
        aspect: float = 0.0,
        round_: bool = False,
        min_size: float = 16.0,
    ) -> Tuple[Rect, bool]:
        """Crop rectangle over a picture in image pixels; returns ``(rect, changed)``."""
        keep = self._frame_keepalive
        opts = CuiCropperOpts()
        opts.width = to_c_size(width)
        opts.height = to_c_size(height)
        opts.aspect = float(aspect)
        opts.round = bool(round_)
        opts.min_size = float(min_size)
        c_rect = CuiRect(float(crop.x), float(crop.y), float(crop.w), float(crop.h))
        keep.extend((opts, c_rect))
        changed = bool(self._lib.cui_cropper_ex(
            self._ctx, encode_str(id, keep), int(texture), int(image_width), int(image_height),
            ctypes.byref(c_rect), ctypes.byref(opts),
        ))
        self._record_change(changed)
        return (
            Rect(float(c_rect.x), float(c_rect.y), float(c_rect.w), float(c_rect.h)),
            changed,
        )

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
        fg: ColorLike = None,
    ) -> float:
        if fg is not None:
            color = fg
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
        fg: ColorLike = None,
        group_thousands: bool = True,
    ) -> None:
        if fg is not None:
            color = fg
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

    # ---- Canvas & bars / voice (CUI post-1.4) ----

    def result_card(
        self,
        id: str,
        image: int,
        title: str,
        *,
        caption: Optional[str] = None,
        badge: Optional[str] = None,
        badge_tone: Tone = Tone.NEUTRAL,
        image_w: int = 0,
        image_h: int = 0,
        width: SizeLike = None,
        aspect: float = 1.25,
    ) -> bool:
        """Picture cropped to rounded corners with a status chip, title and
        caption on a fade (CUI post-1.4). Returns ``True`` when the card was
        activated.
        """
        keep = self._frame_keepalive
        opts = CuiResultCardOpts()
        opts.caption = encode_opt(caption, keep)
        opts.badge = encode_opt(badge, keep)
        opts.badge_tone = int(badge_tone)
        opts.image_w = int(image_w)
        opts.image_h = int(image_h)
        opts.width = to_c_size(width)
        opts.aspect = float(aspect)
        keep.append(opts)
        clicked = bool(self._lib.cui_result_card_ex(
            self._ctx, encode_str(id, keep), int(image), encode_str(title, keep), ctypes.byref(opts)
        ))
        self._record_change(clicked)
        return clicked

    def voice_wave(
        self,
        id: str,
        levels: Sequence[float],
        *,
        clip: bool = False,
        progress: float = 0.0,
        owners: Optional[Sequence[int]] = None,
        owner: int = 0,
        color: ColorLike = None,
        fg: ColorLike = None,
        pitch: float = 0.0,
        step: float = 0.0,
        width: SizeLike = None,
    ) -> float:
        """A voice drawn as fine dots — 13 rows mirrored around a centre line
        (CUI post-1.4). With ``clip=True`` it shows a whole clip with a
        playhead; returns the updated ``progress`` (seek by click, drag or
        arrow keys). ``owners`` marks which of two voices each column belongs
        to (0/1); ``owner`` picks the voice being shown.
        """
        if fg is not None:
            color = fg
        keep = self._frame_keepalive
        n = len(levels)
        c_levels = (c_float * max(n, 1))(*(float(v) for v in levels))
        c_prog = c_float(float(progress))
        opts = CuiVoiceWaveOpts()
        opts.clip = bool(clip)
        opts.progress = ctypes.pointer(c_prog)
        if owners:
            m = max(n, 1)
            o_arr = (c_uint8 * m)()
            for i in range(m):
                o_arr[i] = int(owners[i]) & 0xFF if i < len(owners) else 0
            opts.owners = o_arr
            keep.append(o_arr)
        opts.owner = int(owner)
        opts.color = to_c_color(color)
        opts.pitch = float(pitch)
        opts.step = float(step)
        opts.width = to_c_size(width)
        keep.extend((c_levels, c_prog, opts))
        changed = bool(self._lib.cui_voice_wave_ex(
            self._ctx, encode_str(id, keep), c_levels, n, ctypes.byref(opts)
        ))
        self._record_change(changed)
        return float(c_prog.value)

    def voice_note(
        self,
        id: str,
        levels: Sequence[float],
        duration: float,
        *,
        position: float = 0.0,
        speed: float = 1.0,
        playing: bool = False,
        mine: bool = False,
        width: SizeLike = None,
    ) -> VoiceNoteResult:
        """A recorded message in a bubble: play/pause, the waveform as the
        seek bar, played/total time and a 1x/1.5x/2x speed chip
        (CUI post-1.4). The app plays the audio and passes the position back;
        returns the updated :class:`nexa.VoiceNoteResult`.
        """
        keep = self._frame_keepalive
        n = len(levels)
        c_levels = (c_float * max(n, 1))(*(float(v) for v in levels))
        note = CuiVoiceNote()
        note.levels = c_levels
        note.count = n
        note.position = float(position)
        note.duration = float(duration)
        note.speed = float(speed)
        note.playing = bool(playing)
        opts = CuiVoiceNoteOpts()
        opts.mine = bool(mine)
        opts.width = to_c_size(width)
        keep.extend((c_levels, note, opts))
        flags = int(self._lib.cui_voice_note_ex(
            self._ctx, encode_str(id, keep), ctypes.byref(note), ctypes.byref(opts)
        ))
        self._record_change(bool(flags) or note.playing != playing)
        return VoiceNoteResult(float(note.position), float(note.speed), bool(note.playing), flags)

    def voice_session(
        self,
        id: str,
        state: VoiceState,
        levels: Optional[Sequence[float]] = None,
        *,
        owners: Optional[Sequence[int]] = None,
        label: Optional[str] = None,
        transcript: Optional[str] = None,
        upcoming: Optional[str] = None,
        speaker: int = 0,
        you: Optional[str] = None,
        assistant: Optional[str] = None,
        muted: Optional[list] = None,
        no_end: bool = False,
        width: SizeLike = None,
    ) -> int:
        """A spoken conversation with an assistant on one scrolling timeline
        (CUI post-1.4): state label (Listening/Thinking/Speaking/Muted), the
        live transcript with the unspoken part dimmed, and Mute/End buttons.

        ``muted`` is a one-element list updated in place; returns CUI's raw
        result (non-zero when the user interacted).
        """
        keep = self._frame_keepalive
        c_muted = None
        if muted is not None:
            c_muted = c_bool(bool(muted[0] if muted else False))
            keep.append(c_muted)
        n = 0
        c_levels = None
        if levels is not None:
            n = len(levels)
            c_levels = (c_float * max(n, 1))(*(float(v) for v in levels))
            keep.append(c_levels)
        opts = CuiVoiceSessionOpts()
        if owners:
            m = max(n, 1)
            o_arr = (c_uint8 * m)()
            for i in range(m):
                o_arr[i] = int(owners[i]) & 0xFF if i < len(owners) else 0
            opts.owners = o_arr
            keep.append(o_arr)
        opts.label = encode_opt(label, keep)
        opts.transcript = encode_opt(transcript, keep)
        opts.upcoming = encode_opt(upcoming, keep)
        opts.speaker = int(speaker)
        opts.you = encode_opt(you, keep)
        opts.assistant = encode_opt(assistant, keep)
        if c_muted is not None:
            opts.muted = ctypes.pointer(c_muted)
        opts.no_end = bool(no_end)
        opts.width = to_c_size(width)
        keep.append(opts)
        result = int(self._lib.cui_voice_session_ex(
            self._ctx, encode_str(id, keep), int(state), c_levels, n, ctypes.byref(opts)
        ))
        if muted is not None and c_muted is not None and muted:
            muted[0] = bool(c_muted.value)
        self._record_change(bool(result))
        return result
