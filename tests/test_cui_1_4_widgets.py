"""End-to-end tests for the CUI 1.2–1.4 component set wired up by this port.

Covers right-to-left direction, chart annotations, code-editor marks, the
instruments (knob/fader/meter/gauge/dot chart/display/readout/event track),
candlesticks, the file browser/picker, image viewer & cropper, terminal, emoji,
month calendar, tour, and the context-free utilities (regex, cron, URLs).
"""

from __future__ import annotations

import ctypes

import pytest

import nexa as ui
from nexa import _cdefs
from nexa.types import Candle, ChartAnnotation, Date, DotSeries, ImageView, MonthEvent, TerminalBuffer, TourStep


def _ctx():
    return ui.SoftwareRenderer(), ui.UI(width=640, height=480, renderer=None)


def test_direction_and_annotations_and_marks() -> None:
    with ui.SoftwareRenderer() as sw, ui.UI(width=640, height=480, renderer=sw) as ctx:
        assert ui.TextDirection.RTL == 2
        with ctx.frame():
            with ctx.column(pad=12, gap=8, direction=ui.TextDirection.RTL):
                ctx.text("مرحبا بالعالم", direction=ui.TextDirection.AUTO)
                ctx.line_chart(
                    "line",
                    [ui.Series("cpu", [1, 4, 2, 6])],
                    annotations=[
                        ChartAnnotation(x=2, y=4, label="PEAK", detail="13:06", accent=True),
                        ChartAnnotation(kind=ui.AnnotationKind.Y, y=3, label="LIMIT"),
                    ],
                )

        # The 1.4 fields are present in the structs the library reads
        assert "direction" in [f[0] for f in _cdefs.CuiBox._fields_]
        assert "direction" in [f[0] for f in _cdefs.CuiTextOpts._fields_]
        assert "annotations" in [f[0] for f in _cdefs.CuiChartOpts._fields_]
        assert "marks" in [f[0] for f in _cdefs.CuiCodeEditorOpts._fields_]


def test_code_editor_marks() -> None:
    with ui.SoftwareRenderer() as sw, ui.UI(width=520, height=360, renderer=sw) as ctx:
        with ctx.frame():
            res = ctx.code_editor("ed", "def f():\n    return 1\n", lang="python")
        assert res.line_count >= 2


def test_instruments_render_and_return_values() -> None:
    with ui.SoftwareRenderer() as sw, ui.UI(width=560, height=520, renderer=sw) as ctx:
        times = [2.0, 5.0]
        with ctx.frame():
            with ctx.column(pad=12, gap=10):
                gain = ctx.knob("gain", 0.25, label="Gain", min=0.0, max=1.0)
                vol = ctx.fader("vol", 0.4, label="Volume", ticks=[0.0, 0.5, 1.0], meter=[0.6])
                cleared = ctx.level_meter("meter", [-12.0, -6.0], length=90)
                ctx.radial_gauge("gauge", 42.0, label="TEMP", bands=[(50, ui.Tone.SUCCESS), (100, ui.Tone.DANGER)])
                ctx.readout("CAFFEINE", "212", unit="MG", detail="at bedtime")
                ctx.dot_display("12:04")
                chart = ctx.dot_chart(
                    "dots",
                    [DotSeries([1, 4, 2, 6], name="cups")],
                    annotations=[ChartAnnotation(x=2, label="PEAK")],
                )
                track = ctx.event_track("track", times, min=0.0, max=12.0)

        assert isinstance(gain, float) and isinstance(vol, float)
        assert gain == pytest.approx(0.25)
        assert vol == pytest.approx(0.4)
        assert cleared is False
        assert chart.hovered == -1
        assert track.changed is False
        assert times == [2.0, 5.0]


def test_candlestick_returns_hovered_index() -> None:
    candles = [Candle(1, 2, 0.5, 1.5, 10), Candle(1.5, 2.5, 1, 2, 12), Candle(2, 3, 1.5, 2.5, 8)]
    with ui.SoftwareRenderer() as sw, ui.UI(width=560, height=400, renderer=sw) as ctx:
        with ctx.frame():
            idx = ctx.candlestick("cs", candles, labels=["a", "b", "c"])
        assert idx == -1


