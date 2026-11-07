"""Developer & editor tools: property inspector, typed property editors, and ring-buffer log console."""

from __future__ import annotations

import ctypes
import threading
import time
from ctypes import c_bool, c_char_p, c_double, c_float, c_int, c_uint8, c_uint32
from typing import List, Optional, Sequence, Tuple, Union

from .._cdefs import (
    CuiCurveKey,
    CuiCurveOpts,
    CuiCurveResult,
    CuiFlameOpts,
    CuiFlameResult,
    CuiFlameSpan,
    CuiFlameView,
    CuiGradientOpts,
    CuiGradientResult,
    CuiGradientStop,
    CuiHexRange,
    CuiHexResult,
    CuiHexSelection,
    CuiHexViewOpts,
    CuiInspectorOpts,
    CuiLogViewOpts,
    CuiPropOpts,
    CuiTimelineClip,
    CuiTimelineEditorOpts,
    CuiTimelineEditorResult,
    CuiTimelineTrack,
    CuiTimelineView,
    encode_opt,
    encode_str,
    encode_str_array,
    make_text_buffer,
    to_c_color,
    to_c_size,
    to_packed_color,
)
from .._lib import get_cdll
from ..scopes import ConditionalScope
from ..types import (
    Color,
    ColorLike,
    CurveKey,
    CurveMode,
    CurveResult,
    FlameResult,
    FlameSpan,
    FlameView,
    GradientResult,
    GradientStop,
    HexRange,
    HexResult,
    HexSelection,
    LogLevel,
    Rect,
    Size,
    SizeKind,
    SizeLike,
    TimelineClip,
    TimelineEditorResult,
    TimelineRuler,
    TimelineTrack,
    TimelineView,
)


def flame_sort(spans: List[FlameSpan]) -> List[FlameSpan]:
    """Sort ``spans`` in-place by ``(depth, start)`` via CUI's C99 ``cui_flame_sort``."""
    n = len(spans)
    if n <= 1:
        return spans
    lib = get_cdll()
    keep: list = []
    c_spans = (CuiFlameSpan * n)()
    for i, sp in enumerate(spans):
        c_spans[i].name = encode_str(sp.name, keep)
        c_spans[i].start = float(sp.start)
        c_spans[i].end = float(sp.end)
        c_spans[i].depth = int(sp.depth)
        c_spans[i].color_key = int(sp.color_key) & 0xFFFFFFFF
    lib.cui_flame_sort(c_spans, n)
    spans[:] = [
        FlameSpan(
            c_spans[i].name.decode("utf-8", errors="replace") if c_spans[i].name else "",
            float(c_spans[i].start),
            float(c_spans[i].end),
            int(c_spans[i].depth),
            int(c_spans[i].color_key),
        )
        for i in range(n)
    ]
    return spans


def curve_eval(keys: Sequence[CurveKey], x: float) -> float:
    """Evaluate cubic Bezier / linear / step keyframe curve at ``x`` via C99 ``cui_curve_eval``."""
    n = len(keys)
    if n == 0:
        return 0.0
    lib = get_cdll()
    c_keys = (CuiCurveKey * n)()
    for i, k in enumerate(keys):
        c_keys[i].x = float(k.x)
        c_keys[i].y = float(k.y)
        c_keys[i].in_dx = float(k.in_dx)
        c_keys[i].in_dy = float(k.in_dy)
        c_keys[i].out_dx = float(k.out_dx)
        c_keys[i].out_dy = float(k.out_dy)
        c_keys[i].mode = int(k.mode)
    return float(lib.cui_curve_eval(c_keys, n, float(x)))


def gradient_eval(stops: Sequence[GradientStop], t: float) -> Color:
    """Evaluate perceptual OKLab color ramp at ``t`` in ``[0, 1]`` via C99 ``cui_gradient_eval``."""
    n = len(stops)
    if n == 0:
        return Color(0, 0, 0, 255)
    lib = get_cdll()
    c_stops = (CuiGradientStop * n)()
    for i, st in enumerate(stops):
        c_stops[i].pos = float(st.pos)
        c_stops[i].color = to_c_color(st.color)
    packed = int(lib.nexa_gradient_eval(c_stops, n, float(t)))
    return Color._from_packed(packed)


