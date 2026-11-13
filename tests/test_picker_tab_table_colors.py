"""Per-call colours reach the framebuffer for select, tabs, tab_bar and table."""

from __future__ import annotations

from typing import Callable

import nexa as ui

Draw = Callable[[ui.UI], None]


def _render(draw: Draw, width: int = 360, height: int = 220, frames: int = 1) -> bytearray:
    """Render ``frames`` frames and return the last one.

    The moving tab indicator is placed from the previous frame's rects, so the
    tests that check it need more than one frame.
    """
    with ui.SoftwareRenderer(threads=1) as sw:
        with ui.UI(width=width, height=height, theme=ui.ThemeMode.DARK, renderer=sw) as ctx:
            buf = bytearray(width * height * 4)
            for _ in range(frames):
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


# --------------------------------------------------------------------------
# select
# --------------------------------------------------------------------------


def test_select_background_and_value_colour() -> None:
    buf = _render(
        lambda ctx: ctx.select("s", ["Alpha", "Beta"], 0, bg="#2a1d05", color="#ffd28a", border_color="#7a5210")
    )
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (42, 29, 5), 12)), "field background"
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (255, 210, 138), 30)), "selected value"
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (122, 82, 16), 40)), "field border"


def test_select_placeholder_colour() -> None:
    buf = _render(lambda ctx: ctx.select("s", ["Alpha"], -1, placeholder="pick one", placeholder_color="#8b5cf6"))
    assert _has_colour(buf, lambda r, g, b: r > 110 and b > 200 and g < 130)


def test_select_alias_colour_equals_text_color() -> None:
    via_alias = _render(lambda ctx: ctx.select("s", ["Alpha"], 0, color="#00ff88", bg="#101010"))
    via_explicit = _render(lambda ctx: ctx.select("s", ["Alpha"], 0, text_color="#00ff88", bg="#101010"))
    assert via_alias == via_explicit


def test_select_focus_colour_changes_pixels() -> None:
    plain = _render(lambda ctx: ctx.select("s", ["Alpha", "Beta"], 0))
    coloured = _render(lambda ctx: ctx.select("s", ["Alpha", "Beta"], 0, border_color="#00c2ff", focus_color="#00c2ff"))
    assert plain != coloured


# --------------------------------------------------------------------------
# tabs / tab_bar
# --------------------------------------------------------------------------


def test_tabs_indicator_colour() -> None:
    buf = _render(
        lambda ctx: ctx.tabs("t", ["One", "Two", "Three"], 0, indicator_color="#ff2d95"), frames=3
    )
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (255, 45, 149), 30)), "underline indicator"


def test_tabs_label_colours() -> None:
    buf = _render(lambda ctx: ctx.tabs("t", ["One", "Two"], 0, color="#6b7a8f", active_color="#ffd166"))
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (255, 209, 102), 40)), "active label"
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (107, 122, 143), 24)), "resting label"


def test_tabs_pill_and_segmented_backgrounds() -> None:
    pill = _render(
        lambda ctx: ctx.tabs(
            "t", ["One", "Two"], 0, variant=ui.TabsVariant.PILL, bg="#1b1230", indicator_color="#7c5cff"
        ),
        frames=3,
    )
    assert _has_colour(pill, lambda r, g, b: _near(r, g, b, (27, 18, 48), 12)), "pill track"
    assert _has_colour(pill, lambda r, g, b: _near(r, g, b, (124, 92, 255), 40)), "pill highlight"


def test_tab_bar_colours() -> None:
    items = [ui.TabBarItem(icon="file", label="Docs"), ui.TabBarItem(icon="search", label="Find")]
    buf = _render(
        lambda ctx: ctx.tab_bar(
            "tb", items, 0, bg="#12060f", border_color="#ff2d95", indicator_color="#ff2d95", active_color="#ffd166"
        )
    )
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (18, 6, 15), 10)), "bar background"
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (255, 209, 102), 40)), "active label"


# --------------------------------------------------------------------------
# table
# --------------------------------------------------------------------------


def _table(ctx: ui.UI, **colours) -> None:
    with ctx.table(
        "tbl",
        [ui.TableColumn("Name", width=ui.FILL), ui.TableColumn("Status", width=90)],
        **colours,
    ) as t:
        if not t:
            return
        t.row()
        t.cell_text("Alpha")
        t.cell_text("ok")
        t.row()
        t.cell_text("Beta")
        t.cell_text("warn")


def test_table_background_and_border() -> None:
    buf = _render(lambda ctx: _table(ctx, bg="#0d1f2b", border_color="#00c2ff"))
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (13, 31, 43), 10)), "table surface"
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (0, 194, 255), 40)), "table border"


def test_table_header_colours() -> None:
    buf = _render(lambda ctx: _table(ctx, header_bg="#2a1d05", header_color="#ffd28a", text_color="#ffffff"))
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (42, 29, 5), 12)), "header background"
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (255, 210, 138), 30)), "header label"


def test_table_text_colour() -> None:
    buf = _render(lambda ctx: _table(ctx, text_color="#00ff88"))
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (0, 255, 136), 40)), "body cell text"


def test_table_selected_row_colour() -> None:
    def draw(ctx: ui.UI) -> None:
        with ctx.table("tbl", [ui.TableColumn("Name", width=ui.FILL)], selectable=True, selected_bg="#3b1d5e") as t:
            if not t:
                return
            t.row(selected=True)
            t.cell_text("Alpha")

    assert _has_colour(_render(draw), lambda r, g, b: _near(r, g, b, (59, 29, 94), 14))


def test_table_colours_change_pixels() -> None:
    assert _render(lambda ctx: _table(ctx)) != _render(lambda ctx: _table(ctx, header_bg="#2a1d05", bg="#0d1f2b"))


# --------------------------------------------------------------------------
# discoverability
# --------------------------------------------------------------------------


def test_colour_arguments_are_visible_in_the_public_signatures() -> None:
    import inspect

    expected = {
        "select": ("bg", "color", "text_color", "placeholder_color", "border_color", "focus_color"),
        "tabs": ("bg", "color", "active_color", "indicator_color"),
        "tab_bar": ("bg", "border_color", "color", "active_color", "indicator_color"),
        "table": ("bg", "border_color", "header_bg", "header_color", "text_color", "selected_bg"),
    }
    for name, params in expected.items():
        sig = inspect.signature(getattr(ui.UI, name))
        for param in params:
            assert param in sig.parameters, f"{name}() is missing {param}="
