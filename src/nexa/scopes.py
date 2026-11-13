"""Lightweight ``__slots__`` context managers for nexa container & composite scopes."""

from __future__ import annotations

import ctypes
from ctypes import c_bool, c_float, c_int
from typing import Any, Callable, Iterator, List, Optional, Sequence, Tuple

from ._cdefs import (
    CuiKanbanColumnOpts,
    CuiKanbanMove,
    CuiNodeOpts,
    CuiNodeView,
    CuiPinOpts,
    CuiTableSort,
    CuiTreeTableEvents,
    encode_opt,
    encode_str,
    make_text_buffer,
    to_c_color,
)
from .types import (
    ColorLike,
    KanbanMove,
    NodeView,
    TableSort,
    TreeFlags,
    TreeNode,
    TreeTableEvents,
)


class BoxScope:
    """Unconditional container scope returning its ``cui_id`` on enter."""

    __slots__ = ("_end_fn", "_ctx", "id")

    def __init__(self, ctx: int, end_fn: Callable[[int], Any], node_id: int = 0) -> None:
        self._ctx = ctx
        self._end_fn = end_fn
        self.id = int(node_id)

    def __enter__(self) -> int:
        return self.id

    def __exit__(self, *exc) -> None:
        self._end_fn(self._ctx)


class ColorScope:
    """Wraps a scope and gives its children a default text colour (``fg=``).

    ``with ctx.column(fg="#7c5cff"):`` pushes the colour for the lifetime of the
    block; ``ctx.text()`` and ``ctx.heading()`` use it when no ``color=`` is
    passed. Attributes of the wrapped scope (``.id``, ``.clicked``, ``.open``)
    are reachable through the wrapper, and ``bool()`` follows the inner scope.
    """

    __slots__ = ("_ui", "_inner", "_fg", "_pushed", "_prev")

    def __init__(self, ui: Any, inner: Any, fg: Any) -> None:
        self._ui = ui
        self._inner = inner
        self._fg = fg
        self._pushed = False
        self._prev = None

    def __enter__(self) -> Any:
        if self._fg is not None:
            stack = self._ui._fg_stack
            self._prev = stack[-1] if stack else None
            stack.append(self._fg)
            # mirrored on a plain attribute: text() reads it on every call, and a
            # property access there costs ~0.1 µs (measured) on a hot path
            self._ui._fg_current = self._fg
            self._pushed = True
        return self._inner.__enter__()

    def __exit__(self, *exc: Any) -> Any:
        try:
            return self._inner.__exit__(*exc)
        finally:
            if self._pushed:
                self._ui._fg_stack.pop()
                self._ui._fg_current = self._prev
                self._pushed = False

    def __bool__(self) -> bool:
        return bool(self._inner)

    def __getattr__(self, name: str) -> Any:
        try:
            inner = object.__getattribute__(self, "_inner")
        except AttributeError:  # pragma: no cover - defensive
            raise AttributeError(name) from None
        return getattr(inner, name)


class SimpleScope:
    """Unconditional scope calling ``end_fn(ctx)`` on exit."""

    __slots__ = ("_ctx", "_end_fn")

    def __init__(self, ctx: int, end_fn: Callable[[int], Any]) -> None:
        self._ctx = ctx
        self._end_fn = end_fn

    def __enter__(self) -> SimpleScope:
        return self

    def __exit__(self, *exc) -> None:
        self._end_fn(self._ctx)


class CardScope:
    """Unconditional card scope exposing ``.clicked`` (for ``hoverable=True`` cards)."""

    __slots__ = ("_ctx", "_end_fn", "clicked")

    def __init__(self, ctx: int, end_fn: Callable[[int], Any], clicked: bool) -> None:
        self._ctx = ctx
        self._end_fn = end_fn
        self.clicked = bool(clicked)

    def __bool__(self) -> bool:
        return self.clicked

    def __enter__(self) -> CardScope:
        return self

    def __exit__(self, *exc) -> None:
        self._end_fn(self._ctx)


class ConditionalScope:
    """Scope where CUI only expects ``end_fn`` when ``begin`` returned ``True``.

    Usage::
        with ui.menu("File") as m:
            if m:
                if ui.menu_item("Save"): ...
    """

    __slots__ = ("_ctx", "_end_fn", "visible")

    def __init__(self, ctx: int, end_fn: Callable[[int], Any], visible: bool) -> None:
        self._ctx = ctx
        self._end_fn = end_fn
        self.visible = bool(visible)

    def __bool__(self) -> bool:
        return self.visible

    def __enter__(self) -> ConditionalScope:
        return self

    def __exit__(self, *exc) -> None:
        if self.visible:
            self._end_fn(self._ctx)


