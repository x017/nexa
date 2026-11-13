"""Creative controls: the eight CUI post-1.4 widgets for editors, generators and design tools."""

from __future__ import annotations

import ctypes
from ctypes import c_bool, c_float, c_int, c_uint32
from typing import List, Optional, Sequence, Union

from .._cdefs import (
    CuiAspect,
    CuiAspectPickerOpts,
    CuiColor,
    CuiGradientSliderOpts,
    CuiGradientStop,
    CuiOptionActionOpts,
    CuiPaletteStripOpts,
    CuiRatioSliderOpts,
    CuiSeedFieldOpts,
    CuiStepSliderOpts,
    CuiStatusTagOpts,
    encode_opt,
    encode_str,
    encode_str_array,
    to_c_color,
    to_c_size,
)
from ..types import (
    ColorLike,
    ControlSize,
    GradientStop,
    GradientTrack,
    SeedResult,
    SizeLike,
    TagStatus,
    Tone,
    WellResult,
)


class CreativeMixin:
    __slots__ = ()

    def status_tag(
        self,
        label: str,
        status: TagStatus = TagStatus.PENDING,
        *,
        size: ControlSize = ControlSize.MD,
        removable: bool = False,
        icon: Optional[str] = None,
        tone: Optional[Tone] = None,
        id: Optional[str] = None,
    ) -> bool:
        """Icon + label + tinted fill for a workflow state (CUI post-1.4).

        Returns ``True`` when a removable tag's x (or Enter/Delete/Backspace)
        was activated.
        """
        keep = self._frame_keepalive
        opts = CuiStatusTagOpts()
        opts.size = int(size)
        opts.removable = bool(removable)
        opts.icon = encode_opt(icon, keep)
        if tone is not None:
            opts.tone = int(tone)
        opts.id = encode_opt(id, keep)
        keep.append(opts)
        clicked = bool(self._lib.cui_status_tag_ex(
            self._ctx, encode_str(label, keep), int(status), ctypes.byref(opts)
        ))
        self._record_change(clicked)
        return clicked

    def ratio_slider(
        self,
        first: str,
        second: str,
        ratio: float,
        *,
        tone: Tone = Tone.NEUTRAL,
        step: float = 0.0,
        height: float = 0.0,
        width: SizeLike = None,
        disabled: bool = False,
    ) -> float:
        """A whole split into two named parts with a bar to drag (CUI post-1.4).

        Arrow keys adjust, Shift steps by ten, Home/End jump. Returns the new
        ratio (``0..1``, the share of ``first``).
        """
        keep = self._frame_keepalive
        c_ratio = c_float(float(ratio))
        opts = CuiRatioSliderOpts()
        opts.tone = int(tone)
        opts.step = float(step)
        opts.height = float(height)
        opts.width = to_c_size(width)
        opts.disabled = bool(disabled)
        keep.extend((c_ratio, opts))
        changed = bool(self._lib.cui_ratio_slider_ex(
            self._ctx, encode_str(first, keep), encode_str(second, keep),
            ctypes.byref(c_ratio), ctypes.byref(opts),
        ))
        self._record_change(changed or c_ratio.value != float(ratio))
        return float(c_ratio.value)

    def gradient_slider(
        self,
        label: str,
        value: float,
        *,
        min: float = 0.0,
        max: float = 1.0,
        track: GradientTrack = GradientTrack.HUE,
        stops: Optional[Sequence[GradientStop]] = None,
        color: ColorLike = None,
        step: float = 0.0,
        format: Optional[str] = None,
        value_text: Optional[str] = None,
        swatch: bool = False,
        tool: Optional[str] = None,
        tool_tooltip: Optional[str] = None,
        tool_on: bool = False,
        plain: bool = False,
        disabled: bool = False,
    ) -> WellResult:
        """A slider whose track *is* the value (CUI post-1.4): a hue wheel, a
        white-balance ramp, opacity over a checkerboard, or your own ``stops``.
        Returns :class:`nexa.WellResult` — the new value, whether it changed,
        and whether the optional ``tool`` button was clicked.
        """
        keep = self._frame_keepalive
        c_val = c_float(float(value))
        opts = CuiGradientSliderOpts()
        opts.track = int(track)
        if stops:
            n = len(stops)
            arr = (CuiGradientStop * n)()
            for i, s in enumerate(stops):
                arr[i].pos = float(s.pos)
                arr[i].color = to_c_color(s.color)
            opts.stops = arr
            opts.stop_count = n
            keep.append(arr)
        opts.color = to_c_color(color)
        opts.step = float(step)
        opts.format = encode_opt(format, keep)
        opts.value = encode_opt(value_text, keep)
        opts.swatch = bool(swatch)
        opts.tool = encode_opt(tool, keep)
        opts.tool_tooltip = encode_opt(tool_tooltip, keep)
        opts.tool_on = bool(tool_on)
        opts.plain = bool(plain)
        opts.disabled = bool(disabled)
        keep.extend((c_val, opts))
        flags = int(self._lib.cui_gradient_slider_ex(
            self._ctx, encode_str(label, keep), ctypes.byref(c_val),
            float(min), float(max), ctypes.byref(opts),
        ))
        self._record_change(bool(flags))
        return WellResult(float(c_val.value), bool(flags & 1), bool(flags & 2))

    def step_slider(
        self,
        label: str,
        value: int,
        *,
        min: int = 0,
        max: int = 10,
        labels: Optional[Sequence[str]] = None,
        format: Optional[str] = None,
        value_text: Optional[str] = None,
        tool: Optional[str] = None,
        tool_tooltip: Optional[str] = None,
        tool_on: bool = False,
        plain: bool = False,
        disabled: bool = False,
    ) -> WellResult:
        """A few stops marked with dots; the thumb snaps to each (CUI post-1.4).

        ``labels`` names the stops. Returns :class:`nexa.WellResult`.
        """
        keep = self._frame_keepalive
        c_val = c_int(int(value))
        opts = CuiStepSliderOpts()
        if labels:
            arr, n = encode_str_array(labels, keep)
            opts.labels = arr
            opts.format = encode_opt(format, keep) if format else None
        else:
            opts.format = encode_opt(format, keep)
        opts.value = encode_opt(value_text, keep)
        opts.tool = encode_opt(tool, keep)
        opts.tool_tooltip = encode_opt(tool_tooltip, keep)
        opts.tool_on = bool(tool_on)
        opts.plain = bool(plain)
        opts.disabled = bool(disabled)
        keep.extend((c_val, opts))
        flags = int(self._lib.cui_step_slider_ex(
            self._ctx, encode_str(label, keep), ctypes.byref(c_val),
            int(min), int(max), ctypes.byref(opts),
        ))
        self._record_change(bool(flags))
        return WellResult(int(c_val.value), bool(flags & 1), bool(flags & 2))

    def palette_strip(
        self,
        label: str,
        colors: List[ColorLike],
        locked: Optional[List[bool]] = None,
        *,
        seed: Optional[int] = None,
        value_text: Optional[str] = None,
        no_shuffle: bool = False,
        height: float = 32.0,
        plain: bool = False,
    ) -> bool:
        """Joined swatches you lock with a click; shuffle recolors the rest
        from ``seed`` (CUI post-1.4). ``colors`` and ``locked`` are updated in
        place. Returns ``True`` when anything changed this frame.
        """
        keep = self._frame_keepalive
        n = len(colors)
        if n == 0:
            return False
        c_colors = (CuiColor * n)()
        for i, c in enumerate(colors):
            c_colors[i] = to_c_color(c)
        c_locked = None
        if locked is not None:
            m = min(len(locked), n)
            c_locked = (c_bool * n)()
            for i in range(n):
                c_locked[i] = bool(locked[i]) if i < m else False
            keep.append(c_locked)
        c_seed = None
        if seed is not None:
            c_seed = c_uint32(int(seed) & 0xFFFFFFFF)
            keep.append(c_seed)
        opts = CuiPaletteStripOpts()
        if c_seed is not None:
            opts.seed = ctypes.pointer(c_seed)
        opts.value = encode_opt(value_text, keep)
        opts.no_shuffle = bool(no_shuffle)
        opts.height = float(height)
        opts.plain = bool(plain)
        keep.extend((c_colors, opts))
        flags = int(self._lib.cui_palette_strip_ex(
            self._ctx, encode_str(label, keep), c_colors, c_locked, n, ctypes.byref(opts)
        ))
        # Write the (possibly shuffled) palette back in the caller's type.
        for i in range(n):
            cc = c_colors[i]
            if isinstance(colors[i], str):
                colors[i] = f"#{cc.r:02x}{cc.g:02x}{cc.b:02x}"  # type: ignore[assignment]
            else:
                colors[i] = (cc.r, cc.g, cc.b, cc.a)  # type: ignore[assignment]
        if locked is not None and c_locked is not None:
            for i in range(min(len(locked), n)):
                locked[i] = bool(c_locked[i])
        changed = bool(flags & 1) or bool(flags & 2)
        self._record_change(changed)
        return changed

    def aspect_picker(
        self,
        label: str,
        index: int,
        *,
        ratios: Optional[Sequence[Sequence[Union[int, str]]]] = None,
        custom: bool = True,
        custom_label: Optional[str] = None,
        base: int = 0,
        value_text: Optional[str] = None,
        plain: bool = False,
    ) -> int:
        """Each ratio drawn in its own proportions (CUI post-1.4).

        ``ratios`` are ``(width, height[, label])`` tuples — omit it for the
        built-in photo set. Returns the chosen index (``-1`` when nothing is
        selected; a Custom slot, when enabled, reports ``len(ratios)``).
        """
        keep = self._frame_keepalive
        c_idx = c_int(int(index))
        opts = CuiAspectPickerOpts()
        if ratios:
            n = len(ratios)
            arr = (CuiAspect * max(n, 1))()
            for i, r in enumerate(ratios):
                arr[i].w = int(r[0])
                arr[i].h = int(r[1])
                if len(r) > 2:
                    arr[i].label = encode_str(str(r[2]), keep)
            opts.ratios = arr
            opts.count = n
            keep.append(arr)
        opts.custom = bool(custom)
        opts.custom_label = encode_opt(custom_label, keep)
        opts.base = int(base)
        opts.value = encode_opt(value_text, keep)
        opts.plain = bool(plain)
        keep.extend((c_idx, opts))
        changed = bool(self._lib.cui_aspect_picker_ex(
            self._ctx, encode_str(label, keep), ctypes.byref(c_idx), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return int(c_idx.value)

    def option_action(
        self,
        label: str,
        items: Sequence[str],
        index: int,
        *,
        icon: Optional[str] = None,
        tooltip: Optional[str] = None,
        action_on: bool = False,
        action_disabled: bool = False,
        value_text: Optional[str] = None,
        plain: bool = False,
    ) -> WellResult:
        """A compact segmented choice and the icon button of the action it
        feeds (CUI post-1.4). Returns :class:`nexa.WellResult` — the new index,
        whether it changed, and whether the action button was clicked.
        """
        keep = self._frame_keepalive
        arr, n = encode_str_array(items, keep)
        c_idx = c_int(int(index))
        opts = CuiOptionActionOpts()
        opts.tooltip = encode_opt(tooltip, keep)
        opts.action_on = bool(action_on)
        opts.action_disabled = bool(action_disabled)
        opts.value = encode_opt(value_text, keep)
        opts.plain = bool(plain)
        keep.extend((c_idx, opts))
        flags = int(self._lib.cui_option_action_ex(
            self._ctx, encode_str(label, keep), arr, n, ctypes.byref(c_idx),
            encode_opt(icon, keep), ctypes.byref(opts),
        ))
        self._record_change(bool(flags))
        return WellResult(int(c_idx.value), bool(flags & 1), bool(flags & 2))

    def seed_field(
        self,
        label: str,
        seed: int,
        locked: bool = False,
        *,
        value_text: Optional[str] = None,
        random_text: Optional[str] = None,
        fixed_text: Optional[str] = None,
        plain: bool = False,
    ) -> SeedResult:
        """A seed in the monospaced font (CUI post-1.4): the dice rolls a new
        one with rolling digits, the lock keeps it. Returns the updated
        ``(seed, locked, changed)`` as :class:`nexa.SeedResult`.
        """
        keep = self._frame_keepalive
        c_seed = c_uint32(int(seed) & 0xFFFFFFFF)
        c_locked = c_bool(bool(locked))
        opts = CuiSeedFieldOpts()
        opts.value = encode_opt(value_text, keep)
        opts.random_text = encode_opt(random_text, keep)
        opts.fixed_text = encode_opt(fixed_text, keep)
        opts.plain = bool(plain)
        keep.extend((c_seed, c_locked, opts))
        flags = int(self._lib.cui_seed_field_ex(
            self._ctx, encode_str(label, keep),
            ctypes.byref(c_seed), ctypes.byref(c_locked), ctypes.byref(opts),
        ))
        changed = bool(flags & 1) or bool(flags & 2)
        self._record_change(changed)
        return SeedResult(int(c_seed.value), bool(c_locked.value), changed)
