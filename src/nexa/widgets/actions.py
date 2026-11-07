"""Buttons, segmented controls, toggle groups, command palette, and action triggers."""

from __future__ import annotations

import ctypes
from ctypes import c_bool, c_int
from typing import List, Optional, Sequence, Tuple

from .._cdefs import (
    CuiButtonOpts,
    CuiCommand,
    CuiConfirmOpts,
    CuiHoldOpts,
    CuiReaction,
    CuiSegmentedOpts,
    CuiSpeedAction,
    CuiSpeedDialOpts,
    CuiSplitButtonOpts,
    CuiStatusButtonOpts,
    CuiSwipeAction,
    CuiToggleGroupOpts,
    encode_opt,
    encode_str,
    encode_str_array,
    to_c_color,
    to_c_size,
)
from ..scopes import SimpleScope, SwipeScope
from ..types import (
    ButtonVariant,
    ColorLike,
    Command,
    ControlSize,
    Placement,
    Reaction,
    SizeLike,
    SpeedAction,
    Status,
    SwipeAction,
)


def _build_button_opts(
    keep: list,
    *,
    variant: ButtonVariant = ButtonVariant.DEFAULT,
    size: ControlSize = ControlSize.MD,
    icon: Optional[str] = None,
    icon_right: Optional[str] = None,
    disabled: bool = False,
    loading: bool = False,
    full_width: bool = False,
    selected: bool = False,
    tooltip: Optional[str] = None,
    shortcut: Optional[str] = None,
    width: SizeLike = None,
    color: ColorLike = None,
) -> CuiButtonOpts:
    opts = CuiButtonOpts()
    opts.variant = int(variant)
    opts.size = int(size)
    opts.icon = encode_opt(icon, keep)
    opts.icon_right = encode_opt(icon_right, keep)
    opts.disabled = bool(disabled)
    opts.loading = bool(loading)
    opts.full_width = bool(full_width)
    opts.selected = bool(selected)
    opts.tooltip = encode_opt(tooltip, keep)
    opts.shortcut = encode_opt(shortcut, keep)
    opts.width = to_c_size(width)
    opts.color = to_c_color(color)
    keep.append(opts)
    return opts


