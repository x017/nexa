"""Layout containers, cards, scroll areas, split views, and identity scopes."""

from __future__ import annotations

import ctypes
from ctypes import c_float
from typing import Optional, Union

from .._cdefs import (
    CuiBox,
    CuiCardOpts,
    CuiScrollOpts,
    CuiSplitOpts,
    encode_opt,
    encode_str,
    to_c_color,
    to_c_size,
)
from ..scopes import ColorScope, BoxScope, CardScope, SimpleScope, SplitScope
from ..types import Align, ColorLike, Direction, Elevation, Justify, Rect, SizeLike, TextDirection


def _build_box_opts(
    keep: list,
    *,
    id: Optional[str] = None,
    dir: Direction = Direction.COLUMN,
    width: SizeLike = None,
    height: SizeLike = None,
    min_width: float = 0.0,
    max_width: float = 0.0,
    min_height: float = 0.0,
    max_height: float = 0.0,
    pad: float = 0.0,
    pad_x: float = 0.0,
    pad_y: float = 0.0,
    pad_top: float = 0.0,
    pad_right: float = 0.0,
    pad_bottom: float = 0.0,
    pad_left: float = 0.0,
    gap: float = 0.0,
    columns: int = 0,
    min_column_width: float = 0.0,
    wrap: bool = False,
    align: Align = Align.DEFAULT,
    justify: Justify = Justify.START,
    bg: ColorLike = None,
    border_color: ColorLike = None,
    border: float = 0.0,
    radius: float = 0.0,
    radius_tl: float = 0.0,
    radius_tr: float = 0.0,
    radius_br: float = 0.0,
    radius_bl: float = 0.0,
    elevation: Elevation = Elevation.NONE,
    scroll_x: bool = False,
    scroll_y: bool = False,
    clip: bool = False,
    opacity: float = 0.0,
    direction: TextDirection = TextDirection.INHERIT,
) -> CuiBox:
    opts = CuiBox()
    opts.id = encode_opt(id, keep)
    opts.dir = int(dir)
    opts.width = to_c_size(width)
    opts.height = to_c_size(height)
    opts.min_width = float(min_width)
    opts.max_width = float(max_width)
    opts.min_height = float(min_height)
    opts.max_height = float(max_height)
    opts.pad = float(pad)
    opts.pad_x = float(pad_x)
    opts.pad_y = float(pad_y)
    opts.pad_top = float(pad_top)
    opts.pad_right = float(pad_right)
    opts.pad_bottom = float(pad_bottom)
    opts.pad_left = float(pad_left)
    opts.gap = float(gap)
    opts.columns = int(columns)
    opts.min_column_width = float(min_column_width)
    opts.wrap = bool(wrap)
    opts.align = int(align)
    opts.justify = int(justify)
    opts.bg = to_c_color(bg)
    opts.border_color = to_c_color(border_color)
    opts.border = float(border)
    opts.radius = float(radius)
    opts.radius_tl = float(radius_tl)
    opts.radius_tr = float(radius_tr)
    opts.radius_br = float(radius_br)
    opts.radius_bl = float(radius_bl)
    opts.elevation = int(elevation)
    opts.scroll_x = bool(scroll_x)
    opts.scroll_y = bool(scroll_y)
    opts.clip = bool(clip)
    opts.opacity = float(opacity)
    opts.direction = int(direction)
    keep.append(opts)
    return opts