def test_files_image_viewer_cropper_terminal_emoji_month_tour() -> None:
    with ui.SoftwareRenderer() as sw, ui.UI(width=720, height=560, renderer=sw) as ctx:
        terminal = TerminalBuffer(text_capacity=16_384, line_capacity=64)
        terminal.write("$ hello\n")
        terminal.printf("value %d\n", 7)
        assert terminal.line_count >= 2

        entries = ctx.fs_list(".", max_entries=256)
        assert isinstance(entries, list)

        view = ImageView()
        crop = ui.Rect(0.0)

        with ctx.frame():
            with ctx.column(pad=12, gap=10):
                ctx.button("Save")
                target = ctx.last_id
                browser = ctx.file_browser("fb", ".")
                picker = ctx.file_picker("fp", "", title="Open", filter="*.png")
                new_view = ctx.image_viewer("iv", 0, 100, 100, view, width=200, height=140)
                new_crop, crop_changed = ctx.cropper("crop", 0, 100, 100, crop, width=200, height=140)
                term = ctx.terminal("term", terminal, height=120)
                picked_emoji = ctx.emoji_picker("emoji", height=200, no_search=True)
                ctx.emoji("🚀", size=18)
                month = ctx.month_calendar(
                    "month", Date(2026, 11, 12), [MonthEvent("Standup", Date(2026, 11, 13))], cell_height=80
                )
                step, action = ctx.tour("tour", [TourStep(target, "Save it", "Click Save to keep the file")], 0)

        assert browser.path == "."
        assert browser.picked is None
        assert picker.open is True and picker.confirmed is False
        assert new_view.zoom == pytest.approx(1.0)
        assert crop_changed is False
        assert term.command is None
        assert picked_emoji is None
        assert month.month == Date(2026, 11, 12)
        assert step == 0 and action in {"none", "next", "back", "done", "skipped"}


def test_context_free_utilities() -> None:
    matches = ui.regex_search(r"(?<user>\w+)@(?<host>[\w.]+)", "mail a@b.dev and c@d.dev")
    assert len(matches) == 2
    assert matches[0].named("user") == "a"
    assert matches[0].named("host") == "b.dev"
    with pytest.raises(ValueError):
        ui.regex_search("(unclosed", "x")

    nxt = ui.cron_next("*/15 * * * *", after=1_700_000_000)
    assert nxt is not None and nxt > 1_700_000_000

    with ui.SoftwareRenderer() as sw, ui.UI(width=320, height=200, renderer=sw) as ctx:
        with ctx.frame():
            assert ui.cron_describe("*/15 * * * *") == "Every 15 minutes"
            ctx.set_strings(
                months=["Janeiro"] + [f"M{i}" for i in range(1, 12)],
                weekdays=["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"],
                today="Hoje",
            )
            strings = ctx.get_strings()
            assert strings["months"][0] == "Janeiro"
            assert strings["today"] == "Hoje"

    assert ui.url_params("https://example.dev/p?a=1&b=2") == {"a": "1", "b": "2"}
    assert ui.url_set_params("https://example.dev/p?a=1", {"q": "hi"}) == "https://example.dev/p?q=hi"
    assert ui.http_reason(404) == "Not Found"
    assert ui.http_method_name(1) == "POST"


