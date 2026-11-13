"""Dot Matrix — the CUI post-1.4 dither family in one window.

Demonstrates ``spinner`` styles, dither ``progress``, ``pattern_meter``,
``status_spinner``, ``skeleton_group``, ``veil`` and the dithered/stacked
``line_chart`` — everything drawn in ordered-dither dots, no blending.

    python examples/dither.py

The veil is live: click it (or focus it and press Enter/Space) to dissolve the
cover, click again to bring it back.  Runs headless with
``NEXA_HEADLESS=1 CUI_SCREENSHOT=out.png``.
"""

from __future__ import annotations

import math
import time

import nexa as ui

STYLES = [
    ("arc", ui.SpinnerStyle.ARC),
    ("comet", ui.SpinnerStyle.COMET),
    ("dots", ui.SpinnerStyle.DOT_MATRIX),
    ("radar", ui.SpinnerStyle.RADAR),
    ("orbit", ui.SpinnerStyle.ORBIT),
    ("spiral", ui.SpinnerStyle.SPIRAL),
    ("plasma", ui.SpinnerStyle.PLASMA),
    ("bounce", ui.SpinnerStyle.BOUNCE),
]

LABELS = [f"{6 + i * 2}:00" for i in range(24)]
BUILD = [1, 2, 4, 6, 5, 3, 2, 4, 7, 8, 6, 4, 3, 5, 6, 4, 2, 1, 1, 0, 0, 0, 0, 0]
TEST = [0, 1, 2, 3, 3, 2, 1, 2, 3, 4, 3, 2, 1, 2, 3, 2, 1, 0, 0, 0, 0, 0, 0, 0]


def main() -> None:
    started = time.time()
    revealed = False

    def draw(ctx: ui.UI) -> None:
        nonlocal revealed
        elapsed = time.time() - started
        ctx.request_redraw()  # the dither animations keep moving

        with ctx.column(width=ui.FILL, height=ui.FILL, pad=20, gap=14, bg=ui.Color.BACKGROUND):
            with ctx.row(align=ui.Align.CENTER, width=ui.FILL):
                ctx.heading("Dot Matrix", level=2)
                ctx.badge("CUI dither", tone=ui.Tone.ACCENT, dot=True)
                ctx.spacer()
                ctx.secondary("ordered 8×8, a dot is the colour or nothing")

            with ctx.row(width=ui.FILL, gap=16):
                # ---- spinner styles ------------------------------------
                with ctx.card(width=ui.GROW(3), pad=16, gap=12):
                    ctx.secondary("Spinner styles")
                    with ctx.row(gap=18, width=ui.FILL, wrap=True):
                        for name, style in STYLES:
                            with ctx.column(gap=6, align=ui.Align.CENTER):
                                ctx.spinner(26, style=style, color="#7dd3fc", track="#1e293b")
                                ctx.text(name, size=11, color=ui.Color.TEXT_MUTED)

                    ctx.secondary("Progress")
                    value = (elapsed * 0.22) % 1.15
                    ctx.progress(min(value, 1.0), dither=True, label="indexing", tone=ui.Tone.ACCENT)
                    ctx.progress(0.0, dither=True, indeterminate=True, label="sweeping", tone=ui.Tone.TEAL)

                # ---- pattern meter + status spinner ---------------------
                with ctx.card(width=ui.GROW(2), pad=16, gap=12):
                    ctx.secondary("Pattern meter")
                    parts = [
                        ui.MeterPart("build", 46 + 10 * math.sin(elapsed), "#22d3ee"),
                        ui.MeterPart("test", 28, "#a78bfa"),
                        ui.MeterPart("idle", 16, density=0.14),
                    ]
                    focused = ctx.pattern_meter("cpu", parts, total=100, label="cpu", unit="%")
                    if focused >= 0:
                        ctx.text(f"focused: {parts[focused].name}", size=11, color=ui.Color.TEXT_MUTED)

                    ctx.secondary("Status spinner")
                    phase = int(elapsed) % 6
                    status = ui.Status.BUSY if phase < 4 else ui.Status.SUCCESS
                    alive = ctx.status_spinner("deploy", status, size=28, color="#34d399")
                    if not alive:
                        ctx.text("done — the widget retired itself", size=11, color=ui.Color.TEXT_MUTED)

            with ctx.row(width=ui.FILL, gap=16):
                # ---- skeleton group + veil ------------------------------
                with ctx.card(width=ui.GROW(2), pad=16, gap=12):
                    ctx.secondary("Skeleton group (one shine)")
                    with ctx.skeleton_group(dither=True, width=ui.FILL, gap=10):
                        ctx.skeleton(width=ui.FILL, height=14)
                        ctx.skeleton(width=ui.PCT(70), height=14)
                        with ctx.row(gap=10, width=ui.FILL):
                            ctx.skeleton(width=48, height=48)
                            with ctx.column(gap=6, width=ui.FILL):
                                ctx.skeleton(width=ui.FILL, height=12)
                                ctx.skeleton(width=ui.PCT(60), height=12)

                    ctx.secondary("Veil")
                    with ctx.veil("secret", revealed, label="Deploy token", hint="Click to show", width=ui.FILL) as v:
                        with ctx.card(pad=10, width=ui.FILL):
                            ctx.text("sk_live_51H8x…9dQ2", size=13, color="#34d399")
                    revealed = v.revealed
                    ctx.text(
                        "revealed" if revealed else "covered — click the dots",
                        size=11,
                        color=ui.Color.TEXT_MUTED,
                    )

                # ---- dithered chart ------------------------------------
                with ctx.card(width=ui.GROW(3), pad=16, gap=12):
                    ctx.secondary("Dithered area, stacked bands")
                    ctx.line_chart(
                        "load",
                        [
                            ui.Series("build", BUILD),
                            ui.Series("test", TEST),
                        ],
                        labels=LABELS,
                        stacked=True,
                        dither=True,
                        height=190.0,
                        width=ui.FILL,
                    )

    with ui.App("Dot Matrix — nexa", width=1080, height=680, theme=ui.ThemeMode.DARK, accent=ui.Accent.BLUE) as app:
        app.run(draw)


if __name__ == "__main__":
    main()