class LayoutMixin:
    __slots__ = ()

    # ---- Scoped layout containers ----

    def _scope(self, inner: BoxScope, fg: ColorLike) -> "BoxScope | ColorScope":
        """Wrap a container scope so ``fg=`` tints the text drawn inside it."""
        return inner if fg is None else ColorScope(self, inner, fg)

    def box(
        self,
        *,
        fg: ColorLike = None,
        bg: ColorLike = None,
        border_color: ColorLike = None,
        **kwargs: Any,
    ) -> "BoxScope | ColorScope":
        """Container scope.

        ``bg`` / ``border_color`` paint the container itself; ``fg`` is the text
        colour inherited by ``text()``, ``heading()``, ``markdown()`` and
        ``expandable_text()`` inside it. Layout arguments (``pad``, ``gap``,
        ``width``, ``radius``, ``align``…) are documented on the container
        reference page.
        """
        opts = _build_box_opts(self._frame_keepalive, bg=bg, border_color=border_color, **kwargs)
        nid = int(self._lib.cui_box_begin(self._ctx, ctypes.byref(opts)))
        return self._scope(BoxScope(self._ctx, self._lib.cui_box_end, nid), fg)

    def row(
        self,
        *,
        fg: ColorLike = None,
        bg: ColorLike = None,
        border_color: ColorLike = None,
        **kwargs: Any,
    ) -> "BoxScope | ColorScope":
        """Horizontal container; same colour arguments as :meth:`box`."""
        kwargs.setdefault("dir", Direction.ROW)
        opts = _build_box_opts(self._frame_keepalive, bg=bg, border_color=border_color, **kwargs)
        nid = int(self._lib.cui_row_begin(self._ctx, ctypes.byref(opts)))
        return self._scope(BoxScope(self._ctx, self._lib.cui_box_end, nid), fg)

    def column(
        self,
        *,
        fg: ColorLike = None,
        bg: ColorLike = None,
        border_color: ColorLike = None,
        **kwargs: Any,
    ) -> "BoxScope | ColorScope":
        """Vertical container; same colour arguments as :meth:`box`."""
        kwargs.setdefault("dir", Direction.COLUMN)
        opts = _build_box_opts(self._frame_keepalive, bg=bg, border_color=border_color, **kwargs)
        nid = int(self._lib.cui_column_begin(self._ctx, ctypes.byref(opts)))
        return self._scope(BoxScope(self._ctx, self._lib.cui_box_end, nid), fg)

    def grid(
        self,
        columns: int = 0,
        *,
        min_column_width: float = 0.0,
        fg: ColorLike = None,
        bg: ColorLike = None,
        border_color: ColorLike = None,
        **kwargs: Any,
    ) -> "BoxScope | ColorScope":
        """Grid container; same colour arguments as :meth:`box`."""
        kwargs["dir"] = Direction.GRID
        kwargs["columns"] = columns
        kwargs["min_column_width"] = min_column_width
        return self.box(fg=fg, bg=bg, border_color=border_color, **kwargs)

    def stack(
        self,
        *,
        fg: ColorLike = None,
        bg: ColorLike = None,
        border_color: ColorLike = None,
        **kwargs: Any,
    ) -> "BoxScope | ColorScope":
        """Overlay stack; same colour arguments as :meth:`box`."""
        kwargs["dir"] = Direction.STACK
        return self.box(fg=fg, bg=bg, border_color=border_color, **kwargs)

    def card(
        self,
        *,
        id: Optional[str] = None,
        width: SizeLike = None,
        height: SizeLike = None,
        min_width: float = 0.0,
        max_width: float = 0.0,
        pad: float = 0.0,
        pad_x: float = 0.0,
        pad_y: float = 0.0,
        gap: float = 0.0,
        dir: Direction = Direction.COLUMN,
        align: Align = Align.DEFAULT,
        wrap: bool = False,
        hoverable: bool = False,
        muted: bool = False,
        selected: bool = False,
        bg: ColorLike = None,
        border_color: ColorLike = None,
        fg: ColorLike = None,
    ) -> "CardScope | ColorScope":
        keep = self._frame_keepalive
        opts = CuiCardOpts()
        opts.id = encode_opt(id, keep)
        opts.width = to_c_size(width)
        opts.height = to_c_size(height)
        opts.min_width = float(min_width)
        opts.max_width = float(max_width)
        opts.pad = float(pad)
        opts.pad_x = float(pad_x)
        opts.pad_y = float(pad_y)
        opts.gap = float(gap)
        opts.dir = int(dir)
        opts.align = int(align)
        opts.wrap = bool(wrap)
        opts.hoverable = bool(hoverable)
        opts.muted = bool(muted)
        opts.selected = bool(selected)
        if bg is not None:
            opts.bg = to_c_color(bg)
        if border_color is not None:
            opts.border_color = to_c_color(border_color)
        keep.append(opts)
        clicked = bool(self._lib.cui_card_begin(self._ctx, ctypes.byref(opts)))
        scope = CardScope(self._ctx, self._lib.cui_card_end, clicked)
        return scope if fg is None else ColorScope(self, scope, fg)

    def scroll(
        self,
        id: Optional[str] = None,
        *,
        width: SizeLike = None,
        height: SizeLike = None,
        horizontal: bool = False,
        pad: float = 0.0,
        gap: float = 0.0,
        fade_edges: bool = False,
        fade_color: ColorLike = None,
    ) -> SimpleScope:
        keep = self._frame_keepalive
        opts = CuiScrollOpts()
        opts.id = encode_opt(id, keep)
        opts.width = to_c_size(width)
        opts.height = to_c_size(height)
        opts.horizontal = bool(horizontal)
        opts.pad = float(pad)
        opts.gap = float(gap)
        opts.fade_edges = bool(fade_edges)
        opts.fade_color = to_c_color(fade_color)
        keep.append(opts)
        self._lib.cui_scroll_begin(self._ctx, ctypes.byref(opts))
        return SimpleScope(self._ctx, self._lib.cui_scroll_end)

    def scroll_to(self, scroll_id: str, y: float) -> None:
        self._lib.cui_scroll_to(self._ctx, encode_str(scroll_id, self._frame_keepalive), float(y))

    def split(
        self,
        id: str,
        ratio: float,
        *,
        vertical: bool = False,
        min_first: float = 0.0,
        min_second: float = 0.0,
        width: SizeLike = None,
        height: SizeLike = None,
    ) -> SplitScope:
        keep = self._frame_keepalive
        c_ratio = c_float(float(ratio))
        opts = CuiSplitOpts()
        opts.vertical = bool(vertical)
        opts.min_first = float(min_first)
        opts.min_second = float(min_second)
        opts.width = to_c_size(width)
        opts.height = to_c_size(height)
        keep.extend((c_ratio, opts))
        self._lib.cui_split_begin(self._ctx, encode_str(id, keep), ctypes.byref(c_ratio), ctypes.byref(opts))
        return SplitScope(self, c_ratio)

    def spacer(self) -> None:
        self._lib.cui_spacer(self._ctx)

    def gap(self, size: float) -> None:
        self._lib.cui_gap(self._ctx, float(size))

    def separator(self) -> None:
        self._lib.cui_separator(self._ctx)

    # ---- Identity & Disabled Scopes ----

    def id_scope(self, key: Union[str, int]) -> SimpleScope:
        if isinstance(key, int):
            self._lib.cui_push_id_int(self._ctx, int(key))
        else:
            self._lib.cui_push_id(self._ctx, encode_str(str(key), self._frame_keepalive))
        return SimpleScope(self._ctx, self._lib.cui_pop_id)

    def disabled_scope(self, disabled: bool = True) -> SimpleScope:
        self._lib.cui_push_disabled(self._ctx, bool(disabled))
        return SimpleScope(self._ctx, self._lib.cui_pop_disabled)

    def make_id(self, key: str) -> int:
        return int(self._lib.cui_make_id(self._ctx, encode_str(key, self._frame_keepalive)))

    def push_id(self, key: Union[str, int]) -> None:
        if isinstance(key, int):
            self._lib.cui_push_id_int(self._ctx, int(key))
        else:
            self._lib.cui_push_id(self._ctx, encode_str(str(key), self._frame_keepalive))

    def pop_id(self) -> None:
        self._lib.cui_pop_id(self._ctx)

    def push_disabled(self, disabled: bool = True) -> None:
        self._lib.cui_push_disabled(self._ctx, bool(disabled))

    def pop_disabled(self) -> None:
        self._lib.cui_pop_disabled(self._ctx)

    @property
    def is_disabled(self) -> bool:
        return bool(self._lib.cui_is_disabled(self._ctx))

    @property
    def last_id(self) -> int:
        return int(self._lib.cui_last_id(self._ctx))

    @property
    def last_rect(self) -> Rect:
        out = (c_float * 4)()
        self._lib.nexa_last_rect(self._ctx, out)
        return Rect(out[0], out[1], out[2], out[3])

    @property
    def last_hovered(self) -> bool:
        return bool(self._lib.cui_last_hovered(self._ctx))

    def get_rect(self, widget_id: int) -> Rect:
        out = (c_float * 4)()
        self._lib.nexa_get_rect(self._ctx, int(widget_id), out)
        return Rect(out[0], out[1], out[2], out[3])

    # ---- Explicit begin / end pairs (full control for early returns) ----

    def box_begin(self, **kwargs) -> int:
        opts = _build_box_opts(self._frame_keepalive, **kwargs)
        return int(self._lib.cui_box_begin(self._ctx, ctypes.byref(opts)))

    def row_begin(self, **kwargs) -> int:
        kwargs.setdefault("dir", Direction.ROW)
        opts = _build_box_opts(self._frame_keepalive, **kwargs)
        return int(self._lib.cui_row_begin(self._ctx, ctypes.byref(opts)))

    def column_begin(self, **kwargs) -> int:
        kwargs.setdefault("dir", Direction.COLUMN)
        opts = _build_box_opts(self._frame_keepalive, **kwargs)
        return int(self._lib.cui_column_begin(self._ctx, ctypes.byref(opts)))

    def box_end(self) -> None:
        self._lib.cui_box_end(self._ctx)
