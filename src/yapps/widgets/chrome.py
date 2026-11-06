"""Desktop application chrome: menu bars, toolbars, status bars, and document tab strips."""

from __future__ import annotations

import ctypes
from ctypes import c_bool, c_int
from typing import Optional, Sequence

from .._cdefs import (
    CuiDocTab,
    CuiDocTabsOpts,
    CuiMenuBarMenuOpts,
    CuiMenuBarOpts,
    CuiStatusBarOpts,
    CuiStatusItemOpts,
    CuiStatusProgressOpts,
    CuiToolbarOpts,
    CuiToolOpts,
    encode_opt,
    encode_str,
)
from ..scopes import ConditionalScope, SimpleScope
from ..types import DocTab, DocTabsResult, Tone


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

    def toolbar(self, id: str = "toolbar", *, no_border: bool = False) -> SimpleScope:
        keep = self._frame_keepalive
        opts = CuiToolbarOpts(0, bool(no_border))
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
    ) -> bool:
        keep = self._frame_keepalive
        opts = CuiToolOpts()
        opts.label = encode_opt(label, keep)
        opts.tooltip = encode_opt(tooltip, keep)
        opts.shortcut = encode_opt(shortcut, keep)
        opts.disabled = bool(disabled)
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
    ) -> bool:
        keep = self._frame_keepalive
        c_val = c_bool(bool(value))
        opts = CuiToolOpts()
        opts.label = encode_opt(label, keep)
        opts.tooltip = encode_opt(tooltip, keep)
        opts.shortcut = encode_opt(shortcut, keep)
        opts.toggle = ctypes.pointer(c_val)
        opts.disabled = bool(disabled)
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
        self._lib.yapps_doc_tabs(
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