class OpenStateScope:
    """Conditional scope with an ``open`` state value (dialog, sheet, accordion, tree, expandable_card).

    Check ``if scope:`` before building body items, and read ``scope.open`` for
    the updated open boolean!
    """

    __slots__ = ("_ctx", "_end_fn", "_request_redraw", "_initial_open", "visible", "open", "clicked")

    def __init__(self, ctx: int, end_fn: Callable[[int], Any],
                 visible: bool, is_open: bool, clicked: bool = False,
                 request_redraw: Optional[Callable[[int], Any]] = None) -> None:
        self._ctx = ctx
        self._end_fn = end_fn
        self._request_redraw = request_redraw
        self._initial_open = bool(is_open)
        self.visible = bool(visible)
        self.open = bool(is_open)
        self.clicked = bool(clicked)

    @property
    def expanded(self) -> bool:
        return self.open

    @expanded.setter
    def expanded(self, value: bool) -> None:
        self.open = bool(value)

    def __bool__(self) -> bool:
        return self.visible

    def __enter__(self) -> OpenStateScope:
        return self

    def __exit__(self, *exc) -> None:
        if self.visible:
            self._end_fn(self._ctx)
        if bool(self.open) != self._initial_open and self._request_redraw is not None:
            self._request_redraw(self._ctx)


class SplitScope:
    """Resizable two-pane split view. Call ``split.next()`` between pane 1 and pane 2, and read ``split.ratio``."""

    __slots__ = ("_ui", "_c_ratio", "_did_next", "ratio")

    def __init__(self, ui: Any, c_ratio: c_float) -> None:
        self._ui = ui
        self._c_ratio = c_ratio
        self._did_next = False
        self.ratio = float(c_ratio.value)

    def next(self) -> None:
        if not self._did_next:
            self._ui._lib.cui_split_next(self._ui._ctx)
            self._did_next = True

    def __enter__(self) -> SplitScope:
        return self

    def __exit__(self, *exc) -> None:
        if not self._did_next:
            self._ui._lib.cui_split_next(self._ui._ctx)
        self._ui._lib.cui_split_end(self._ui._ctx)
        self.ratio = float(self._c_ratio.value)
        self._ui._record_change(False)


class VirtualListScope:
    """Virtualized list scope; unpacks as ``(first, last)`` or iterate ``for idx in vlist:``."""

    __slots__ = ("_ctx", "_end_fn", "first", "last")

    def __init__(self, ctx: int, end_fn: Callable[[int], Any], first: int, last: int) -> None:
        self._ctx = ctx
        self._end_fn = end_fn
        self.first = int(first)
        self.last = int(last)

    @property
    def indices(self) -> range:
        return range(self.first, self.last)

    def __iter__(self) -> Iterator[int]:
        yield self.first
        yield self.last

    def __enter__(self) -> VirtualListScope:
        return self

    def __exit__(self, *exc) -> None:
        self._end_fn(self._ctx)


class TableScope:
    """Scoped table helper keeping column definitions & sort state alive."""

    __slots__ = ("_ui", "visible", "_c_sort", "sort", "_keep")

    def __init__(self, ui: Any, visible: bool, c_sort: Optional[CuiTableSort],
                 init_sort: Optional[TableSort], keep: List[Any]) -> None:
        self._ui = ui
        self.visible = bool(visible)
        self._c_sort = c_sort
        self._keep = keep
        if c_sort is not None:
            self.sort: Optional[TableSort] = TableSort(int(c_sort.column), bool(c_sort.descending))
        else:
            self.sort = init_sort

    def __bool__(self) -> bool:
        return self.visible

    def row(self, selected: bool = False) -> bool:
        return bool(self._ui._lib.cui_table_row(self._ui._ctx, bool(selected)))

    def cell(self) -> None:
        self._ui._lib.cui_table_cell(self._ui._ctx)

    def cell_text(self, text: str) -> None:
        b = encode_str(text, self._ui._frame_keepalive)
        self._ui._lib.cui_table_cell_text(self._ui._ctx, b)

    def __enter__(self) -> TableScope:
        return self

    def __exit__(self, *exc) -> None:
        if self.visible:
            self._ui._lib.cui_table_end(self._ui._ctx)
            if self._c_sort is not None:
                self.sort = TableSort(int(self._c_sort.column), bool(self._c_sort.descending))


