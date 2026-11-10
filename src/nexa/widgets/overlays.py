"""Overlays, menus, popovers, dialogs, sheets, hover cards, accordions, and disclosure widgets."""

from __future__ import annotations

import ctypes
from ctypes import c_bool
from typing import Optional

from .._cdefs import (
    CuiConfirmPopoverOpts,
    CuiDialogOpts,
    CuiExpandableCardOpts,
    CuiExpandableTextOpts,
    CuiHoverCardOpts,
    CuiMenuItemOpts,
    CuiMenuOpts,
    CuiPopoverOpts,
    CuiSheetOpts,
    CuiUserMenuOpts,
    encode_opt,
    encode_str,
    to_c_color,
)
from ..scopes import ConditionalScope, OpenStateScope, SimpleScope
from ..types import ButtonVariant, ColorLike, Placement, Side, Tone


class OverlaysMixin:
    __slots__ = ()

    # ---- Popovers & Hover Cards ----

    def popover(
        self,
        id: str,
        *,
        placement: Placement = Placement.BOTTOM_START,
        width: float = 0.0,
        pad: float = 0.0,
        gap: float = 0.0,
    ) -> ConditionalScope:
        keep = self._frame_keepalive
        opts = CuiPopoverOpts()
        opts.placement = int(placement)
        opts.width = float(width)
        opts.pad = float(pad)
        opts.gap = float(gap)
        keep.append(opts)
        vis = bool(self._lib.cui_popover_begin(self._ctx, encode_str(id, keep), ctypes.byref(opts)))
        return ConditionalScope(self._ctx, self._lib.cui_popover_end, vis)

    def popover_open(self, id: str) -> None:
        self._lib.cui_popover_open(self._ctx, encode_str(id, self._frame_keepalive))

    def popover_close(self, id: str) -> None:
        self._lib.cui_popover_close(self._ctx, encode_str(id, self._frame_keepalive))

    def popover_toggle(self, id: str) -> None:
        self._lib.cui_popover_toggle(self._ctx, encode_str(id, self._frame_keepalive))

    def popover_is_open(self, id: str) -> bool:
        return bool(self._lib.cui_popover_is_open(self._ctx, encode_str(id, self._frame_keepalive)))

    def hover_card(
        self,
        id: str,
        *,
        placement: Placement = Placement.BOTTOM_START,
        width: float = 0.0,
        delay: float = 0.0,
    ) -> ConditionalScope:
        keep = self._frame_keepalive
        opts = CuiHoverCardOpts()
        opts.placement = int(placement)
        opts.width = float(width)
        opts.delay = float(delay)
        keep.append(opts)
        vis = bool(self._lib.cui_hover_card_begin(self._ctx, encode_str(id, keep), ctypes.byref(opts)))
        return ConditionalScope(self._ctx, self._lib.cui_hover_card_end, vis)

    def confirm_popover(
        self,
        id: str,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        confirm_label: Optional[str] = None,
        cancel_label: Optional[str] = None,
        danger: bool = False,
        placement: Placement = Placement.BOTTOM_START,
    ) -> bool:
        keep = self._frame_keepalive
        opts = CuiConfirmPopoverOpts()
        opts.title = encode_opt(title, keep)
        opts.description = encode_opt(description, keep)
        opts.confirm_label = encode_opt(confirm_label, keep)
        opts.cancel_label = encode_opt(cancel_label, keep)
        opts.danger = bool(danger)
        opts.placement = int(placement)
        keep.append(opts)
        confirmed = bool(self._lib.cui_confirm_popover_ex(self._ctx, encode_str(id, keep), ctypes.byref(opts)))
        self._record_change(confirmed)
        return confirmed

    def confirm_popover_open(self, id: str) -> None:
        """Open a ``confirm_popover`` anchored to the preceding widget (alias for ``popover_open``)."""
        self.popover_open(id)

    def tooltip(self, text: str) -> None:
        self._lib.cui_tooltip(self._ctx, encode_str(text, self._frame_keepalive))

    # ---- Menus ----

    def menu(
        self,
        label: str,
        *,
        icon: Optional[str] = None,
        variant: ButtonVariant = ButtonVariant.DEFAULT,
        placement: Placement = Placement.BOTTOM_START,
        width: float = 0.0,
        icon_only: bool = False,
    ) -> ConditionalScope:
        keep = self._frame_keepalive
        opts = CuiMenuOpts()
        opts.icon = encode_opt(icon, keep)
        opts.variant = int(variant)
        opts.placement = int(placement)
        opts.width = float(width)
        opts.icon_only = bool(icon_only)
        keep.append(opts)
        vis = bool(self._lib.cui_menu_begin(self._ctx, encode_str(label, keep), ctypes.byref(opts)))
        return ConditionalScope(self._ctx, self._lib.cui_menu_end, vis)

    def context_menu(self, id: str) -> ConditionalScope:
        vis = bool(self._lib.cui_context_menu_begin(self._ctx, encode_str(id, self._frame_keepalive)))
        return ConditionalScope(self._ctx, self._lib.cui_context_menu_end, vis)

    def user_menu(
        self,
        name: str,
        *,
        detail: Optional[str] = None,
        status: Optional[str] = None,
        avatar: int = 0,
        compact: bool = False,
        placement: Placement = Placement.TOP_START,
        width: float = 0.0,
    ) -> ConditionalScope:
        keep = self._frame_keepalive
        opts = CuiUserMenuOpts()
        opts.detail = encode_opt(detail, keep)
        opts.status = encode_opt(status, keep)
        opts.avatar = int(avatar)
        opts.compact = bool(compact)
        opts.placement = int(placement)
        opts.width = float(width)
        keep.append(opts)
        vis = bool(self._lib.cui_user_menu_begin(self._ctx, encode_str(name, keep), ctypes.byref(opts)))
        return ConditionalScope(self._ctx, self._lib.cui_user_menu_end, vis)

    def menu_item(
        self,
        label: str,
        *,
        icon: Optional[str] = None,
        shortcut: Optional[str] = None,
        danger: bool = False,
        disabled: bool = False,
        checked: bool = False,
    ) -> bool:
        keep = self._frame_keepalive
        opts = CuiMenuItemOpts()
        opts.icon = encode_opt(icon, keep)
        opts.shortcut = encode_opt(shortcut, keep)
        opts.danger = bool(danger)
        opts.disabled = bool(disabled)
        opts.checked = bool(checked)
        keep.append(opts)
        chosen = bool(self._lib.cui_menu_item_ex(self._ctx, encode_str(label, keep), ctypes.byref(opts)))
        self._record_change(chosen)
        return chosen

    def menu_separator(self) -> None:
        self._lib.cui_menu_separator(self._ctx)

    def menu_label(self, text: str) -> None:
        self._lib.cui_menu_label(self._ctx, encode_str(text, self._frame_keepalive))

    # ---- Modal Dialogs & Sheets ----

    def dialog(
        self,
        title: str,
        is_open: bool,
        *,
        description: Optional[str] = None,
        width: float = 0.0,
        no_close_button: bool = False,
        persistent: bool = False,
    ) -> OpenStateScope:
        keep = self._frame_keepalive
        c_open = c_bool(bool(is_open))
        opts = CuiDialogOpts()
        opts.description = encode_opt(description, keep)
        opts.width = float(width)
        opts.no_close_button = bool(no_close_button)
        opts.persistent = bool(persistent)
        keep.extend((c_open, opts))
        vis = bool(self._lib.cui_dialog_begin(
            self._ctx, encode_str(title, keep), ctypes.byref(c_open), ctypes.byref(opts)
        ))
        if bool(c_open.value) != bool(is_open):
            self._record_change(True)
        return OpenStateScope(
            self._ctx, self._lib.cui_dialog_end, vis, bool(c_open.value),
            request_redraw=self._lib.cui_request_redraw,
        )

    def dialog_footer(self) -> SimpleScope:
        self._lib.cui_dialog_footer_begin(self._ctx)
        return SimpleScope(self._ctx, self._lib.cui_dialog_footer_end)

    def sheet(
        self,
        title: str,
        is_open: bool,
        *,
        side: Side = Side.RIGHT,
        size: float = 0.0,
        description: Optional[str] = None,
    ) -> OpenStateScope:
        keep = self._frame_keepalive
        c_open = c_bool(bool(is_open))
        opts = CuiSheetOpts()
        opts.side = int(side)
        opts.size = float(size)
        opts.description = encode_opt(description, keep)
        keep.extend((c_open, opts))
        vis = bool(self._lib.cui_sheet_begin(
            self._ctx, encode_str(title, keep), ctypes.byref(c_open), ctypes.byref(opts)
        ))
        if bool(c_open.value) != bool(is_open):
            self._record_change(True)
        return OpenStateScope(
            self._ctx, self._lib.cui_sheet_end, vis, bool(c_open.value),
            request_redraw=self._lib.cui_request_redraw,
        )

    # ---- Accordion & Expandable Disclosure ----

    def accordion(self, title: str, is_open: bool) -> OpenStateScope:
        keep = self._frame_keepalive
        c_open = c_bool(bool(is_open))
        keep.append(c_open)
        vis = bool(self._lib.cui_accordion_begin(
            self._ctx, encode_str(title, keep), ctypes.byref(c_open)
        ))
        if bool(c_open.value) != bool(is_open):
            self._record_change(True)
        return OpenStateScope(
            self._ctx, self._lib.cui_accordion_end, vis, bool(c_open.value),
            request_redraw=self._lib.cui_request_redraw,
        )

    def expandable_card(
        self,
        title: str,
        is_open: bool,
        *,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        badge: Optional[str] = None,
        badge_tone: Tone = Tone.NEUTRAL,
    ) -> OpenStateScope:
        keep = self._frame_keepalive
        c_open = c_bool(bool(is_open))
        opts = CuiExpandableCardOpts()
        opts.description = encode_opt(description, keep)
        opts.icon = encode_opt(icon, keep)
        opts.badge = encode_opt(badge, keep)
        opts.badge_tone = int(badge_tone)
        keep.extend((c_open, opts))
        vis = bool(self._lib.cui_expandable_card_begin(
            self._ctx, encode_str(title, keep), ctypes.byref(c_open), ctypes.byref(opts)
        ))
        if bool(c_open.value) != bool(is_open):
            self._record_change(True)
        return OpenStateScope(
            self._ctx, self._lib.cui_expandable_card_end, vis, bool(c_open.value),
            request_redraw=self._lib.cui_request_redraw,
        )

    def expandable_text(
        self,
        id: str,
        text: str,
        *,
        lines: int = 3,
        size: float = 0.0,
        color: ColorLike = None,
        fade_to: ColorLike = None,
    ) -> bool:
        keep = self._frame_keepalive
        opts = CuiExpandableTextOpts()
        opts.lines = int(lines)
        opts.size = float(size)
        opts.color = to_c_color(color)
        opts.fade_to = to_c_color(fade_to)
        keep.append(opts)
        return bool(self._lib.cui_expandable_text_ex(
            self._ctx, encode_str(id, keep), encode_str(text, keep), ctypes.byref(opts)
        ))