class ActionsMixin:
    __slots__ = ()

    def button(self, label: str, **kwargs) -> bool:
        keep = self._frame_keepalive
        opts = _build_button_opts(keep, **kwargs)
        clicked = bool(self._lib.cui_button_ex(self._ctx, encode_str(label, keep), ctypes.byref(opts)))
        self._record_change(clicked)
        return clicked

    def icon_button(self, icon: str, **kwargs) -> bool:
        keep = self._frame_keepalive
        opts = _build_button_opts(keep, **kwargs)
        clicked = bool(self._lib.cui_icon_button_ex(self._ctx, encode_str(icon, keep), ctypes.byref(opts)))
        self._record_change(clicked)
        return clicked

    def button_group(self) -> SimpleScope:
        self._lib.cui_button_group_begin(self._ctx)
        return SimpleScope(self._ctx, self._lib.cui_button_group_end)

    def copy_button(self, id: str, text_to_copy: str) -> bool:
        keep = self._frame_keepalive
        clicked = bool(self._lib.cui_copy_button(
            self._ctx, encode_str(id, keep), encode_str(text_to_copy, keep)
        ))
        self._record_change(clicked)
        return clicked

    def hold_button(
        self,
        label: str,
        *,
        duration: float = 0.0,
        icon: Optional[str] = None,
        variant: ButtonVariant = ButtonVariant.DEFAULT,
    ) -> bool:
        keep = self._frame_keepalive
        opts = CuiHoldOpts()
        opts.duration = float(duration)
        opts.icon = encode_opt(icon, keep)
        opts.variant = int(variant)
        keep.append(opts)
        fired = bool(self._lib.cui_hold_button_ex(self._ctx, encode_str(label, keep), ctypes.byref(opts)))
        self._record_change(fired)
        return fired

    def confirm_button(
        self,
        label: str,
        *,
        confirm_label: Optional[str] = None,
        icon: Optional[str] = None,
        variant: ButtonVariant = ButtonVariant.DEFAULT,
        size: ControlSize = ControlSize.MD,
        timeout: float = 0.0,
    ) -> bool:
        keep = self._frame_keepalive
        opts = CuiConfirmOpts()
        opts.confirm_label = encode_opt(confirm_label, keep)
        opts.icon = encode_opt(icon, keep)
        opts.variant = int(variant)
        opts.size = int(size)
        opts.timeout = float(timeout)
        keep.append(opts)
        confirmed = bool(self._lib.cui_confirm_button_ex(self._ctx, encode_str(label, keep), ctypes.byref(opts)))
        self._record_change(confirmed)
        return confirmed

    def status_button(
        self,
        label: str,
        status: Status = Status.IDLE,
        *,
        busy_label: Optional[str] = None,
        success_label: Optional[str] = None,
        error_label: Optional[str] = None,
        icon: Optional[str] = None,
        variant: ButtonVariant = ButtonVariant.PRIMARY,
        size: ControlSize = ControlSize.MD,
    ) -> bool:
        keep = self._frame_keepalive
        opts = CuiStatusButtonOpts()
        opts.busy_label = encode_opt(busy_label, keep)
        opts.success_label = encode_opt(success_label, keep)
        opts.error_label = encode_opt(error_label, keep)
        opts.icon = encode_opt(icon, keep)
        opts.variant = int(variant)
        opts.size = int(size)
        keep.append(opts)
        clicked = bool(self._lib.cui_status_button_ex(
            self._ctx, encode_str(label, keep), int(status), ctypes.byref(opts)
        ))
        self._record_change(clicked)
        return clicked

    def split_button(
        self,
        label: str,
        items: Sequence[str],
        *,
        variant: ButtonVariant = ButtonVariant.PRIMARY,
        size: ControlSize = ControlSize.MD,
        icon: Optional[str] = None,
        item_icons: Optional[Sequence[Optional[str]]] = None,
        disabled: bool = False,
    ) -> int:
        keep = self._frame_keepalive
        arr, n = encode_str_array(items, keep)
        icons_arr, _ = encode_str_array(item_icons, keep) if item_icons else (None, 0)
        opts = CuiSplitButtonOpts()
        opts.variant = int(variant)
        opts.size = int(size)
        opts.icon = encode_opt(icon, keep)
        if icons_arr is not None:
            opts.item_icons = icons_arr
        opts.disabled = bool(disabled)
        keep.append(opts)
        res = int(self._lib.cui_split_button_ex(self._ctx, encode_str(label, keep), arr, n, ctypes.byref(opts)))
        self._record_change(res >= 0)
        return res

    def segmented(
        self,
        id: str,
        items: Sequence[str],
        index: int,
        *,
        size: ControlSize = ControlSize.MD,
        full_width: bool = False,
        icons: Optional[Sequence[Optional[str]]] = None,
    ) -> int:
        keep = self._frame_keepalive
        arr, n = encode_str_array(items, keep)
        icons_arr, _ = encode_str_array(icons, keep) if icons else (None, 0)
        c_idx = c_int(int(index))
        opts = CuiSegmentedOpts()
        opts.size = int(size)
        opts.full_width = bool(full_width)
        if icons_arr is not None:
            opts.icons = icons_arr
        keep.append(opts)
        changed = bool(self._lib.cui_segmented_ex(
            self._ctx, encode_str(id, keep), arr, n, ctypes.byref(c_idx), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return int(c_idx.value)

    def toggle_group(
        self,
        id: str,
        labels: Sequence[str],
        values: Sequence[bool],
        *,
        icons: Optional[Sequence[Optional[str]]] = None,
        exclusive: bool = False,
        icon_only: bool = False,
        size: ControlSize = ControlSize.MD,
    ) -> List[bool]:
        keep = self._frame_keepalive
        n = len(labels)
        if len(values) != n:
            raise ValueError(f"toggle_group values length ({len(values)}) must match labels length ({n})")
        arr, _ = encode_str_array(labels, keep)
        icons_arr, _ = encode_str_array(icons, keep) if icons else (None, 0)
        c_vals = (c_bool * n)(*(bool(v) for v in values))
        opts = CuiToggleGroupOpts()
        if icons_arr is not None:
            opts.icons = icons_arr
        opts.exclusive = bool(exclusive)
        opts.icon_only = bool(icon_only)
        opts.size = int(size)
        keep.extend((c_vals, opts))
        changed = bool(self._lib.cui_toggle_group_ex(
            self._ctx, encode_str(id, keep), arr, n, c_vals, ctypes.byref(opts)
        ))
        self._record_change(changed)
        return [bool(c_vals[i]) for i in range(n)]

    def reactions(self, id: str, items: Sequence[Reaction]) -> Tuple[List[Reaction], int]:
        keep = self._frame_keepalive
        n = len(items)
        arr = (CuiReaction * n)()
        for i, r in enumerate(items):
            arr[i].icon = encode_str(r.icon, keep)
            arr[i].count = int(r.count)
            arr[i].active = bool(r.active)
        keep.append(arr)
        clicked_idx = int(self._lib.cui_reactions(self._ctx, encode_str(id, keep), arr, n))
        self._record_change(clicked_idx >= 0)
        updated = [Reaction(items[i].icon, int(arr[i].count), bool(arr[i].active)) for i in range(n)]
        return updated, clicked_idx

    def speed_dial(
        self,
        id: str,
        actions: Sequence[SpeedAction],
        *,
        icon: Optional[str] = None,
        placement: Placement = Placement.TOP,
        tooltip: Optional[str] = None,
    ) -> int:
        keep = self._frame_keepalive
        n = len(actions)
        arr = (CuiSpeedAction * n)()
        for i, a in enumerate(actions):
            arr[i].icon = encode_str(a.icon, keep)
            arr[i].label = encode_str(a.label, keep)
        opts = CuiSpeedDialOpts()
        opts.icon = encode_opt(icon, keep)
        opts.placement = int(placement)
        opts.tooltip = encode_opt(tooltip, keep)
        keep.extend((arr, opts))
        chosen = int(self._lib.cui_speed_dial_ex(
            self._ctx, encode_str(id, keep), arr, n, ctypes.byref(opts)
        ))
        self._record_change(chosen >= 0)
        return chosen

    def theme_switcher(self, mode: int, *, with_system: bool = False) -> int:
        c_mode = c_int(int(mode))
        changed = bool(self._lib.cui_theme_switcher(self._ctx, ctypes.byref(c_mode), bool(with_system)))
        self._record_change(changed)
        return int(c_mode.value)

    def theme_toggle(self) -> bool:
        toggled = bool(self._lib.cui_theme_toggle(self._ctx))
        self._record_change(toggled)
        return toggled

    def swipe_item(
        self,
        id: str,
        *,
        left: Sequence[SwipeAction] = (),
        right: Sequence[SwipeAction] = (),
    ) -> SwipeScope:
        keep = self._frame_keepalive
        nl = len(left)
        nr = len(right)
        l_arr = (CuiSwipeAction * nl)() if nl else None
        r_arr = (CuiSwipeAction * nr)() if nr else None
        for i, a in enumerate(left):
            l_arr[i].icon = encode_opt(a.icon, keep)
            l_arr[i].label = encode_str(a.label, keep)
            l_arr[i].tone = int(a.tone)
        for i, a in enumerate(right):
            r_arr[i].icon = encode_opt(a.icon, keep)
            r_arr[i].label = encode_str(a.label, keep)
            r_arr[i].tone = int(a.tone)
        if l_arr is not None:
            keep.append(l_arr)
        if r_arr is not None:
            keep.append(r_arr)
        self._lib.cui_swipe_item_begin(self._ctx, encode_str(id, keep), l_arr, nl, r_arr, nr)
        return SwipeScope(self, keep)

    def command_palette(self, is_open: bool, commands: Sequence[Command]) -> Tuple[bool, int]:
        """Spotlight-style command palette; returns ``(is_open, chosen_index_or_neg1)``."""
        keep = self._frame_keepalive
        c_open = c_bool(bool(is_open))
        n = len(commands)
        arr = (CuiCommand * n)()
        for i, cmd in enumerate(commands):
            arr[i].title = encode_str(cmd.title, keep)
            arr[i].icon = encode_opt(cmd.icon, keep)
            arr[i].group = encode_opt(cmd.group, keep)
            arr[i].shortcut = encode_opt(cmd.shortcut, keep)
        keep.append(arr)
        chosen = int(self._lib.cui_command_palette(self._ctx, ctypes.byref(c_open), arr, n))
        new_open = bool(c_open.value)
        self._record_change(chosen >= 0 or new_open != is_open)
        return new_open, chosen
