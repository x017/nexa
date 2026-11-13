"""Select, combobox, multi-select, date/time/calendar/wheel pickers, color picker, and range sliders."""

from __future__ import annotations

import ctypes
from ctypes import c_bool, c_float, c_int
from typing import List, Optional, Sequence, Tuple

from .._cdefs import (
    CuiColor,
    CuiEmojiPickerOpts,
    CuiDate,
    CuiDateOpts,
    CuiDateRange,
    CuiDateRangeOpts,
    CuiHistogramOpts,
    CuiMultiSelectOpts,
    CuiRulerOpts,
    CuiSelectOpts,
    CuiTimeOpts,
    CuiWheelOpts,
    encode_opt,
    encode_str,
    encode_str_array,
    to_c_color,
    to_c_date,
    to_c_date_range,
    to_c_size,
)
from ..types import Color, ColorLike, Date, DateRange, SizeLike, Tone


class PickersMixin:
    __slots__ = ()

    def select(
        self,
        id: str,
        items: Sequence[str],
        index: int,
        *,
        label: Optional[str] = None,
        placeholder: Optional[str] = None,
        icons: Optional[Sequence[Optional[str]]] = None,
        searchable: bool = False,
        disabled: bool = False,
        width: SizeLike = None,
        bg: ColorLike = None,
        color: ColorLike = None,
        text_color: ColorLike = None,
        placeholder_color: ColorLike = None,
        border_color: ColorLike = None,
        focus_color: ColorLike = None,
    ) -> int:
        """Dropdown. Colours mirror :meth:`input`: ``bg`` is the field surface,
        ``color``/``text_color`` the selected value, ``placeholder_color`` the
        hint shown while nothing is chosen, ``border_color`` the resting edge
        and ``focus_color`` the edge it blends to while hovered or open.
        """
        keep = self._frame_keepalive
        arr, n = encode_str_array(items, keep)
        icons_arr, _ = encode_str_array(icons, keep) if icons else (None, 0)
        c_idx = c_int(int(index))
        opts = CuiSelectOpts()
        opts.label = encode_opt(label, keep)
        opts.placeholder = encode_opt(placeholder, keep)
        if icons_arr is not None:
            opts.icons = icons_arr
        opts.searchable = bool(searchable)
        opts.disabled = bool(disabled)
        opts.width = to_c_size(width)
        if bg is not None:
            opts.bg = to_c_color(bg)
        if text_color is not None or color is not None:
            opts.text_color = to_c_color(text_color if text_color is not None else color)
        if placeholder_color is not None:
            opts.placeholder_color = to_c_color(placeholder_color)
        if border_color is not None:
            opts.border_color = to_c_color(border_color)
        if focus_color is not None:
            opts.focus_color = to_c_color(focus_color)
        keep.append(opts)
        changed = bool(self._lib.cui_select_ex(
            self._ctx, encode_str(id, keep), arr, n, ctypes.byref(c_idx), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return int(c_idx.value)

    def combobox(self, id: str, items: Sequence[str], index: int, **kwargs) -> int:
        """Convenience alias for ``select(..., searchable=True)``."""
        kwargs["searchable"] = True
        return self.select(id, items, index, **kwargs)

    def multi_select(
        self,
        id: str,
        items: Sequence[str],
        selected: Sequence[bool],
        *,
        label: Optional[str] = None,
        placeholder: Optional[str] = None,
        icons: Optional[Sequence[Optional[str]]] = None,
        searchable: bool = True,
        max_chips: int = 0,
        width: SizeLike = None,
    ) -> List[bool]:
        keep = self._frame_keepalive
        n = len(items)
        if len(selected) != n:
            raise ValueError(f"selected length ({len(selected)}) must equal items length ({n})")
        arr, _ = encode_str_array(items, keep)
        icons_arr, _ = encode_str_array(icons, keep) if icons else (None, 0)
        c_sel = (c_bool * n)(*(bool(s) for s in selected))
        opts = CuiMultiSelectOpts()
        opts.label = encode_opt(label, keep)
        opts.placeholder = encode_opt(placeholder, keep)
        if icons_arr is not None:
            opts.icons = icons_arr
        opts.searchable = bool(searchable)
        opts.max_chips = int(max_chips)
        opts.width = to_c_size(width)
        keep.extend((c_sel, opts))
        changed = bool(self._lib.cui_multi_select_ex(
            self._ctx, encode_str(id, keep), arr, n, c_sel, ctypes.byref(opts)
        ))
        self._record_change(changed)
        return [bool(c_sel[i]) for i in range(n)]

    def calendar(self, id: str, value: Date) -> Date:
        c_d = to_c_date(value)
        changed = bool(self._lib.cui_calendar(self._ctx, encode_str(id, self._frame_keepalive), ctypes.byref(c_d)))
        self._record_change(changed)
        return Date(int(c_d.year), int(c_d.month), int(c_d.day))

    def date_picker(
        self,
        id: str,
        value: Date,
        *,
        label: Optional[str] = None,
        placeholder: Optional[str] = None,
        width: SizeLike = None,
    ) -> Date:
        keep = self._frame_keepalive
        c_d = to_c_date(value)
        opts = CuiDateOpts()
        opts.label = encode_opt(label, keep)
        opts.placeholder = encode_opt(placeholder, keep)
        opts.width = to_c_size(width)
        keep.append(opts)
        changed = bool(self._lib.cui_date_picker_ex(
            self._ctx, encode_str(id, keep), ctypes.byref(c_d), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return Date(int(c_d.year), int(c_d.month), int(c_d.day))

    def range_calendar(self, id: str, value: DateRange, *, months: int = 2) -> DateRange:
        c_dr = to_c_date_range(value)
        changed = bool(self._lib.cui_range_calendar(
            self._ctx, encode_str(id, self._frame_keepalive), ctypes.byref(c_dr), int(months)
        ))
        self._record_change(changed)
        return DateRange(
            Date(int(c_dr.start.year), int(c_dr.start.month), int(c_dr.start.day)),
            Date(int(c_dr.end.year), int(c_dr.end.month), int(c_dr.end.day)),
        )

    def date_range_picker(
        self,
        id: str,
        value: DateRange,
        *,
        label: Optional[str] = None,
        placeholder: Optional[str] = None,
        width: SizeLike = None,
        no_presets: bool = False,
    ) -> DateRange:
        keep = self._frame_keepalive
        c_dr = to_c_date_range(value)
        opts = CuiDateRangeOpts()
        opts.label = encode_opt(label, keep)
        opts.placeholder = encode_opt(placeholder, keep)
        opts.width = to_c_size(width)
        opts.no_presets = bool(no_presets)
        keep.append(opts)
        changed = bool(self._lib.cui_date_range_picker_ex(
            self._ctx, encode_str(id, keep), ctypes.byref(c_dr), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return DateRange(
            Date(int(c_dr.start.year), int(c_dr.start.month), int(c_dr.start.day)),
            Date(int(c_dr.end.year), int(c_dr.end.month), int(c_dr.end.day)),
        )

    def time_picker(
        self,
        id: str,
        hour: int,
        minute: int,
        *,
        label: Optional[str] = None,
        twelve_hour: bool = False,
        minute_step: int = 1,
        width: SizeLike = None,
    ) -> Tuple[int, int]:
        keep = self._frame_keepalive
        c_h = c_int(int(hour))
        c_m = c_int(int(minute))
        opts = CuiTimeOpts()
        opts.label = encode_opt(label, keep)
        opts.twelve_hour = bool(twelve_hour)
        opts.minute_step = int(minute_step)
        opts.width = to_c_size(width)
        keep.append(opts)
        changed = bool(self._lib.cui_time_picker_ex(
            self._ctx, encode_str(id, keep), ctypes.byref(c_h), ctypes.byref(c_m), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return int(c_h.value), int(c_m.value)

    def time_dial(self, id: str, hour: int, minute: int, *, size: float = 200.0) -> Tuple[int, int]:
        c_h = c_int(int(hour))
        c_m = c_int(int(minute))
        changed = bool(self._lib.cui_time_dial(
            self._ctx, encode_str(id, self._frame_keepalive), ctypes.byref(c_h), ctypes.byref(c_m), float(size)
        ))
        self._record_change(changed)
        return int(c_h.value), int(c_m.value)

    def wheel_picker(
        self,
        id: str,
        items: Sequence[str],
        index: int,
        *,
        rows: int = 0,
        width: SizeLike = None,
        loop: bool = False,
        join_left: bool = False,
        join_right: bool = False,
    ) -> int:
        keep = self._frame_keepalive
        arr, n = encode_str_array(items, keep)
        c_idx = c_int(int(index))
        opts = CuiWheelOpts()
        opts.rows = int(rows)
        opts.width = to_c_size(width)
        opts.loop = bool(loop)
        opts.join_left = bool(join_left)
        opts.join_right = bool(join_right)
        keep.append(opts)
        changed = bool(self._lib.cui_wheel_picker_ex(
            self._ctx, encode_str(id, keep), arr, n, ctypes.byref(c_idx), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return int(c_idx.value)

    def ruler_slider(
        self,
        label: str,
        value: float,
        min_value: float,
        max_value: float,
        *,
        step: float = 0.0,
        major_every: int = 0,
        spacing: float = 0.0,
        format: Optional[str] = None,
        unit: Optional[str] = None,
        width: SizeLike = None,
    ) -> float:
        keep = self._frame_keepalive
        c_val = c_float(float(value))
        opts = CuiRulerOpts()
        opts.step = float(step)
        opts.major_every = int(major_every)
        opts.spacing = float(spacing)
        opts.format = encode_opt(format, keep)
        opts.unit = encode_opt(unit, keep)
        opts.width = to_c_size(width)
        keep.append(opts)
        changed = bool(self._lib.cui_ruler_slider_ex(
            self._ctx, encode_str(label, keep), ctypes.byref(c_val),
            float(min_value), float(max_value), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return float(c_val.value)

    def histogram_slider(
        self,
        label: str,
        bins: Sequence[float],
        lo: float,
        hi: float,
        min_value: float,
        max_value: float,
        *,
        height: float = 0.0,
        format: Optional[str] = None,
    ) -> Tuple[float, float]:
        keep = self._frame_keepalive
        n = len(bins)
        c_bins = (c_float * n)(*(float(b) for b in bins))
        c_lo = c_float(float(lo))
        c_hi = c_float(float(hi))
        opts = CuiHistogramOpts()
        opts.height = float(height)
        opts.format = encode_opt(format, keep)
        keep.extend((c_bins, opts))
        changed = bool(self._lib.cui_histogram_slider_ex(
            self._ctx, encode_str(label, keep), c_bins, n,
            ctypes.byref(c_lo), ctypes.byref(c_hi),
            float(min_value), float(max_value), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return float(c_lo.value), float(c_hi.value)

    def color_picker(self, id: str, value: ColorLike) -> Color:
        from ctypes import c_uint32
        from .._cdefs import to_packed_color
        c_col = c_uint32(to_packed_color(value))
        changed = bool(self._lib.nexa_color_picker(
            self._ctx, encode_str(id, self._frame_keepalive), ctypes.byref(c_col)
        ))
        self._record_change(changed)
        return Color._from_packed(int(c_col.value))

    # ---- Emoji (CUI 1.2) ----

    def load_emoji_font(self, path: Optional[str] = None) -> bool:
        """Load a color emoji font: the system's when ``path`` is None, else that file."""
        if path is None:
            return bool(self._lib.cui_emoji_font_load_system(self._ctx))
        return bool(self._lib.cui_emoji_font_load_file(self._ctx, path.encode("utf-8")))

    def emoji_supported(self, text: str) -> bool:
        """Whether the loaded font (or platform) can draw ``text`` as an emoji."""
        raw = text.encode("utf-8")
        return bool(self._lib.cui_emoji_supported(self._ctx, raw, len(raw)))

    def emoji(self, text: str, *, size: float = 16.0) -> None:
        """Draw one emoji (any grapheme cluster) at ``size`` points."""
        self._lib.cui_emoji(self._ctx, encode_str(text, self._frame_keepalive), float(size))

    def emoji_picker(
        self,
        id: str,
        *,
        width: SizeLike = None,
        height: float = 280.0,
        size: float = 26.0,
        recent: str = "",
        tone: int = 0,
        placeholder: Optional[str] = None,
        empty_text: Optional[str] = None,
        hint: Optional[str] = None,
        group_names: Sequence[str] = (),
        no_search: bool = False,
        no_preview: bool = False,
        no_tone: bool = False,
    ) -> Optional[str]:
        """The 1,914-emoji picker with search, groups and recent emoji.

        Returns the emoji chosen this frame (or None).  ``recent`` is a
        space-separated list the picker keeps up to date, so pass it back and
        save it; ``tone`` is the 0-5 skin tone.
        """
        keep = self._frame_keepalive
        opts = CuiEmojiPickerOpts()
        opts.width = to_c_size(width)
        opts.height = float(height)
        opts.size = float(size)
        recent_buf = ctypes.create_string_buffer(recent.encode("utf-8"), 2048)
        opts.recent = ctypes.cast(recent_buf, ctypes.c_char_p)
        opts.recent_cap = ctypes.c_size_t(len(recent_buf))
        c_tone = c_int(int(tone))
        opts.tone = ctypes.cast(ctypes.byref(c_tone), ctypes.POINTER(c_int))
        opts.placeholder = encode_opt(placeholder, keep)
        opts.empty_text = encode_opt(empty_text, keep)
        opts.hint = encode_opt(hint, keep)
        if group_names:
            arr, n = encode_str_array(group_names, keep)
            opts.group_names = arr
            del n
        opts.no_search = bool(no_search)
        opts.no_preview = bool(no_preview)
        opts.no_tone = bool(no_tone)
        keep.extend((opts, recent_buf, c_tone))
        picked = self._lib.cui_emoji_picker_ex(self._ctx, encode_str(id, keep), ctypes.byref(opts))
        self._record_change(picked is not None)
        if not picked:
            return None
        return picked.decode("utf-8", errors="replace")