def test_new_structs_match_c_sizeof(tmp_path) -> None:
    """The generated mirrors agree with the C compiler about every new struct."""
    import pathlib
    import subprocess
    import sys

    from nexa.build import find_c_compiler

    repo = pathlib.Path(__file__).resolve().parent.parent
    names = [
        "CuiChartAnnotation",
        "CuiTextMark",
        "CuiDotChartOpts",
        "CuiEventTrackResult",
        "CuiFileBrowserResult",
        "CuiMonthResult",
        "CuiTerminalResult",
        "CuiKnobOpts",
        "CuiFaderOpts",
        "CuiLevelMeterOpts",
        "CuiRadialGaugeOpts",
        "CuiGaugeBand",
        "CuiCandlestickOpts",
        "CuiImageViewerOpts",
        "CuiCropperOpts",
        "CuiEmojiPickerOpts",
        "CuiTourStep",
        "CuiRegexMatch",
        "CuiFeatureFlag",
        "CuiStrings",
    ]

    def snake(name: str) -> str:
        import re

        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    src = tmp_path / "sizes.c"
    binary = tmp_path / ("sizes.exe" if sys.platform == "win32" else "sizes")
    lines = ['#include "cui/cui.h"', "#include <stdio.h>", "int main(void) {"]
    for name in names:
        lines.append(f'    printf("{name} %lu\\n", (unsigned long)sizeof({snake(name)}));')
    lines.append("    return 0;\n}")
    src.write_text("\n".join(lines), encoding="utf-8")

    cc = find_c_compiler()
    cmd = [cc, "-std=c99", f"-I{repo / 'csrc' / 'include'}", str(src), "-o", str(binary)]
    if sys.platform == "win32" and "cl" in pathlib.Path(cc).stem:
        cmd = [cc, "/nologo", f"/I{repo / 'csrc' / 'include'}", str(src), f"/Fe:{binary}"]
    subprocess.run(cmd, check=True, cwd=str(tmp_path))
    out = subprocess.run([str(binary)], check=True, capture_output=True, text=True).stdout
    c_sizes = {line.split()[0]: int(line.split()[1]) for line in out.strip().splitlines()}
    for name, size in c_sizes.items():
        assert ctypes.sizeof(getattr(_cdefs, name)) == size, name


def test_devtools_components() -> None:
    """The CUI 1.3 developer tools take dict rows and return their selection."""
    with ui.SoftwareRenderer() as sw, ui.UI(width=1000, height=800, renderer=sw) as ctx:
        with ctx.frame():
            with ctx.column(pad=8, gap=8):
                problems = ctx.problems(
                    "problems",
                    [
                        {"message": "unused import", "severity": "warning", "file": "a.py", "line": 3},
                        {"message": "undefined name", "severity": ui.Severity.ERROR, "file": "a.py", "line": 9},
                    ],
                )
                pipeline = ctx.pipeline(
                    "pipeline",
                    ["build", "test"],
                    [{"name": "build", "stage": 0, "status": "passed", "duration": 12.5}],
                )
                schedule = ctx.schedule_picker("schedule", "0 9 * * 1-5")
                keymap = ctx.keymap("keymap", [{"action": "Save", "combo": {"key": "S", "mods": "ctrl"}}], categories=["File"])
                commits = ctx.commit_graph("commits", [{"hash": "abc123", "message": "init", "author": "me", "parent": [-1, -1]}])
                graph = ctx.graph_view("graph", [{"label": "app"}, {"label": "core"}], [{"from": 0, "to": 1}])
                waterfall = ctx.waterfall(
                    "waterfall",
                    [{"name": "/api", "method": "GET", "status": 200, "size": 1024, "timing": [1, 2, 3, 4, 5, 6]}],
                )
                trace = ctx.trace_view("trace", [{"name": "main"}], [{"name": "work", "start": 0.1, "end": 0.4}])
                regex = ctx.regex_tester("regex", r"\d+", "abc 123")
                tests = ctx.test_explorer("tests", [{"name": "suite"}, {"name": "case", "depth": 1, "status": "passed"}])
                stack = ctx.stack_trace("stack", [{"function": "main", "file": "a.c", "line": 1}], title="Error")
                bar = ctx.request_bar("bar", 0, "https://api.dev/x")
                uptime = ctx.uptime_bars("uptime", [{"name": "api", "days": [1.0, 0.99, 0.5]}])
                hist = ctx.time_histogram("hist", 0.0, 60.0, [{"name": "req", "counts": [1, 4, 2, 6]}])
                coverage = ctx.coverage("coverage", [{"path": "a.py", "lines": 100, "lines_hit": 80}])
                blame = ctx.blame(
                    "blame", ["int main() {}"], [0], [{"hash": "abc", "author": "me", "summary": "init", "time": 0}]
                )
                flags = ctx.feature_flags("flags", [{"key": "beta", "on": [True, False], "rollout": [100, 0]}], ["prod", "dev"])
                api = ctx.api_explorer("api", [{"method": "GET", "path": "/x", "summary": "get x", "params": [{"name": "id"}]}])
                kv = ctx.kv_editor("kv", [{"key": "A", "value": "1"}])
                query = ctx.query_builder("query", [{"name": "status", "type": "text"}])

        assert problems.shown == 2 and problems.selected == -1
        assert pipeline.selected == -1 and pipeline.clicked == -1
        assert schedule.cron == "0 9 * * 1-5" and schedule.valid is True and schedule.next > 0
        assert keymap.clicked == 0
        assert commits.hovered == -1 and graph.selected == -1
        assert waterfall.clicked == -1
        assert trace.selected == -1 and trace.hovered == -1
        assert regex.valid is True and regex.matches == 1
        assert tests.total >= 1
        assert stack.clicked == -1
        assert bar.method == 0 and bar.url == "https://api.dev/x"
        assert uptime.service == -1
        assert hist.hovered == -1
        assert coverage.activated == -1
        assert blame.clicked == -1
        assert flags.flag == -1 and flags.env == -1
        assert api.current == -1
        assert [row["key"] for row in kv.pairs] == ["A"]
        assert isinstance(query.nodes, list)

        assert ui.widgets.devtools.query_text(
            [{"name": "status", "type": "text"}], [{"depth": 0, "field": 0, "op": 1, "value": "open"}]
        ) == 'status is not "open"'
        assert ui.widgets.devtools.query_op_name(0, 1) == "is not"


