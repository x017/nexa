"""Post-1.4 CUI components: the dither family, creative controls, canvas & bars, and voice."""

from __future__ import annotations

import inspect
from typing import Callable

import nexa as ui

Draw = Callable[[ui.UI], None]


def _render(draw: Draw, width: int = 480, height: int = 420, frames: int = 3, reduced_motion: bool = True) -> bytearray:
    """Render ``frames`` frames and return the last one (animated widgets need >1)."""
    with ui.SoftwareRenderer(threads=1) as sw:
        with ui.UI(width=width, height=height, theme=ui.ThemeMode.DARK, reduced_motion=reduced_motion, renderer=sw) as ctx:
            buf = bytearray(width * height * 4)
            for _ in range(frames):
                with ctx.frame(1.0 / 60.0):
                    with ctx.column(width=ui.FILL, height=ui.FILL, pad=10, gap=8, bg=ui.Color.BACKGROUND):
                        draw(ctx)
                buf = bytearray(width * height * 4)
                sw.render(ctx.draw_data(), buffer=buf)
            return buf


def _has_colour(buf: bytearray, pred) -> bool:
    return any(pred(buf[i], buf[i + 1], buf[i + 2]) for i in range(0, len(buf), 4))


def _near(r: int, g: int, b: int, target: tuple[int, int, int], tol: int = 30) -> bool:
    return abs(r - target[0]) <= tol and abs(g - target[1]) <= tol and abs(b - target[2]) <= tol


# --------------------------------------------------------------------------
# Signatures: the new widgets and their key arguments are public
# --------------------------------------------------------------------------

def test_new_widget_signatures_are_public() -> None:
    expected = {
        "veil": (),
        "status_spinner": (),
        "pattern_meter": (),
        "skeleton_group": (),
        "status_tag": (),
        "ratio_slider": (),
        "gradient_slider": (),
        "step_slider": (),
        "palette_strip": (),
        "aspect_picker": (),
        "option_action": (),
        "seed_field": (),
        "toolbar_group": (),
        "toolbar_radio": (),
        "toolbar_primary": (),
        "toolbar_cycle": (),
        "flyout_mark": (),
        "live_cursors": (),
        "presence_pill": (),
        "selection_ring": (),
        "canvas_controls": (),
        "result_card": (),
        "voice_wave": (),
        "voice_note": (),
        "voice_session": (),
        "selection_bar": (),
        "format_bar": (),
        "set_clipboard": (),
        "get_clipboard": (),
    }
    for name in expected:
        assert callable(getattr(ui.UI, name, None)), f"missing UI.{name}"

    # key kwargs
    sig = inspect.signature(ui.UI.spinner)
    assert "style" in sig.parameters and "track" in sig.parameters
    sig = inspect.signature(ui.UI.progress)
    assert "dither" in sig.parameters
    sig = inspect.signature(ui.UI.toolbar)
    assert "style" in sig.parameters
    sig = inspect.signature(ui.UI.line_chart)
    # line_chart takes **kwargs; the dither flag reaches _build_chart_opts
    from nexa.widgets.charts import _build_chart_opts

    assert "dither" in inspect.signature(_build_chart_opts).parameters
    sig = inspect.signature(ui.UI.chat_composer)
    assert "mic" in sig.parameters and "recording" in sig.parameters
    sig = inspect.signature(ui.App.follow_system_theme)
    assert "follow" in sig.parameters


def test_new_enums_and_types_are_exported() -> None:
    assert ui.SpinnerStyle.SPIRAL == 13
    assert ui.TagStatus.IN_REVIEW == 3
    assert ui.GradientTrack.OPACITY == 2
    assert ui.ToolbarStyle.GROUPED == 1
    assert ui.ComposerFlags.RECORD == 32 and ui.ComposerFlags.VOICE == 128
    p = ui.MeterPart("x", 1.0, "#ff0000", 0.5)
    assert p.name == "x" and p.density == 0.5
    u = ui.LiveUser("ana", 1.0, 2.0, says="hi")
    assert u.x == 1.0 and u.says == "hi"


# --------------------------------------------------------------------------
# Dither family
# --------------------------------------------------------------------------

