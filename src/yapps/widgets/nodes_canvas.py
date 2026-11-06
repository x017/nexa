"""Node graph editor, custom vector canvas, immediate-mode 2D primitives, and persistent per-id state."""

from __future__ import annotations

import ctypes
from ctypes import c_float, c_int
from typing import Callable, Optional, Sequence, Tuple, Union

from .._cdefs import (
    CanvasTrampFn,
    CuiNodeEditorOpts,
    CuiNodeView,
    CuiVec2,
    encode_str,
    to_c_corners,
    to_c_size,
    to_packed_color,
)
from ..scopes import NodeEditorScope, SimpleScope
from ..types import (
    CanvasResult,
    ColorLike,
    CornersLike,
    FontRole,
    NodeView,
    Rect,
    SizeLike,
    Vec2,
)


def _unpack_xy(p: Union[Vec2, Tuple[float, float]]) -> Tuple[float, float]:
    if isinstance(p, tuple):
        return float(p[0]), float(p[1])
    return float(p.x), float(p.y)


def _unpack_rect(r: Union[Rect, Tuple[float, float, float, float]]) -> Tuple[float, float, float, float]:
    if isinstance(r, tuple):
        return float(r[0]), float(r[1]), float(r[2]), float(r[3])
    return float(r.x), float(r.y), float(r.w), float(r.h)