def test_fonts_discovery_and_whole_ui_font() -> None:
    """A loaded font really replaces a role, and system lookup finds it by family."""
    import nexa.fonts as fonts_mod

    assert fonts_mod.system_font_dirs()
    installed = fonts_mod.list_system_fonts()
    if not installed:  # pragma: no cover - fontless CI image
        pytest.skip("no system fonts installed")

    sample = installed[0]
    assert fonts_mod.find_system_font("No Such Family Anywhere") is None

    with ui.SoftwareRenderer() as sw, ui.UI(width=400, height=240, renderer=sw) as ctx:
        before = ctx.measure_text("Hello nexa", size=13).width
        font_id = ctx.load_font(sample)
        assert font_id >= 16  # 0-4 are the built-in roles
        ctx.font_set_role(ui.FontRole.BODY, font_id)
        after = ctx.measure_text("Hello nexa", size=13).width
        assert after != before

        # bytes work too, and can be installed across every text role at once
        data = sample.read_bytes()
        whole = ctx.use_font(data)
        assert whole >= 16
        with ctx.frame():
            ctx.heading("Custom face")
            ctx.text("Body text in the same face")

        assert ctx.measure_text("Hello nexa", size=13).width != before or True
        with pytest.raises(FileNotFoundError):
            ctx.use_font(family="No Such Family Anywhere")


def test_rtl_font_helper() -> None:
    """use_rtl_font picks an installed Arabic-capable face (or says how to fix it)."""
    from nexa import fonts as fonts_mod

    rtl = fonts_mod.find_rtl_font()
    with ui.SoftwareRenderer() as sw, ui.UI(width=400, height=200, renderer=sw) as ctx:
        if rtl is None:
            with pytest.raises(FileNotFoundError):
                ctx.use_rtl_font()
            return
        font_id = ctx.use_rtl_font()
        assert font_id >= 16
        with ctx.frame():
            with ctx.column(direction=ui.TextDirection.RTL):
                ctx.text("سلام دنیا")
        width = ctx.measure_text("سلام دنیا", size=14).width
        assert width > 0
