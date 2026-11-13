"""``fg=`` is a per-widget alias of ``color=``.

Contract checked here:

- every function in ``nexa.widgets`` that takes a ``color`` parameter also
  takes a keyword-only ``fg: ColorLike = None`` and resolves it into ``color``
  before the first real statement (AST scan). Containers in ``layout.py`` are
  the exception: their ``fg=`` is the inherited region colour and they never
  take ``color=``;
- ``fg=`` renders the same pixels as ``color=``, wins when both are passed,
  and ``fg=None`` changes nothing.
"""

from __future__ import annotations

import ast
import pathlib
from typing import Callable

import nexa as ui

ROOT = pathlib.Path(__file__).resolve().parents[1]
WIDGETS = ROOT / "src" / "nexa" / "widgets"

RED = "#ff2040"
WIDTH, HEIGHT = 420, 240

REBIND = ast.parse("if fg is not None:\n    color = fg\n").body[0]


def _render(draw: Callable[[ui.UI], None]) -> bytearray:
    with ui.SoftwareRenderer(threads=1) as sw:
        with ui.UI(width=WIDTH, height=HEIGHT, theme=ui.ThemeMode.DARK, renderer=sw) as ctx:
            with ctx.frame(1.0 / 60.0):
                with ctx.column(width=ui.FILL, height=ui.FILL, pad=8, gap=4,
                                bg=ui.Color.BACKGROUND):
                    draw(ctx)
            buf = bytearray(WIDTH * HEIGHT * 4)
            sw.render(ctx.draw_data(), buffer=buf)
            return buf


def test_every_color_parameter_has_an_fg_alias() -> None:
    checked = 0
    for path in sorted(WIDGETS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            pos = [a.arg for a in node.args.args]
            kw = [a.arg for a in node.args.kwonlyargs]
            if "color" in pos or "color" in kw:
                checked += 1
                assert "fg" in kw, (
                    f"{path.name}:{node.lineno} {node.name}() takes color= "
                    f"but has no keyword-only fg="
                )
                # the alias must be resolved before anything reads `color`
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                        and isinstance(first.value.value, str):
                    first = node.body[1]  # skip the docstring
                assert ast.dump(first) == ast.dump(REBIND), (
                    f"{path.name}:{node.lineno} {node.name}() must start with "
                    f"'if fg is not None: color = fg'"
                )
            if "fg" in kw and path.name != "layout.py":
                assert "color" in pos or "color" in kw, (
                    f"{path.name}:{node.lineno} {node.name}() takes fg= without color= "
                    f"(only layout containers may do that)"
                )
    assert checked >= 40, f"expected the colour sweep to cover 40+ functions, saw {checked}"


_CASES: list[tuple[str, Callable[[ui.UI, str], None]]] = [
    ("heading", lambda c, w: c.heading("Hello", level=2, **{w: RED})),
    ("text", lambda c, w: c.text("body copy", size=14, **{w: RED})),
    ("button", lambda c, w: c.button("Go", **{w: RED})),
    ("input", lambda c, w: c.input("in", "val", **{w: RED})),
    ("select", lambda c, w: c.select("s", ["A", "B"], 0, **{w: RED})),
    ("spinner", lambda c, w: c.spinner(20, **{w: RED})),
    ("tabs", lambda c, w: c.tabs("t", ["One", "Two"], 0, **{w: RED})),
    ("markdown", lambda c, w: c.markdown("md", "# Title\n\ntext", **{w: RED})),
    ("knob", lambda c, w: c.knob("k", 0.5, **{w: RED})),
    ("icon", lambda c, w: c.icon("*", 18, **{w: RED})),
    ("loader", lambda c, w: c.loader(**{w: RED})),
    ("veil", lambda c, w: c.veil("v", True, **{w: RED})),
]


def test_fg_renders_the_same_pixels_as_color() -> None:
    for name, draw in _CASES:
        via_color = _render(lambda c, draw=draw: draw(c, "color"))
        via_fg = _render(lambda c, draw=draw: draw(c, "fg"))
        assert via_color == via_fg, f"{name}: fg= does not render like color="


def test_fg_wins_over_color_and_none_is_a_noop() -> None:
    default = _render(lambda c: c.heading("Hello", level=2))
    none = _render(lambda c: c.heading("Hello", level=2, fg=None))
    assert default == none, "fg=None must be a no-op"

    fg_only = _render(lambda c: c.heading("Hello", level=2, fg=RED))
    both = _render(lambda c: c.heading("Hello", level=2, color="#00ff00", fg=RED))
    assert both == fg_only, "fg= must win over color= when both are passed"