class NodesCanvasMixin:
    __slots__ = ()

    # ---- Node Graph Editor ----

    def node_editor(
        self,
        id: str,
        view: NodeView,
        *,
        width: SizeLike = None,
        height: SizeLike = None,
        no_grid: bool = False,
        no_minimap: bool = False,
    ) -> NodeEditorScope:
        keep = self._frame_keepalive
        c_view = CuiNodeView(float(view.x), float(view.y), float(view.zoom))
        opts = CuiNodeEditorOpts()
        opts.width = to_c_size(width)
        opts.height = to_c_size(height)
        opts.no_grid = bool(no_grid)
        opts.no_minimap = bool(no_minimap)
        keep.extend((c_view, opts))
        vis = bool(self._lib.cui_node_editor_begin_ex(
            self._ctx, encode_str(id, keep), ctypes.byref(c_view), ctypes.byref(opts)
        ))
        return NodeEditorScope(self, vis, c_view)

    # ---- Custom Canvas & Vector Drawing Primitives ----

    def canvas(
        self,
        id: str,
        width: SizeLike,
        height: SizeLike,
        paint: Optional[Callable[[UI_TYPE, Rect], None]] = None,
    ) -> CanvasResult:
        """Custom-drawn widget box; invokes ``paint(ui, rect)`` after layout with exact bounds."""
        keep = self._frame_keepalive
        sw = to_c_size(width)
        sh = to_c_size(height)
        out_rect = (c_float * 4)()
        out_flags = (c_int * 3)()
        out_mouse = (c_float * 2)()

        if paint is not None:
            slot = len(self._frame_canvas_cbs)
            self._frame_canvas_cbs.append(paint)
            c_fn = self._canvas_trampoline
        else:
            slot = 0
            c_fn = ctypes.cast(None, CanvasTrampFn)

        self._lib.yapps_canvas(
            self._ctx, encode_str(id, keep),
            int(sw.kind), float(sw.value), int(sh.kind), float(sh.value),
            c_fn, slot, out_rect, out_flags, out_mouse
        )
        clicked = bool(out_flags[2])
        self._record_change(clicked)
        return CanvasResult(
            Rect(float(out_rect[0]), float(out_rect[1]), float(out_rect[2]), float(out_rect[3])),
            bool(out_flags[0]),
            bool(out_flags[1]),
            clicked,
            Vec2(float(out_mouse[0]), float(out_mouse[1])),
        )

    def draw_rect(
        self,
        rect: Union[Rect, Tuple[float, float, float, float]],
        fill: ColorLike,
        *,
        radius: CornersLike = 0.0,
    ) -> None:
        x, y, w, h = _unpack_rect(rect)
        c = to_c_corners(radius)
        self._lib.yapps_draw_rect(
            self._ctx, x, y, w, h, c.tl, c.tr, c.br, c.bl, to_packed_color(fill)
        )

    def draw_rect_border(
        self,
        rect: Union[Rect, Tuple[float, float, float, float]],
        fill: ColorLike,
        border_color: ColorLike,
        border_width: float = 1.0,
        *,
        radius: CornersLike = 0.0,
    ) -> None:
        x, y, w, h = _unpack_rect(rect)
        c = to_c_corners(radius)
        self._lib.yapps_draw_rect_border(
            self._ctx, x, y, w, h, c.tl, c.tr, c.br, c.bl,
            to_packed_color(fill), to_packed_color(border_color), float(border_width)
        )

    def draw_rect_gradient(
        self,
        rect: Union[Rect, Tuple[float, float, float, float]],
        top: ColorLike,
        bottom: ColorLike,
        *,
        radius: CornersLike = 0.0,
    ) -> None:
        x, y, w, h = _unpack_rect(rect)
        c = to_c_corners(radius)
        self._lib.yapps_draw_rect_gradient(
            self._ctx, x, y, w, h, c.tl, c.tr, c.br, c.bl,
            to_packed_color(top), to_packed_color(bottom)
        )

    def draw_shadow(
        self,
        rect: Union[Rect, Tuple[float, float, float, float]],
        blur: float,
        *,
        radius: CornersLike = 0.0,
        spread: float = 0.0,
        offset: Union[Vec2, Tuple[float, float]] = (0.0, 2.0),
        color: ColorLike = (0, 0, 0, 64),
    ) -> None:
        x, y, w, h = _unpack_rect(rect)
        ox, oy = _unpack_xy(offset)
        c = to_c_corners(radius)
        self._lib.yapps_draw_shadow(
            self._ctx, x, y, w, h, c.tl, c.tr, c.br, c.bl,
            float(blur), float(spread), ox, oy, to_packed_color(color)
        )

    def draw_line(
        self,
        a: Union[Vec2, Tuple[float, float]],
        b: Union[Vec2, Tuple[float, float]],
        color: ColorLike,
        thickness: float = 1.5,
    ) -> None:
        ax, ay = _unpack_xy(a)
        bx, by = _unpack_xy(b)
        self._lib.yapps_draw_line(self._ctx, ax, ay, bx, by, float(thickness), to_packed_color(color))

    def draw_polyline(
        self,
        points: Sequence[Union[Vec2, Tuple[float, float]]],
        color: ColorLike,
        thickness: float = 1.5,
        *,
        closed: bool = False,
    ) -> None:
        n = len(points)
        if n < 2:
            return
        arr = (c_float * (n * 2))()
        for i, p in enumerate(points):
            arr[i * 2], arr[i * 2 + 1] = _unpack_xy(p)
        self._lib.yapps_draw_polyline(
            self._ctx, arr, n, float(thickness), to_packed_color(color), bool(closed)
        )

    def draw_polygon(
        self,
        points: Sequence[Union[Vec2, Tuple[float, float]]],
        color: ColorLike,
    ) -> None:
        n = len(points)
        if n < 3:
            return
        arr = (c_float * (n * 2))()
        for i, p in enumerate(points):
            arr[i * 2], arr[i * 2 + 1] = _unpack_xy(p)
        self._lib.yapps_draw_polygon(self._ctx, arr, n, to_packed_color(color))

    def draw_circle(
        self,
        center: Union[Vec2, Tuple[float, float]],
        radius: float,
        color: ColorLike,
    ) -> None:
        cx, cy = _unpack_xy(center)
        self._lib.yapps_draw_circle(self._ctx, cx, cy, float(radius), to_packed_color(color))

    def draw_arc(
        self,
        center: Union[Vec2, Tuple[float, float]],
        radius: float,
        angle_start: float,
        angle_end: float,
        color: ColorLike,
        thickness: float = 2.0,
    ) -> None:
        cx, cy = _unpack_xy(center)
        self._lib.yapps_draw_arc(
            self._ctx, cx, cy, float(radius), float(angle_start), float(angle_end),
            float(thickness), to_packed_color(color)
        )

    def draw_text(
        self,
        text: str,
        pos: Union[Vec2, Tuple[float, float]],
        color: ColorLike,
        *,
        size: float = 13.0,
        font: Union[FontRole, int] = FontRole.BODY,
    ) -> None:
        px, py = _unpack_xy(pos)
        raw = text.encode("utf-8")
        self._lib.yapps_draw_text(
            self._ctx, int(font), float(size), px, py, to_packed_color(color), raw, len(raw)
        )

    def draw_icon(
        self,
        icon: str,
        rect: Union[Rect, Tuple[float, float, float, float]],
        color: ColorLike,
        *,
        size: float = 16.0,
    ) -> None:
        x, y, w, h = _unpack_rect(rect)
        self._lib.yapps_draw_icon(
            self._ctx, icon.encode("utf-8"), x, y, w, h, float(size), to_packed_color(color)
        )

    def draw_image(
        self,
        texture: int,
        rect: Union[Rect, Tuple[float, float, float, float]],
        *,
        uv: Union[Rect, Tuple[float, float, float, float]] = (0.0, 0.0, 1.0, 1.0),
        radius: CornersLike = 0.0,
        tint: ColorLike = (255, 255, 255, 255),
    ) -> None:
        x, y, w, h = _unpack_rect(rect)
        u0, v0, u1, v1 = _unpack_rect(uv)
        c = to_c_corners(radius)
        self._lib.yapps_draw_image(
            self._ctx, int(texture), x, y, w, h, u0, v0, u1, v1,
            c.tl, c.tr, c.br, c.bl, to_packed_color(tint)
        )

    def push_clip(self, rect: Union[Rect, Tuple[float, float, float, float]]) -> None:
        x, y, w, h = _unpack_rect(rect)
        self._lib.yapps_push_clip(self._ctx, x, y, w, h)

    def pop_clip(self) -> None:
        self._lib.cui_pop_clip(self._ctx)

    def clip_scope(self, rect: Union[Rect, Tuple[float, float, float, float]]) -> SimpleScope:
        self.push_clip(rect)
        return SimpleScope(self._ctx, self._lib.cui_pop_clip)

    def state_buffer(self, key: Union[str, int], byte_size: int) -> memoryview:
        """Low-level persistent zero-initialized byte buffer managed by CUI per widget ID."""
        cid = int(key) if isinstance(key, int) else self.make_id(key)
        ptr = self._lib.cui_state(self._ctx, cid, int(byte_size))
        if not ptr:
            raise MemoryError("cui_state allocation failed")
        arr_t = ctypes.c_uint8 * int(byte_size)
        return memoryview(arr_t.from_address(int(ptr))).cast("B")


UI_TYPE = object