class LogBuffer:
    """Zero-allocation C-backed ring buffer for ``ui.log_view(...)``.

    Thread-safe: ``append`` / ``info`` / ``warn`` / ``error`` can be called from
    any background thread or ``asyncio`` task!
    """

    __slots__ = ("_lib", "_handle", "_t0", "_lock")

    def __init__(self, max_lines: int = 4096, text_bytes: int = 256 * 1024) -> None:
        self._lib = get_cdll()
        self._handle = self._lib.nexa_log_create(max(16, int(max_lines)), max(1024, int(text_bytes)))
        if not self._handle:
            raise MemoryError("nexa_log_create failed")
        self._t0 = time.monotonic()
        self._lock = threading.Lock()

    def close(self) -> None:
        if self._handle:
            self._lib.nexa_log_destroy(self._handle)
            self._handle = None

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def append(self, level: LogLevel, message: str, timestamp: Optional[float] = None) -> None:
        raw = message.encode("utf-8", errors="replace")
        ts = float(timestamp) if timestamp is not None else (time.monotonic() - self._t0)
        with self._lock:
            if self._handle:
                self._lib.cui_log_append_text(self._handle, int(level), ts, raw, len(raw))

    def trace(self, message: str) -> None:
        self.append(LogLevel.TRACE, message)

    def debug(self, message: str) -> None:
        self.append(LogLevel.DEBUG, message)

    def info(self, message: str) -> None:
        self.append(LogLevel.INFO, message)

    def warn(self, message: str) -> None:
        self.append(LogLevel.WARN, message)

    def error(self, message: str) -> None:
        self.append(LogLevel.ERROR, message)

    def clear(self) -> None:
        with self._lock:
            if self._handle:
                self._lib.cui_log_clear(self._handle)

    def __len__(self) -> int:
        with self._lock:
            return int(self._lib.nexa_log_count(self._handle)) if self._handle else 0

    @property
    def total_appended(self) -> int:
        with self._lock:
            return int(self._lib.nexa_log_total(self._handle)) if self._handle else 0

    def get_line(self, index: int) -> Optional[Tuple[LogLevel, float, str]]:
        with self._lock:
            if not self._handle:
                return None
            t_out = c_double(0.0)
            lvl_out = c_int(0)
            txt_out = c_char_p()
            len_out = c_int(0)
            ok = bool(self._lib.nexa_log_line_at(
                self._handle, int(index), ctypes.byref(t_out),
                ctypes.byref(lvl_out), ctypes.byref(txt_out), ctypes.byref(len_out)
            ))
            if not ok:
                return None
            text = ctypes.string_at(txt_out, int(len_out.value)).decode("utf-8", errors="replace") if txt_out.value else ""
            return LogLevel(int(lvl_out.value)), float(t_out.value), text


def _build_prop_opts(
    keep: list,
    *,
    min: float = 0.0,
    max: float = 0.0,
    step: float = 0.0,
    format: Optional[str] = None,
    suffix: Optional[str] = None,
    placeholder: Optional[str] = None,
    tooltip: Optional[str] = None,
    disabled: bool = False,
    checkbox: bool = False,
) -> CuiPropOpts:
    opts = CuiPropOpts()
    opts.min = float(min)
    opts.max = float(max)
    opts.step = float(step)
    opts.format = encode_opt(format, keep)
    opts.suffix = encode_opt(suffix, keep)
    opts.placeholder = encode_opt(placeholder, keep)
    opts.tooltip = encode_opt(tooltip, keep)
    opts.disabled = bool(disabled)
    opts.checkbox = bool(checkbox)
    keep.append(opts)
    return opts


