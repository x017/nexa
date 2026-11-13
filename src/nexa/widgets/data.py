"""Data display, rich text & code: trees, tree tables, lists, virtual lists, tables, data grids, markdown, code editor, diff viewer, code & JSON."""

from __future__ import annotations

import ctypes
from ctypes import CFUNCTYPE, c_bool, c_char_p, c_int, c_uint32, c_void_p
from typing import Any, Callable, List, Optional, Sequence, Tuple

from .._cdefs import (
    CuiCodeEditorOpts,
    CuiCodeEditorResult,
    CuiCodeOpts,
    CuiDiffHunk,
    CuiDiffOpts,
    CuiDiffRange,
    CuiDiffResult,
    CuiDiffRow,
    CuiDiffStats,
    CuiFilterField,
    CuiGridColumn,
    CuiGridOpts,
    CuiJsonOpts,
    CuiListItemOpts,
    CuiMarkdownOpts,
    CuiMarkdownResult,
    CuiTableColumn,
    CuiTableOpts,
    CuiTableSort,
    CuiTimelineOpts,
    CuiTreeNode,
    CuiTreeOpts,
    CuiTreeTableOpts,
    encode_opt,
    encode_str,
    encode_str_array,
    make_text_buffer,
    to_c_color,
    to_c_size,
)
from .._lib import get_cdll
from ..scopes import (
    DataGridScope,
    OpenStateScope,
    ReorderScope,
    TableScope,
    TreeTableScope,
    VirtualListScope,
)
from ..types import (
    CodeEditorResult,
    ColorLike,
    DiffFlags,
    DiffHunk,
    DiffMode,
    DiffRange,
    DiffResult,
    DiffRow,
    DiffRowKind,
    DiffStats,
    FilterField,
    GridColumn,
    MarkdownResult,
    SizeLike,
    TableColumn,
    TableSort,
    Tone,
    TreeFlags,
    TreeNode,
)

_TREE_LABEL_FN = CFUNCTYPE(c_char_p, c_void_p, c_int)
_TREE_CMP_FN = CFUNCTYPE(c_int, c_void_p, c_int, c_int)


def diff_compute(
    old_text: str,
    new_text: str,
    *,
    ignore_eol: bool = False,
    max_hunks: int = 256,
) -> Tuple[List[DiffHunk], DiffStats]:
    """Headless Myers line diff backed by CUI's C99 diff engine (no UI context required)."""
    lib = get_cdll()
    old_b = old_text.encode("utf-8")
    new_b = new_text.encode("utf-8")
    flags = int(DiffFlags.IGNORE_EOL) if ignore_eol else 0
    cap = max(1, int(max_hunks))
    c_hunks = (CuiDiffHunk * cap)()
    c_stats = CuiDiffStats()
    total = int(lib.cui_diff_compute(
        old_b, len(old_b), new_b, len(new_b), flags, c_hunks, cap, ctypes.byref(c_stats)
    ))
    if total > cap:
        c_hunks = (CuiDiffHunk * total)()
        total = int(lib.cui_diff_compute(
            old_b, len(old_b), new_b, len(new_b), flags, c_hunks, total, ctypes.byref(c_stats)
        ))
    hunks = [
        DiffHunk(
            int(c_hunks[i].old_start),
            int(c_hunks[i].old_count),
            int(c_hunks[i].new_start),
            int(c_hunks[i].new_count),
        )
        for i in range(max(0, total))
    ]
    stats = DiffStats(
        added=int(c_stats.added),
        removed=int(c_stats.removed),
        hunks=int(c_stats.hunks),
        old_lines=int(c_stats.old_lines),
        new_lines=int(c_stats.new_lines),
        approximate=bool(c_stats.approximate),
    )
    return hunks, stats


def diff_words(
    old_line: str,
    new_line: str,
    *,
    max_ranges: int = 64,
) -> Tuple[bool, List[DiffRange], List[DiffRange]]:
    """Headless intraline word/token diff backed by CUI's C99 diff engine."""
    lib = get_cdll()
    old_b = old_line.encode("utf-8")
    new_b = new_line.encode("utf-8")
    cap = max(1, int(max_ranges))
    c_old = (CuiDiffRange * cap)()
    c_new = (CuiDiffRange * cap)()
    n_old = c_int(0)
    n_new = c_int(0)
    ok = bool(lib.cui_diff_words(
        old_b, len(old_b), new_b, len(new_b),
        c_old, ctypes.byref(n_old), c_new, ctypes.byref(n_new), cap
    ))
    old_ranges = [DiffRange(int(c_old[i].start), int(c_old[i].length)) for i in range(min(cap, int(n_old.value)))]
    new_ranges = [DiffRange(int(c_new[i].start), int(c_new[i].length)) for i in range(min(cap, int(n_new.value)))]
    return ok, old_ranges, new_ranges


