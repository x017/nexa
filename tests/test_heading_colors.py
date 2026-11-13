"""Heading/text foreground & background colors actually reach the framebuffer."""

from __future__ import annotations

from typing import Callable

import nexa as ui

Draw = Callable[[ui.UI], None]


def _render(draw: Draw, width: int = 260, height: int = 120) -> bytearray:
    with ui.SoftwareRenderer(threads=1) as sw:
        with ui.UI(width=width, height=height, theme=ui.ThemeMode.DARK, renderer=sw) as ctx:
            with ctx.frame(1.0 / 60.0):
                with ctx.column(width=ui.FILL, height=ui.FILL, pad=8, gap=6, bg=ui.Color.BACKGROUND):
                    draw(ctx)
            buf = bytearray(width * height * 4)
            sw.render(ctx.draw_data(), buffer=buf)
            return buf


def _has_colour(buf: bytearray, pred: Callable[[int, int, int], bool]) -> bool:
    for i in range(0, len(buf), 4):
        if pred(buf[i], buf[i + 1], buf[i + 2]):
            return True
    return False


def test_heading_hex_colour() -> None:
    buf = _render(lambda ctx: ctx.heading("Coloured", level=2, color="#ff2040"))
    assert _has_colour(buf, lambda r, g, b: r > 180 and g < 80 and b < 110)


def test_heading_rgb_tuple_and_token() -> None:
    rgb = _render(lambda ctx: ctx.heading("Green", level=2, color=(40, 220, 90)))
    assert _has_colour(rgb, lambda r, g, b: g > 170 and r < 120 and b < 140)

    token = _render(lambda ctx: ctx.heading("Accent", level=2, color=ui.Color.ACCENT))
    default = _render(lambda ctx: ctx.heading("Accent", level=2))
    assert token != default, "a token colour must change the pixels"


def test_heading_background_chip() -> None:
    buf = _render(lambda ctx: ctx.heading("Chip", level=3, color="#ffffff", bg=(0, 140, 60)))
    assert _has_colour(buf, lambda r, g, b: g > 110 and r < 90 and b < 110)


def test_heading_is_unchanged_without_overrides() -> None:
    """The fast path must still be the C heading (no colour/size kwargs)."""
    buf = _render(lambda ctx: ctx.heading("Plain", level=1))
    assert _has_colour(buf, lambda r, g, b: r > 200 and g > 200 and b > 200)


def test_text_colour_and_alpha() -> None:
    solid = _render(lambda ctx: ctx.text("mmmm", size=20, color="#22c55e"))
    faint = _render(lambda ctx: ctx.text("mmmm", size=20, color=ui.with_alpha("#22c55e", 0.2)))
    assert _has_colour(solid, lambda r, g, b: g > 150 and r < 120)
    assert solid != faint, "with_alpha must blend against the background"
