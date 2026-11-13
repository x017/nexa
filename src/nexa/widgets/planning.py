"""Planning & scheduling components: Kanban boards, week calendar, and Gantt chart."""

from __future__ import annotations

import ctypes
from typing import List, Sequence, Tuple

from .._cdefs import (
    CuiCalEvent,
    CuiDate,
    CuiGanttOpts,
    CuiGanttTask,
    CuiMonthEvent,
    CuiMonthOpts,
    CuiMonthResult,
    CuiWeekOpts,
    encode_opt,
    encode_str,
    encode_str_array,
    to_c_date,
    to_c_size,
)
from ..scopes import KanbanScope
from ..types import CalEvent, Date, GanttTask, MonthEvent, MonthResult, SizeLike, Tone


class PlanningMixin:
    __slots__ = ()

    def kanban(self, id: str) -> KanbanScope:
        self._lib.cui_kanban_begin(self._ctx, encode_str(id, self._frame_keepalive))
        return KanbanScope(self)

    def week_calendar(
        self,
        id: str,
        week_start: Date,
        events: Sequence[CalEvent],
        *,
        start_hour: float = 0.0,
        end_hour: float = 0.0,
        hour_height: float = 0.0,
        height: SizeLike = None,
        read_only: bool = False,
    ) -> Tuple[List[CalEvent], int]:
        """Interactive 7-day calendar; returns ``(updated_events, clicked_index_or_neg1)``."""
        keep = self._frame_keepalive
        n = len(events)
        arr = (CuiCalEvent * n)()
        for i, ev in enumerate(events):
            arr[i].title = encode_str(ev.title, keep)
            arr[i].detail = encode_opt(ev.detail, keep)
            arr[i].day = int(ev.day)
            arr[i].start = float(ev.start)
            arr[i].end = float(ev.end)
            arr[i].tone = int(ev.tone)
        opts = CuiWeekOpts()
        opts.start_hour = float(start_hour)
        opts.end_hour = float(end_hour)
        opts.hour_height = float(hour_height)
        opts.height = to_c_size(height)
        opts.read_only = bool(read_only)
        keep.extend((arr, opts))
        clicked = int(self._lib.nexa_week_calendar(
            self._ctx, encode_str(id, keep),
            int(week_start.year), int(week_start.month), int(week_start.day),
            arr, n, ctypes.byref(opts)
        ))
        updated = [
            CalEvent(
                events[i].title, int(arr[i].day), float(arr[i].start), float(arr[i].end),
                events[i].detail, events[i].tone
            )
            for i in range(n)
        ]
        moved = any(
            (updated[i].day != events[i].day or updated[i].start != events[i].start or updated[i].end != events[i].end)
            for i in range(n)
        )
        self._record_change(clicked >= 0 or moved)
        return updated, clicked

    def gantt(
        self,
        id: str,
        tasks: Sequence[GanttTask],
        origin: Date,
        days: int,
        *,
        day_width: float = 0.0,
        row_height: float = 0.0,
        height: SizeLike = None,
        today: int = -1,
        read_only: bool = False,
    ) -> Tuple[List[GanttTask], int]:
        """Interactive Gantt chart; returns ``(updated_tasks, clicked_index_or_neg1)``."""
        keep = self._frame_keepalive
        n = len(tasks)
        arr = (CuiGanttTask * n)()
        for i, t in enumerate(tasks):
            arr[i].name = encode_str(t.name, keep)
            arr[i].owner = encode_opt(t.owner, keep)
            arr[i].start = int(t.start)
            arr[i].end = int(t.end)
            arr[i].progress = float(t.progress)
            arr[i].tone = int(t.tone)
            arr[i].depends_on = int(t.depends_on)
            arr[i].milestone = bool(t.milestone)
        opts = CuiGanttOpts()
        opts.day_width = float(day_width)
        opts.row_height = float(row_height)
        opts.height = to_c_size(height)
        opts.today = int(today)
        opts.read_only = bool(read_only)
        keep.extend((arr, opts))
        clicked = int(self._lib.nexa_gantt(
            self._ctx, encode_str(id, keep), arr, n,
            int(origin.year), int(origin.month), int(origin.day), int(days), ctypes.byref(opts)
        ))
        updated = [
            GanttTask(
                tasks[i].name, int(arr[i].start), int(arr[i].end),
                owner=tasks[i].owner, progress=float(arr[i].progress),
                tone=tasks[i].tone, depends_on=tasks[i].depends_on, milestone=tasks[i].milestone
            )
            for i in range(n)
        ]
        moved = any((updated[i].start != tasks[i].start or updated[i].end != tasks[i].end) for i in range(n))
        self._record_change(clicked >= 0 or moved)
        return updated, clicked

    def month_calendar(
        self,
        id: str,
        month: Date,
        events: Sequence[MonthEvent] = (),
        *,
        selected: Optional[Date] = None,
        first_weekday: int = 0,
        cell_height: float = 104.0,
        month_names: Sequence[str] = (),
        day_names: Sequence[str] = (),
        hour12: bool = False,
    ) -> MonthResult:
        """Month grid with day cells holding events; arrows and Today move ``month``.

        The month actually shown comes back on ``result.month`` — keep it.
        """
        keep = self._frame_keepalive
        c_month = to_c_date(month)
        c_sel = to_c_date(selected if selected is not None else month)
        n = len(events)
        arr = (CuiMonthEvent * n)()
        for i, ev in enumerate(events):
            arr[i].title = encode_str(ev.title, keep)
            arr[i].start = to_c_date(ev.start)
            arr[i].end = to_c_date(ev.end)
            arr[i].time = float(ev.time)
            arr[i].all_day = bool(ev.all_day)
            arr[i].tone = int(ev.tone)
        opts = CuiMonthOpts()
        opts.selected = ctypes.cast(ctypes.byref(c_sel), ctypes.POINTER(CuiDate))
        opts.first_weekday = int(first_weekday)
        opts.cell_height = float(cell_height)
        if month_names:
            m_arr, _ = encode_str_array(month_names, keep)
            opts.month_names = m_arr
        if day_names:
            d_arr, _ = encode_str_array(day_names, keep)
            opts.day_names = d_arr
        opts.hour12 = bool(hour12)
        out = CuiMonthResult()
        keep.extend((arr, opts, out))
        self._lib.nexa_month_calendar_ex(
            self._ctx, encode_str(id, keep), ctypes.byref(c_month), arr, n,
            ctypes.byref(opts), ctypes.byref(out),
        )
        res = MonthResult(
            event=int(out.event),
            day_clicked=0 if out.day_clicked else -1,
            month_changed=bool(out.month_changed),
            month=Date(c_month.year, c_month.month, c_month.day),
        )
        self._record_change(bool(res))
        return res