class DataGridScope:
    """Virtualized spreadsheet-grade data grid scope."""

    __slots__ = (
        "_ui", "visible", "first", "last", "_nrows",
        "_c_sel", "_c_sort", "_c_cursor", "_c_anchor", "_keep",
        "selected", "sort", "cursor", "anchor",
    )

    def __init__(
        self,
        ui: Any,
        visible: bool,
        first: int,
        last: int,
        nrows: int,
        c_sel: Any,
        c_sort: Optional[CuiTableSort],
        c_cursor: Optional[c_int],
        keep: List[Any],
        c_anchor: Optional[c_int] = None,
    ) -> None:
        self._ui = ui
        self.visible = bool(visible)
        self.first = int(first)
        self.last = int(last)
        self._nrows = nrows
        self._c_sel = c_sel
        self._c_sort = c_sort
        self._c_cursor = c_cursor
        self._c_anchor = c_anchor
        self._keep = keep
        self.selected: Optional[List[bool]] = None
        self.sort: Optional[TableSort] = (
            TableSort(int(c_sort.column), bool(c_sort.descending)) if c_sort is not None else None
        )
        self.cursor: int = int(c_cursor.value) if c_cursor is not None else -1
        self.anchor: int = int(c_anchor.value) if c_anchor is not None else -1

    def __bool__(self) -> bool:
        return self.visible

    @property
    def rows(self) -> range:
        return range(self.first, self.last)

    def row(self, row_index: int) -> bool:
        return bool(self._ui._lib.cui_data_grid_row(self._ui._ctx, int(row_index)))

    def cell(self) -> None:
        self._ui._lib.cui_data_grid_cell(self._ui._ctx)

    def cell_text(self, text: str) -> None:
        b = encode_str(text, self._ui._frame_keepalive)
        self._ui._lib.cui_data_grid_cell_text(self._ui._ctx, b)

    def cell_edit(self, text: str, max_bytes: int = 256) -> str:
        buf, cap = make_text_buffer(text, max_bytes)
        committed = bool(self._ui._lib.cui_data_grid_cell_edit(self._ui._ctx, buf, cap))
        self._ui._record_change(committed)
        return buf.value.decode("utf-8", errors="replace") if committed else text

    def edit(self, text: str, max_bytes: int = 256) -> str:
        buf, cap = make_text_buffer(text, max_bytes)
        committed = bool(self._ui._lib.cui_data_grid_edit(self._ui._ctx, buf, cap))
        self._ui._record_change(committed)
        return buf.value.decode("utf-8", errors="replace") if committed else text

    def __enter__(self) -> DataGridScope:
        return self

    def __exit__(self, *exc) -> None:
        if self.visible:
            self._ui._lib.cui_data_grid_end(self._ui._ctx)
        if self._c_sel is not None:
            self.selected = [bool(self._c_sel[i]) for i in range(self._nrows)]
        if self._c_sort is not None:
            self.sort = TableSort(int(self._c_sort.column), bool(self._c_sort.descending))
        if self._c_cursor is not None:
            self.cursor = int(self._c_cursor.value)
        if self._c_anchor is not None:
            self.anchor = int(self._c_anchor.value)


class ReorderScope:
    """Drag-to-reorder list scope; exposes updated ``.order`` and ``.changed`` on exit."""

    __slots__ = ("_ui", "_c_order", "_count", "order", "changed")

    def __init__(self, ui: Any, c_order: Any, count: int) -> None:
        self._ui = ui
        self._c_order = c_order
        self._count = count
        self.order: List[int] = [int(c_order[i]) for i in range(count)]
        self.changed: bool = False

    def item(self, position: int) -> SimpleScope:
        self._ui._lib.cui_reorder_item_begin(self._ui._ctx, int(position))
        return SimpleScope(self._ui._ctx, self._ui._lib.cui_reorder_item_end)

    def __enter__(self) -> ReorderScope:
        return self

    def __exit__(self, *exc) -> None:
        self.changed = bool(self._ui._lib.cui_reorder_end(self._ui._ctx))
        self.order = [int(self._c_order[i]) for i in range(self._count)]
        self._ui._record_change(self.changed)


