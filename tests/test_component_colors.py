"""Per-component color overrides reach the framebuffer (inputs, cards, buttons)."""

from __future__ import annotations

from typing import Callable

import nexa as ui

Draw = Callable[[ui.UI], None]


def _render(draw: Draw, width: int = 320, height: int = 140) -> bytearray:
    with ui.SoftwareRenderer(threads=1) as sw:
        with ui.UI(width=width, height=height, theme=ui.ThemeMode.DARK, renderer=sw) as ctx:
            with ctx.frame(1.0 / 60.0):
                with ctx.column(width=ui.FILL, height=ui.FILL, pad=10, gap=10, bg=ui.Color.BACKGROUND):
                    draw(ctx)
            buf = bytearray(width * height * 4)
            sw.render(ctx.draw_data(), buffer=buf)
            return buf


def _has_colour(buf: bytearray, pred: Callable[[int, int, int], bool]) -> bool:
    return any(pred(buf[i], buf[i + 1], buf[i + 2]) for i in range(0, len(buf), 4))


def _near(r: int, g: int, b: int, target: tuple[int, int, int], tol: int = 26) -> bool:
    return abs(r - target[0]) <= tol and abs(g - target[1]) <= tol and abs(b - target[2]) <= tol


def test_input_background_and_text_colour() -> None:
    buf = _render(
        lambda ctx: ctx.input("f", "value", bg="#2a1d05", text_color="#ffd28a", border_color="#7a5210")
    )
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (42, 29, 5), 12)), "field background"
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (255, 210, 138), 30)), "field text"
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (122, 82, 16), 40)), "field border"


def test_input_placeholder_colour() -> None:
    buf = _render(lambda ctx: ctx.input("f", "", placeholder="type…", placeholder_color="#8b5cf6"))
    assert _has_colour(buf, lambda r, g, b: r > 110 and b > 200 and g < 130)


def test_input_alias_colour_equals_text_color() -> None:
    via_alias = _render(lambda ctx: ctx.input("f", "same text", color="#00ff88", bg="#101010"))
    via_explicit = _render(lambda ctx: ctx.input("f", "same text", text_color="#00ff88", bg="#101010"))
    assert via_alias == via_explicit


def test_input_border_and_focus_colours_change_pixels() -> None:
    plain = _render(lambda ctx: ctx.input("f", "text"))
    edged = _render(lambda ctx: ctx.input("f", "text", border_color="#00c2ff", focus_color="#00c2ff"))
    assert plain != edged


def test_textarea_takes_the_same_colours() -> None:
    buf = _render(lambda ctx: ctx.textarea("t", "multi", bg="#0d1f2b", text_color="#7ce7ff", height=70))
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (13, 31, 43), 12))


def test_card_background_and_border() -> None:
    buf = _render(lambda ctx: _card(ctx, bg="#1b1230", border_color="#7c5cff"))
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (27, 18, 48), 10))
    plain = _render(lambda ctx: _card(ctx, None, None))
    assert plain != buf


def _card(ctx: ui.UI, bg, border_color) -> None:
    with ctx.card(pad=14, bg=bg, border_color=border_color):
        ctx.text("card body")


def test_button_colour() -> None:
    coloured = _render(lambda ctx: ctx.button("Action", color="#ff5c8a"))
    plain = _render(lambda ctx: ctx.button("Action"))
    assert coloured != plain
    assert _has_colour(coloured, lambda r, g, b: _near(r, g, b, (255, 92, 138), 40))


def test_box_border_colour_still_works() -> None:
    buf = _render(lambda ctx: _box(ctx))
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (0, 200, 255), 40))


def _box(ctx: ui.UI) -> None:
    with ctx.box(bg="#101820", border_color="#00c8ff", border=2.0, pad=10, radius=8):
        ctx.text("boxed")


def test_colour_arguments_are_visible_in_the_public_signatures() -> None:
    """A colour you cannot discover is a colour nobody uses."""
    import inspect

    for name in ("input", "textarea", "search"):
        params = inspect.signature(getattr(ui.UI, name)).parameters
        for kw in ("bg", "color", "text_color", "placeholder_color", "border_color", "focus_color"):
            assert kw in params, f"{name}() does not expose {kw}="


def test_number_has_no_colour_arguments_yet() -> None:
    """`cui_number_opts` carries no colours upstream, so there is nothing to pass.

    Pinned so the day CUI (or a local delta) adds them, this test fails and the
    docs table gets updated instead of quietly going stale.
    """
    import inspect

    params = inspect.signature(ui.UI.number).parameters
    for kw in ("bg", "color", "text_color", "border_color", "focus_color", "fg"):
        assert kw not in params, f"number() gained {kw}=; update the colour table in docs"
