"""Project Tracker: Kanban board, Gantt chart, Week Calendar & team presence (port of tracker.c)."""

from __future__ import annotations

import nexa as ui


def main() -> None:
    tab = 0
    columns = [
        ("Backlog", ui.Color.series(0), [
            {"id": 101, "title": "Wayland native fractional scale", "tag": "Platform", "tone": ui.Tone.INFO},
            {"id": 102, "title": "Export SVG vector snapshot", "tag": "Render", "tone": ui.Tone.VIOLET},
        ]),
        ("In Progress", ui.Color.series(1), [
            {"id": 103, "title": "Asyncio cooperative frame driver", "tag": "Python", "tone": ui.Tone.ACCENT},
            {"id": 104, "title": "Virtualized 1M-row data grid", "tag": "Data", "tone": ui.Tone.WARNING},
        ]),
        ("Done", ui.Color.series(2), [
            {"id": 105, "title": "Zero-header dlopen X11 backend", "tag": "Linux", "tone": ui.Tone.SUCCESS},
        ]),
    ]

    gantt_tasks = [
        ui.GanttTask("Core ABI bridge", 0, 4, progress=1.0, owner="Maya", tone=ui.Tone.SUCCESS),
        ui.GanttTask("150 Widget Mixins", 3, 9, progress=0.85, owner="Liam", tone=ui.Tone.ACCENT, depends_on=0),
        ui.GanttTask("Async & Channels", 7, 12, progress=0.6, owner="Sora", tone=ui.Tone.VIOLET, depends_on=1),
        ui.GanttTask("v1.0 Release", 12, 12, progress=0.0, owner="Team", tone=ui.Tone.WARNING, depends_on=2, milestone=True),
    ]

    cal_events = [
        ui.CalEvent("Design review", day=0, start=9.5, end=11.0, detail="Room B", tone=ui.Tone.ACCENT),
        ui.CalEvent("Perf profiling", day=1, start=13.0, end=15.0, detail="60fps check", tone=ui.Tone.TEAL),
        ui.CalEvent("Release sync", day=3, start=10.0, end=11.5, detail="All hands", tone=ui.Tone.VIOLET),
    ]

    team = [
        ui.PresenceUser("Maya Okafor", color=ui.Color.series(0)),
        ui.PresenceUser("Liam Chen", color=ui.Color.series(1)),
        ui.PresenceUser("Sora Takahashi", color=ui.Color.series(2)),
        ui.PresenceUser("Elena Rostova", color=ui.Color.series(3), idle=True),
    ]
    next_id = 200

    def draw(ctx: ui.UI) -> None:
        nonlocal tab, gantt_tasks, cal_events, next_id

        with ctx.column(width=ui.FILL, height=ui.FILL, bg=ui.Color.BACKGROUND):
            with ctx.row(width=ui.FILL, pad_x=24, pad_y=12, gap=16, align=ui.Align.CENTER):
                ctx.heading("Sprint Planning", level=3)
                tab = ctx.tabs(
                    "tracker_tabs", ["Kanban Board", "Gantt Timeline", "Week Schedule"], tab,
                    icons=[ui.Icon.GRID_3X3, ui.Icon.SLIDERS_HORIZONTAL, ui.Icon.CALENDAR],
                    variant=ui.TabsVariant.PILL,
                )
                ctx.spacer()
                ctx.presence("team_pres", team)
                ctx.theme_toggle()

            ctx.separator()

            with ctx.box(width=ui.FILL, height=ui.FILL, pad=20):
                if tab == 0:
                    with ctx.kanban("sprint_board") as board:
                        for col_title, dot_col, cards in columns:
                            with board.column(col_title, len(cards), dot=dot_col, width=300) as col_scope:
                                if col_scope.add_clicked:
                                    cards.append({
                                        "id": next_id,
                                        "title": f"New task #{next_id}",
                                        "tag": "Task",
                                        "tone": ui.Tone.NEUTRAL,
                                    })
                                    next_id += 1
                                for item in cards:
                                    with board.card(item["id"]):
                                        with ctx.column(gap=8, width=ui.FILL):
                                            ctx.text(item["title"], font=ui.FontRole.MEDIUM)
                                            with ctx.row(align=ui.Align.CENTER):
                                                ctx.badge(item["tag"], tone=item["tone"], size=ui.ControlSize.SM)
                                                ctx.spacer()
                                                ctx.muted(f"#{item['id']}")

                    if board.move is not None:
                        mv = board.move
                        moved_card = None
                        for idx, c in enumerate(columns[mv.from_column][2]):
                            if c["id"] == mv.card:
                                moved_card = columns[mv.from_column][2].pop(idx)
                                break
                        if moved_card is not None:
                            dst = columns[mv.to_column][2]
                            dst.insert(min(mv.to_index, len(dst)), moved_card)

                elif tab == 1:
                    gantt_tasks, _ = ctx.gantt(
                        "roadmap", gantt_tasks, ui.Date(2026, 11, 2), 16,
                        height=ui.FILL, today=4,
                    )
                else:
                    cal_events, _ = ctx.week_calendar(
                        "week_sched", ui.Date(2026, 11, 2), cal_events,
                        start_hour=8.0, end_hour=18.0, height=ui.FILL,
                    )

    with ui.App("Tracker — nexa", width=1100, height=700) as app:
        app.run(draw)


if __name__ == "__main__":
    main()
