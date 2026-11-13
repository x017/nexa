"""``fg=`` on container scopes tints the text drawn inside them.

The colour is a Python-side stack: ``ctx.column(fg=...)`` pushes it on enter and
pops it on exit, so ``ctx.text()`` / ``ctx.heading()`` inherit it, an explicit
``color=`` still wins, and nothing leaks past the ``with`` block (including when
the block raises).
"""

from __future__ import annotations

from typing import Callable

import nexa as ui

Draw = Callable[[ui.UI], None]

RED = (255, 40, 40)
BLUE = (40, 40, 255)
WIDTH, HEIGHT = 360, 200


def _render(draw: Draw) -> bytearray:
    with ui.SoftwareRenderer(threads=1) as sw:
        with ui.UI(width=WIDTH, height=HEIGHT, theme=ui.ThemeMode.DARK, renderer=sw) as ctx:
            with ctx.frame(1.0 / 60.0):
                with ctx.column(width=ui.FILL, height=ui.FILL, pad=10, gap=6, bg=ui.Color.BACKGROUND):
                    draw(ctx)
            buf = bytearray(WIDTH * HEIGHT * 4)
            sw.render(ctx.draw_data(), buffer=buf)
            return buf


def _count(buf: bytearray, pred: Callable[[int, int, int], bool],
           y0: int = 0, y1: int = 10 ** 6) -> int:
    total = 0
    for i in range(0, len(buf), 4):
        y = (i // 4) // WIDTH
        if y0 <= y < y1 and pred(buf[i], buf[i + 1], buf[i + 2]):
            total += 1
    return total


def _reddish(r: int, g: int, b: int) -> bool:
    return r > g + 50 and r > b + 50


def _bluish(r: int, g: int, b: int) -> bool:
    return b > r + 50 and b > g + 50


# ---------------------------------------------------------------------------

def test_text_inherits_fg() -> None:
    def draw(ctx: ui.UI) -> None:
        with ctx.column(fg=RED):
            ctx.text("inherited colour")

    assert _count(_render(draw), _reddish) > 200


def test_heading_inherits_fg() -> None:
    def draw(ctx: ui.UI) -> None:
        with ctx.column(fg=RED):
            ctx.heading("red title")

    assert _count(_render(draw), _reddish) > 200


def test_heading_without_fg_stays_theme_coloured() -> None:
    def draw(ctx: ui.UI) -> None:
        ctx.heading("theme title")

    assert _count(_render(draw), _reddish) == 0


def test_explicit_colour_beats_inherited_fg() -> None:
    def draw(ctx: ui.UI) -> None:
        with ctx.column(fg=RED):
            ctx.text("explicit blue", color=BLUE)

    buf = _render(draw)
    assert _count(buf, _bluish) > 200
    assert _count(buf, _reddish) == 0


def test_fg_does_not_leak_out_of_the_scope() -> None:
    def draw(ctx: ui.UI) -> None:
        with ctx.column(fg=RED):
            ctx.text("inside")
        ctx.text("outside")

    buf = _render(draw)
    assert _count(buf, _reddish, y0=0, y1=HEIGHT // 3) > 100   # inside
    assert _count(buf, _reddish, y0=HEIGHT // 2, y1=HEIGHT) == 0  # outside


def test_stack_unwinds_after_the_block() -> None:
    def draw(ctx: ui.UI) -> None:
        with ctx.column(fg=RED):
            ctx.text("inside")
        assert ctx.current_fg is None
        assert ctx._fg_stack == []

    _render(draw)


def test_nested_scopes_restore_the_outer_colour() -> None:
    def draw(ctx: ui.UI) -> None:
        with ctx.column(fg=RED):
            ctx.text("outer red")
            with ctx.column(fg=BLUE):
                ctx.text("inner blue")
            assert ctx._fg_stack == [RED]
            ctx.text("red again")

    buf = _render(draw)
    assert _count(buf, _reddish) > 200
    assert _count(buf, _bluish) > 100


def test_fg_is_popped_when_the_block_raises() -> None:
    def draw(ctx: ui.UI) -> None:
        try:
            with ctx.column(fg=RED):
                ctx.text("boom")
                raise RuntimeError("inner failure")
        except RuntimeError:
            pass
        assert ctx.current_fg is None
        assert ctx._fg_stack == []

    _render(draw)


def test_fg_none_is_a_no_op() -> None:
    def draw(ctx: ui.UI) -> None:
        with ctx.column(fg=None) as scope:
            assert isinstance(scope, int), "fg=None should return the plain BoxScope id"
            assert ctx.current_fg is None
        ctx.text("still theme coloured")

    _render(draw)


def test_card_and_grid_accept_fg() -> None:
    def draw(ctx: ui.UI) -> None:
        with ctx.card(fg=RED):
            ctx.text("card text")
        with ctx.grid(2, fg=BLUE):
            ctx.text("grid text")

    buf = _render(draw)
    assert _count(buf, _reddish) > 100
    assert _count(buf, _bluish) > 100


def test_wrapped_scope_forwards_the_inner_scope() -> None:
    seen = {}

    def draw(ctx: ui.UI) -> None:
        with ctx.card(fg=RED, hoverable=True) as card:
            seen["card"] = card
            ctx.text("card")
        with ctx.column(fg=RED) as box_id:
            seen["box"] = box_id

    _render(draw)
    assert hasattr(seen["card"], "clicked"), "wrapper must forward CardScope attributes"
    assert isinstance(bool(seen["card"]), bool)
    assert isinstance(seen["box"], int), "wrapper must return the box id from __enter__"


def test_shorthands_keep_their_own_colour() -> None:
    """`label`/`muted`/`code` are theme micro-styles: `fg=` must not repaint them."""
    def draw(ctx: ui.UI) -> None:
        with ctx.column(fg=RED):
            ctx.label("plain label")

    assert _count(_render(draw), _reddish) == 0


def test_markdown_and_expandable_text_inherit_fg() -> None:
    def draw(ctx: ui.UI) -> None:
        with ctx.column(fg=RED):
            ctx.markdown("md", "**bold** and *em* text")
            ctx.expandable_text("ex", "clamped body copy " * 20)

    assert _count(_render(draw), _reddish) > 500


# ---------------------------------------------------------------------------
# the colour arguments are discoverable: they appear in the signature
# ---------------------------------------------------------------------------

def test_container_colour_arguments_are_in_the_signature() -> None:
    import inspect

    for name in ("box", "row", "column", "grid", "stack"):
        params = inspect.signature(getattr(ui.UI, name)).parameters
        for kw in ("fg", "bg", "border_color"):
            assert kw in params, f"{name}() does not expose {kw}="
    card = inspect.signature(ui.UI.card).parameters
    for kw in ("fg", "bg", "border_color"):
        assert kw in card, f"card() does not expose {kw}="


def test_container_bg_and_border_still_paint() -> None:
    def draw(ctx: ui.UI) -> None:
        with ctx.column(bg="#123456", border_color="#ff00ff", border=2, pad=12):
            ctx.text("on a painted container")

    buf = _render(draw)
    assert _count(buf, lambda r, g, b: abs(r - 18) < 6 and abs(g - 52) < 6 and abs(b - 86) < 6) > 1000
    assert _count(buf, lambda r, g, b: r > 200 and b > 200 and g < 80) > 20
