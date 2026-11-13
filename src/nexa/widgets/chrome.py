"""Desktop application chrome: menu bars, toolbars, status bars, and document tab strips."""

from __future__ import annotations

import ctypes
from ctypes import c_bool, c_int
from typing import Optional, Sequence

from .._cdefs import (
    CuiDockPanelOpts,
    CuiDockspaceOpts,
    CuiDocTab,
    CuiDocTabsOpts,
    CuiMenuBarMenuOpts,
    CuiMenuBarOpts,
    CuiStatusBarOpts,
    CuiStatusItemOpts,
    CuiStatusProgressOpts,
    CuiToolbarOpts,
    CuiToolbarRadioOpts,
    CuiToolOpts,
    encode_opt,
    encode_str,
    encode_str_array,
    to_c_size,
)
from ..scopes import ConditionalScope, OpenStateScope, SimpleScope
from ..types import DocTab, DocTabsResult, SizeLike, Tone, ToolbarStyle


class ChromeMixin:
    __slots__ = ()

    # ---- Menu Bar ----

    def menu_bar(self, id: str = "menubar", *, no_border: bool = False) -> SimpleScope:
        keep = self._frame_keepalive
        opts = CuiMenuBarOpts(0, bool(no_border))
        keep.append(opts)
        self._lib.cui_menu_bar_begin(self._ctx, encode_str(id, keep), ctypes.byref(opts))
        return SimpleScope(self._ctx, self._lib.cui_menu_bar_end)

    def menu_bar_menu(
        self,
        label: str,
        *,
        mnemonic: Optional[str] = None,
        width: float = 0.0,
        disabled: bool = False,
    ) -> ConditionalScope:
        keep = self._frame_keepalive
        opts = CuiMenuBarMenuOpts()
        opts.mnemonic = ord(mnemonic[0]) if mnemonic else 0
        opts.width = float(width)
        opts.disabled = bool(disabled)
        keep.append(opts)
        vis = bool(self._lib.cui_menu_bar_menu_begin(self._ctx, encode_str(label, keep), ctypes.byref(opts)))
        return ConditionalScope(self._ctx, self._lib.cui_menu_bar_menu_end, vis)

    # ---- Toolbar ----

    def toolbar(
        self,
        id: str = "toolbar",
        *,
        no_border: bool = False,
        style: ToolbarStyle = ToolbarStyle.PLAIN,
    ) -> SimpleScope:
        """Toolbar strip. ``GROUPED`` puts items in raised groups inside one
        pill (CUI post-1.4), ``FLOATING`` is one bordered pill for bars over
        content; both keep the keys and overflow menu.
        """
        keep = self._frame_keepalive
        opts = CuiToolbarOpts()
        opts.no_border = bool(no_border)
        opts.style = int(style)
        keep.append(opts)
        self._lib.cui_toolbar_begin(self._ctx, encode_str(id, keep), ctypes.byref(opts))
        return SimpleScope(self._ctx, self._lib.cui_toolbar_end)

    def toolbar_button(
        self,
        icon: Optional[str] = None,
        *,
        label: Optional[str] = None,
        tooltip: Optional[str] = None,
        shortcut: Optional[str] = None,
        disabled: bool = False,
        tone: Tone = Tone.NEUTRAL,
        flyout: bool = False,
    ) -> bool:
        keep = self._frame_keepalive
        opts = CuiToolOpts()
        opts.label = encode_opt(label, keep)
        opts.tooltip = encode_opt(tooltip, keep)
        opts.shortcut = encode_opt(shortcut, keep)
        opts.disabled = bool(disabled)
        opts.tone = int(tone)
        opts.flyout = bool(flyout)
        keep.append(opts)
        clicked = bool(self._lib.cui_toolbar_button_ex(
            self._ctx, encode_opt(icon, keep), ctypes.byref(opts)
        ))
        self._record_change(clicked)
        return clicked

    def toolbar_toggle(
        self,
        value: bool,
        icon: Optional[str] = None,
        *,
        label: Optional[str] = None,
        tooltip: Optional[str] = None,
        shortcut: Optional[str] = None,
        disabled: bool = False,
        tone: Tone = Tone.NEUTRAL,
        flyout: bool = False,
    ) -> bool:
        keep = self._frame_keepalive
        c_val = c_bool(bool(value))
        opts = CuiToolOpts()
        opts.label = encode_opt(label, keep)
        opts.tooltip = encode_opt(tooltip, keep)
        opts.shortcut = encode_opt(shortcut, keep)
        opts.toggle = ctypes.pointer(c_val)
        opts.disabled = bool(disabled)
        opts.tone = int(tone)
        opts.flyout = bool(flyout)
        keep.extend((c_val, opts))
        clicked = bool(self._lib.cui_toolbar_button_ex(
            self._ctx, encode_opt(icon, keep), ctypes.byref(opts)
        ))
        self._record_change(clicked)
        return bool(c_val.value)

    def toolbar_separator(self) -> None:
        self._lib.cui_toolbar_separator(self._ctx)

    def toolbar_spacer(self) -> None:
        self._lib.cui_toolbar_spacer(self._ctx)

    def toolbar_group(self) -> SimpleScope:
        """Raised group of items inside a ``GROUPED`` toolbar (CUI post-1.4)."""
        self._lib.cui_toolbar_group_begin(self._ctx)
        return SimpleScope(self._ctx, self._lib.cui_toolbar_group_end)

    def toolbar_radio(
        self,
        id: str,
        icons: Sequence[str],
        index: int,
        *,
        labels: Optional[Sequence[str]] = None,
    ) -> int:
        """Inset radio set inside a toolbar group (CUI post-1.4); ``labels``
        name the icons for the overflow menu. Returns the chosen index.
        """
        keep = self._frame_keepalive
        icon_arr, n = encode_str_array(list(icons), keep)
        c_idx = c_int(int(index))
        opts = CuiToolbarRadioOpts()
        if labels:
            lab_arr, _ = encode_str_array(list(labels), keep)
            opts.labels = lab_arr
        keep.extend((c_idx, opts))
        changed = bool(self._lib.cui_toolbar_radio_ex(
            self._ctx, encode_str(id, keep), icon_arr, n, ctypes.byref(c_idx), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return int(c_idx.value)

    def toolbar_primary(
        self,
        icon: Optional[str] = None,
        *,
        label: Optional[str] = None,
        tooltip: Optional[str] = None,
        shortcut: Optional[str] = None,
        disabled: bool = False,
        tone: Tone = Tone.ACCENT,
        flyout: bool = False,
    ) -> bool:
        """Filled primary action in a toolbar group (CUI post-1.4)."""
        keep = self._frame_keepalive
        opts = CuiToolOpts()
        opts.label = encode_opt(label, keep)
        opts.tooltip = encode_opt(tooltip, keep)
        opts.shortcut = encode_opt(shortcut, keep)
        opts.disabled = bool(disabled)
        opts.tone = int(tone)
        opts.flyout = bool(flyout)
        keep.append(opts)
        clicked = bool(self._lib.cui_toolbar_primary_ex(
            self._ctx, encode_opt(icon, keep), ctypes.byref(opts)
        ))
        self._record_change(clicked)
        return clicked

    def toolbar_cycle(
        self,
        id: str,
        items: Sequence[str],
        index: int,
        *,
        label: Optional[str] = None,
        tooltip: Optional[str] = None,
        shortcut: Optional[str] = None,
        disabled: bool = False,
        tone: Tone = Tone.NEUTRAL,
        flyout: bool = False,
    ) -> int:
        """Small picker that steps through its choices on each click
        (CUI post-1.4), e.g. ``["1x", "2x", "4x"]``. Returns the new index.
        """
        keep = self._frame_keepalive
        arr, n = encode_str_array(list(items), keep)
        c_idx = c_int(int(index))
        opts = CuiToolOpts()
        opts.label = encode_opt(label, keep)
        opts.tooltip = encode_opt(tooltip, keep)
        opts.shortcut = encode_opt(shortcut, keep)
        opts.disabled = bool(disabled)
        opts.tone = int(tone)
        opts.flyout = bool(flyout)
        keep.extend((c_idx, opts))
        changed = bool(self._lib.cui_toolbar_cycle_ex(
            self._ctx, encode_str(id, keep), arr, n, ctypes.byref(c_idx), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return int(c_idx.value)

    def flyout_mark(self) -> None:
        """Corner mark saying the button under the pointer opens a flyout
        (CUI post-1.4)."""
        self._lib.cui_flyout_mark(self._ctx)

    # ---- Status Bar ----

    def status_bar(self, id: str = "statusbar", *, no_border: bool = False) -> SimpleScope:
        keep = self._frame_keepalive
        opts = CuiStatusBarOpts(0, bool(no_border))
        keep.append(opts)
        self._lib.cui_status_bar_begin(self._ctx, encode_str(id, keep), ctypes.byref(opts))
        return SimpleScope(self._ctx, self._lib.cui_status_bar_end)

    def status_bar_spacer(self) -> None:
        self._lib.cui_status_bar_spacer(self._ctx)

    def status_bar_text(
        self,
        text: str,
        *,
        icon: Optional[str] = None,
        tone: Tone = Tone.NEUTRAL,
        tooltip: Optional[str] = None,
        disabled: bool = False,
    ) -> None:
        keep = self._frame_keepalive
        opts = CuiStatusItemOpts()
        opts.icon = encode_opt(icon, keep)
        opts.tone = int(tone)
        opts.tooltip = encode_opt(tooltip, keep)
        opts.disabled = bool(disabled)
        keep.append(opts)
        self._lib.cui_status_bar_text_ex(self._ctx, encode_str(text, keep), ctypes.byref(opts))

    def status_bar_item(
        self,
        label: str,
        *,
        icon: Optional[str] = None,
        tone: Tone = Tone.NEUTRAL,
        tooltip: Optional[str] = None,
        disabled: bool = False,
    ) -> bool:
        keep = self._frame_keepalive
        opts = CuiStatusItemOpts()
        opts.icon = encode_opt(icon, keep)
        opts.tone = int(tone)
        opts.tooltip = encode_opt(tooltip, keep)
        opts.disabled = bool(disabled)
        keep.append(opts)
        clicked = bool(self._lib.cui_status_bar_item_ex(self._ctx, encode_str(label, keep), ctypes.byref(opts)))
        self._record_change(clicked)
        return clicked

    def status_bar_progress(
        self,
        value: float = 0.0,
        *,
        label: Optional[str] = None,
        indeterminate: bool = False,
        width: float = 0.0,
    ) -> None:
        keep = self._frame_keepalive
        opts = CuiStatusProgressOpts()
        opts.label = encode_opt(label, keep)
        opts.indeterminate = bool(indeterminate)
        opts.width = float(width)
        keep.append(opts)
        self._lib.cui_status_bar_progress_ex(self._ctx, float(value), ctypes.byref(opts))

    # ---- Document Tabs ----

    def doc_tabs(
        self,
        id: str,
        tabs: Sequence[DocTab],
        selected: int,
        *,
        shortcuts: bool = False,
        no_close: bool = False,
        no_reorder: bool = False,
    ) -> DocTabsResult:
        keep = self._frame_keepalive
        n = len(tabs)
        arr = (CuiDocTab * n)()
        for i, tb in enumerate(tabs):
            arr[i].title = encode_str(tb.title, keep)
            arr[i].icon = encode_opt(tb.icon, keep)
            arr[i].tooltip = encode_opt(tb.tooltip, keep)
            arr[i].dirty = bool(tb.dirty)
        c_sel = c_int(int(selected))
        opts = CuiDocTabsOpts(0, bool(shortcuts), bool(no_close), bool(no_reorder))
        out_flags = (c_int * 4)()
        keep.extend((arr, opts))
        self._lib.nexa_doc_tabs(
            self._ctx, encode_str(id, keep), arr, n, ctypes.byref(c_sel), ctypes.byref(opts), out_flags
        )
        changed = bool(out_flags[0]) or int(out_flags[1]) >= 0 or int(out_flags[2]) >= 0
        self._record_change(changed)
        return DocTabsResult(
            int(c_sel.value),
            bool(out_flags[0]),
            int(out_flags[1]),
            int(out_flags[2]),
            int(out_flags[3]),
        )

    # ---- Docking Workspace (CUI 1.1.0) ----

    def dockspace(
        self,
        id: str = "dockspace",
        *,
        layout: Optional[str] = None,
        width: SizeLike = None,
        height: SizeLike = None,
        min_panel_width: float = 0.0,
        min_panel_height: float = 0.0,
        shortcuts: bool = True,
    ) -> SimpleScope:
        """Multi-split tabbed docking workspace.

        Optional initial ``layout`` DSL example:
        ``"h0.24([*Explorer],v0.68([*Editor,Diff],[*Console,Hex]))"``
        (with or without the ``"dock1 "`` header prefix).
        """
        keep = self._frame_keepalive
        norm_layout = layout
        if norm_layout is not None:
            s = norm_layout.strip()
            if s and not s.startswith("dock1 "):
                norm_layout = "dock1 " + s
        opts = CuiDockspaceOpts()
        opts.layout = encode_opt(norm_layout, keep)
        opts.width = to_c_size(width)
        opts.height = to_c_size(height)
        opts.min_panel_width = float(min_panel_width)
        opts.min_panel_height = float(min_panel_height)
        opts.shortcuts = bool(shortcuts)
        keep.append(opts)
        self._lib.cui_dockspace_begin_ex(self._ctx, encode_str(id, keep), ctypes.byref(opts))
        return SimpleScope(self._ctx, self._lib.cui_dockspace_end)

    def dock_panel(
        self,
        title: str,
        is_open: Optional[bool] = None,
        *,
        icon: Optional[str] = None,
        dirty: bool = False,
    ) -> OpenStateScope:
        """Dockable panel inside an active ``dockspace``; check ``if panel:`` before building body."""
        keep = self._frame_keepalive
        opts = CuiDockPanelOpts()
        opts.icon = encode_opt(icon, keep)
        opts.dirty = bool(dirty)
        keep.append(opts)
        if is_open is None:
            vis = bool(self._lib.cui_dock_panel_begin_ex(
                self._ctx, encode_str(title, keep), None, ctypes.byref(opts)
            ))
            return OpenStateScope(self._ctx, self._lib.cui_dock_panel_end, vis, True)
        c_open = c_bool(bool(is_open))
        keep.append(c_open)
        vis = bool(self._lib.cui_dock_panel_begin_ex(
            self._ctx, encode_str(title, keep), ctypes.byref(c_open), ctypes.byref(opts)
        ))
        if bool(c_open.value) != bool(is_open):
            self._record_change(True)
        return OpenStateScope(self._ctx, self._lib.cui_dock_panel_end, vis, bool(c_open.value))

    def dock_save(self, id: str = "dockspace") -> str:
        """Serialize the current split/tab layout of ``dockspace(id)`` into a string."""
        keep = self._frame_keepalive
        cid = encode_str(id, keep)
        needed = int(self._lib.cui_dock_save(self._ctx, cid, None, 0))
        if needed <= 0:
            return ""
        buf = ctypes.create_string_buffer(needed + 1)
        self._lib.cui_dock_save(self._ctx, cid, buf, needed + 1)
        return buf.value.decode("utf-8", errors="replace")

    def dock_load(self, id: str, layout: str) -> bool:
        """Restore a serialized layout string into ``dockspace(id)``."""
        keep = self._frame_keepalive
        s = layout.strip()
        norm_layout = ("dock1 " + s) if (s and not s.startswith("dock1 ")) else s
        return bool(self._lib.cui_dock_load(
            self._ctx, encode_str(id, keep), encode_str(norm_layout, keep)
        ))