class SwipeScope:
    """Swipeable row scope; after exiting, ``.action`` holds triggered action index (or ``-1``)."""

    __slots__ = ("_ui", "action", "_keep")

    def __init__(self, ui: Any, keep: List[Any]) -> None:
        self._ui = ui
        self.action = -1
        self._keep = keep

    def __enter__(self) -> SwipeScope:
        return self

    def __exit__(self, *exc) -> None:
        self.action = int(self._ui._lib.cui_swipe_item_end(self._ui._ctx))


class CarouselScope:
    """Carousel scope; build each slide inside ``with carousel.slide():`` and read ``carousel.index``."""

    __slots__ = ("_ui", "_c_idx", "index", "changed")

    def __init__(self, ui: Any, c_idx: c_int, changed: bool) -> None:
        self._ui = ui
        self._c_idx = c_idx
        self.changed = bool(changed)
        self.index = int(c_idx.value)

    def slide(self) -> SimpleScope:
        self._ui._lib.cui_carousel_slide_begin(self._ui._ctx)
        return SimpleScope(self._ui._ctx, self._ui._lib.cui_carousel_slide_end)

    def __enter__(self) -> CarouselScope:
        return self

    def __exit__(self, *exc) -> None:
        self._ui._lib.cui_carousel_end(self._ui._ctx)
        self.index = int(self._c_idx.value)
        self._ui._record_change(self.changed)


class CardStackScope:
    """Flickable deck of cards; after exit ``.flicked`` is ``-1`` (left), ``1`` (right), or ``0``."""

    __slots__ = ("_ui", "flicked")

    def __init__(self, ui: Any) -> None:
        self._ui = ui
        self.flicked = 0

    def item(self, depth: int) -> SimpleScope:
        self._ui._lib.cui_card_stack_item_begin(self._ui._ctx, int(depth))
        return SimpleScope(self._ui._ctx, self._ui._lib.cui_card_stack_item_end)

    def __enter__(self) -> CardStackScope:
        return self

    def __exit__(self, *exc) -> None:
        self.flicked = int(self._ui._lib.cui_card_stack_end(self._ui._ctx))


class KanbanColumnScope:
    __slots__ = ("_ctx", "_end_fn", "add_clicked")

    def __init__(self, ctx: int, end_fn: Callable[[int], Any], add_clicked: bool) -> None:
        self._ctx = ctx
        self._end_fn = end_fn
        self.add_clicked = bool(add_clicked)

    def __enter__(self) -> KanbanColumnScope:
        return self

    def __exit__(self, *exc) -> None:
        self._end_fn(self._ctx)


class KanbanScope:
    """Kanban board scope; after exiting, ``board.move`` is ``KanbanMove`` if a card was dropped."""

    __slots__ = ("_ui", "move")

    def __init__(self, ui: Any) -> None:
        self._ui = ui
        self.move: Optional[KanbanMove] = None

    def column(self, title: str, card_count: int, *, dot: ColorLike = None,
               limit: int = 0, width: float = 0.0) -> KanbanColumnScope:
        keep = self._ui._frame_keepalive
        opts = CuiKanbanColumnOpts()
        opts.dot = to_c_color(dot)
        opts.limit = int(limit)
        opts.width = float(width)
        keep.append(opts)
        add_clicked = bool(self._ui._lib.cui_kanban_column_begin_ex(
            self._ui._ctx, encode_str(title, keep), int(card_count), ctypes.byref(opts)
        ))
        return KanbanColumnScope(self._ui._ctx, self._ui._lib.cui_kanban_column_end, add_clicked)

    def card(self, card_id: int) -> CardScope:
        clicked = bool(self._ui._lib.cui_kanban_card_begin(self._ui._ctx, int(card_id)))
        return CardScope(self._ui._ctx, self._ui._lib.cui_kanban_card_end, clicked)

    def __enter__(self) -> KanbanScope:
        return self

    def __exit__(self, *exc) -> None:
        mv = CuiKanbanMove()
        if self._ui._lib.cui_kanban_end(self._ui._ctx, ctypes.byref(mv)):
            self.move = KanbanMove(mv.card, mv.from_column, mv.to_column, mv.to_index)
            self._ui._record_change(True)
        else:
            self.move = None


