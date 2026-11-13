"""Studio — the CUI post-1.4 canvas & bars components in one window.

``toolbar`` with the GROUPED style (groups, radio set, cycle picker, primary
action), ``format_bar`` editing a live ``TextFormat``, ``live_cursors`` +
``presence_pill`` + ``selection_ring`` over a shared canvas,
``canvas_controls`` driving a node view, a ``result_card`` and the
``selection_bar`` that slides up under a multi-select list.

    python examples/creative.py  # sibling: the eight creative controls

Runs headless with ``NEXA_HEADLESS=1 CUI_SCREENSHOT=out.png``.
"""

from __future__ import annotations

import math
import time

import nexa as ui

ITEMS = [
    "hero-banner.png", "logo-mark.svg", "type-scale.json", "tokens.yaml",
    "onboarding-01.png", "empty-state.svg", "brand-motion.mp4",
]


def main() -> None:
    started = time.time()
    view = ui.NodeView(0.0, 0.0, 1.0)
    toggles = [ui.CanvasToggle(ui.Icon.GRID_3X3, "Snap to grid", True),
               ui.CanvasToggle(ui.Icon.MAXIMIZE_2, "Show guides", False)]
    fmt = ui.TextFormat(color=int(ui.Tone.ACCENT), bold=True, size=18)
    zoom = 1
    tool_mode = 0
    selected = [True, False, True, False, False, False, False]
    texture = [0]

    def draw(ctx: ui.UI) -> None:
        nonlocal view, zoom, tool_mode, selected, texture
        elapsed = time.time() - started
        ctx.request_redraw()  # cursors glide, playhead moves

        # Generate the card thumbnail once the context exists.
        if not texture[0]:
            w = h = 96
            rgba = bytearray(w * h * 4)
            for y in range(h):
                for x in range(w):
                    i = (y * w + x) * 4
                    rgba[i] = x * 255 // w
                    rgba[i + 1] = y * 255 // h
                    rgba[i + 2] = 140
                    rgba[i + 3] = 255
            texture[0] = ctx.image_create(w, h, bytes(rgba))

        with ctx.column(width=ui.FILL, height=ui.FILL, bg=ui.Color.BACKGROUND):
            # ---- grouped toolbar ----------------------------------------
            with ctx.toolbar("studio-tools", style=ui.ToolbarStyle.GROUPED):
                with ctx.toolbar_group():
                    ctx.toolbar_button(ui.Icon.PLAY, label="Run", tone=ui.Tone.SUCCESS)
                    ctx.toolbar_button(ui.Icon.SQUARE, label="Stop")
                with ctx.toolbar_group():
                    tool_mode = ctx.toolbar_radio("tool", [ui.Icon.PENCIL, ui.Icon.SCISSORS, ui.Icon.MOVE], tool_mode)
                    zoom = ctx.toolbar_cycle("zoom", ["1x", "2x", "4x", "8x"], zoom)
                ctx.toolbar_spacer()
                if ctx.toolbar_primary(ui.Icon.PLUS, label="New layer"):
                    ctx.toast("New layer", tone=ui.Tone.SUCCESS)

            with ctx.column(width=ui.FILL, height=ui.FILL, pad=16, gap=12):
                with ctx.row(align=ui.Align.CENTER, width=ui.FILL):
                    ctx.heading("Studio", level=2)
                    ctx.badge("canvas & bars", tone=ui.Tone.INFO, dot=True)
                    ctx.spacer()
                    # Presence: who is here right now.
                    users = [
                        ui.LiveUser("ana", 0, 0, speaking=(int(elapsed) % 4) < 2),
                        ui.LiveUser("bo", 0, 0, away=(int(elapsed / 5) % 2) == 1),
                        ui.LiveUser("cy", 0, 0),
                    ]
                    ctx.presence_pill("who", users, max_visible=3)

                with ctx.row(width=ui.FILL, gap=16):
                    # ---- shared canvas ----------------------------------
                    with ctx.card(width=ui.GROW(3), pad=12, gap=8):
                        ctx.secondary("Shared canvas — cursors, ring, zoom rail")
                        res = ctx.canvas_controls("zoom-rail", view, steps=[0.5, 1, 2, 4], toggles=toggles)
                        if res.zoomed or res.fit:
                            pass  # view was updated in place
                        rect = ctx.canvas("board", ui.FILL, 260.0)
                        # Two collaborators drifting; the ring marks the selection.
                        ax = 90 + 60 * math.sin(elapsed * 0.8)
                        ay = 80 + 40 * math.cos(elapsed * 0.6)
                        bx = 220 + 70 * math.cos(elapsed * 0.5)
                        by = 150 + 50 * math.sin(elapsed * 0.7)
                        ctx.live_cursors(
                            "cursors",
                            [ui.LiveUser("ana", ax, ay, says="here?"), ui.LiveUser("bo", bx, by)],
                            view=view,
                        )
                        ctx.selection_ring("#22d3ee", name="ana", radius=14)
                        ctx.text(
                            f"zoom ×{view.zoom:.2f}  " + ("snap " if toggles[0].on else ""),
                            size=11, color=ui.Color.TEXT_MUTED,
                        )
                        _ = rect

                    # ---- result card + format --------------------------
                    with ctx.card(width=ui.GROW(2), pad=14, gap=10):
                        ctx.secondary("Result card")
                        if ctx.result_card(
                            "card", texture[0], "sunset-study.png",
                            caption="rendered 2 min ago", badge="ready", badge_tone=ui.Tone.SUCCESS,
                            aspect=1.25, width=ui.FILL,
                        ):
                            ctx.toast("Card opened", tone=ui.Tone.INFO)

                        ctx.secondary("Format bar")
                        fr = ctx.format_bar(
                            "fmt", fmt,
                            styles=[("Normal", 13), ("Header", 28, 15), ("Quote", 15, 13)],
                            colors=[ui.Tone.NEUTRAL, ui.Tone.INFO, ui.Tone.SUCCESS, ui.Tone.WARNING, ui.Tone.DANGER],
                            footer="Text options",
                        )
                        if fr.delete:
                            ctx.toast("Delete confirmed", tone=ui.Tone.DANGER)
                        with ctx.row(gap=8, width=ui.FILL):
                            ctx.text("Preview", size=11, color=ui.Color.TEXT_MUTED)
                            ctx.spacer()
                            ctx.text(
                                f"bold={fmt.bold} underline={fmt.underline} size={fmt.size:.0f}",
                                size=11, color=ui.Color.TEXT_SECONDARY,
                            )

                # ---- selection bar ------------------------------------
                with ctx.card(width=ui.FILL, pad=12, gap=8):
                    ctx.secondary("Multi-select list")
                    with ctx.column(width=ui.FILL, gap=4):
                        for i, name in enumerate(ITEMS):
                            if ctx.checkbox(name, selected[i]):
                                selected[i] = not selected[i]
                    actions = [
                        ui.SelectionAction("Archive", icon=ui.Icon.ARCHIVE),
                        ui.SelectionAction("Download", icon=ui.Icon.DOWNLOAD),
                        ui.SelectionAction("Delete", icon=ui.Icon.TRASH, tone=ui.Tone.DANGER),
                    ]
                    picked = ctx.selection_bar("files", actions, selected, count_format="%d selected")
                    if picked >= 0:
                        ctx.toast(f"{actions[picked].label} ({sum(selected)} items)", tone=ui.Tone.ACCENT)
                    elif picked == -2:
                        ctx.toast("Selection cleared", tone=ui.Tone.NEUTRAL)

    with ui.App("Studio — nexa", width=1120, height=800, theme=ui.ThemeMode.DARK, accent=ui.Accent.BLUE) as app:
        app.run(draw)


if __name__ == "__main__":
    main()