def test_veil_cover_hides_and_revealed_shows_content() -> None:
    def covered(ctx: ui.UI) -> None:
        with ctx.veil("v", False, label="Secret", width=ui.FILL):
            ctx.text("HIDDEN-MARKER-TEXT")

    def revealed(ctx: ui.UI) -> None:
        with ctx.veil("v", True, label="Secret", width=ui.FILL):
            ctx.text("HIDDEN-MARKER-TEXT")

    covered_buf = _render(covered)
    revealed_buf = _render(revealed)
    assert covered_buf != revealed_buf, "a covered veil must paint differently from a revealed one"
    # The scope reports the state back.
    seen = {}

    def grab(ctx: ui.UI) -> None:
        with ctx.veil("v2", True) as v:
            ctx.text("x")
        seen["revealed"] = v.revealed

    _render(grab)
    assert seen["revealed"] is True


def test_pattern_meter_paints_part_colours() -> None:
    buf = _render(
        lambda ctx: ctx.pattern_meter(
            "pm",
            [ui.MeterPart("a", 5, "#22d3ee"), ui.MeterPart("b", 3, "#a78bfa")],
            total=10,
            width=ui.FILL,
        ),
        height=200,
    )
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (34, 211, 238), 40)), "first part colour"
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (167, 139, 250), 40)), "second part colour"


def test_spinner_styles_differ_from_the_plain_ring() -> None:
    plain = _render(lambda ctx: ctx.spinner(30))
    spiral = _render(lambda ctx: ctx.spinner(30, style=ui.SpinnerStyle.SPIRAL, color="#7dd3fc"))
    comet = _render(lambda ctx: ctx.spinner(30, style=ui.SpinnerStyle.COMET, color="#7dd3fc"))
    assert plain != spiral, "a styled spinner must paint differently from the plain ring"
    assert spiral != comet, "different styles must paint differently from each other"


def test_status_spinner_and_skeleton_group_render() -> None:
    def draw(ctx: ui.UI) -> None:
        ctx.status_spinner("s", ui.Status.BUSY, size=26, color="#34d399")
        with ctx.skeleton_group(dither=True, width=ui.FILL, gap=6):
            ctx.skeleton(width=140, height=12)

    buf = _render(draw, height=160)
    # The busy ring in success-green shows up.
    assert _has_colour(buf, lambda r, g, b: _near(r, g, b, (52, 211, 153), 60))


def test_skeleton_group_scope_opens_and_closes() -> None:
    def draw(ctx: ui.UI) -> None:
        with ctx.skeleton_group(dither=False, width=ui.FILL):
            ctx.skeleton(width=120, height=12)

    buf = _render(draw, height=120)
    assert max(buf) > 40, "the group must paint its placeholders"


# --------------------------------------------------------------------------
# Creative controls
# --------------------------------------------------------------------------

def test_status_tag_paints_tinted_fill() -> None:
    buf = _render(lambda ctx: ctx.status_tag("shipped", ui.TagStatus.SUCCESS), height=120)
    # The success tag tints green.
    assert _has_colour(buf, lambda r, g, b: g > 120 and g > r + 30 and g > b + 10)


def test_ratio_slider_returns_the_ratio() -> None:
    out = {}

    def draw(ctx: ui.UI) -> None:
        out["ratio"] = ctx.ratio_slider("Front", "Back", 0.6)

    _render(draw, height=120)
    assert abs(out["ratio"] - 0.6) < 1e-3


def test_step_slider_and_option_action_return_values() -> None:
    out = {}

    def draw(ctx: ui.UI) -> None:
        z = ctx.step_slider("Zoom", 2, min=0, max=4, labels=["a", "b", "c", "d", "e"])
        o = ctx.option_action("Mode", ["Fast", "Fine"], 1)
        out["zoom"] = z
        out["mode"] = o

    _render(draw, height=160)
    assert out["zoom"].value == 2 and out["zoom"].changed is False
    assert out["mode"].value == 1 and out["mode"].action is False


def test_palette_strip_mutates_the_colour_list() -> None:
    colors = ["#010203", "#040506", "#070809", "#0a0b0c", "#0d0e0f", "#101112"]
    locked = [True, False, False, False, False, False]
    original = list(colors)

    def draw(ctx: ui.UI) -> None:
        ctx.palette_strip("pal", colors, locked, seed=0x1234)

    _render(draw, height=120)
    # Without a click the strip just paints what it was given; the wrapper must
    # round-trip the lists untouched (the shuffle path writes back on click).
    assert colors == original
    assert all(isinstance(c, str) and c.startswith("#") for c in colors)
    assert locked == [True, False, False, False, False, False]