class NodeScope:
    """Single node scope in a ``node_editor``; exposes updated ``.x``, ``.y``, and ``.selected``."""

    __slots__ = ("_ui", "_cx", "_cy", "selected", "x", "y")

    def __init__(self, ui: Any, cx: c_float, cy: c_float, selected: bool) -> None:
        self._ui = ui
        self._cx = cx
        self._cy = cy
        self.selected = bool(selected)
        self.x = float(cx.value)
        self.y = float(cy.value)

    def __enter__(self) -> NodeScope:
        return self

    def __exit__(self, *exc) -> None:
        self._ui._lib.cui_node_end(self._ui._ctx)
        self.x = float(self._cx.value)
        self.y = float(self._cy.value)


class NodeEditorScope:
    """Interactive pan/zoom node graph editor scope."""

    __slots__ = ("_ui", "visible", "_c_view", "view", "created_links", "removed_links", "deleted_nodes")

    def __init__(self, ui: Any, visible: bool, c_view: CuiNodeView) -> None:
        self._ui = ui
        self.visible = bool(visible)
        self._c_view = c_view
        self.view = NodeView(float(c_view.x), float(c_view.y), float(c_view.zoom))
        self.created_links: List[Tuple[int, int]] = []
        self.removed_links: List[int] = []
        self.deleted_nodes: List[int] = []

    def __bool__(self) -> bool:
        return self.visible

    def node(self, node_id: int, x: float, y: float, title: str, *,
             width: float = 0.0, icon: Optional[str] = None) -> NodeScope:
        keep = self._ui._frame_keepalive
        cx = c_float(float(x))
        cy = c_float(float(y))
        opts = CuiNodeOpts()
        opts.width = float(width)
        opts.icon = encode_opt(icon, keep)
        keep.extend((cx, cy, opts))
        sel = bool(self._ui._lib.cui_node_begin_ex(
            self._ui._ctx, int(node_id), ctypes.byref(cx), ctypes.byref(cy),
            encode_str(title, keep), ctypes.byref(opts)
        ))
        return NodeScope(self._ui, cx, cy, sel)

    def input(self, pin_id: int, label: str, *, pin_type: int = 0) -> bool:
        keep = self._ui._frame_keepalive
        opts = CuiPinOpts(0, int(pin_type))
        return bool(self._ui._lib.cui_node_input_ex(
            self._ui._ctx, int(pin_id), encode_str(label, keep), ctypes.byref(opts)
        ))

    def output(self, pin_id: int, label: str, *, pin_type: int = 0) -> bool:
        keep = self._ui._frame_keepalive
        opts = CuiPinOpts(0, int(pin_type))
        return bool(self._ui._lib.cui_node_output_ex(
            self._ui._ctx, int(pin_id), encode_str(label, keep), ctypes.byref(opts)
        ))

    def content(self) -> SimpleScope:
        self._ui._lib.cui_node_content_begin(self._ui._ctx)
        return SimpleScope(self._ui._ctx, self._ui._lib.cui_node_content_end)

    def link(self, link_id: int, from_pin: int, to_pin: int) -> bool:
        return bool(self._ui._lib.cui_node_link(self._ui._ctx, int(link_id), int(from_pin), int(to_pin)))

    def __enter__(self) -> NodeEditorScope:
        return self

    def __exit__(self, *exc) -> None:
        if self.visible:
            a, b, ident = c_int(0), c_int(0), c_int(0)
            while self._ui._lib.cui_node_link_created(self._ui._ctx, ctypes.byref(a), ctypes.byref(b)):
                self.created_links.append((int(a.value), int(b.value)))
            while self._ui._lib.cui_node_link_removed(self._ui._ctx, ctypes.byref(ident)):
                self.removed_links.append(int(ident.value))
            while self._ui._lib.cui_node_deleted(self._ui._ctx, ctypes.byref(ident)):
                self.deleted_nodes.append(int(ident.value))
            self._ui._lib.cui_node_editor_end(self._ui._ctx)
        self.view = NodeView(float(self._c_view.x), float(self._c_view.y), float(self._c_view.zoom))


