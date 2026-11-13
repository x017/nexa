"""Value-returning selection controls: checkbox, switch, radio, sliders, chips, rating, tiles."""

from __future__ import annotations

import ctypes
from ctypes import c_bool, c_float, c_int
from typing import Optional, Sequence, Tuple

from .._cdefs import (
    CuiCheckOpts,
    CuiChipOpts,
    CuiChoice,
    CuiRadioCardsOpts,
    CuiSelectionAction,
    CuiSelectionBarOpts,
    CuiSliderOpts,
    CuiTileOpts,
    encode_opt,
    encode_str,
    encode_str_array,
    to_c_color,
    to_c_size,
)
from ..types import Choice, ColorLike, SelectionAction, SizeLike


class SelectionMixin:
    __slots__ = ()

    def checkbox(
        self,
        label: str,
        value: bool,
        *,
        description: Optional[str] = None,
        disabled: bool = False,
        indeterminate: bool = False,
    ) -> bool:
        keep = self._frame_keepalive
        c_val = c_bool(bool(value))
        opts = CuiCheckOpts()
        opts.description = encode_opt(description, keep)
        opts.disabled = bool(disabled)
        opts.indeterminate = bool(indeterminate)
        keep.append(opts)
        changed = bool(self._lib.cui_checkbox_ex(
            self._ctx, encode_str(label, keep), ctypes.byref(c_val), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return bool(c_val.value)

    def switch(
        self,
        label: str,
        value: bool,
        *,
        description: Optional[str] = None,
        disabled: bool = False,
    ) -> bool:
        keep = self._frame_keepalive
        c_val = c_bool(bool(value))
        opts = CuiCheckOpts()
        opts.description = encode_opt(description, keep)
        opts.disabled = bool(disabled)
        keep.append(opts)
        changed = bool(self._lib.cui_switch_ex(
            self._ctx, encode_str(label, keep), ctypes.byref(c_val), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return bool(c_val.value)

    def radio(
        self,
        label: str,
        value: int,
        option: int,
        *,
        description: Optional[str] = None,
        disabled: bool = False,
    ) -> int:
        keep = self._frame_keepalive
        c_val = c_int(int(value))
        opts = CuiCheckOpts()
        opts.description = encode_opt(description, keep)
        opts.disabled = bool(disabled)
        keep.append(opts)
        changed = bool(self._lib.cui_radio_ex(
            self._ctx, encode_str(label, keep), ctypes.byref(c_val), int(option), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return int(c_val.value)

    def radio_group(self, id: str, items: Sequence[str], index: int) -> int:
        keep = self._frame_keepalive
        arr, n = encode_str_array(items, keep)
        c_idx = c_int(int(index))
        changed = bool(self._lib.cui_radio_group(
            self._ctx, encode_str(id, keep), arr, n, ctypes.byref(c_idx)
        ))
        self._record_change(changed)
        return int(c_idx.value)

    def radio_cards(
        self,
        id: str,
        choices: Sequence[Choice],
        index: int,
        *,
        columns: int = 0,
    ) -> int:
        keep = self._frame_keepalive
        n = len(choices)
        arr = (CuiChoice * n)()
        for i, ch in enumerate(choices):
            arr[i].title = encode_str(ch.title, keep)
            arr[i].description = encode_opt(ch.description, keep)
            arr[i].icon = encode_opt(ch.icon, keep)
            arr[i].badge = encode_opt(ch.badge, keep)
        c_idx = c_int(int(index))
        opts = CuiRadioCardsOpts(0, int(columns))
        keep.extend((arr, opts))
        changed = bool(self._lib.cui_radio_cards_ex(
            self._ctx, encode_str(id, keep), arr, n, ctypes.byref(c_idx), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return int(c_idx.value)

    def slider(
        self,
        label: str,
        value: float,
        min_value: float = 0.0,
        max_value: float = 1.0,
        *,
        step: float = 0.0,
        show_value: bool = False,
        format: Optional[str] = None,
        disabled: bool = False,
        width: SizeLike = None,
    ) -> float:
        keep = self._frame_keepalive
        c_val = c_float(float(value))
        opts = CuiSliderOpts()
        opts.step = float(step)
        opts.show_value = bool(show_value)
        opts.format = encode_opt(format, keep)
        opts.disabled = bool(disabled)
        opts.width = to_c_size(width)
        keep.append(opts)
        changed = bool(self._lib.cui_slider_ex(
            self._ctx, encode_str(label, keep), ctypes.byref(c_val),
            float(min_value), float(max_value), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return float(c_val.value)

    def range_slider(
        self,
        label: str,
        lo: float,
        hi: float,
        min_value: float = 0.0,
        max_value: float = 1.0,
    ) -> Tuple[float, float]:
        keep = self._frame_keepalive
        c_lo = c_float(float(lo))
        c_hi = c_float(float(hi))
        changed = bool(self._lib.cui_range_slider(
            self._ctx, encode_str(label, keep),
            ctypes.byref(c_lo), ctypes.byref(c_hi), float(min_value), float(max_value)
        ))
        self._record_change(changed)
        return float(c_lo.value), float(c_hi.value)

    def rating(self, id: str, value: int, max_stars: int = 5) -> int:
        keep = self._frame_keepalive
        c_val = c_int(int(value))
        changed = bool(self._lib.cui_rating(self._ctx, encode_str(id, keep), ctypes.byref(c_val), int(max_stars)))
        self._record_change(changed)
        return int(c_val.value)

    def chip(
        self,
        label: str,
        selected: bool,
        *,
        icon: Optional[str] = None,
        disabled: bool = False,
    ) -> bool:
        keep = self._frame_keepalive
        c_sel = c_bool(bool(selected))
        opts = CuiChipOpts()
        opts.icon = encode_opt(icon, keep)
        opts.disabled = bool(disabled)
        keep.append(opts)
        changed = bool(self._lib.cui_chip_ex(
            self._ctx, encode_str(label, keep), ctypes.byref(c_sel), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return bool(c_sel.value)

    def control_tile(
        self,
        label: str,
        on: bool,
        *,
        icon: Optional[str] = None,
        detail: Optional[str] = None,
        color: ColorLike = None,
        width: SizeLike = None,
        wide: bool = False,
    ) -> bool:
        keep = self._frame_keepalive
        c_on = c_bool(bool(on))
        opts = CuiTileOpts()
        opts.icon = encode_opt(icon, keep)
        opts.detail = encode_opt(detail, keep)
        opts.color = to_c_color(color)
        opts.width = to_c_size(width)
        opts.wide = bool(wide)
        keep.append(opts)
        changed = bool(self._lib.cui_control_tile_ex(
            self._ctx, encode_str(label, keep), ctypes.byref(c_on), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return bool(c_on.value)

    def selection_bar(
        self,
        id: str,
        actions: Sequence[object],
        selected: list,
        *,
        count_format: Optional[str] = None,
        anchor: int = 0,
        no_escape: bool = False,
    ) -> int:
        """A bar that slides up under a list while something is selected
        (CUI post-1.4): count, clear button and labelled actions.

        ``selected`` is the list of per-item flags, updated in place (Esc or
        clear zeroes it). ``actions`` are :class:`nexa.SelectionAction` (or
        ``(label, icon, tone)`` tuples). Returns the action picked, ``-1``
        (``CUI_SELECTION_NONE``) for no interaction, or ``-2``
        (``CUI_SELECTION_CLEARED``).
        """
        keep = self._frame_keepalive
        n = len(selected)
        sel = (c_bool * max(n, 1))()
        for i in range(max(n, 1)):
            sel[i] = bool(selected[i]) if i < n else False
        keep.append(sel)
        m = len(actions)
        arr = (CuiSelectionAction * max(m, 1))()
        for i, a in enumerate(actions):
            if not isinstance(a, SelectionAction):
                a = SelectionAction(*a)  # (label, icon, tone)
            arr[i].icon = encode_opt(a.icon, keep)
            arr[i].label = encode_str(a.label, keep)
            arr[i].tone = int(a.tone)
        keep.append(arr)
        opts = CuiSelectionBarOpts()
        opts.selected = sel
        opts.item_count = n
        opts.count_format = encode_opt(count_format, keep)
        opts.anchor = int(anchor)
        opts.no_escape = bool(no_escape)
        keep.append(opts)
        result = int(self._lib.cui_selection_bar_ex(
            self._ctx, encode_str(id, keep), n, arr, m, ctypes.byref(opts)
        ))
        for i in range(n):
            selected[i] = bool(sel[i])
        self._record_change(result != -1)
        return result
