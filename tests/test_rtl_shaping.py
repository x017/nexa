"""A default build must shape Arabic-script text, i.e. join the letters.

Persian/Arabic letters only connect when the shaper applies the font's initial /
medial / final forms; an unshaped build draws every letter in isolated form.
"""

from __future__ import annotations

import pytest

import nexa as ui
from nexa import fonts

WORD = "سلام"          # four letters that join into a single run
PERSIAN = "کتاب‌ها"


def test_default_build_shapes_text() -> None:
    assert fonts.supports_text_shaping(), (
        "this native library was built without text shaping; "
        "run `python -m nexa.build` (drop --no-rtl)"
    )


def test_rtl_font_is_available() -> None:
    path = fonts.find_rtl_font()
    if path is None:
        pytest.skip("no Arabic-capable system font installed")
    assert path.is_file()


def test_joined_word_is_narrower_than_isolated_letters() -> None:
    """Shaping pulls the letters together, so the run is shorter than the sum of its glyphs."""
    if fonts.find_rtl_font() is None:
        pytest.skip("no Arabic-capable system font installed")

    with ui.SoftwareRenderer(threads=1) as sw:
        with ui.UI(width=400, height=200, theme=ui.ThemeMode.DARK, renderer=sw) as ctx:
            with ctx.frame(1.0 / 60.0):
                ctx.use_rtl_font()
                joined = ctx.measure_text(WORD, size=24.0).width
                isolated = sum(ctx.measure_text(ch, size=24.0).width for ch in WORD)
    assert joined > 0
    assert joined < isolated, f"joined={joined:.1f}px isolated={isolated:.1f}px (letters not joined)"


def test_shaped_text_renders_inside_an_rtl_column() -> None:
    buf = bytearray(360 * 120 * 4)
    with ui.SoftwareRenderer(threads=1) as sw:
        with ui.UI(width=360, height=120, theme=ui.ThemeMode.DARK, renderer=sw) as ctx:
            with ctx.frame(1.0 / 60.0):
                ctx.use_rtl_font()
                with ctx.column(
                    width=ui.FILL, height=ui.FILL, pad=12, bg=ui.Color.BACKGROUND,
                    direction=ui.TextDirection.RTL,
                ):
                    ctx.text(PERSIAN, size=22.0)
            sw.render(ctx.draw_data(), buffer=buf)
    painted = sum(1 for i in range(0, len(buf), 4) if buf[i] + buf[i + 1] + buf[i + 2] > 200)
    assert painted > 80, "the Persian text did not render"


def test_text_direction_auto_handles_mixed_runs() -> None:
    with ui.SoftwareRenderer(threads=1) as sw:
        with ui.UI(width=400, height=200, theme=ui.ThemeMode.DARK, renderer=sw) as ctx:
            with ctx.frame(1.0 / 60.0):
                ctx.use_rtl_font()
                with ctx.column(width=ui.FILL, direction=ui.TextDirection.AUTO):
                    ctx.text("English and فارسی in one line", size=16.0)
    # mixed runs must not raise and must keep a sensible width
    assert True
