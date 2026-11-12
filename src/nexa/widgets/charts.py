"""16 interactive, spring-animated data visualization & chart components."""

from __future__ import annotations

import ctypes
from ctypes import c_float
from typing import Optional, Sequence

from .._cdefs import (
    CuiBarListOpts,
    CuiCandle,
    CuiCandlestickOpts,
    CuiCalendarHeatmapOpts,
    CuiChartOpts,
    CuiFunnelOpts,
    CuiHeatmapOpts,
    CuiRadarOpts,
    CuiRingsOpts,
    CuiSankeyLink,
    CuiSankeyOpts,
    CuiScatterOpts,
    CuiScatterSeries,
    CuiSeries,
    CuiSplitBarOpts,
    CuiTreemapOpts,
    CuiVec2,
    CuiVizItem,
    CuiWaffleOpts,
    encode_opt,
    encode_str,
    encode_str_array,
    to_c_color,
    to_c_size,
    to_packed_color,
)
from ..types import Candle, Color, ColorLike, Date, SankeyLink, ScatterSeries, Series, SizeLike, VizItem


def _build_chart_opts(
    keep: list,
    *,
    width: SizeLike = None,
    height: float = 0.0,
    labels: Optional[Sequence[Optional[str]]] = None,
    area: bool = False,
    no_grid: bool = False,
    no_legend: bool = False,
    stacked: bool = False,
    smooth: bool = False,
    format: Optional[str] = None,
    min_y: float = 0.0,
    max_y: float = 0.0,
    annotations: Sequence[object] = (),
) -> CuiChartOpts:
    opts = CuiChartOpts()
    opts.width = to_c_size(width)
    opts.height = float(height)
    if labels:
        l_arr, l_n = encode_str_array(labels, keep)
        opts.labels = l_arr
        opts.label_count = l_n
    opts.area = bool(area)
    opts.no_grid = bool(no_grid)
    opts.no_legend = bool(no_legend)
    opts.stacked = bool(stacked)
    opts.smooth = bool(smooth)
    opts.format = encode_opt(format, keep)
    opts.min = float(min_y)
    opts.max = float(max_y)
    if annotations:
        from .._cdefs import chart_annotations

        ann_arr, ann_n, ann_keep = chart_annotations(annotations)
        opts.annotations = ann_arr
        opts.annotation_count = ann_n
        keep.append(ann_keep)
    keep.append(opts)
    return opts


def _pack_series(series: Sequence[Series], keep: list):
    n = len(series)
    arr = (CuiSeries * n)()
    for i, s in enumerate(series):
        arr[i].name = encode_str(s.name, keep)
        m = len(s.values)
        vals = (c_float * m)(*(float(v) for v in s.values))
        keep.append(vals)
        arr[i].values = vals
        arr[i].count = m
        arr[i].color = to_c_color(s.color)
    keep.append(arr)
    return arr, n


def _pack_viz_items(items: Sequence[VizItem], keep: list):
    n = len(items)
    arr = (CuiVizItem * n)()
    for i, it in enumerate(items):
        arr[i].label = encode_str(it.label, keep)
        arr[i].value = float(it.value)
        arr[i].color = to_c_color(it.color)
    keep.append(arr)
    return arr, n