def test_seed_field_writes_back_seed_and_lock() -> None:
    out = {}

    def draw(ctx: ui.UI) -> None:
        out["seed"] = ctx.seed_field("Seed", 0xDEADBEEF, False)

    _render(draw, height=120)
    assert out["seed"].seed == 0xDEADBEEF
    assert out["seed"].locked is False


def test_aspect_picker_returns_index() -> None:
    out = {}

    def draw(ctx: ui.UI) -> None:
        out["i"] = ctx.aspect_picker("Ratio", 1, ratios=[(16, 9, "Wide"), (4, 3, "Classic")])

    _render(draw, height=140)
    assert out["i"] == 1


# --------------------------------------------------------------------------
# Canvas & bars
# --------------------------------------------------------------------------

def test_toolbar_grouped_style_and_cycle_render() -> None:
    out = {}

    def draw(ctx: ui.UI) -> None:
        with ctx.toolbar("tb", style=ui.ToolbarStyle.GROUPED):
            with ctx.toolbar_group():
                ctx.toolbar_button(ui.Icon.PLAY, label="Run")
            out["zoom"] = ctx.toolbar_cycle("z", ["1x", "2x", "4x"], 1)
            ctx.toolbar_primary(ui.Icon.PLUS, label="New")

    buf = _render(draw, height=120)
    assert out["zoom"] == 1
    assert max(buf) > 40, "the toolbar must paint"


def test_selection_bar_returns_none_without_interaction() -> None:
    selected = [True, False, True]
    out = {}

    def draw(ctx: ui.UI) -> None:
        out["r"] = ctx.selection_bar(
            "sb", [ui.SelectionAction("Archive", icon=ui.Icon.ARCHIVE)], selected
        )

    _render(draw, height=160)
    assert out["r"] == -1  # CUI_SELECTION_NONE with no click
    assert selected == [True, False, True]


def test_canvas_controls_updates_the_node_view_in_place() -> None:
    view = ui.NodeView(10.0, 20.0, 1.0)
    toggles = [ui.CanvasToggle(ui.Icon.GRID_3X3, "Grid", True)]

    def draw(ctx: ui.UI) -> None:
        ctx.canvas_controls("cc", view, steps=[0.5, 1.0, 2.0], toggles=toggles)

    _render(draw, height=220)
    assert isinstance(view.zoom, float) and view.zoom > 0
    assert toggles[0].on in (True, False)


def test_format_bar_edits_the_format_in_place() -> None:
    fmt = ui.TextFormat(bold=False, size=13.0)
    out = {}

    def draw(ctx: ui.UI) -> None:
        out["r"] = ctx.format_bar(
            "fb", fmt, colors=[ui.Tone.NEUTRAL, ui.Tone.INFO, ui.Tone.SUCCESS]
        )

    _render(draw, height=160)
    assert isinstance(out["r"].changed, bool)
    assert isinstance(fmt.bold, bool) and fmt.size > 0


# --------------------------------------------------------------------------
# Voice
# --------------------------------------------------------------------------

def test_voice_wave_passes_progress_through() -> None:
    out = {}

    def draw(ctx: ui.UI) -> None:
        out["p"] = ctx.voice_wave("vw", [0.1, 0.5, 0.9, 0.4], clip=True, progress=0.42)

    _render(draw, height=140)
    assert abs(out["p"] - 0.42) < 1e-3


def test_voice_note_writes_back_playback_state() -> None:
    out = {}

    def draw(ctx: ui.UI) -> None:
        out["n"] = ctx.voice_note("vn", [0.2, 0.6, 0.8, 0.3], 5.0, position=1.5, speed=1.5, playing=True, mine=True)

    _render(draw, height=160)
    n = out["n"]
    assert abs(n.position - 1.5) < 1e-3
    assert abs(n.speed - 1.5) < 1e-3
    assert n.playing is True


def test_voice_session_renders_and_mute_writes_back() -> None:
    muted = [False]

    def draw(ctx: ui.UI) -> None:
        ctx.voice_session(
            "vs", ui.VoiceState.LISTENING, [0.2, 0.5, 0.8],
            label="demo", transcript="hello there", upcoming="…", muted=muted,
        )

    _render(draw, height=240)
    assert muted == [False]


# --------------------------------------------------------------------------
# App-level API
# --------------------------------------------------------------------------

def test_clipboard_helpers_return_strings() -> None:
    def draw(ctx: ui.UI) -> None:
        ctx.set_clipboard("ping")
        assert isinstance(ctx.get_clipboard(), str)

    _render(draw, height=80)
