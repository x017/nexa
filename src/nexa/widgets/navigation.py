"""Navigation components: tabs, sidebar nav, breadcrumbs, pagination, steppers, tab bar, dock, TOC."""

from __future__ import annotations

import ctypes
from ctypes import c_int
from typing import Optional, Sequence

from .._cdefs import (
    CuiDockItemOpts,
    CuiDockOpts,
    CuiNavOpts,
    CuiTabBarItem,
    CuiTabBarOpts,
    CuiTabsOpts,
    CuiTocItem,
    encode_opt,
    encode_str,
    encode_str_array,
    to_c_color,
    to_c_size,
)
from ..scopes import SimpleScope
from ..types import ColorLike, SizeLike, TabBarItem, TabsVariant, TocItem


class NavigationMixin:
    __slots__ = ()

    def tabs(
        self,
        id: str,
        items: Sequence[str],
        index: int,
        *,
        variant: TabsVariant = TabsVariant.UNDERLINE,
        icons: Optional[Sequence[Optional[str]]] = None,
        full_width: bool = False,
    ) -> int:
        keep = self._frame_keepalive
        arr, n = encode_str_array(items, keep)
        icons_arr, _ = encode_str_array(icons, keep) if icons else (None, 0)
        c_idx = c_int(int(index))
        opts = CuiTabsOpts()
        opts.variant = int(variant)
        if icons_arr is not None:
            opts.icons = icons_arr
        opts.full_width = bool(full_width)
        keep.append(opts)
        changed = bool(self._lib.cui_tabs_ex(
            self._ctx, encode_str(id, keep), arr, n, ctypes.byref(c_idx), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return int(c_idx.value)

    def nav_item(
        self,
        label: str,
        *,
        icon: Optional[str] = None,
        badge: Optional[str] = None,
        selected: bool = False,
        group: Optional[str] = None,
    ) -> bool:
        keep = self._frame_keepalive
        opts = CuiNavOpts()
        opts.icon = encode_opt(icon, keep)
        opts.badge = encode_opt(badge, keep)
        opts.selected = bool(selected)
        opts.group = encode_opt(group, keep)
        keep.append(opts)
        clicked = bool(self._lib.cui_nav_item_ex(self._ctx, encode_str(label, keep), ctypes.byref(opts)))
        self._record_change(clicked)
        return clicked

    def nav_section(self, title: str) -> None:
        self._lib.cui_nav_section(self._ctx, encode_str(title, self._frame_keepalive))

    def breadcrumb(self, items: Sequence[str]) -> int:
        keep = self._frame_keepalive
        arr, n = encode_str_array(items, keep)
        clicked = int(self._lib.cui_breadcrumb(self._ctx, arr, n))
        self._record_change(clicked >= 0)
        return clicked

    def pagination(self, id: str, page: int, page_count: int) -> int:
        keep = self._frame_keepalive
        c_page = c_int(int(page))
        changed = bool(self._lib.cui_pagination(
            self._ctx, encode_str(id, keep), ctypes.byref(c_page), int(page_count)
        ))
        self._record_change(changed)
        return int(c_page.value)

    def stepper(self, steps: Sequence[str], current: int) -> None:
        keep = self._frame_keepalive
        arr, n = encode_str_array(steps, keep)
        self._lib.cui_stepper(self._ctx, arr, n, int(current))

    def tab_bar(
        self,
        id: str,
        items: Sequence[TabBarItem],
        selected: int,
        *,
        width: SizeLike = None,
        labels_on_selected_only: bool = False,
    ) -> int:
        keep = self._frame_keepalive
        n = len(items)
        arr = (CuiTabBarItem * n)()
        for i, it in enumerate(items):
            arr[i].icon = encode_str(it.icon, keep)
            arr[i].label = encode_str(it.label, keep)
            arr[i].badge = int(it.badge)
        c_sel = c_int(int(selected))
        opts = CuiTabBarOpts()
        opts.width = to_c_size(width)
        opts.labels_on_selected_only = bool(labels_on_selected_only)
        keep.extend((arr, opts))
        changed = bool(self._lib.cui_tab_bar_ex(
            self._ctx, encode_str(id, keep), arr, n, ctypes.byref(c_sel), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return int(c_sel.value)

    def dock(self, id: str, *, size: float = 0.0, magnify: float = 0.0) -> SimpleScope:
        keep = self._frame_keepalive
        opts = CuiDockOpts(0, float(size), float(magnify))
        keep.append(opts)
        self._lib.cui_dock_begin(self._ctx, encode_str(id, keep), ctypes.byref(opts))
        return SimpleScope(self._ctx, self._lib.cui_dock_end)

    def dock_item(
        self,
        icon: str,
        label: str,
        *,
        color: ColorLike = None,
        running: bool = False,
        badge: int = 0,
    ) -> bool:
        keep = self._frame_keepalive
        opts = CuiDockItemOpts()
        opts.color = to_c_color(color)
        opts.running = bool(running)
        opts.badge = int(badge)
        keep.append(opts)
        clicked = bool(self._lib.cui_dock_item_ex(
            self._ctx, encode_str(icon, keep), encode_str(label, keep), ctypes.byref(opts)
        ))
        self._record_change(clicked)
        return clicked

    def dock_separator(self) -> None:
        self._lib.cui_dock_separator(self._ctx)

    def toc(self, scroll_id: str, items: Sequence[TocItem]) -> int:
        keep = self._frame_keepalive
        n = len(items)
        arr = (CuiTocItem * n)()
        for i, it in enumerate(items):
            arr[i].title = encode_str(it.title, keep)
            arr[i].anchor = encode_str(it.anchor, keep)
            arr[i].level = int(it.level)
        keep.append(arr)
        return int(self._lib.cui_toc(self._ctx, encode_str(scroll_id, keep), arr, n))

    def toc_anchor(self, anchor: str) -> None:
        self._lib.cui_toc_anchor(self._ctx, encode_str(anchor, self._frame_keepalive))
