"""Instrument components: knobs, faders, meters, gauges, dot charts, readouts & event tracks.

These are the components CUI 1.4 added for interfaces that read like an
instrument — a value as dots, a label in the monospaced font, hairlines and one
accent.  They take and return plain Python values like every other nexa widget.
"""

from __future__ import annotations

import builtins
import ctypes
from ctypes import c_double, c_float, c_int
from typing import List, Optional, Sequence, Tuple

from .._cdefs import (
    CuiDotChartOpts,
    CuiDotChartResult,
    CuiDotDisplayOpts,
    CuiDotSeries,
    CuiEventTrackOpts,
    CuiEventTrackResult,
    CuiFaderOpts,
    CuiKnobOpts,
    CuiLevelMeterOpts,
    CuiRadialGaugeOpts,
    CuiReadoutOpts,
    encode_opt,
    encode_str,
    to_c_color,
    to_c_size,
)
from ..types import (
    Align,
    ColorLike,
    ControlSize,
    DotChartResult,
    DotSeries,
    EventTrackResult,
    FontRole,
    SizeLike,
    Tone,
)


class InstrumentsMixin:
    __slots__ = ()

    # ---- Knob, fader, meter & gauge ----

    def knob(
        self,
        id: str,
        value: float,
        *,
        min: float = 0.0,
        max: float = 1.0,
        label: Optional[str] = None,
        unit: Optional[str] = None,
        format: Optional[str] = None,
        size: float = 0.0,
        step: float = 0.0,
        reset: float = 0.0,
        bipolar: bool = False,
        log_scale: bool = False,
        hide_value: bool = False,
        disabled: bool = False,
        color: ColorLike = None,
    ) -> float:
        """Rotary knob dragged vertically (or with the arrow keys); returns the new value."""
        keep = self._frame_keepalive
        opts = CuiKnobOpts()
        opts.label = encode_opt(label, keep)
        opts.unit = encode_opt(unit, keep)
        opts.format = encode_opt(format, keep)
        opts.size = float(size)
        opts.step = float(step)
        opts.reset = float(reset)
        opts.bipolar = bool(bipolar)
        opts.log_scale = bool(log_scale)
        opts.hide_value = bool(hide_value)
        opts.disabled = bool(disabled)
        opts.color = to_c_color(color)
        c_val = c_float(float(value))
        keep.extend((opts, c_val))
        changed = bool(self._lib.cui_knob_ex(
            self._ctx, encode_str(id, keep), ctypes.byref(c_val), float(min), float(max), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return float(c_val.value)

    def fader(
        self,
        id: str,
        value: float,
        *,
        min: float = 0.0,
        max: float = 1.0,
        label: Optional[str] = None,
        unit: Optional[str] = None,
        format: Optional[str] = None,
        length: float = 160.0,
        horizontal: bool = False,
        step: float = 0.0,
        reset: float = 0.0,
        ticks: Sequence[float] = (),
        meter: Optional[Sequence[float]] = None,
        meter_channels: int = 1,
        hide_value: bool = False,
        disabled: bool = False,
    ) -> float:
        """Linear fader with ticks and an optional VU meter beside the track."""
        keep = self._frame_keepalive
        opts = CuiFaderOpts()
        opts.label = encode_opt(label, keep)
        opts.unit = encode_opt(unit, keep)
        opts.format = encode_opt(format, keep)
        opts.length = float(length)
        opts.horizontal = bool(horizontal)
        opts.step = float(step)
        opts.reset = float(reset)
        if ticks:
            arr = (c_float * len(ticks))(*[float(t) for t in ticks])
            keep.append(arr)
            opts.ticks = ctypes.cast(arr, ctypes.POINTER(c_float))
            opts.tick_count = len(ticks)
        if meter is not None:
            levels = [float(v) for v in (meter if isinstance(meter, (list, tuple)) else [meter])]
            channels = int(meter_channels or len(levels)) or 1
            meter_arr = (c_float * builtins.max(1, channels))()
            for i in range(builtins.min(channels, len(levels))):
                meter_arr[i] = levels[i]
            keep.append(meter_arr)
            opts.meter = ctypes.cast(meter_arr, ctypes.POINTER(c_float))
            opts.meter_channels = channels
        opts.hide_value = bool(hide_value)
        opts.disabled = bool(disabled)
        c_val = c_float(float(value))
        keep.extend((opts, c_val))
        changed = bool(self._lib.cui_fader_ex(
            self._ctx, encode_str(id, keep), ctypes.byref(c_val), float(min), float(max), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return float(c_val.value)

    def level_meter(
        self,
        id: str,
        levels: Sequence[float],
        *,
        min_db: float = -48.0,
        max_db: float = 6.0,
        length: float = 160.0,
        thickness: float = 10.0,
        horizontal: bool = False,
        scale: bool = True,
        segmented: bool = True,
        hold: float = 1.6,
        decay: float = 24.0,
    ) -> bool:
        """Bars that jump to each peak and fall back; returns True when a clip light was cleared."""
        keep = self._frame_keepalive
        opts = CuiLevelMeterOpts()
        opts.min_db = float(min_db)
        opts.max_db = float(max_db)
        opts.length = float(length)
        opts.thickness = float(thickness)
        opts.horizontal = bool(horizontal)
        opts.scale = bool(scale)
        opts.segmented = bool(segmented)
        opts.hold = float(hold)
        opts.decay = float(decay)
        n = builtins.max(1, len(levels))
        arr = (c_float * n)(*[float(v) for v in levels][:n])
        keep.extend((opts, arr))
        cleared = bool(self._lib.cui_level_meter_ex(self._ctx, encode_str(id, keep), arr, n, ctypes.byref(opts)))
        self._record_change(cleared)
        return cleared

    def radial_gauge(
        self,
        id: str,
        value: float,
        *,
        min: float = 0.0,
        max: float = 100.0,
        label: Optional[str] = None,
        unit: Optional[str] = None,
        format: Optional[str] = None,
        size: float = 200.0,
        sweep: float = 240.0,
        ticks: int = 5,
        target: Optional[float] = None,
        bands: Sequence[Tuple[float, Tone]] = (),
        no_needle: bool = False,
    ) -> None:
        """Arc gauge with an accent arc, ticks, optional tone bands and a target mark.

        ``bands`` are ``(up_to_value, tone)`` pairs, each stretching from the band
        before it (or ``min``) up to its own value.
        """
        keep = self._frame_keepalive
        opts = CuiRadialGaugeOpts()
        opts.label = encode_opt(label, keep)
        opts.unit = encode_opt(unit, keep)
        opts.format = encode_opt(format, keep)
        opts.size = float(size)
        opts.sweep = float(sweep)
        opts.ticks = int(ticks)
        opts.target = -1.0 if target is None else float(target)
        opts.show_target = target is not None
        opts.no_needle = bool(no_needle)
        if bands:
            from .._cdefs import CuiGaugeBand

            arr = (CuiGaugeBand * len(bands))()
            for i, (up_to, band_tone) in enumerate(bands):
                arr[i].to = float(up_to)
                arr[i].tone = int(band_tone)
            keep.append(arr)
            opts.bands = ctypes.cast(arr, ctypes.POINTER(CuiGaugeBand))
            opts.band_count = len(bands)
        keep.append(opts)
        self._lib.cui_radial_gauge_ex(self._ctx, encode_str(id, keep), float(value), float(min), float(max), ctypes.byref(opts))

    # ---- Dot charts, displays & readouts ----

    def dot_chart(
        self,
        id: str,
        series: Sequence[DotSeries],
        *,
        count: Optional[int] = None,
        width: SizeLike = None,
        height: float = 220.0,
        x_min: float = 0.0,
        x_max: Optional[float] = None,
        x_units: str = "number",
        x_format: Optional[str] = None,
        x_step: float = 0.0,
        min: Optional[float] = None,
        max: Optional[float] = None,
        format: Optional[str] = None,
        unit: Optional[str] = None,
        pitch: float = 0.0,
        no_grid: bool = False,
        no_axis: bool = False,
        no_readout: bool = False,
        annotations: Sequence[object] = (),
    ) -> DotChartResult:
        """Values as a grid of dots, lit up to each column's value and dim above it."""
        keep = self._frame_keepalive
        n = len(series)
        arr = (CuiDotSeries * n)()
        longest = 0
        for i, s in enumerate(series):
            values = (c_float * builtins.max(1, len(s.values)))(*s.values) if s.values else (c_float * 1)()
            keep.append(values)
            arr[i].values = ctypes.cast(values, ctypes.POINTER(c_float))
            arr[i].name = encode_opt(s.name, keep)
            arr[i].accent = bool(s.accent)
            longest = builtins.max(longest, len(s.values))
        opts = CuiDotChartOpts()
        opts.width = to_c_size(width)
        opts.height = float(height)
        opts.x_min = float(x_min)
        opts.x_max = float(x_max) if x_max is not None else 0.0
        opts.x_units = 1 if str(x_units).lower() in ("hours", "time") else 0
        opts.x_format = encode_opt(x_format, keep)
        opts.x_step = float(x_step)
        opts.min = float(min) if min is not None else 0.0
        opts.max = float(max) if max is not None else 0.0
        opts.format = encode_opt(format, keep)
        opts.unit = encode_opt(unit, keep)
        opts.pitch = float(pitch)
        opts.no_grid = bool(no_grid)
        opts.no_axis = bool(no_axis)
        opts.no_readout = bool(no_readout)
        from .._cdefs import chart_annotations

        ann_arr, ann_n, ann_keep = chart_annotations(annotations)
        if ann_n:
            opts.annotations = ann_arr
            opts.annotation_count = ann_n
            keep.append(ann_keep)
        out = CuiDotChartResult()
        keep.extend((arr, opts, out))
        self._lib.nexa_dot_chart_ex(
            self._ctx, encode_str(id, keep), arr, n, int(count if count is not None else longest),
            ctypes.byref(opts), ctypes.byref(out),
        )
        res = DotChartResult(
            hovered=int(out.hovered),
            x=float(out.x),
            value=float(out.value),
            clicked=bool(out.clicked),
        )
        self._record_change(res.clicked)
        return res

    def dot_display(
        self,
        text: str,
        *,
        pitch: float = 0.0,
        color: ColorLike = None,
        accent: bool = False,
        no_dim: bool = False,
        marquee: bool = False,
        align: Align = Align.START,
        width: SizeLike = None,
    ) -> None:
        """Text in a 5x7 dot font, for clocks, counters and status lines."""
        keep = self._frame_keepalive
        opts = CuiDotDisplayOpts()
        opts.pitch = float(pitch)
        opts.color = to_c_color(color)
        opts.accent = bool(accent)
        opts.no_dim = bool(no_dim)
        opts.marquee = bool(marquee)
        opts.align = int(align)
        opts.width = to_c_size(width)
        keep.append(opts)
        self._lib.cui_dot_display_ex(self._ctx, encode_str(text, keep), ctypes.byref(opts))

    def readout(
        self,
        label: str,
        value: str,
        *,
        unit: Optional[str] = None,
        detail: Optional[str] = None,
        size: ControlSize = ControlSize.MD,
        tone: Tone = Tone.NEUTRAL,
        accent: bool = False,
        align: Align = Align.START,
        width: SizeLike = None,
    ) -> None:
        """A label, a figure with its unit on the value's baseline, and a line of context."""
        keep = self._frame_keepalive
        opts = CuiReadoutOpts()
        opts.unit = encode_opt(unit, keep)
        opts.detail = encode_opt(detail, keep)
        opts.size = int(size)
        opts.tone = int(tone)
        opts.accent = bool(accent)
        opts.align = int(align)
        opts.width = to_c_size(width)
        keep.append(opts)
        self._lib.cui_readout_ex(
            self._ctx, encode_str(label, keep), encode_str(value, keep), ctypes.byref(opts)
        )

    # ---- Event track ----

    def event_track(
        self,
        id: str,
        times: List[float],
        *,
        capacity: int = 256,
        min: float = 0.0,
        max: float = 24.0,
        width: SizeLike = None,
        step: float = 0.0,
        units: str = "number",
        format: Optional[str] = None,
        label_step: float = 0.0,
        selected: int = -1,
        no_add: bool = False,
        no_remove: bool = False,
        no_axis: bool = False,
    ) -> EventTrackResult:
        """Moments on a time axis as draggable dots; edits ``times`` in place."""
        keep = self._frame_keepalive
        cap = builtins.max(int(capacity), len(times) + 8)
        buf = (c_double * cap)()
        for i, t in enumerate(times[:cap]):
            buf[i] = float(t)
        c_count = c_int(builtins.min(len(times), cap))
        opts = CuiEventTrackOpts()
        opts.width = to_c_size(width)
        opts.step = float(step)
        opts.units = 1 if str(units).lower() in ("hours", "time") else 0
        opts.format = encode_opt(format, keep)
        opts.label_step = float(label_step)
        c_selected = c_int(int(selected))
        opts.selected = ctypes.cast(ctypes.byref(c_selected), ctypes.POINTER(c_int))
        opts.no_add = bool(no_add)
        opts.no_remove = bool(no_remove)
        opts.no_axis = bool(no_axis)
        out = CuiEventTrackResult()
        keep.extend((buf, c_count, c_selected, opts, out))
        self._lib.nexa_event_track_ex(
            self._ctx, encode_str(id, keep), buf, ctypes.byref(c_count), cap,
            float(min), float(max), ctypes.byref(opts), ctypes.byref(out),
        )
        times[:] = [float(buf[i]) for i in range(builtins.max(0, int(c_count.value)))]
        res = EventTrackResult(
            changed=bool(out.changed),
            added=int(out.added),
            removed=int(out.removed),
            selected=int(c_selected.value) if int(c_selected.value) >= 0 else int(out.selected),
            dragging=bool(out.dragging),
        )
        self._record_change(res.changed)
        return res