def markdown_apply_task(markdown_text: str, result: MarkdownResult) -> str:
    """Apply a GFM task-list checkbox toggle reported by ``markdown`` and return updated text."""
    return result.apply_task(markdown_text)


def tree_sort(
    nodes: Sequence[TreeNode],
    root: int = -1,
    *,
    key: Optional[Callable[[int], Any]] = None,
    reverse: bool = False,
) -> int:
    """Recursively sort sibling chains in ``nodes`` in-place via ``cui_tree_sort``.

    Returns the new ``root`` index (when ``root >= 0`` and ``root``'s sibling chain is sorted).
    """
    n = len(nodes)
    if n == 0:
        return root
    lib = get_cdll()
    c_nodes = (CuiTreeNode * n)()
    for i, nd in enumerate(nodes):
        c_nodes[i].parent = int(nd.parent)
        c_nodes[i].first_child = int(nd.first_child)
        c_nodes[i].next_sibling = int(nd.next_sibling)
        c_nodes[i].flags = int(nd.flags)
    keys = [key(i) for i in range(n)] if key is not None else list(range(n))
    sign = -1 if reverse else 1

    @_TREE_CMP_FN
    def _cmp(_user: int, a: int, b: int) -> int:
        ka, kb = keys[a], keys[b]
        if ka < kb:
            return -sign
        if ka > kb:
            return sign
        return 0

    new_root = int(lib.cui_tree_sort(c_nodes, n, int(root), ctypes.cast(_cmp, c_void_p), None))
    for i, nd in enumerate(nodes):
        nd.parent = int(c_nodes[i].parent)
        nd.first_child = int(c_nodes[i].first_child)
        nd.next_sibling = int(c_nodes[i].next_sibling)
        nd.flags = TreeFlags(int(c_nodes[i].flags))
    return new_root


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
        self._lib.nexa_virtual_list_begin(
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
        hide_checkboxes: bool = False,
        anchor: Optional[int] = None,
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
            c_cols[i].priority = int(col.priority)

        nrows = int(row_count)
        opts = CuiGridOpts()
        opts.width = to_c_size(width)
        opts.height = to_c_size(height)
        opts.row_height = float(row_height)
        opts.striped = bool(striped)
        opts.hide_checkboxes = bool(hide_checkboxes)

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

        c_anchor = None
        if anchor is not None:
            c_anchor = c_int(int(anchor))
            opts.anchor = ctypes.pointer(c_anchor)
            keep.append(c_anchor)

        first = c_int(0)
        last = c_int(0)
        keep.extend((c_cols, opts))
        vis = bool(self._lib.cui_data_grid_begin_ex(
            self._ctx, encode_str(id, keep), c_cols, ncols, nrows,
            ctypes.byref(first), ctypes.byref(last), ctypes.byref(opts)
        ))
        return DataGridScope(
            self, vis, int(first.value), int(last.value), nrows, c_sel, c_sort, c_cursor, keep, c_anchor
        )

    def tree_table(
        self,
        id: str,
        columns: Sequence[GridColumn],
        nodes: Sequence[TreeNode],
        *,
        width: SizeLike = None,
        height: SizeLike = None,
        row_height: float = 0.0,
        root: int = 0,
        sort: Optional[TableSort] = None,
        cursor: Optional[int] = None,
        guides: bool = True,
        labels: Optional[Sequence[str]] = None,
        label_fn: Optional[Callable[[int], str]] = None,
    ) -> TreeTableScope:
        """Virtualized hierarchical tree-table with multi-column resize, sort, guides, and type-ahead."""
        keep = self._frame_keepalive
        ncols = len(columns)
        c_cols = (CuiGridColumn * ncols)()
        for i, col in enumerate(columns):
            c_cols[i].title = encode_str(col.title, keep)
            c_cols[i].width = float(col.width)
            c_cols[i].align = int(col.align)
            c_cols[i].sortable = bool(col.sortable)
            c_cols[i].fixed = bool(col.fixed)
            c_cols[i].priority = int(col.priority)

        n = len(nodes)
        c_nodes = (CuiTreeNode * max(n, 1))()
        for i, nd in enumerate(nodes):
            c_nodes[i].parent = int(nd.parent)
            c_nodes[i].first_child = int(nd.first_child)
            c_nodes[i].next_sibling = int(nd.next_sibling)
            c_nodes[i].flags = int(nd.flags)

        opts = CuiTreeTableOpts()
        opts.width = to_c_size(width)
        opts.height = to_c_size(height)
        opts.row_height = float(row_height)
        opts.root = int(root)
        opts.guides = bool(guides)

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

        if labels is not None or label_fn is not None:
            encoded_labels = (
                [s.encode("utf-8") for s in labels] if labels is not None else None
            )

            @_TREE_LABEL_FN
            def _cb(_user: int, idx: int) -> Optional[bytes]:
                if encoded_labels is not None:
                    return encoded_labels[idx] if 0 <= idx < len(encoded_labels) else b""
                if label_fn is not None and 0 <= idx < n:
                    b = label_fn(idx).encode("utf-8")
                    keep.append(b)
                    return b
                return b""

            keep.append(_cb)
            if encoded_labels is not None:
                keep.append(encoded_labels)
            opts.label = ctypes.cast(_cb, c_void_p)

        keep.extend((c_cols, c_nodes, opts))
        self._lib.cui_tree_table_begin_ex(
            self._ctx, encode_str(id, keep), c_cols, ncols, c_nodes, n, ctypes.byref(opts)
        )
        return TreeTableScope(self, nodes, c_nodes, n, c_sort, c_cursor, keep)

    def tree_sort(
        self,
        nodes: Sequence[TreeNode],
        root: int = -1,
        *,
        key: Optional[Callable[[int], Any]] = None,
        reverse: bool = False,
    ) -> int:
        return tree_sort(nodes, root, key=key, reverse=reverse)

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

    # ---- CUI 1.1.0: Rich Markdown, Code Editor & Diff Viewer ----

    def markdown(
        self,
        id: str,
        text: str,
        *,
        width: SizeLike = None,
        fit_content: bool = False,
        size: float = 0.0,
        color: ColorLike = None,
        streaming: bool = False,
        compact: bool = False,
    ) -> MarkdownResult:
        """Render CommonMark + GFM markdown (headings, lists, task items, tables, fenced code, alerts, links)."""
        keep = self._frame_keepalive
        raw = encode_str(text, keep)
        opts = CuiMarkdownOpts()
        opts.width = to_c_size(width)
        opts.fit_content = bool(fit_content)
        opts.length = len(raw)
        opts.size = float(size)
        opts.color = to_c_color(color if color is not None else self._fg_current)
        opts.streaming = bool(streaming)
        opts.compact = bool(compact)
        out = CuiMarkdownResult()
        keep.extend((opts, out))
        self._lib.nexa_markdown_ex(
            self._ctx, encode_str(id, keep), raw, ctypes.byref(opts), ctypes.byref(out)
        )
        res = MarkdownResult(
            link=out.link.decode("utf-8", errors="replace") if out.link else None,
            hovered_link=out.hovered_link.decode("utf-8", errors="replace") if out.hovered_link else None,
            task_offset=int(out.task_offset),
            task_line=int(out.task_line),
            task_checked=bool(out.task_checked),
            height=float(out.height),
        )
        self._record_change(bool(res))
        return res

    def markdown_apply_task(self, text: str, result: MarkdownResult) -> str:
        """Apply a GFM task-list checkbox toggle reported by ``markdown`` and return updated text."""
        return result.apply_task(text)

    def code_editor(
        self,
        id: str,
        text: str,
        *,
        lang: Optional[str] = None,
        width: SizeLike = None,
        height: float = 320.0,
        size: float = 0.0,
        tab_size: int = 4,
        use_tabs: bool = False,
        read_only: bool = False,
        no_line_numbers: bool = False,
        autofocus: bool = False,
        placeholder: Optional[str] = None,
        max_bytes: int = 0,
    ) -> CodeEditorResult:
        """Editable multi-line source editor with syntax highlighting, undo/redo, bracket match, and find bar."""
        keep = self._frame_keepalive
        raw_len = len(text.encode("utf-8"))
        cap = int(max_bytes) if max_bytes > 0 else max(4096, raw_len * 2 + 1024)
        buf, cap = make_text_buffer(text, cap)
        opts = CuiCodeEditorOpts()
        opts.lang = encode_opt(lang, keep)
        opts.width = to_c_size(width)
        opts.height = float(height)
        opts.size = float(size)
        opts.tab_size = int(tab_size)
        opts.use_tabs = bool(use_tabs)
        opts.read_only = bool(read_only)
        opts.no_line_numbers = bool(no_line_numbers)
        opts.autofocus = bool(autofocus)
        opts.placeholder = encode_opt(placeholder, keep)
        out = CuiCodeEditorResult()
        keep.extend((buf, opts, out))
        self._lib.nexa_code_editor_ex(
            self._ctx, encode_str(id, keep), buf, cap, ctypes.byref(opts), ctypes.byref(out)
        )
        changed = bool(out.changed)
        new_text = buf.value.decode("utf-8", errors="replace") if changed else text
        self._record_change(changed)
        return CodeEditorResult(
            text=new_text,
            changed=changed,
            refused=bool(out.refused),
            focused=bool(out.focused),
            cursor=int(out.cursor),
            anchor=int(out.anchor),
            line=int(out.line),
            column=int(out.column),
            line_count=int(out.line_count),
            length=int(out.length),
            bracket=int(out.bracket),
            bracket_match=int(out.bracket_match),
            find_matches=int(out.find_matches),
            find_index=int(out.find_index),
        )

    def code_editor_goto(self, id: str, line: int, column: int = 1) -> None:
        keep = self._frame_keepalive
        self._lib.cui_code_editor_goto(self._ctx, encode_str(id, keep), int(line), int(column))

    def code_editor_select(self, id: str, anchor: int, cursor: int) -> None:
        keep = self._frame_keepalive
        self._lib.cui_code_editor_select(self._ctx, encode_str(id, keep), int(anchor), int(cursor))

    def code_editor_find(self, id: str, query: Optional[str] = None) -> None:
        keep = self._frame_keepalive
        self._lib.cui_code_editor_find(self._ctx, encode_str(id, keep), encode_opt(query, keep))

    def diff_view(
        self,
        id: str,
        old_text: str,
        new_text: str,
        *,
        mode: DiffMode = DiffMode.SPLIT,
        language: Optional[str] = None,
        old_title: Optional[str] = None,
        new_title: Optional[str] = None,
        current: Optional[int] = None,
        context: int = 3,
        no_fold: bool = False,
        ignore_eol: bool = False,
        split_min_width: float = 0.0,
        width: SizeLike = None,
        height: float = 340.0,
        size: float = 0.0,
    ) -> DiffResult:
        """Side-by-side or unified inline diff viewer with intraline word highlights and hunk folding."""
        keep = self._frame_keepalive
        opts = CuiDiffOpts()
        opts.mode = int(mode)
        opts.language = encode_opt(language, keep)
        opts.old_title = encode_opt(old_title, keep)
        opts.new_title = encode_opt(new_title, keep)
        opts.context = int(context)
        opts.no_fold = bool(no_fold)
        opts.ignore_eol = bool(ignore_eol)
        opts.split_min_width = float(split_min_width)
        opts.width = to_c_size(width)
        opts.height = float(height)
        opts.size = float(size)
        if current is not None:
            c_cur = c_int(int(current))
            opts.current = ctypes.pointer(c_cur)
            keep.append(c_cur)
        out = CuiDiffResult()
        keep.extend((opts, out))
        self._lib.nexa_diff_view_ex(
            self._ctx,
            encode_str(id, keep),
            encode_str(old_text, keep),
            encode_str(new_text, keep),
            ctypes.byref(opts),
            ctypes.byref(out),
        )
        self._record_change(bool(out.current_changed))
        return DiffResult(
            added=int(out.added),
            removed=int(out.removed),
            changes=int(out.changes),
            current=int(out.current),
            current_changed=bool(out.current_changed),
            mode=DiffMode(int(out.mode)),
            folds=int(out.folds),
            hidden=int(out.hidden),
            recomputed=bool(out.recomputed),
            approximate=bool(out.approximate),
        )

    def diff_view_rows(self, id: str, *, offset: int = 0, max_rows: int = 256) -> List[DiffRow]:
        """Inspect visible/flattened diff rows from a ``diff_view`` widget."""
        keep = self._frame_keepalive
        cap = max(1, int(max_rows))
        c_rows = (CuiDiffRow * cap)()
        total = int(self._lib.cui_diff_view_rows(
            self._ctx, encode_str(id, keep), c_rows, int(offset), cap
        ))
        n = min(cap, max(0, total - int(offset)))
        return [
            DiffRow(
                DiffRowKind(int(c_rows[i].kind)),
                int(c_rows[i].old_line),
                int(c_rows[i].new_line),
                int(c_rows[i].change),
                int(c_rows[i].hidden),
            )
            for i in range(n)
        ]

    def diff_compute(
        self,
        old_text: str,
        new_text: str,
        *,
        ignore_eol: bool = False,
        max_hunks: int = 256,
    ) -> Tuple[List[DiffHunk], DiffStats]:
        return diff_compute(old_text, new_text, ignore_eol=ignore_eol, max_hunks=max_hunks)

    def diff_words(
        self,
        old_line: str,
        new_line: str,
        *,
        max_ranges: int = 64,
    ) -> Tuple[bool, List[DiffRange], List[DiffRange]]:
        return diff_words(old_line, new_line, max_ranges=max_ranges)
