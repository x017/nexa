"""Reactor Console — the CUI 1.4 instrument cluster in one window.

Demonstrates ``knob``, ``fader``, ``level_meter``, ``radial_gauge``, ``readout``,
``dot_display``, ``dot_chart`` and ``event_track``.  Every instrument returns the
value the user dialed in, so the whole console is plain floats — no state class,
no callbacks.

    python examples/instruments.py

Drag a knob up/down to turn it (double-click to reset), drag a fader, click an
empty spot on the event track to log an event.  Runs headless with
``NEXA_HEADLESS=1 CUI_SCREENSHOT=out.png``.
"""

from __future__ import annotations

import math
import time

import nexa as ui

# One reading per hour for the dot chart.
LOAD = [0, 0, 1, 2, 2, 1, 3, 4, 3, 2, 5, 4, 3, 2, 4, 5, 3, 2, 1, 1, 0, 0, 0, 0]


def main() -> None:
    gain = 0.32
    tone = 0.55
    volume = 0.6
    balance = 0.5
    peak = 0.0
    events = [0.6, 2.4, 6.1, 9.5, 13.2, 18.4]
    selected = -1
    started = time.time()

    def draw(ctx: ui.UI) -> None:
        nonlocal gain, tone, volume, balance, peak, selected

        elapsed = time.time() - started
        core = 42.0 + 16.0 * math.sin(elapsed * 0.9) + 6.0 * math.sin(elapsed * 4.3)
        ctx.request_redraw()  # the console is animated, so keep frames coming

        # Two channels of fake linear peak levels driven by the reactor; CUI
        # converts them to dB for the scale (1.0 would clip).
        wobble = 0.5 + 0.5 * math.sin(elapsed * 2.1)
        left = min(0.98, 0.05 + 0.85 * (core / 100.0) * (0.55 + 0.45 * wobble))
        right = min(0.98, left * (1.0 + 0.12 * math.sin(elapsed * 0.7)))
        peak = max(peak * 0.985, left)

        with ctx.column(width=ui.FILL, height=ui.FILL, bg=ui.Color.BACKGROUND, pad=22, gap=16):
            with ctx.row(align=ui.Align.CENTER, width=ui.FILL):
                ctx.heading("Reactor Console", level=2)
                ctx.badge("LIVE", tone=ui.Tone.SUCCESS, dot=True)
                ctx.spacer()
                ctx.dot_display(f"T+{int(elapsed) // 60:02d}:{int(elapsed) % 60:02d}", accent=True)

            with ctx.row(width=ui.FILL, height=ui.FILL, gap=16):
                # ---- dials & gains ------------------------------------------
                with ctx.card(width=ui.GROW(2), min_width=340, height=ui.FILL, pad=18, gap=14):
                    ctx.secondary("Manual gain staging")
                    with ctx.row(gap=14, align=ui.Align.CENTER, width=ui.FILL):
                        gain = ctx.knob("gain", gain, label="INPUT", format="%+.0f%%", size=70.0, bipolar=True)
                        tone = ctx.knob("tone", tone, label="TONE", unit="%", size=70.0, step=0.05)
                        with ctx.column(gap=4, align=ui.Align.CENTER):
                            ctx.radial_gauge(
                                "reactor",
                                core,
                                label="CORE",
                                unit="%",
                                size=106.0,
                                target=62.0,
                                bands=[(50.0, ui.Tone.SUCCESS), (78.0, ui.Tone.WARNING), (100.0, ui.Tone.DANGER)],
                            )
                            ctx.text("target 62%", size=11, color=ui.Color.TEXT_MUTED)

                    with ctx.row(gap=26, align=ui.Align.END, width=ui.FILL, wrap=True):
                        volume = ctx.fader(
                            "volume",
                            volume,
                            label="MASTER",
                            format="%.0f%%",
                            length=176.0,
                            ticks=[0.0, 0.25, 0.5, 0.75, 1.0],
                            meter=[peak],
                        )
                        balance = ctx.fader(
                            "balance", balance, label="BAL", format="%.2f",
                            length=176.0, ticks=[0.0, 0.5, 1.0], reset=0.5,
                        )
                        ctx.readout(
                            "OUTPUT",
                            f"{core * volume:.0f}",
                            unit="%",
                            detail="post-fader",
                            accent=True,
                            size=ui.ControlSize.LG,
                        )

                # ---- meters & trend -----------------------------------------
                with ctx.card(width=ui.GROW(3), min_width=400, height=ui.FILL, pad=18, gap=14):
                    ctx.secondary("Levels & 24 h load")
                    ctx.level_meter(
                        "main_meter",
                        [left, right],
                        horizontal=True,
                        length=0.0,
                        thickness=16.0,
                        hold=1.8,
                    )
                    ctx.dot_chart(
                        "load",
                        [ui.DotSeries(LOAD, name="load", accent=True)],
                        height=300.0,
                        x_units="hours",
                        x_step=6.0,
                        unit="%",
                        annotations=[
                            ui.ChartAnnotation(x=10, y=5, label="PEAK", detail="13:00", accent=True),
                            ui.ChartAnnotation(kind=ui.AnnotationKind.Y, y=3.0, label="LIMIT"),
                        ],
                    )

                    ctx.secondary("Event track")
                    track = ctx.event_track(
                        "events",
                        events,
                        min=0.0,
                        max=24.0,
                        units="hours",
                        step=4.0,
                        selected=selected,
                    )
                    selected = track.selected
                    ctx.text(
                        "click an empty spot to log · drag a tick to move it",
                        size=11,
                        color=ui.Color.TEXT_MUTED,
                    )

                # ---- readouts & event log -----------------------------------
                with ctx.card(width=ui.GROW(2), min_width=310, height=ui.FILL, pad=18, gap=14):
                    ctx.secondary("Session readouts")
                    with ctx.row(gap=14, width=ui.FILL, wrap=True):
                        ctx.readout("EVENTS", str(len(events)), unit="logged", size=ui.ControlSize.SM)
                        ctx.readout("GAIN", f"{gain * 100:+.0f}", unit="%", size=ui.ControlSize.SM)
                        ctx.readout("TONE", f"{tone * 100:.0f}", unit="%", size=ui.ControlSize.SM)

                    ctx.secondary("Channel strip")
                    with ctx.row(gap=18, align=ui.Align.CENTER, width=ui.FILL):
                        for name, level in (("L", left), ("R", right), ("SUB", left * 0.6)):
                            with ctx.column(gap=6, align=ui.Align.CENTER):
                                ctx.level_meter(
                                    f"strip_{name}", [level], length=140.0, thickness=12.0,
                                    hold=1.8, segmented=True,
                                )
                                ctx.text(name, size=11, color=ui.Color.TEXT_MUTED)

                    with ctx.card(pad=12, gap=6, width=ui.FILL):
                        ctx.text(f"peak {20 * math.log10(max(peak, 1e-4)):+.1f} dBFS", size=12)
                        ctx.text("coolant loop nominal", size=12, color=ui.Color.TEXT_SECONDARY)
                        ctx.status_button("Sync telemetry", ui.Status.IDLE, icon=ui.Icon.REFRESH_CW)

    with ui.App(
        "Reactor Console — nexa", width=1200, height=820, theme=ui.ThemeMode.DARK, accent=ui.Accent.VIOLET
    ) as app:
        app.run(draw)


if __name__ == "__main__":
    main()
