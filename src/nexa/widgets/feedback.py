"""Feedback & status indicators: toasts, alerts, banners, progress, badges, avatars, metrics, checklists."""

from __future__ import annotations

import ctypes
from ctypes import c_bool, c_float, c_uint32
from typing import List, Optional, Sequence, Tuple

from .._cdefs import (
    CuiAlertOpts,
    CuiAvatarOpts,
    CuiBadgeOpts,
    CuiBannerOpts,
    CuiChecklistOpts,
    CuiCheckStep,
    CuiCountdownOpts,
    CuiEmptyOpts,
    CuiLoaderOpts,
    CuiMeterPart,
    CuiMetricOpts,
    CuiPatternMeterOpts,
    CuiProgressOpts,
    CuiSkeletonGroupOpts,
    CuiSpinnerOpts,
    CuiStatusSpinnerOpts,
    CuiToastOpts,
    c_texture,
    encode_opt,
    encode_str,
    encode_str_array,
    to_c_color,
    to_c_size,
)
from ..scopes import SimpleScope
from ..types import (
    CheckStep,
    ColorLike,
    ControlSize,
    LoaderStyle,
    MeterPart,
    SizeLike,
    SpinnerStyle,
    Status,
    Tone,
)


class FeedbackMixin:
    __slots__ = ()

    def toast(
        self,
        title: str,
        *,
        description: Optional[str] = None,
        tone: Tone = Tone.NEUTRAL,
        duration: float = 0.0,
        action: Optional[str] = None,
        show_timer: bool = False,
    ) -> int:
        keep = self._frame_keepalive
        opts = CuiToastOpts()
        opts.description = encode_opt(description, keep)
        opts.tone = int(tone)
        opts.duration = float(duration)
        opts.action = encode_opt(action, keep)
        opts.show_timer = bool(show_timer)
        keep.append(opts)
        return int(self._lib.cui_toast_ex(self._ctx, encode_str(title, keep), ctypes.byref(opts)))

    def toast_action_clicked(self, handle: int) -> bool:
        return bool(self._lib.cui_toast_action_clicked(self._ctx, int(handle)))

    def toast_dismiss(self, handle: int) -> None:
        self._lib.cui_toast_dismiss(self._ctx, int(handle))

    def alert(
        self,
        title: str,
        *,
        description: Optional[str] = None,
        tone: Tone = Tone.NEUTRAL,
        icon: Optional[str] = None,
        dismissible: bool = False,
    ) -> bool:
        keep = self._frame_keepalive
        opts = CuiAlertOpts()
        opts.description = encode_opt(description, keep)
        opts.tone = int(tone)
        opts.icon = encode_opt(icon, keep)
        opts.dismissible = bool(dismissible)
        keep.append(opts)
        return bool(self._lib.cui_alert_ex(self._ctx, encode_str(title, keep), ctypes.byref(opts)))

    def banner(
        self,
        text: str,
        is_open: bool,
        *,
        tone: Tone = Tone.INFO,
        icon: Optional[str] = None,
        action: Optional[str] = None,
        dismissible: bool = True,
    ) -> Tuple[bool, bool]:
        """Top-of-view announcement banner; returns ``(is_open, action_clicked)``."""
        keep = self._frame_keepalive
        c_open = c_bool(bool(is_open))
        opts = CuiBannerOpts()
        opts.tone = int(tone)
        opts.icon = encode_opt(icon, keep)
        opts.action = encode_opt(action, keep)
        opts.dismissible = bool(dismissible)
        keep.append(opts)
        action_clicked = bool(self._lib.cui_banner_ex(
            self._ctx, encode_str(text, keep), ctypes.byref(c_open), ctypes.byref(opts)
        ))
        new_open = bool(c_open.value)
        self._record_change(action_clicked or new_open != is_open)
        return new_open, action_clicked

    def progress(
        self,
        value: float = 0.0,
        *,
        indeterminate: bool = False,
        tone: Tone = Tone.ACCENT,
        height: float = 0.0,
        label: Optional[str] = None,
        show_value: bool = False,
        width: SizeLike = None,
        dither: bool = False,
    ) -> None:
        keep = self._frame_keepalive
        opts = CuiProgressOpts()
        opts.indeterminate = bool(indeterminate)
        opts.tone = int(tone)
        opts.height = float(height)
        opts.label = encode_opt(label, keep)
        opts.show_value = bool(show_value)
        opts.width = to_c_size(width)
        opts.dither = bool(dither)
        keep.append(opts)
        self._lib.cui_progress_ex(self._ctx, float(value), ctypes.byref(opts))

    def progress_ring(self, label: str, value: float, *, size: float = 80.0) -> None:
        self._lib.cui_progress_ring(
            self._ctx, encode_str(label, self._frame_keepalive), float(value), float(size)
        )

    def spinner(
        self,
        size: float = 18.0,
        *,
        style: SpinnerStyle = SpinnerStyle.ARC,
        color: ColorLike = None,
        fg: ColorLike = None,
        track: ColorLike = None,
    ) -> None:
        """Loading spinner. ``style`` picks a dither animation (CUI post-1.4):
        comet ring, dot matrix, radar sweep, orbit, spiral …; the default
        ``ARC`` with no colours is the plain ring. ``track`` is the dots' base
        colour (defaults to ``color`` at 12%).
        """
        if fg is not None:
            color = fg
        if style == SpinnerStyle.ARC and color is None and track is None:
            self._lib.cui_spinner(self._ctx, float(size))
            return
        keep = self._frame_keepalive
        opts = CuiSpinnerOpts()
        opts.style = int(style)
        opts.color = to_c_color(color)
        opts.track = to_c_color(track)
        keep.append(opts)
        self._lib.cui_spinner_ex(self._ctx, float(size), ctypes.byref(opts))

    def loader(
        self,
        *,
        style: LoaderStyle = LoaderStyle.DOTS,
        size: float = 0.0,
        color: ColorLike = None,
        fg: ColorLike = None,
    ) -> None:
        if fg is not None:
            color = fg
        keep = self._frame_keepalive
        opts = CuiLoaderOpts()
        opts.style = int(style)
        opts.size = float(size)
        opts.color = to_c_color(color)
        keep.append(opts)
        self._lib.cui_loader_ex(self._ctx, ctypes.byref(opts))

    def skeleton(self, width: SizeLike = None, height: float = 16.0) -> None:
        s = to_c_size(width)
        self._lib.nexa_skeleton(self._ctx, int(s.kind), float(s.value), float(height))

    def skeleton_group(
        self,
        *,
        dither: bool = False,
        width: SizeLike = None,
        gap: float = 8.0,
    ) -> SimpleScope:
        """Placeholders built inside this scope share one shine (CUI post-1.4).

        With ``dither`` they are drawn in dots with a brighter band sweeping
        across. Nest groups; build the skeletons inside with :meth:`skeleton`.
        """
        keep = self._frame_keepalive
        opts = CuiSkeletonGroupOpts()
        opts.dither = bool(dither)
        opts.width = to_c_size(width)
        opts.gap = float(gap)
        keep.append(opts)
        self._lib.cui_skeleton_group_begin_ex(self._ctx, ctypes.byref(opts))
        return SimpleScope(self._ctx, self._lib.cui_skeleton_group_end)

    def status_spinner(
        self,
        id: str,
        status: Status,
        *,
        size: float = 0.0,
        color: ColorLike = None,
        fg: ColorLike = None,
        keep_visible: bool = False,
    ) -> bool:
        """A dither ring while ``status`` is BUSY that resolves to a check or
        cross (CUI post-1.4). Returns ``False`` once there is nothing left to
        show, so you can drop the widget; ``keep_visible=True`` holds the
        result instead of dissolving it.
        """
        if fg is not None:
            color = fg
        ka = self._frame_keepalive
        opts = CuiStatusSpinnerOpts()
        opts.size = float(size)
        opts.color = to_c_color(color)
        opts.keep = bool(keep_visible)
        ka.append(opts)
        alive = bool(self._lib.cui_status_spinner_ex(
            self._ctx, encode_str(id, ka), int(status), ctypes.byref(opts)
        ))
        self._record_change(alive)
        return alive

    def pattern_meter(
        self,
        id: str,
        parts: Sequence[object],
        *,
        total: float = 0.0,
        label: Optional[str] = None,
        unit: Optional[str] = None,
        format: Optional[str] = None,
        free_label: Optional[str] = None,
        grayscale: bool = False,
        no_legend: bool = False,
        height: float = 0.0,
        width: SizeLike = None,
    ) -> int:
        """Stacked usage bar whose parts differ in colour and dot density
        (CUI post-1.4). ``parts`` are :class:`nexa.MeterPart` (or plain
        ``(name, value[, color[, density]])`` tuples). Returns the part under
        the pointer / keyboard focus, or ``-1``.
        """
        keep = self._frame_keepalive
        n = len(parts)
        c_parts = (CuiMeterPart * max(n, 1))()
        for i, p in enumerate(parts):
            if not isinstance(p, MeterPart):
                p = MeterPart(*p)  # type: ignore[misc]
            c_parts[i].name = encode_str(p.name, keep)
            c_parts[i].value = float(p.value)
            if p.color is not None:
                c_parts[i].color = to_c_color(p.color)
            c_parts[i].density = float(p.density)
        keep.append(c_parts)
        opts = CuiPatternMeterOpts()
        opts.total = float(total)
        opts.label = encode_opt(label, keep)
        opts.unit = encode_opt(unit, keep)
        opts.format = encode_opt(format, keep)
        opts.free_label = encode_opt(free_label, keep)
        opts.grayscale = bool(grayscale)
        opts.no_legend = bool(no_legend)
        opts.height = float(height)
        opts.width = to_c_size(width)
        keep.append(opts)
        focused = int(self._lib.cui_pattern_meter_ex(
            self._ctx, encode_str(id, keep), c_parts, n, ctypes.byref(opts)
        ))
        self._record_change(focused >= 0)
        return focused

    def badge(
        self,
        text: str,
        *,
        tone: Tone = Tone.NEUTRAL,
        dot: bool = False,
        solid: bool = False,
        icon: Optional[str] = None,
        size: ControlSize = ControlSize.MD,
    ) -> None:
        keep = self._frame_keepalive
        opts = CuiBadgeOpts()
        opts.tone = int(tone)
        opts.dot = bool(dot)
        opts.solid = bool(solid)
        opts.icon = encode_opt(icon, keep)
        opts.size = int(size)
        keep.append(opts)
        self._lib.cui_badge_ex(self._ctx, encode_str(text, keep), ctypes.byref(opts))

    def avatar(
        self,
        name: str,
        *,
        size: float = 0.0,
        image: int = 0,
        status: Optional[str] = None,
        square: bool = False,
    ) -> None:
        keep = self._frame_keepalive
        opts = CuiAvatarOpts()
        opts.size = float(size)
        opts.image = int(image)
        opts.status = encode_opt(status, keep)
        opts.square = bool(square)
        keep.append(opts)
        self._lib.cui_avatar_ex(self._ctx, encode_str(name, keep), ctypes.byref(opts))

    def avatar_group(
        self, names: Sequence[str], *, max_visible: int = 4, size: float = 32.0
    ) -> None:
        keep = self._frame_keepalive
        arr, n = encode_str_array(names, keep)
        self._lib.cui_avatar_group(self._ctx, arr, n, int(max_visible), float(size))

    def avatar_upload(
        self, id: str, name: str, image: int = 0, *, size: float = 72.0
    ) -> Tuple[int, bool]:
        """Avatar with image drop/upload; returns ``(image_tex, browse_clicked)``."""
        keep = self._frame_keepalive
        c_tex = c_texture(int(image))
        rc = int(self._lib.cui_avatar_upload(
            self._ctx, encode_str(id, keep), encode_str(name, keep), ctypes.byref(c_tex), float(size)
        ))
        self._record_change(rc != 0)
        return int(c_tex.value), (rc == -1)

    def empty_state(
        self,
        title: str,
        *,
        icon: Optional[str] = None,
        description: Optional[str] = None,
        action: Optional[str] = None,
    ) -> bool:
        keep = self._frame_keepalive
        opts = CuiEmptyOpts()
        opts.icon = encode_opt(icon, keep)
        opts.description = encode_opt(description, keep)
        opts.action = encode_opt(action, keep)
        keep.append(opts)
        clicked = bool(self._lib.cui_empty_state_ex(self._ctx, encode_str(title, keep), ctypes.byref(opts)))
        self._record_change(clicked)
        return clicked

    def metric(
        self,
        label: str,
        value: str,
        *,
        delta: float = 0.0,
        delta_label: Optional[str] = None,
        spark: Optional[Sequence[float]] = None,
        icon: Optional[str] = None,
        width: SizeLike = None,
        lower_is_better: bool = False,
    ) -> None:
        keep = self._frame_keepalive
        opts = CuiMetricOpts()
        opts.delta = float(delta)
        opts.delta_label = encode_opt(delta_label, keep)
        if spark:
            n = len(spark)
            c_spark = (c_float * n)(*(float(v) for v in spark))
            keep.append(c_spark)
            opts.spark = c_spark
            opts.spark_count = n
        opts.icon = encode_opt(icon, keep)
        opts.width = to_c_size(width)
        opts.lower_is_better = bool(lower_is_better)
        keep.append(opts)
        self._lib.cui_metric_ex(
            self._ctx, encode_str(label, keep), encode_str(value, keep), ctypes.byref(opts)
        )

    def meter(self, label: str, used: float, total: float, unit: str = "") -> None:
        keep = self._frame_keepalive
        self._lib.cui_meter(
            self._ctx, encode_str(label, keep), float(used), float(total), encode_str(unit, keep)
        )

    def countdown(
        self,
        id: str,
        seconds_left: float,
        *,
        hide_days: bool = False,
        compact: bool = False,
    ) -> None:
        keep = self._frame_keepalive
        opts = CuiCountdownOpts(0, bool(hide_days), bool(compact))
        keep.append(opts)
        self._lib.cui_countdown_ex(
            self._ctx, encode_str(id, keep), float(seconds_left), ctypes.byref(opts)
        )

    def checklist(
        self,
        id: str,
        steps: Sequence[CheckStep],
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Tuple[List[CheckStep], int]:
        """Onboarding checklist; returns ``(updated_steps, clicked_action_index_or_neg1)``."""
        keep = self._frame_keepalive
        n = len(steps)
        arr = (CuiCheckStep * n)()
        for i, st in enumerate(steps):
            arr[i].title = encode_str(st.title, keep)
            arr[i].description = encode_opt(st.description, keep)
            arr[i].action = encode_opt(st.action, keep)
            arr[i].done = bool(st.done)
        opts = CuiChecklistOpts()
        opts.title = encode_opt(title, keep)
        opts.description = encode_opt(description, keep)
        keep.extend((arr, opts))
        action_idx = int(self._lib.cui_checklist_ex(
            self._ctx, encode_str(id, keep), arr, n, ctypes.byref(opts)
        ))
        updated = [
            CheckStep(steps[i].title, steps[i].description, steps[i].action, bool(arr[i].done))
            for i in range(n)
        ]
        changed = action_idx >= 0 or any(updated[i].done != steps[i].done for i in range(n))
        self._record_change(changed)
        return updated, action_idx