class TreeTableScope:
    """Virtualized hierarchical tree-table scope (``ui.tree_table(...)``).

    Iterate visible rows via ``for node_idx in tree.rows():``, draw the indented
    disclosure name cell with ``tree.name(label, icon=...)``, and emit extra
    columns via ``tree.cell_text(...)`` / ``tree.cell()`` / ``tree.cell_edit(...)``.
    On exit, ``nodes[i].flags`` are synchronized in-place and ``tree.events``,
    ``tree.sort``, and ``tree.cursor`` are populated.
    """

    __slots__ = (
        "_ui", "_py_nodes", "_c_nodes", "_count",
        "_c_sort", "_c_cursor", "_keep",
        "events", "sort", "cursor",
    )

    def __init__(
        self,
        ui: Any,
        py_nodes: Sequence[TreeNode],
        c_nodes: Any,
        count: int,
        c_sort: Optional[CuiTableSort],
        c_cursor: Optional[c_int],
        keep: List[Any],
    ) -> None:
        self._ui = ui
        self._py_nodes = py_nodes
        self._c_nodes = c_nodes
        self._count = count
        self._c_sort = c_sort
        self._c_cursor = c_cursor
        self._keep = keep
        self.events = TreeTableEvents()
        self.sort: Optional[TableSort] = (
            TableSort(int(c_sort.column), bool(c_sort.descending)) if c_sort is not None else None
        )
        self.cursor: int = int(c_cursor.value) if c_cursor is not None else -1

    def row(self) -> int:
        return int(self._ui._lib.cui_tree_table_row(self._ui._ctx))

    def rows(self) -> Iterator[int]:
        while True:
            idx = int(self._ui._lib.cui_tree_table_row(self._ui._ctx))
            if idx < 0:
                break
            yield idx

    @property
    def depth(self) -> int:
        return int(self._ui._lib.cui_tree_table_depth(self._ui._ctx))

    def name(self, text: str, icon: Optional[str] = None) -> None:
        keep = self._ui._frame_keepalive
        self._ui._lib.cui_tree_table_name(
            self._ui._ctx, encode_str(text, keep), encode_opt(icon, keep)
        )

    def cell(self) -> None:
        self._ui._lib.cui_data_grid_cell(self._ui._ctx)

    def cell_text(self, text: str) -> None:
        b = encode_str(text, self._ui._frame_keepalive)
        self._ui._lib.cui_data_grid_cell_text(self._ui._ctx, b)

    def cell_edit(self, text: str, max_bytes: int = 256) -> str:
        buf, cap = make_text_buffer(text, max_bytes)
        committed = bool(self._ui._lib.cui_data_grid_cell_edit(self._ui._ctx, buf, cap))
        self._ui._record_change(committed)
        return buf.value.decode("utf-8", errors="replace") if committed else text

    def __enter__(self) -> TreeTableScope:
        return self

    def __exit__(self, *exc) -> None:
        ev = CuiTreeTableEvents()
        self._ui._lib.nexa_tree_table_end(self._ui._ctx, ctypes.byref(ev))
        for i in range(self._count):
            self._py_nodes[i].flags = TreeFlags(int(self._c_nodes[i].flags))
        loads = (
            tuple(int(ev.load[i]) for i in range(int(ev.load_count)))
            if ev.load and ev.load_count > 0
            else ()
        )
        self.events = TreeTableEvents(
            activated=int(ev.activated),
            expanded=int(ev.expanded),
            collapsed=int(ev.collapsed),
            load=loads,
            selection_changed=bool(ev.selection_changed),
            sort_changed=bool(ev.sort_changed),
        )
        if self._c_sort is not None:
            self.sort = TableSort(int(self._c_sort.column), bool(self._c_sort.descending))
        if self._c_cursor is not None:
            self.cursor = int(self._c_cursor.value)
        self._ui._record_change(bool(self.events))


class PathBarMenuScope:
    """Popup menu scope attached to a ``path_bar(..., menus=True)`` segment chevron."""

    __slots__ = ("_ctx", "_end_fn", "visible", "segment")

    def __init__(self, ctx: int, end_fn: Callable[[int], Any], visible: bool, segment: int) -> None:
        self._ctx = ctx
        self._end_fn = end_fn
        self.visible = bool(visible)
        self.segment = int(segment)

    def __bool__(self) -> bool:
        return self.visible

    def __enter__(self) -> PathBarMenuScope:
        return self

    def __exit__(self, *exc) -> None:
        if self.visible:
            self._end_fn(self._ctx)


# Documented ergonomic aliases
TreeScope = OpenStateScope
SwipeItemScope = SwipeScope
