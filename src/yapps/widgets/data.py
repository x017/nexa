"""Data display: trees, lists, virtual lists, reorder lists, tables, data grids, filter bar, code & JSON."""

from __future__ import annotations

import ctypes
from ctypes import c_bool, c_int, c_uint32
from typing import List, Optional, Sequence, Tuple

from .._cdefs import (
    CuiCodeOpts,
    CuiFilterField,
    CuiGridColumn,
    CuiGridOpts,
    CuiJsonOpts,
    CuiListItemOpts,
    CuiTableColumn,
    CuiTableOpts,
    CuiTableSort,
    CuiTimelineOpts,
    CuiTreeOpts,
    encode_opt,
    encode_str,
    encode_str_array,
    make_text_buffer,
    to_c_size,
)
from ..scopes import DataGridScope, OpenStateScope, ReorderScope, TableScope, VirtualListScope
from ..types import (
    FilterField,
    GridColumn,
    SizeLike,
    TableColumn,
    TableSort,
    Tone,
)


class DataMixin:
    __slots__ = ()

    def tree(
        self,
        label: str,
        is_open: bool = False,
        *,
        icon: Optional[str] = None,
        leaf: bool = False,
        selected: bool = False,
    ) -> OpenStateScope:
        keep = self._frame_keepalive
        c_open = c_bool(bool(is_open))
        opts = CuiTreeOpts()
        opts.icon = encode_opt(icon, keep)
        opts.leaf = bool(leaf)
        opts.selected = bool(selected)
        keep.extend((c_open, opts))
        vis = bool(self._lib.cui_tree_begin(
            self._ctx, encode_str(label, keep), ctypes.byref(c_open), ctypes.byref(opts)
        ))
        clicked = bool(self._lib.cui_tree_clicked(self._ctx))
        return OpenStateScope(self._ctx, self._lib.cui_tree_end, vis, bool(c_open.value), clicked)

    def tree_cell(
        self,
        label: str,
        depth: int,
        has_children: bool,
        is_open: bool,
        *,
        icon: Optional[str] = None,
    ) -> bool:
        keep = self._frame_keepalive
        c_open = c_bool(bool(is_open))
        toggled = bool(self._lib.cui_tree_cell(
            self._ctx, encode_str(label, keep), int(depth), bool(has_children),
            ctypes.byref(c_open), encode_opt(icon, keep)
        ))
        self._record_change(toggled)
        return bool(c_open.value)

    def list_item(
        self,
        title: str,
        *,
        icon: Optional[str] = None,
        subtitle: Optional[str] = None,
        trailing: Optional[str] = None,
        selected: bool = False,
        avatar: Optional[str] = None,
    ) -> bool:
        keep = self._frame_keepalive
        opts = CuiListItemOpts()
        opts.icon = encode_opt(icon, keep)
        opts.subtitle = encode_opt(subtitle, keep)
        opts.trailing = encode_opt(trailing, keep)
        opts.selected = bool(selected)
        opts.avatar = encode_opt(avatar, keep)
        keep.append(opts)
        clicked = bool(self._lib.cui_list_item_ex(self._ctx, encode_str(title, keep), ctypes.byref(opts)))
        self._record_change(clicked)
        return clicked

    def virtual_list(
        self,
        id: str,
        count: int,
        row_height: float,
        height: SizeLike = None,
    ) -> VirtualListScope:
        keep = self._frame_keepalive
        first = c_int(0)
        last = c_int(0)
        sz = to_c_size(height)
        self._lib.yapps_virtual_list_begin(
            self._ctx, encode_str(id, keep), int(count), float(row_height),
            int(sz.kind), float(sz.value), ctypes.byref(first), ctypes.byref(last)
        )
        return VirtualListScope(self._ctx, self._lib.cui_virtual_list_end, int(first.value), int(last.value))

    def reorder(self, id: str, order: Sequence[int]) -> ReorderScope:
        keep = self._frame_keepalive
        n = len(order)
        c_order = (c_int * n)(*(int(x) for x in order))
        keep.append(c_order)
        self._lib.cui_reorder_begin(self._ctx, encode_str(id, keep), c_order, n)
        return ReorderScope(self, c_order, n)

    def timeline_item(
        self,
        title: str,
        *,
        time: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        tone: Tone = Tone.NEUTRAL,
        last: bool = False,
    ) -> None:
        keep = self._frame_keepalive
        opts = CuiTimelineOpts()
        opts.time = encode_opt(time, keep)
        opts.description = encode_opt(description, keep)
        opts.icon = encode_opt(icon, keep)
        opts.tone = int(tone)
        opts.last = bool(last)
        keep.append(opts)
        self._lib.cui_timeline_item_ex(self._ctx, encode_str(title, keep), ctypes.byref(opts))

    def table(
        self,
        id: str,
        columns: Sequence[TableColumn],
        *,
        sort: Optional[TableSort] = None,
        height: SizeLike = None,
        striped: bool = False,
        compact: bool = False,
        selectable: bool = False,
    ) -> TableScope:
        keep = self._frame_keepalive
        ncols = len(columns)
        c_cols = (CuiTableColumn * ncols)()
        for i, col in enumerate(columns):
            c_cols[i].title = encode_str(col.title, keep)
            c_cols[i].width = to_c_size(col.width)
            c_cols[i].align = int(col.align)
            c_cols[i].sortable = bool(col.sortable)
        c_sort = CuiTableSort(int(sort.column), bool(sort.descending)) if sort is not None else None
        opts = CuiTableOpts()
        if c_sort is not None:
            opts.sort = ctypes.pointer(c_sort)
            keep.append(c_sort)
        opts.height = to_c_size(height)
        opts.striped = bool(striped)
        opts.compact = bool(compact)
        opts.selectable = bool(selectable)
        keep.extend((c_cols, opts))
        vis = bool(self._lib.cui_table_begin_ex(
            self._ctx, encode_str(id, keep), c_cols, ncols, ctypes.byref(opts)
        ))
        return TableScope(self, vis, c_sort, sort, keep)

    def data_grid(
        self,
        id: str,
        columns: Sequence[GridColumn],
        row_count: int,
        *,
        width: SizeLike = None,
        height: SizeLike = None,
        row_height: float = 0.0,
        selected: Optional[Sequence[bool]] = None,
        sort: Optional[TableSort] = None,
        striped: bool = False,
        cursor: Optional[int] = None,
    ) -> DataGridScope:
        keep = self._frame_keepalive
        ncols = len(columns)
        c_cols = (CuiGridColumn * ncols)()
        for i, col in enumerate(columns):
            c_cols[i].title = encode_str(col.title, keep)
            c_cols[i].width = float(col.width)
            c_cols[i].align = int(col.align)
            c_cols[i].sortable = bool(col.sortable)
            c_cols[i].fixed = bool(col.fixed)

        nrows = int(row_count)
        opts = CuiGridOpts()
        opts.width = to_c_size(width)
        opts.height = to_c_size(height)
        opts.row_height = float(row_height)
        opts.striped = bool(striped)

        c_sel = None
        if selected is not None:
            if len(selected) != nrows:
                raise ValueError(f"selected length ({len(selected)}) must match row_count ({nrows})")
            c_sel = (c_bool * max(nrows, 1))(*(bool(s) for s in selected))
            opts.selected = c_sel
            keep.append(c_sel)

        c_sort = None
        if sort is not None:
            c_sort = CuiTableSort(int(sort.column), bool(sort.descending))
            opts.sort = ctypes.pointer(c_sort)
            keep.append(c_sort)

        c_cursor = None
        if cursor is not None:
            c_cursor = c_int(int(cursor))
            opts.cursor = ctypes.pointer(c_cursor)
            keep.append(c_cursor)

        first = c_int(0)
        last = c_int(0)
        keep.extend((c_cols, opts))
        vis = bool(self._lib.cui_data_grid_begin_ex(
            self._ctx, encode_str(id, keep), c_cols, ncols, nrows,
            ctypes.byref(first), ctypes.byref(last), ctypes.byref(opts)
        ))
        return DataGridScope(
            self, vis, int(first.value), int(last.value), nrows, c_sel, c_sort, c_cursor, keep
        )

    def filter_bar(
        self,
        id: str,
        fields: Sequence[FilterField],
        selected_masks: Sequence[int],
        search: str,
        *,
        max_search_bytes: int = 256,
    ) -> Tuple[List[int], str]:
        keep = self._frame_keepalive
        n = len(fields)
        if len(selected_masks) != n:
            raise ValueError(f"selected_masks length ({len(selected_masks)}) must equal fields length ({n})")
        arr = (CuiFilterField * n)()
        for i, f in enumerate(fields):
            arr[i].name = encode_str(f.name, keep)
            arr[i].icon = encode_opt(f.icon, keep)
            opts_arr, opts_n = encode_str_array(f.options, keep)
            arr[i].options = opts_arr
            arr[i].option_count = opts_n
        c_sel = (c_uint32 * n)(*(int(m) & 0xFFFFFFFF for m in selected_masks))
        buf, cap = make_text_buffer(search, max_search_bytes)
        keep.extend((arr, c_sel))
        changed = bool(self._lib.cui_filter_bar(
            self._ctx, encode_str(id, keep), arr, n, c_sel, buf, cap
        ))
        self._record_change(changed)
        new_search = buf.value.decode("utf-8", errors="replace") if changed else search
        return [int(c_sel[i]) for i in range(n)], new_search

    def code_block(
        self,
        id: str,
        code: str,
        *,
        lang: Optional[str] = None,
        title: Optional[str] = None,
        line_numbers: bool = False,
        highlight_from: int = 0,
        highlight_to: int = 0,
        max_height: float = 0.0,
        size: float = 0.0,
        no_header: bool = False,
    ) -> None:
        keep = self._frame_keepalive
        opts = CuiCodeOpts()
        opts.lang = encode_opt(lang, keep)
        opts.title = encode_opt(title, keep)
        opts.line_numbers = bool(line_numbers)
        opts.highlight_from = int(highlight_from)
        opts.highlight_to = int(highlight_to)
        opts.max_height = float(max_height)
        opts.size = float(size)
        opts.no_header = bool(no_header)
        keep.append(opts)
        self._lib.cui_code_block_ex(
            self._ctx, encode_str(id, keep), encode_str(code, keep), ctypes.byref(opts)
        )

    def json_view(
        self,
        id: str,
        json_text: str,
        *,
        expand_depth: int = 2,
        max_height: float = 0.0,
    ) -> bool:
        keep = self._frame_keepalive
        opts = CuiJsonOpts(0, int(expand_depth), float(max_height))
        keep.append(opts)
        return bool(self._lib.cui_json_view_ex(
            self._ctx, encode_str(id, keep), encode_str(json_text, keep), ctypes.byref(opts)
        ))