class ToolsMixin:
    __slots__ = ()

    def inspector(
        self,
        id: str,
        *,
        width: SizeLike = None,
        label_width: float = 0.0,
    ) -> ConditionalScope:
        keep = self._frame_keepalive
        opts = CuiInspectorOpts()
        opts.width = to_c_size(width)
        opts.label_width = float(label_width)
        keep.append(opts)
        vis = bool(self._lib.cui_inspector_begin_ex(self._ctx, encode_str(id, keep), ctypes.byref(opts)))
        return ConditionalScope(self._ctx, self._lib.cui_inspector_end, vis)

    def inspector_group(self, title: str, is_open: Optional[bool] = None) -> Tuple[bool, bool]:
        """Inspector section header; returns ``(visible, is_open)``."""
        keep = self._frame_keepalive
        if is_open is None:
            vis = bool(self._lib.cui_inspector_group(self._ctx, encode_str(title, keep), None))
            return vis, True
        c_open = c_bool(bool(is_open))
        vis = bool(self._lib.cui_inspector_group(self._ctx, encode_str(title, keep), ctypes.byref(c_open)))
        new_open = bool(c_open.value)
        self._record_change(new_open != is_open)
        return vis, new_open

    def prop_float(self, label: str, value: float, **kwargs) -> float:
        keep = self._frame_keepalive
        c_val = c_float(float(value))
        opts = _build_prop_opts(keep, **kwargs)
        changed = bool(self._lib.cui_prop_float_ex(
            self._ctx, encode_str(label, keep), ctypes.byref(c_val), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return float(c_val.value)

    def prop_int(self, label: str, value: int, **kwargs) -> int:
        keep = self._frame_keepalive
        c_val = c_int(int(value))
        opts = _build_prop_opts(keep, **kwargs)
        changed = bool(self._lib.cui_prop_int_ex(
            self._ctx, encode_str(label, keep), ctypes.byref(c_val), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return int(c_val.value)

    def prop_text(self, label: str, value: str, *, max_bytes: int = 256, **kwargs) -> str:
        keep = self._frame_keepalive
        buf, cap = make_text_buffer(value, max_bytes)
        opts = _build_prop_opts(keep, **kwargs)
        changed = bool(self._lib.cui_prop_text_ex(
            self._ctx, encode_str(label, keep), buf, cap, ctypes.byref(opts)
        ))
        self._record_change(changed)
        return buf.value.decode("utf-8", errors="replace") if changed else value

    def prop_bool(self, label: str, value: bool, **kwargs) -> bool:
        keep = self._frame_keepalive
        c_val = c_bool(bool(value))
        opts = _build_prop_opts(keep, **kwargs)
        changed = bool(self._lib.cui_prop_bool_ex(
            self._ctx, encode_str(label, keep), ctypes.byref(c_val), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return bool(c_val.value)

    def prop_enum(self, label: str, items: Sequence[str], index: int, **kwargs) -> int:
        keep = self._frame_keepalive
        arr, n = encode_str_array(items, keep)
        c_idx = c_int(int(index))
        opts = _build_prop_opts(keep, **kwargs)
        changed = bool(self._lib.cui_prop_enum_ex(
            self._ctx, encode_str(label, keep), arr, n, ctypes.byref(c_idx), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return int(c_idx.value)

    def prop_color(self, label: str, value: ColorLike, **kwargs) -> Color:
        keep = self._frame_keepalive
        c_col = c_uint32(to_packed_color(value))
        opts = _build_prop_opts(keep, **kwargs)
        changed = bool(self._lib.nexa_prop_color(
            self._ctx, encode_str(label, keep), ctypes.byref(c_col), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return Color._from_packed(int(c_col.value))

    def prop_vec(self, label: str, values: Sequence[float], **kwargs) -> Tuple[float, ...]:
        keep = self._frame_keepalive
        n = len(values)
        if n not in (2, 3, 4):
            raise ValueError(f"prop_vec requires 2, 3, or 4 components, got {n}")
        c_vec = (c_float * n)(*(float(v) for v in values))
        opts = _build_prop_opts(keep, **kwargs)
        changed = bool(self._lib.cui_prop_vec_ex(
            self._ctx, encode_str(label, keep), c_vec, n, ctypes.byref(opts)
        ))
        self._record_change(changed)
        return tuple(float(c_vec[i]) for i in range(n))

    def prop_vec2(self, label: str, xy: Tuple[float, float], **kwargs) -> Tuple[float, float]:
        r = self.prop_vec(label, xy, **kwargs)
        return (r[0], r[1])

    def prop_vec3(self, label: str, xyz: Tuple[float, float, float], **kwargs) -> Tuple[float, float, float]:
        r = self.prop_vec(label, xyz, **kwargs)
        return (r[0], r[1], r[2])

    def prop_vec4(
        self, label: str, xyzw: Tuple[float, float, float, float], **kwargs
    ) -> Tuple[float, float, float, float]:
        r = self.prop_vec(label, xyzw, **kwargs)
        return (r[0], r[1], r[2], r[3])

    def log_view(
        self,
        id: str,
        buffer: LogBuffer,
        *,
        width: SizeLike = None,
        height: SizeLike = 320.0,
        timestamps: bool = False,
        no_toolbar: bool = False,
        size: float = 0.0,
    ) -> None:
        keep = self._frame_keepalive
        opts = CuiLogViewOpts()
        opts.width = to_c_size(width)
        if height is None:
            opts.height = 320.0
        elif isinstance(height, Size):
            opts.height = -1.0 if height.kind in (SizeKind.GROW, SizeKind.PERCENT) else float(height.value)
        else:
            opts.height = float(height)
        opts.timestamps = bool(timestamps)
        opts.no_toolbar = bool(no_toolbar)
        opts.size = float(size)
        keep.extend((buffer, opts))
        with buffer._lock:
            if buffer._handle:
                self._lib.cui_log_view_ex(
                    self._ctx, encode_str(id, keep), buffer._handle, ctypes.byref(opts)
                )

    # ---- CUI 1.1.0: Hex Viewer, Flame Graph, Curves, Gradient & Timeline ----

    def hex_view(
        self,
        id: str,
        data: Union[bytes, bytearray, memoryview],
        selection: Optional[HexSelection] = None,
        *,
        width: SizeLike = None,
        height: float = 280.0,
        base: int = 0,
        bytes_per_row: int = 16,
        ranges: Optional[Sequence[HexRange]] = None,
        editable: bool = False,
        no_ascii: bool = False,
        no_header: bool = False,
        size: float = 0.0,
    ) -> HexResult:
        """Virtualized hex + ASCII inspector/editor.

        Pass a mutable ``bytearray`` with ``editable=True`` for zero-copy in-place nibble/ASCII edits.
        """
        keep = self._frame_keepalive
        nbytes = len(data)
        c_buf = (c_uint8 * max(nbytes, 1))()
        if nbytes > 0:
            ctypes.memmove(c_buf, bytes(data) if not isinstance(data, bytes) else data, nbytes)

        c_sel = None
        if selection is not None:
            c_sel = CuiHexSelection(int(selection.start), int(selection.length), int(selection.cursor))
            keep.append(c_sel)

        opts = CuiHexViewOpts()
        opts.width = to_c_size(width)
        opts.height = float(height)
        opts.base = int(base) & 0xFFFFFFFFFFFFFFFF
        opts.bytes_per_row = int(bytes_per_row)
        opts.no_ascii = bool(no_ascii)
        opts.no_header = bool(no_header)
        opts.size = float(size)
        if editable and nbytes > 0:
            opts.edit = c_buf

        if ranges:
            nr = len(ranges)
            c_ranges = (CuiHexRange * nr)()
            for i, rg in enumerate(ranges):
                c_ranges[i].offset = int(rg.offset)
                c_ranges[i].length = int(rg.length)
                c_ranges[i].tone = int(rg.tone)
                c_ranges[i].label = encode_opt(rg.label, keep)
            opts.ranges = c_ranges
            opts.range_count = nr
            keep.append(c_ranges)

        out = CuiHexResult()
        keep.extend((c_buf, opts, out))
        self._lib.nexa_hex_view_ex(
            self._ctx,
            encode_str(id, keep),
            ctypes.cast(c_buf, ctypes.c_void_p) if nbytes > 0 else None,
            nbytes,
            ctypes.byref(c_sel) if c_sel is not None else None,
            ctypes.byref(opts),
            ctypes.byref(out),
        )
        if bool(out.edited) and editable and isinstance(data, (bytearray, memoryview)) and nbytes > 0:
            data[:] = bytes(c_buf)[:nbytes]
        new_sel = HexSelection(
            int(out.selection.start), int(out.selection.length), int(out.selection.cursor)
        )
        if selection is not None:
            selection.start = new_sel.start
            selection.length = new_sel.length
            selection.cursor = new_sel.cursor
        res = HexResult(
            selection=new_sel,
            selection_changed=bool(out.selection_changed),
            edited=bool(out.edited),
            edit_offset=int(out.edit_offset),
            edit_length=int(out.edit_length),
            hovered=int(out.hovered),
            copied=bool(out.copied),
        )
        self._record_change(bool(res))
        return res

    def hex_view_goto(self, id: str, offset: int) -> None:
        keep = self._frame_keepalive
        self._lib.cui_hex_view_goto(self._ctx, encode_str(id, keep), int(offset))

    def flame_graph(
        self,
        id: str,
        spans: Sequence[FlameSpan],
        *,
        view: Optional[FlameView] = None,
        selected: Optional[int] = None,
        width: SizeLike = None,
        height: float = 240.0,
        row_height: float = 0.0,
        min_range: float = 0.0,
    ) -> FlameResult:
        """Interactive profiler flame graph / icicle chart with wheel zoom, drag pan, and span selection."""
        keep = self._frame_keepalive
        n = len(spans)
        c_spans = (CuiFlameSpan * max(n, 1))()
        for i, sp in enumerate(spans):
            c_spans[i].name = encode_str(sp.name, keep)
            c_spans[i].start = float(sp.start)
            c_spans[i].end = float(sp.end)
            c_spans[i].depth = int(sp.depth)
            c_spans[i].color_key = int(sp.color_key) & 0xFFFFFFFF

        c_view = CuiFlameView(
            float(view.start) if view is not None else 0.0,
            float(view.end) if view is not None else 0.0,
            float(view.scroll) if view is not None else 0.0,
        )
        c_sel = c_int(int(selected) if selected is not None else -1)
        opts = CuiFlameOpts()
        opts.width = to_c_size(width)
        opts.height = float(height)
        opts.row_height = float(row_height)
        opts.min_range = float(min_range)
        out = CuiFlameResult()
        keep.extend((c_spans, c_view, c_sel, opts, out))
        self._lib.nexa_flame_graph_ex(
            self._ctx,
            encode_str(id, keep),
            c_spans if n > 0 else None,
            n,
            ctypes.byref(c_view) if view is not None else None,
            ctypes.byref(c_sel),
            ctypes.byref(opts),
            ctypes.byref(out),
        )
        new_view = FlameView(float(c_view.start), float(c_view.end), float(c_view.scroll))
        if view is not None:
            view.start = new_view.start
            view.end = new_view.end
            view.scroll = new_view.scroll
        res = FlameResult(
            selected=int(c_sel.value),
            view=new_view,
            selection_changed=bool(out.selection_changed),
            view_changed=bool(out.view_changed),
            hovered=int(out.hovered),
            zoomed=int(out.zoomed),
        )
        self._record_change(bool(res))
        return res

    def flame_sort(self, spans: List[FlameSpan]) -> List[FlameSpan]:
        return flame_sort(spans)

    def flame_span_rect(self, flame_id: int, span: FlameSpan) -> Rect:
        keep = self._frame_keepalive
        c_sp = CuiFlameSpan(
            encode_str(span.name, keep),
            float(span.start),
            float(span.end),
            int(span.depth),
            int(span.color_key) & 0xFFFFFFFF,
        )
        out4 = (c_float * 4)()
        self._lib.nexa_flame_span_rect(self._ctx, int(flame_id) & 0xFFFFFFFF, ctypes.byref(c_sp), out4)
        return Rect(float(out4[0]), float(out4[1]), float(out4[2]), float(out4[3]))

    def curve_editor(
        self,
        id: str,
        keys: Sequence[CurveKey],
        *,
        capacity: int = 64,
        x_min: float = 0.0,
        x_max: float = 1.0,
        y_min: float = 0.0,
        y_max: float = 1.0,
        width: SizeLike = None,
        height: float = 200.0,
        x_format: Optional[str] = None,
        y_format: Optional[str] = None,
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        selected: Optional[int] = None,
        snap: bool = False,
        show_playhead: bool = False,
        playhead: float = 0.0,
    ) -> CurveResult:
        """2D Bezier / linear / step curve editor; updates ``keys`` in-place if a ``list`` is passed."""
        keep = self._frame_keepalive
        n = len(keys)
        cap = max(int(capacity), n + 8)
        c_keys = (CuiCurveKey * cap)()
        for i, k in enumerate(keys):
            c_keys[i].x = float(k.x)
            c_keys[i].y = float(k.y)
            c_keys[i].in_dx = float(k.in_dx)
            c_keys[i].in_dy = float(k.in_dy)
            c_keys[i].out_dx = float(k.out_dx)
            c_keys[i].out_dy = float(k.out_dy)
            c_keys[i].mode = int(k.mode)
        c_count = c_int(n)
        opts = CuiCurveOpts()
        opts.x_min = float(x_min)
        opts.x_max = float(x_max)
        opts.y_min = float(y_min)
        opts.y_max = float(y_max)
        opts.width = to_c_size(width)
        opts.height = float(height)
        opts.x_format = encode_opt(x_format, keep)
        opts.y_format = encode_opt(y_format, keep)
        opts.x_label = encode_opt(x_label, keep)
        opts.y_label = encode_opt(y_label, keep)
        opts.snap = bool(snap)
        opts.show_playhead = bool(show_playhead)
        opts.playhead = float(playhead)
        if selected is not None:
            c_sel = c_int(int(selected))
            opts.selected = ctypes.pointer(c_sel)
            keep.append(c_sel)

        out = CuiCurveResult()
        keep.extend((c_keys, c_count, opts, out))
        self._lib.nexa_curve_editor_ex(
            self._ctx, encode_str(id, keep), c_keys, ctypes.byref(c_count), cap, ctypes.byref(opts), ctypes.byref(out)
        )
        new_n = max(0, min(cap, int(c_count.value)))
        new_keys = [
            CurveKey(
                float(c_keys[i].x),
                float(c_keys[i].y),
                float(c_keys[i].in_dx),
                float(c_keys[i].in_dy),
                float(c_keys[i].out_dx),
                float(c_keys[i].out_dy),
                CurveMode(int(c_keys[i].mode)),
            )
            for i in range(new_n)
        ]
        if bool(out.changed) and isinstance(keys, list):
            keys[:] = new_keys
        self._record_change(bool(out.changed))
        return CurveResult(
            keys=new_keys,
            changed=bool(out.changed),
            added=int(out.added),
            removed=int(out.removed),
            selected=int(out.selected),
            hovered=bool(out.hovered),
            hover_x=float(out.hover_x),
            hover_y=float(out.hover_y),
        )

    def curve_eval(self, keys: Sequence[CurveKey], x: float) -> float:
        return curve_eval(keys, x)

    def gradient_editor(
        self,
        id: str,
        stops: Sequence[GradientStop],
        *,
        capacity: int = 32,
        width: SizeLike = None,
        height: float = 0.0,
        selected: Optional[int] = None,
    ) -> GradientResult:
        """OKLab multi-stop color ramp editor; updates ``stops`` in-place if a ``list`` is passed."""
        keep = self._frame_keepalive
        n = len(stops)
        cap = max(int(capacity), n + 8)
        c_stops = (CuiGradientStop * cap)()
        for i, st in enumerate(stops):
            c_stops[i].pos = float(st.pos)
            c_stops[i].color = to_c_color(st.color)
        c_count = c_int(n)
        opts = CuiGradientOpts()
        opts.width = to_c_size(width)
        opts.height = float(height)
        if selected is not None:
            c_sel = c_int(int(selected))
            opts.selected = ctypes.pointer(c_sel)
            keep.append(c_sel)

        out = CuiGradientResult()
        keep.extend((c_stops, c_count, opts, out))
        self._lib.nexa_gradient_editor_ex(
            self._ctx, encode_str(id, keep), c_stops, ctypes.byref(c_count), cap, ctypes.byref(opts), ctypes.byref(out)
        )
        new_n = max(0, min(cap, int(c_count.value)))
        new_stops = [
            GradientStop(
                float(c_stops[i].pos),
                Color(int(c_stops[i].color.r), int(c_stops[i].color.g), int(c_stops[i].color.b), int(c_stops[i].color.a)),
            )
            for i in range(new_n)
        ]
        if bool(out.changed) and isinstance(stops, list):
            stops[:] = new_stops
        self._record_change(bool(out.changed))
        return GradientResult(
            stops=new_stops,
            changed=bool(out.changed),
            added=int(out.added),
            removed=int(out.removed),
            selected=int(out.selected),
        )

    def gradient_eval(self, stops: Sequence[GradientStop], t: float) -> Color:
        return gradient_eval(stops, t)

    def timeline_editor(
        self,
        id: str,
        tracks: Sequence[TimelineTrack],
        time: float = 0.0,
        *,
        start: float = 0.0,
        end: float = 10.0,
        fps: float = 30.0,
        ruler: TimelineRuler = TimelineRuler.SECONDS,
        view: Optional[TimelineView] = None,
        in_point: Optional[float] = None,
        out_point: Optional[float] = None,
        current_track: Optional[int] = None,
        current_key: Optional[int] = None,
        width: SizeLike = None,
        height: float = 260.0,
        row_height: float = 0.0,
        track_width: float = 0.0,
        toggles: bool = True,
        free_drag: bool = False,
        key_headroom: int = 16,
    ) -> TimelineEditorResult:
        """Multi-track keyframe dope sheet & NLE clip timeline editor.

        Synchronizes track toggles, keyframe edits/additions/deletions, and clip trims back into ``tracks``.
        """
        keep = self._frame_keepalive
        nt = len(tracks)
        c_tracks = (CuiTimelineTrack * max(nt, 1))()
        track_buffers = []

        for i, tr in enumerate(tracks):
            c_tracks[i].name = encode_str(tr.name, keep)
            c_tracks[i].icon = encode_opt(tr.icon, keep)
            c_tracks[i].depth = int(tr.depth)
            c_tracks[i].collapsed = bool(tr.collapsed)
            c_tracks[i].muted = bool(tr.muted)
            c_tracks[i].locked = bool(tr.locked)
            c_tracks[i].color = int(tr.color) & 0xFF

            nk = len(tr.keys)
            kcap = max(nk + max(4, int(key_headroom)), 8)
            c_keys = (CuiCurveKey * kcap)()
            for ki, k in enumerate(tr.keys):
                c_keys[ki].x = float(k.x)
                c_keys[ki].y = float(k.y)
                c_keys[ki].in_dx = float(k.in_dx)
                c_keys[ki].in_dy = float(k.in_dy)
                c_keys[ki].out_dx = float(k.out_dx)
                c_keys[ki].out_dy = float(k.out_dy)
                c_keys[ki].mode = int(k.mode)
            c_tracks[i].keys = c_keys
            c_tracks[i].key_count = nk
            c_tracks[i].key_capacity = kcap

            c_ksel = None
            if tr.key_selected is not None:
                c_ksel = (c_bool * kcap)(
                    *(bool(tr.key_selected[ki]) if ki < len(tr.key_selected) else False for ki in range(kcap))
                )
                c_tracks[i].key_selected = c_ksel

            nc = len(tr.clips)
            c_clips = None
            if nc > 0:
                c_clips = (CuiTimelineClip * nc)()
                for ci, cl in enumerate(tr.clips):
                    c_clips[ci].start = float(cl.start)
                    c_clips[ci].end = float(cl.end)
                    c_clips[ci].offset = float(cl.offset)
                    c_clips[ci].name = encode_opt(cl.name, keep)
                    c_clips[ci].selected = bool(cl.selected)
                c_tracks[i].clips = c_clips
                c_tracks[i].clip_count = nc

            track_buffers.append((c_keys, kcap, c_ksel, c_clips))
            keep.extend((c_keys, c_ksel, c_clips))

        c_time = c_float(float(time))
        opts = CuiTimelineEditorOpts()
        opts.start = float(start)
        opts.end = float(end)
        opts.fps = float(fps)
        opts.ruler = int(ruler)
        opts.width = to_c_size(width)
        opts.height = float(height)
        opts.row_height = float(row_height)
        opts.track_width = float(track_width)
        opts.toggles = bool(toggles)
        opts.free_drag = bool(free_drag)

        c_view = None
        if view is not None:
            c_view = CuiTimelineView(float(view.start), float(view.end), float(view.scroll))
            opts.view = ctypes.pointer(c_view)
            keep.append(c_view)

        c_in = None
        if in_point is not None:
            c_in = c_float(float(in_point))
            opts.in_ = ctypes.pointer(c_in)
            keep.append(c_in)

        c_out = None
        if out_point is not None:
            c_out = c_float(float(out_point))
            opts.out = ctypes.pointer(c_out)
            keep.append(c_out)

        if current_track is not None:
            c_ct = c_int(int(current_track))
            opts.current_track = ctypes.pointer(c_ct)
            keep.append(c_ct)

        if current_key is not None:
            c_ck = c_int(int(current_key))
            opts.current_key = ctypes.pointer(c_ck)
            keep.append(c_ck)

        out = CuiTimelineEditorResult()
        keep.extend((c_tracks, c_time, opts, out))
        self._lib.nexa_timeline_editor_ex(
            self._ctx,
            encode_str(id, keep),
            c_tracks if nt > 0 else None,
            nt,
            ctypes.byref(c_time),
            ctypes.byref(opts),
            ctypes.byref(out),
        )

        # Write back track state
        for i, tr in enumerate(tracks):
            c_keys, kcap, c_ksel, c_clips = track_buffers[i]
            tr.collapsed = bool(c_tracks[i].collapsed)
            tr.muted = bool(c_tracks[i].muted)
            tr.locked = bool(c_tracks[i].locked)
            new_nk = max(0, min(kcap, int(c_tracks[i].key_count)))
            tr.keys = [
                CurveKey(
                    float(c_keys[ki].x),
                    float(c_keys[ki].y),
                    float(c_keys[ki].in_dx),
                    float(c_keys[ki].in_dy),
                    float(c_keys[ki].out_dx),
                    float(c_keys[ki].out_dy),
                    CurveMode(int(c_keys[ki].mode)),
                )
                for ki in range(new_nk)
            ]
            if c_ksel is not None:
                tr.key_selected = [bool(c_ksel[ki]) for ki in range(new_nk)]
            if c_clips is not None:
                new_nc = max(0, min(len(tr.clips), int(c_tracks[i].clip_count)))
                tr.clips = [
                    TimelineClip(
                        float(c_clips[ci].start),
                        float(c_clips[ci].end),
                        float(c_clips[ci].offset),
                        c_clips[ci].name.decode("utf-8", errors="replace") if c_clips[ci].name else None,
                        bool(c_clips[ci].selected),
                    )
                    for ci in range(new_nc)
                ]

        new_view = None
        if c_view is not None and view is not None:
            new_view = TimelineView(float(c_view.start), float(c_view.end), float(c_view.scroll))
            view.start = new_view.start
            view.end = new_view.end
            view.scroll = new_view.scroll

        res = TimelineEditorResult(
            float(c_time.value),
            changed=bool(out.changed),
            time_changed=bool(out.time_changed),
            scrubbing=bool(out.scrubbing),
            play_toggled=bool(out.play_toggled),
            selection_changed=bool(out.selection_changed),
            view_changed=bool(out.view_changed),
            keys_moved=bool(out.keys_moved),
            added_track=int(out.added_track),
            added_key=int(out.added_key),
            removed_keys=int(out.removed_keys),
            removed_clips=int(out.removed_clips),
            clip_track=int(out.clip_track),
            clip=int(out.clip),
            toggled=int(out.toggled),
            current_track=int(out.current_track),
            current_key=int(out.current_key),
            hovered_track=int(out.hovered_track),
            hovered_key=int(out.hovered_key),
            view=new_view,
            in_point=float(c_in.value) if c_in is not None else None,
            out_point=float(c_out.value) if c_out is not None else None,
        )
        self._record_change(bool(res))
        return res
