"""Node graph editor, custom vector canvas, immediate-mode 2D primitives, and persistent per-id state."""

from __future__ import annotations

import ctypes
from ctypes import c_bool, c_float, c_int
from typing import Callable, Optional, Sequence, Tuple, Union

from .._cdefs import (
    CanvasTrampFn,
    CuiCanvasControlsOpts,
    CuiCanvasToggle,
    CuiLiveCursorsOpts,
    CuiLiveUser,
    CuiNodeEditorOpts,
    CuiNodeView,
    CuiPresencePillOpts,
    CuiRect,
    CuiSelectionRingOpts,
    CuiVec2,
    encode_opt,
    encode_str,
    to_c_color,
    to_c_corners,
    to_c_size,
    to_packed_color,
)
from ..scopes import NodeEditorScope, SimpleScope
from ..types import (
    CanvasControlsResult,
    CanvasResult,
    CanvasToggle,
    ColorLike,
    CornersLike,
    FontRole,
    LiveUser,
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

        self._lib.nexa_canvas(
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
        self._lib.nexa_draw_rect(
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
        self._lib.nexa_draw_rect_border(
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
        self._lib.nexa_draw_rect_gradient(
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
        fg: ColorLike = None,
    ) -> None:
        if fg is not None:
            color = fg
        x, y, w, h = _unpack_rect(rect)
        ox, oy = _unpack_xy(offset)
        c = to_c_corners(radius)
        self._lib.nexa_draw_shadow(
            self._ctx, x, y, w, h, c.tl, c.tr, c.br, c.bl,
            float(blur), float(spread), ox, oy, to_packed_color(color)
        )

    def draw_line(
        self,
        a: Union[Vec2, Tuple[float, float]],
        b: Union[Vec2, Tuple[float, float]],
        color: ColorLike,
        thickness: float = 1.5,
        *,
        fg: ColorLike = None,
    ) -> None:
        if fg is not None:
            color = fg
        ax, ay = _unpack_xy(a)
        bx, by = _unpack_xy(b)
        self._lib.nexa_draw_line(self._ctx, ax, ay, bx, by, float(thickness), to_packed_color(color))

    def draw_polyline(
        self,
        points: Sequence[Union[Vec2, Tuple[float, float]]],
        color: ColorLike,
        thickness: float = 1.5,
        *,
        closed: bool = False,
        fg: ColorLike = None,
    ) -> None:
        if fg is not None:
            color = fg
        n = len(points)
        if n < 2:
            return
        arr = (c_float * (n * 2))()
        for i, p in enumerate(points):
            arr[i * 2], arr[i * 2 + 1] = _unpack_xy(p)
        self._lib.nexa_draw_polyline(
            self._ctx, arr, n, float(thickness), to_packed_color(color), bool(closed)
        )

    def draw_polygon(
        self,
        points: Sequence[Union[Vec2, Tuple[float, float]]],
        color: ColorLike,
        *,
        fg: ColorLike = None,
    ) -> None:
        if fg is not None:
            color = fg
        n = len(points)
        if n < 3:
            return
        arr = (c_float * (n * 2))()
        for i, p in enumerate(points):
            arr[i * 2], arr[i * 2 + 1] = _unpack_xy(p)
        self._lib.nexa_draw_polygon(self._ctx, arr, n, to_packed_color(color))

    def draw_circle(
        self,
        center: Union[Vec2, Tuple[float, float]],
        radius: float,
        color: ColorLike,
        *,
        fg: ColorLike = None,
    ) -> None:
        if fg is not None:
            color = fg
        cx, cy = _unpack_xy(center)
        self._lib.nexa_draw_circle(self._ctx, cx, cy, float(radius), to_packed_color(color))

    def draw_arc(
        self,
        center: Union[Vec2, Tuple[float, float]],
        radius: float,
        angle_start: float,
        angle_end: float,
        color: ColorLike,
        thickness: float = 2.0,
        *,
        fg: ColorLike = None,
    ) -> None:
        if fg is not None:
            color = fg
        cx, cy = _unpack_xy(center)
        self._lib.nexa_draw_arc(
            self._ctx, cx, cy, float(radius), float(angle_start), float(angle_end),
            float(thickness), to_packed_color(color)
        )

    def draw_bezier(
        self,
        p0: Union[Vec2, Tuple[float, float]],
        p1: Union[Vec2, Tuple[float, float]],
        p2: Union[Vec2, Tuple[float, float]],
        p3: Union[Vec2, Tuple[float, float]],
        color: ColorLike,
        thickness: float = 1.5,
        *,
        segments: int = 24,
        fg: ColorLike = None,
    ) -> None:
        """Draw a smooth cubic Bézier curve through ``(p0, p1, p2, p3)``."""
        if fg is not None:
            color = fg
        n_seg = max(2, int(segments))
        x0, y0 = _unpack_xy(p0)
        x1, y1 = _unpack_xy(p1)
        x2, y2 = _unpack_xy(p2)
        x3, y3 = _unpack_xy(p3)
        n_pts = n_seg + 1
        arr = (c_float * (n_pts * 2))()
        for i in range(n_pts):
            t = i / n_seg
            u = 1.0 - t
            b0 = u * u * u
            b1 = 3.0 * u * u * t
            b2 = 3.0 * u * t * t
            b3 = t * t * t
            arr[i * 2] = b0 * x0 + b1 * x1 + b2 * x2 + b3 * x3
            arr[i * 2 + 1] = b0 * y0 + b1 * y1 + b2 * y2 + b3 * y3
        self._lib.nexa_draw_polyline(
            self._ctx, arr, n_pts, float(thickness), to_packed_color(color), False
        )

    def draw_text(
        self,
        text: str,
        pos: Union[Vec2, Tuple[float, float]],
        color: ColorLike,
        *,
        size: float = 13.0,
        font: Union[FontRole, int] = FontRole.BODY,
        fg: ColorLike = None,
    ) -> None:
        if fg is not None:
            color = fg
        px, py = _unpack_xy(pos)
        raw = text.encode("utf-8")
        self._lib.nexa_draw_text(
            self._ctx, int(font), float(size), px, py, to_packed_color(color), raw, len(raw)
        )

    def draw_icon(
        self,
        icon: str,
        rect: Union[Rect, Tuple[float, float, float, float]],
        color: ColorLike,
        *,
        size: float = 16.0,
        fg: ColorLike = None,
    ) -> None:
        if fg is not None:
            color = fg
        x, y, w, h = _unpack_rect(rect)
        self._lib.nexa_draw_icon(
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
        self._lib.nexa_draw_image(
            self._ctx, int(texture), x, y, w, h, u0, v0, u1, v1,
            c.tl, c.tr, c.br, c.bl, to_packed_color(tint)
        )

    def push_clip(self, rect: Union[Rect, Tuple[float, float, float, float]]) -> None:
        x, y, w, h = _unpack_rect(rect)
        self._lib.nexa_push_clip(self._ctx, x, y, w, h)

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

    # ---- Canvas & bars (CUI post-1.4) ----

    def live_cursors(
        self,
        id: str,
        users: Sequence[LiveUser],
        *,
        view: Optional[NodeView] = None,
        no_glide: bool = False,
    ) -> None:
        """Other people's pointers over a canvas, with name flags and chat
        bubbles that glide to each new position (CUI post-1.4).
        """
        keep = self._frame_keepalive
        n = len(users)
        arr = (CuiLiveUser * max(n, 1))()
        for i, u in enumerate(users):
            arr[i].name = encode_str(u.name, keep)
            if u.color is not None:
                arr[i].color = to_c_color(u.color)
            arr[i].tone = int(u.tone)
            arr[i].x = float(u.x)
            arr[i].y = float(u.y)
            arr[i].says = encode_opt(u.says, keep)
            arr[i].speaking = bool(u.speaking)
            arr[i].away = bool(u.away)
            arr[i].avatar = int(u.avatar)
        opts = CuiLiveCursorsOpts()
        if view is not None:
            c_view = CuiNodeView(float(view.x), float(view.y), float(view.zoom))
            opts.view = ctypes.pointer(c_view)
            keep.append(c_view)
        opts.no_glide = bool(no_glide)
        keep.extend((arr, opts))
        self._lib.cui_live_cursors_ex(self._ctx, encode_str(id, keep), arr, n, ctypes.byref(opts))

    def presence_pill(
        self,
        id: str,
        users: Sequence[LiveUser],
        *,
        size: float = 0.0,
        max_visible: int = 0,
    ) -> None:
        """Shows who is here and who is speaking (CUI post-1.4)."""
        keep = self._frame_keepalive
        n = len(users)
        arr = (CuiLiveUser * max(n, 1))()
        for i, u in enumerate(users):
            arr[i].name = encode_str(u.name, keep)
            if u.color is not None:
                arr[i].color = to_c_color(u.color)
            arr[i].tone = int(u.tone)
            arr[i].speaking = bool(u.speaking)
            arr[i].away = bool(u.away)
            arr[i].avatar = int(u.avatar)
        opts = CuiPresencePillOpts()
        opts.size = float(size)
        opts.max_visible = int(max_visible)
        keep.extend((arr, opts))
        self._lib.cui_presence_pill_ex(self._ctx, encode_str(id, keep), arr, n, ctypes.byref(opts))

    def selection_ring(self, color: ColorLike, *, fg: ColorLike = None, name: Optional[str] = None, radius: float = 0.0) -> None:
        """Marks what someone else has selected on a shared canvas (CUI post-1.4)."""
        if fg is not None:
            color = fg
        keep = self._frame_keepalive
        opts = CuiSelectionRingOpts()
        opts.name = encode_opt(name, keep)
        opts.radius = float(radius)
        keep.append(opts)
        self._lib.cui_selection_ring_ex(self._ctx, to_c_color(color), ctypes.byref(opts))

    def canvas_controls(
        self,
        id: str,
        view: NodeView,
        *,
        steps: Optional[Sequence[float]] = None,
        content: Optional[Rect] = None,
        toggles: Optional[Sequence[CanvasToggle]] = None,
        no_fit: bool = False,
        start_side: bool = False,
    ) -> CanvasControlsResult:
        """Floating zoom rail (in, a percentage that resets to 100%, out, fit
        and your own toggles) driving a node view (CUI post-1.4).

        ``view`` is updated in place (zoom presets keep the middle in place);
        toggles flip their ``on`` in place. Returns which flags fired.
        """
        keep = self._frame_keepalive
        c_view = CuiNodeView(float(view.x), float(view.y), float(view.zoom))
        opts = CuiCanvasControlsOpts()
        if steps:
            n = len(steps)
            s_arr = (c_float * n)(*(float(s) for s in steps))
            opts.steps = s_arr
            opts.step_count = n
            keep.append(s_arr)
        if content is not None:
            opts.content = CuiRect(float(content.x), float(content.y), float(content.w), float(content.h))
        if toggles:
            m = len(toggles)
            t_arr = (CuiCanvasToggle * m)()
            on_cells = [c_bool(bool(t.on)) for t in toggles]
            for i, t in enumerate(toggles):
                t_arr[i].icon = encode_str(t.icon, keep)
                t_arr[i].label = encode_opt(t.label, keep)
                t_arr[i].on = ctypes.pointer(on_cells[i])
            opts.toggles = t_arr
            opts.toggle_count = m
            keep.extend((t_arr, on_cells))
        opts.no_fit = bool(no_fit)
        opts.start_side = bool(start_side)
        keep.extend((c_view, opts))
        flags = int(self._lib.cui_canvas_controls_ex(
            self._ctx, encode_str(id, keep), ctypes.byref(c_view), ctypes.byref(opts)
        ))
        view.x = float(c_view.x)
        view.y = float(c_view.y)
        view.zoom = float(c_view.zoom)
        if toggles:
            for i, t in enumerate(toggles):
                t.on = bool(on_cells[i])
        self._record_change(bool(flags))
        return CanvasControlsResult(flags)


UI_TYPE = object
