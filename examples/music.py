"""Music Studio: Now Playing transport, interactive waveform, carousel & reorderable queue (port of music.c)."""

from __future__ import annotations

import math

import nexa as ui


def main() -> None:
    tracks = [
        ("Subpixel Nocturne", "Glyph Ensemble", 214.0, ui.Color.hex("#4f46e5")),
        ("Critically Damped", "Spring Quartet", 189.0, ui.Color.hex("#0d9488")),
        ("Zero Dependency", "Static Linkers", 242.0, ui.Color.hex("#e11d48")),
        ("Sixty Frames", "Immediate Mode", 176.0, ui.Color.hex("#d97706")),
    ]
    order = [0, 1, 2, 3]
    current_pos = 0
    slide_idx = 0
    playing = True
    progress = 0.34
    peaks = [0.2 + 0.75 * abs(math.sin(i * 0.31) * math.cos(i * 0.11)) for i in range(64)]

    def draw(ctx: ui.UI) -> None:
        nonlocal order, current_pos, slide_idx, playing, progress

        if playing:
            progress = (progress + ctx.dt / 180.0) % 1.0
            ctx.request_redraw()

        t_idx = order[current_pos]
        title, artist, dur, col = tracks[t_idx]

        with ctx.column(width=ui.FILL, height=ui.FILL, bg=ui.Color.BACKGROUND, pad=24, gap=20):
            with ctx.row(align=ui.Align.CENTER):
                ctx.heading("Studio Player", level=2)
                ctx.spacer()
                ctx.theme_toggle()

            with ctx.carousel("featured", len(tracks), slide_idx, height=150, loop=True) as car:
                for i, (tr_title, tr_artist, _, tr_col) in enumerate(tracks):
                    with car.slide():
                        with ctx.box(
                            width=ui.FILL, height=ui.FILL, radius=14, bg=tr_col, pad=20,
                            justify=ui.Justify.END,
                        ):
                            ctx.text(tr_title, font=ui.FontRole.DISPLAY, size=22, color=ui.Color(255, 255, 255))
                            ctx.text(tr_artist, size=14, color=ui.Color(255, 255, 255, 210))
            slide_idx = car.index

            with ctx.row(gap=20, width=ui.FILL, height=ui.FILL, wrap=True):
                with ctx.column(width=ui.GROW(3), min_width=340, gap=16):
                    np = ui.NowPlaying(
                        title=title, artist=artist,
                        position=progress * dur, duration=dur,
                        playing=playing, art_color=col,
                    )
                    np_out, flags = ctx.now_playing("player", np, width=ui.FILL)
                    playing = np_out.playing
                    if flags & ui.PlayerFlags.SEEK:
                        progress = np_out.position / max(1.0, dur)
                    if flags & ui.PlayerFlags.NEXT:
                        current_pos = (current_pos + 1) % len(order)
                        progress = 0.0
                    if flags & ui.PlayerFlags.PREV:
                        current_pos = (current_pos - 1) % len(order)
                        progress = 0.0

                    with ctx.card(pad=16, gap=8, width=ui.FILL):
                        ctx.secondary("Waveform Scrubber")
                        progress = ctx.waveform("wave", peaks, progress, width=ui.FILL, height=64)

                with ctx.card(width=ui.GROW(2), min_width=280, pad=18, gap=12):
                    ctx.heading("Up Next (Drag to reorder)", level=4)
                    with ctx.reorder("queue_reorder", order) as ro:
                        for pos in range(len(order)):
                            idx = order[pos]
                            tr_t, tr_a, tr_d, _ = tracks[idx]
                            with ro.item(pos):
                                if ctx.list_item(
                                    tr_t,
                                    subtitle=tr_a,
                                    icon=ui.Icon.AUDIO_LINES if pos == current_pos else ui.Icon.GRIP_VERTICAL,
                                    trailing=f"{int(tr_d // 60)}:{int(tr_d % 60):02d}",
                                    selected=(pos == current_pos),
                                ):
                                    current_pos = pos
                                    progress = 0.0
                    order = ro.order

    with ui.App("Music — nexa", width=1020, height=720, theme=ui.ThemeMode.DARK, accent=ui.Accent.CORAL) as app:
        app.run(draw)


if __name__ == "__main__":
    main()