class ChartsMixin:
    __slots__ = ()

    def line_chart(self, id: str, series: Sequence[Series], **kwargs) -> None:
        keep = self._frame_keepalive
        arr, n = _pack_series(series, keep)
        opts = _build_chart_opts(keep, **kwargs)
        self._lib.cui_line_chart_ex(self._ctx, encode_str(id, keep), arr, n, ctypes.byref(opts))

    def bar_chart(self, id: str, series: Sequence[Series], **kwargs) -> None:
        keep = self._frame_keepalive
        arr, n = _pack_series(series, keep)
        opts = _build_chart_opts(keep, **kwargs)
        self._lib.cui_bar_chart_ex(self._ctx, encode_str(id, keep), arr, n, ctypes.byref(opts))

    def donut_chart(
        self,
        id: str,
        values: Sequence[float],
        labels: Sequence[str],
        **kwargs,
    ) -> None:
        keep = self._frame_keepalive
        n = min(len(values), len(labels))
        c_vals = (c_float * n)(*(float(values[i]) for i in range(n)))
        c_lbls, _ = encode_str_array(labels[:n], keep)
        opts = _build_chart_opts(keep, **kwargs)
        keep.append(c_vals)
        self._lib.cui_donut_chart_ex(self._ctx, encode_str(id, keep), c_vals, c_lbls, n, ctypes.byref(opts))

    def sparkline(
        self,
        values: Sequence[float],
        *,
        width: SizeLike = 96.0,
        height: float = 28.0,
        color: ColorLike = Color.ACCENT,
    ) -> None:
        keep = self._frame_keepalive
        n = len(values)
        c_vals = (c_float * n)(*(float(v) for v in values))
        keep.append(c_vals)
        sz = to_c_size(width)
        self._lib.nexa_sparkline(
            self._ctx, c_vals, n, int(sz.kind), float(sz.value), float(height), to_packed_color(color)
        )

    def candlestick(
        self,
        id: str,
        candles: Sequence[Candle],
        *,
        width: SizeLike = None,
        height: float = 240.0,
        labels: Optional[Sequence[str]] = None,
        format: Optional[str] = None,
        overlays: Sequence[Series] = (),
        no_volume: bool = False,
        ohlc: bool = False,
        up: ColorLike = None,
        down: ColorLike = None,
    ) -> int:
        """Open/high/low/close chart with volume; returns the candle under the crosshair or -1."""
        keep = self._frame_keepalive
        n = len(candles)
        arr = (CuiCandle * n)()
        for i, candle in enumerate(candles):
            arr[i].open = float(candle.open)
            arr[i].high = float(candle.high)
            arr[i].low = float(candle.low)
            arr[i].close = float(candle.close)
            arr[i].volume = float(candle.volume)
        opts = CuiCandlestickOpts()
        opts.width = to_c_size(width)
        opts.height = float(height)
        if labels:
            l_arr, l_n = encode_str_array(labels, keep)
            opts.labels = l_arr
            opts.label_count = l_n
        opts.format = encode_opt(format, keep)
        if overlays:
            o_arr, o_n = _pack_series(overlays, keep)
            opts.overlays = o_arr
            opts.overlay_count = o_n
        opts.no_volume = bool(no_volume)
        opts.ohlc = bool(ohlc)
        opts.up = to_c_color(up)
        opts.down = to_c_color(down)
        keep.extend((arr, opts))
        idx = int(self._lib.cui_candlestick_ex(self._ctx, encode_str(id, keep), arr, n, ctypes.byref(opts)))
        self._record_change(idx >= 0)
        return idx

    def gauge(self, label: str, value: float, *, size: float = 120.0) -> None:
        self._lib.cui_gauge(self._ctx, encode_str(label, self._frame_keepalive), float(value), float(size))

    def heatmap(
        self,
        id: str,
        values: Sequence[float],
        rows: int,
        cols: int,
        *,
        row_labels: Optional[Sequence[Optional[str]]] = None,
        col_labels: Optional[Sequence[Optional[str]]] = None,
        cell: float = 0.0,
        min_value: float = 0.0,
        max_value: float = 0.0,
        color: ColorLike = None,
        format: Optional[str] = None,
        width: SizeLike = None,
    ) -> int:
        keep = self._frame_keepalive
        expected = int(rows) * int(cols)
        if len(values) < expected:
            raise ValueError(f"heatmap requires at least {expected} values, got {len(values)}")
        c_vals = (c_float * expected)(*(float(values[i]) for i in range(expected)))
        opts = CuiHeatmapOpts()
        if row_labels:
            opts.row_labels, _ = encode_str_array(row_labels, keep)
        if col_labels:
            opts.col_labels, _ = encode_str_array(col_labels, keep)
        opts.cell = float(cell)
        opts.min = float(min_value)
        opts.max = float(max_value)
        opts.color = to_c_color(color)
        opts.format = encode_opt(format, keep)
        opts.width = to_c_size(width)
        keep.extend((c_vals, opts))
        clicked = int(self._lib.cui_heatmap_ex(
            self._ctx, encode_str(id, keep), c_vals, int(rows), int(cols), ctypes.byref(opts)
        ))
        self._record_change(clicked >= 0)
        return clicked

    def calendar_heatmap(
        self,
        id: str,
        start: Date,
        values: Sequence[float],
        *,
        cell: float = 0.0,
        color: ColorLike = None,
        format: Optional[str] = None,
        unit: Optional[str] = None,
    ) -> int:
        keep = self._frame_keepalive
        n = len(values)
        c_vals = (c_float * n)(*(float(v) for v in values))
        opts = CuiCalendarHeatmapOpts()
        opts.cell = float(cell)
        opts.color = to_c_color(color)
        opts.format = encode_opt(format, keep)
        opts.unit = encode_opt(unit, keep)
        keep.extend((c_vals, opts))
        clicked = int(self._lib.nexa_calendar_heatmap(
            self._ctx, encode_str(id, keep), int(start.year), int(start.month), int(start.day),
            c_vals, n, ctypes.byref(opts)
        ))
        self._record_change(clicked >= 0)
        return clicked

    def treemap(
        self,
        id: str,
        items: Sequence[VizItem],
        *,
        width: SizeLike = None,
        height: float = 0.0,
        format: Optional[str] = None,
    ) -> int:
        keep = self._frame_keepalive
        arr, n = _pack_viz_items(items, keep)
        opts = CuiTreemapOpts()
        opts.width = to_c_size(width)
        opts.height = float(height)
        opts.format = encode_opt(format, keep)
        keep.append(opts)
        clicked = int(self._lib.cui_treemap_ex(self._ctx, encode_str(id, keep), arr, n, ctypes.byref(opts)))
        self._record_change(clicked >= 0)
        return clicked

    def radar_chart(
        self,
        id: str,
        series: Sequence[Series],
        axes: Sequence[str],
        *,
        size: float = 0.0,
        max_value: float = 0.0,
        format: Optional[str] = None,
        no_legend: bool = False,
    ) -> int:
        keep = self._frame_keepalive
        s_arr, s_n = _pack_series(series, keep)
        a_arr, a_n = encode_str_array(axes, keep)
        opts = CuiRadarOpts()
        opts.size = float(size)
        opts.max = float(max_value)
        opts.format = encode_opt(format, keep)
        opts.no_legend = bool(no_legend)
        keep.append(opts)
        clicked = int(self._lib.cui_radar_chart_ex(
            self._ctx, encode_str(id, keep), s_arr, s_n, a_arr, a_n, ctypes.byref(opts)
        ))
        self._record_change(clicked >= 0)
        return clicked

    def funnel(
        self,
        id: str,
        stages: Sequence[VizItem],
        *,
        width: SizeLike = None,
        height: float = 0.0,
        format: Optional[str] = None,
        color: ColorLike = None,
    ) -> int:
        keep = self._frame_keepalive
        arr, n = _pack_viz_items(stages, keep)
        opts = CuiFunnelOpts()
        opts.width = to_c_size(width)
        opts.height = float(height)
        opts.format = encode_opt(format, keep)
        opts.color = to_c_color(color)
        keep.append(opts)
        clicked = int(self._lib.cui_funnel_ex(self._ctx, encode_str(id, keep), arr, n, ctypes.byref(opts)))
        self._record_change(clicked >= 0)
        return clicked

    def sankey(
        self,
        id: str,
        nodes: Sequence[str],
        links: Sequence[SankeyLink],
        *,
        width: SizeLike = None,
        height: float = 0.0,
        format: Optional[str] = None,
        node_width: float = 0.0,
    ) -> int:
        keep = self._frame_keepalive
        n_arr, n_cnt = encode_str_array(nodes, keep)
        l_cnt = len(links)
        l_arr = (CuiSankeyLink * l_cnt)()
        for i, lnk in enumerate(links):
            l_arr[i].from_ = int(lnk.source)
            l_arr[i].to = int(lnk.target)
            l_arr[i].value = float(lnk.value)
        opts = CuiSankeyOpts()
        opts.width = to_c_size(width)
        opts.height = float(height)
        opts.format = encode_opt(format, keep)
        opts.node_width = float(node_width)
        keep.extend((l_arr, opts))
        clicked = int(self._lib.cui_sankey_ex(
            self._ctx, encode_str(id, keep), n_arr, n_cnt, l_arr, l_cnt, ctypes.byref(opts)
        ))
        self._record_change(clicked >= 0)
        return clicked

    def waffle(
        self,
        id: str,
        items: Sequence[VizItem],
        *,
        cell: float = 0.0,
        columns: int = 0,
        rows: int = 0,
        format: Optional[str] = None,
    ) -> int:
        keep = self._frame_keepalive
        arr, n = _pack_viz_items(items, keep)
        opts = CuiWaffleOpts()
        opts.cell = float(cell)
        opts.columns = int(columns)
        opts.rows = int(rows)
        opts.format = encode_opt(format, keep)
        keep.append(opts)
        clicked = int(self._lib.cui_waffle_ex(self._ctx, encode_str(id, keep), arr, n, ctypes.byref(opts)))
        self._record_change(clicked >= 0)
        return clicked

    def split_bar(
        self,
        id: str,
        items: Sequence[VizItem],
        *,
        width: SizeLike = None,
        height: float = 0.0,
        format: Optional[str] = None,
        no_legend: bool = False,
    ) -> int:
        keep = self._frame_keepalive
        arr, n = _pack_viz_items(items, keep)
        opts = CuiSplitBarOpts()
        opts.width = to_c_size(width)
        opts.height = float(height)
        opts.format = encode_opt(format, keep)
        opts.no_legend = bool(no_legend)
        keep.append(opts)
        clicked = int(self._lib.cui_split_bar_ex(self._ctx, encode_str(id, keep), arr, n, ctypes.byref(opts)))
        self._record_change(clicked >= 0)
        return clicked

    def bar_list(
        self,
        id: str,
        items: Sequence[VizItem],
        *,
        width: SizeLike = None,
        format: Optional[str] = None,
        max_rows: int = 0,
        keep_order: bool = False,
        color: ColorLike = None,
    ) -> int:
        keep = self._frame_keepalive
        arr, n = _pack_viz_items(items, keep)
        opts = CuiBarListOpts()
        opts.width = to_c_size(width)
        opts.format = encode_opt(format, keep)
        opts.max_rows = int(max_rows)
        opts.keep_order = bool(keep_order)
        opts.color = to_c_color(color)
        keep.append(opts)
        clicked = int(self._lib.cui_bar_list_ex(self._ctx, encode_str(id, keep), arr, n, ctypes.byref(opts)))
        self._record_change(clicked >= 0)
        return clicked

    def activity_rings(
        self,
        id: str,
        rings: Sequence[VizItem],
        *,
        size: float = 0.0,
        thickness: float = 0.0,
        center: Optional[str] = None,
        caption: Optional[str] = None,
        legend: bool = False,
    ) -> int:
        keep = self._frame_keepalive
        arr, n = _pack_viz_items(rings, keep)
        opts = CuiRingsOpts()
        opts.size = float(size)
        opts.thickness = float(thickness)
        opts.center = encode_opt(center, keep)
        opts.caption = encode_opt(caption, keep)
        opts.legend = bool(legend)
        keep.append(opts)
        clicked = int(self._lib.cui_activity_rings_ex(
            self._ctx, encode_str(id, keep), arr, n, ctypes.byref(opts)
        ))
        self._record_change(clicked >= 0)
        return clicked

    def scatter_chart(
        self,
        id: str,
        series: Sequence[ScatterSeries],
        *,
        width: SizeLike = None,
        height: float = 0.0,
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        x_format: Optional[str] = None,
        y_format: Optional[str] = None,
        no_legend: bool = False,
    ) -> int:
        keep = self._frame_keepalive
        ns = len(series)
        arr = (CuiScatterSeries * ns)()
        for i, s in enumerate(series):
            arr[i].name = encode_str(s.name, keep)
            m = len(s.points)
            pts = (CuiVec2 * m)()
            for j, p in enumerate(s.points):
                if isinstance(p, tuple):
                    pts[j].x, pts[j].y = float(p[0]), float(p[1])
                else:
                    pts[j].x, pts[j].y = float(p.x), float(p.y)
            keep.append(pts)
            arr[i].points = pts
            if s.sizes:
                sz_arr = (c_float * m)(*(float(s.sizes[j]) for j in range(m)))
                keep.append(sz_arr)
                arr[i].sizes = sz_arr
            arr[i].count = m
            arr[i].color = to_c_color(s.color)
        opts = CuiScatterOpts()
        opts.width = to_c_size(width)
        opts.height = float(height)
        opts.x_label = encode_opt(x_label, keep)
        opts.y_label = encode_opt(y_label, keep)
        opts.x_format = encode_opt(x_format, keep)
        opts.y_format = encode_opt(y_format, keep)
        opts.no_legend = bool(no_legend)
        keep.extend((arr, opts))
        clicked = int(self._lib.cui_scatter_chart_ex(
            self._ctx, encode_str(id, keep), arr, ns, ctypes.byref(opts)
        ))
        self._record_change(clicked >= 0)
        return clicked
