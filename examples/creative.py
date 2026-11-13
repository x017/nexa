"""Workshop — the eight CUI post-1.4 creative controls in one window.

``status_tag``, ``ratio_slider``, ``gradient_slider``, ``step_slider``,
``palette_strip``, ``aspect_picker``, ``option_action`` and ``seed_field``,
wired together: the seed feeds the palette shuffle, the ratio and aspect
drive a live "export" readout.

    python examples/creative.py

Everything returns its new value each frame — plain variables, no state
class.  Runs headless with ``NEXA_HEADLESS=1 CUI_SCREENSHOT=out.png``.
"""

from __future__ import annotations

import time

import nexa as ui

RATIOS = [(16, 9, "Wide"), (4, 3, "Classic"), (1, 1, "Square"), (9, 16, "Story")]


def main() -> None:
    split = 0.62
    hue = 0.58
    zoom = 2
    palette = ["#22d3ee", "#a78bfa", "#f472b6", "#facc15", "#34d399", "#fb7185"]
    locked = [True, False, False, False, False, False]
    aspect = 0
    mode = 0
    seed = ui.SeedResult(0x5EED1234, locked=False)
    started = time.time()

    def draw(ctx: ui.UI) -> None:
        nonlocal split, hue, zoom, aspect, mode, seed
        ctx.request_redraw()  # the in-progress tag's ring keeps turning
        elapsed = time.time() - started

        with ctx.column(width=ui.FILL, height=ui.FILL, pad=20, gap=14, bg=ui.Color.BACKGROUND):
            with ctx.row(align=ui.Align.CENTER, width=ui.FILL):
                ctx.heading("Workshop", level=2)
                ctx.badge("creative controls", tone=ui.Tone.VIOLET, dot=True)
                ctx.spacer()
                # A tag whose state advances: pending → in progress → submitted.
                phase = int(elapsed / 3) % 3
                tag = (ui.TagStatus.PENDING, ui.TagStatus.IN_PROGRESS, ui.TagStatus.SUBMITTED)[phase]
                ctx.status_tag(
                    ("queued", "building", "shipped")[phase], tag, removable=True, id="job"
                )

            with ctx.row(width=ui.FILL, gap=16):
                # ---- sliders & pickers ----------------------------------
                with ctx.card(width=ui.GROW(3), pad=16, gap=12):
                    split = ctx.ratio_slider("Foreground", "Background", split, tone=ui.Tone.ACCENT)
                    hue = ctx.gradient_slider(
                        "Accent hue", hue, track=ui.GradientTrack.HUE, swatch=True,
                        format="%.0f°", tool="dice", tool_tooltip="Randomize",
                    ).value
                    zr = ctx.step_slider(
                        "Export scale", zoom, min=0, max=4,
                        labels=["25%", "50%", "100%", "200%", "400%"], tool="!", tool_tooltip="Double it",
                    )
                    zoom = int(zr.value)
                    if zr.action:
                        zoom = min(zoom + 1, 4)
                    picked = ctx.aspect_picker("Canvas", aspect, ratios=RATIOS, base=1080)
                    aspect = picked if 0 <= picked < len(RATIOS) else max(aspect, 0)

                # ---- palette + seed ------------------------------------
                with ctx.card(width=ui.GROW(2), pad=16, gap=12):
                    changed = ctx.palette_strip(
                        "Palette", palette, locked, seed=seed.seed & 0xFFFFFFFF, no_shuffle=False
                    )
                    sr = ctx.seed_field("Shuffle seed", seed.seed, seed.locked, plain=False)
                    seed = sr
                    if changed:
                        ctx.text("palette reshuffled from the seed", size=11, color=ui.Color.TEXT_MUTED)
                    with ctx.row(gap=8, width=ui.FILL):
                        idx = ctx.option_action(
                            "Render", ["PNG", "WebP", "AVIF"], mode, icon=">", tooltip="Export"
                        )
                        mode = int(idx.value)
                        if idx.action:
                            ctx.toast(
                                f"Export {['PNG', 'WebP', 'AVIF'][mode]}",
                                description=f"{RATIOS[aspect][0]}×{RATIOS[aspect][1]} @ {zoom}x",
                                tone=ui.Tone.SUCCESS,
                            )

            # ---- live export readout ------------------------------------
            with ctx.card(width=ui.FILL, pad=14, gap=8):
                w, h, _ = RATIOS[aspect]
                scale = (25, 50, 100, 200, 400)[zoom]
                with ctx.row(gap=24, width=ui.FILL, align=ui.Align.CENTER):
                    ctx.readout("EXPORT", f"{w * scale // 10}×{h * scale // 10}", unit="px", size=ui.ControlSize.SM)
                    ctx.readout("SPLIT", f"{split * 100:.0f}", unit="%", size=ui.ControlSize.SM)
                    ctx.readout("HUE", f"{hue * 360:.0f}", unit="°", size=ui.ControlSize.SM)
                    ctx.readout("SEED", f"{seed.seed:08X}", size=ui.ControlSize.SM)
                    ctx.spacer()
                    ctx.secondary("every widget returns its new value each frame")

    with ui.App("Workshop — nexa", width=1040, height=640, theme=ui.ThemeMode.DARK, accent=ui.Accent.VIOLET) as app:
        app.run(draw)


if __name__ == "__main__":
    main()
