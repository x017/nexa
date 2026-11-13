"""DevTools Studio — every CUI 1.3 developer-tool component on four tabs.

The dev tools are data-driven: they take rows as plain dicts named after the C
struct fields and hand back a named tuple with the selection.  Nothing here is
a special widget class, so the panels compose like ordinary layouts.

    python examples/devtools.py

Tabs: **Build** (pipeline, problems, tests, coverage), **Runtime** (trace,
waterfall, request bar, API explorer, dependency graph), **Data** (key/value
editor, query builder, feature flags, regex tester, schedule picker, histogram)
and **Repo** (commit graph, blame, keymap, stack trace, uptime).

Runs headless with ``NEXA_HEADLESS=1 CUI_SCREENSHOT=out.png``.
"""

from __future__ import annotations

import os
import time

import nexa as ui

TABS = ["Build", "Runtime", "Data", "Repo"]

DIAGNOSTICS = [
    {"message": "unused import 'os'", "severity": "warning", "file": "src/nexa/app.py", "line": 12, "source": "ruff", "code": "F401"},
    {"message": "undefined name 'ctx'", "severity": "error", "file": "src/nexa/context.py", "line": 208, "source": "mypy", "code": "name-defined"},
    {"message": "line too long (121 > 100)", "severity": "warning", "file": "examples/devtools.py", "line": 64, "source": "ruff", "code": "E501"},
    {"message": "consider using a dict comprehension", "severity": "info", "file": "src/nexa/build.py", "line": 91, "source": "pylint", "code": "R1717"},
    {"message": "TODO: document the ABI generators", "severity": "hint", "file": "tools/gen_abi.py", "line": 7, "source": "todo", "code": "TODO"},
]

STAGES = ["checkout", "build", "test", "pack", "deploy"]
JOBS = [
    {"name": "lint", "stage": 0, "status": "passed", "duration": 8.4},
    {"name": "abi-audit", "stage": 0, "status": "passed", "duration": 12.1},
    {"name": "linux-x64", "stage": 1, "status": "passed", "duration": 96.0},
    {"name": "win-x64", "stage": 1, "status": "passed", "duration": 104.3},
    {"name": "macos-arm64", "stage": 1, "status": "failed", "duration": 61.7, "allow_failure": False},
    {"name": "pytest-3.11", "stage": 2, "status": "running", "duration": 34.2},
    {"name": "sdist", "stage": 3, "status": "pending", "duration": 0.0},
    {"name": "pypi", "stage": 4, "status": "pending", "duration": 0.0},
]

TESTS = [
    {"name": "tests/", "status": "passed"},
    {"name": "test_abi_parity", "depth": 1, "status": "passed", "duration": 21.4},
    {"name": "test_minimal_build_size", "depth": 1, "status": "passed", "duration": 18.9},
    {"name": "test_cui_1_4_widgets", "depth": 1, "status": "failed", "duration": 0.6,
     "message": "AssertionError: level_meter expected -6 dB, got linear 0.5"},
    {"name": "test_packaging", "depth": 1, "status": "passed", "duration": 9.1},
]

COVERAGE = [
    {"path": "src/nexa/context.py", "lines": 980, "lines_hit": 902, "branches": 210, "branches_hit": 176, "functions": 168, "functions_hit": 161},
    {"path": "src/nexa/widgets/devtools.py", "lines": 540, "lines_hit": 431, "branches": 96, "branches_hit": 61, "functions": 44, "functions_hit": 40},
    {"path": "src/nexa/widgets/instruments.py", "lines": 402, "lines_hit": 388, "branches": 58, "branches_hit": 52, "functions": 18, "functions_hit": 18},
    {"path": "src/nexa/fonts.py", "lines": 198, "lines_hit": 96, "branches": 44, "branches_hit": 17, "functions": 9, "functions_hit": 6},
    {"path": "tools/gen_abi.py", "lines": 307, "lines_hit": 214, "branches": 72, "branches_hit": 38, "functions": 19, "functions_hit": 13},
]

TRACKS = [{"name": "ui"}, {"name": "render"}, {"name": "io"}]
SPANS = [
    {"name": "frame", "start": 0.0, "end": 16.4, "track": 0},
    {"name": "layout", "start": 0.4, "end": 4.1, "track": 0},
    {"name": "paint", "start": 4.1, "end": 9.8, "track": 1},
    {"name": "shadow blurs", "start": 5.2, "end": 8.9, "track": 1},
    {"name": "text atlas", "start": 8.9, "end": 9.6, "track": 1},
    {"name": "socket read", "start": 9.8, "end": 14.2, "track": 2},
    {"name": "json parse", "start": 14.2, "end": 16.0, "track": 2},
]

REQUESTS = [
    {"name": "/api/commits", "method": "GET", "status": 200, "type": "json", "size": 184_320, "start": 0.0, "timing": [18, 42, 61, 120, 88, 12]},
    {"name": "/api/pipeline", "method": "GET", "status": 200, "type": "json", "size": 12_048, "start": 26.0, "timing": [9, 31, 22, 64, 40, 6]},
    {"name": "/api/trace", "method": "POST", "status": 500, "type": "json", "size": 2_112, "start": 58.0, "timing": [12, 88, 140, 210, 61, 4]},
    {"name": "report.css", "method": "GET", "status": 200, "type": "css", "size": 48_900, "start": 74.0, "timing": [4, 12, 9, 26, 18, 2]},
    {"name": "fonts/Inter.woff2", "method": "GET", "status": 200, "type": "font", "size": 121_400, "start": 96.0, "timing": [6, 22, 14, 44, 31, 3]},
]

ENDPOINTS = [
    {"method": "GET", "path": "/v1/builds", "summary": "List builds for a project", "tag": "builds",
     "params": [{"name": "limit", "in": "query", "type": "int", "description": "max rows"}],
     "deprecated": False},
    {"method": "POST", "path": "/v1/builds", "summary": "Queue a new build", "tag": "builds", "deprecated": False,
     "params": [{"name": "ref", "in": "body", "type": "string", "required": True}]},
    {"method": "GET", "path": "/v1/traces/{id}", "summary": "Fetch one trace", "tag": "traces", "deprecated": False},
    {"method": "DELETE", "path": "/v1/cache", "summary": "Drop the artifact cache", "tag": "admin", "deprecated": True},
]

NODES = [
    {"label": "context.py"}, {"label": "widgets/"}, {"label": "_cdefs"}, {"label": "libnexa_cui"},
    {"label": "types.py"}, {"label": "build.py"},
]
EDGES = [{"from": 0, "to": 1}, {"from": 1, "to": 2}, {"from": 2, "to": 3}, {"from": 0, "to": 4}, {"from": 4, "to": 2}, {"from": 5, "to": 3}]

FLAGS = [
    {"key": "abi-audit", "description": "compare every mirrored struct with the compiler", "on": [True, True, False], "rollout": [100, 100, 0]},
    {"key": "streaming-charts", "description": "incremental damage tracking in charts", "on": [True, False, False], "rollout": [60, 0, 0]},
    {"key": "rtl-shaping", "description": "build with the OpenType shaper", "on": [True, True, True], "rollout": [100, 40, 100]},
    {"key": "experimental-devpanels", "description": "opt-in developer panels", "on": [False, True, False], "rollout": [5, 100, 0]},
]
ENVS = ["prod", "staging", "dev"]

COMMITS = [
    {"hash": "7629d5f", "message": "Add whole-UI font installation and RTL font helpers", "author": "sara", "date": "2h", "refs": "HEAD -> main", "parent": [0, -1]},
    {"hash": "12f746a", "message": "Sync vendored CUI to v1.4.0", "author": "yapps", "date": "6h", "refs": "", "parent": [1, -1]},
    {"hash": "7320093", "message": "Merge pull request #8", "author": "x017", "date": "1d", "refs": "", "parent": [2, 3]},
    {"hash": "0a91c44", "message": "Expose the instrument cluster", "author": "sara", "date": "2d", "refs": "tag: v1.4.0", "parent": [4, -1]},
    {"hash": "f0d2b19", "message": "Initial commit", "author": "x017", "date": "1w", "refs": "", "parent": [-1, -1]},
]

BLAME_LINES = [
    "def level_meter(self, id, levels, *, min_db=-48.0, max_db=6.0):",
    "    keep = self._frame_keepalive",
    "    opts = CuiLevelMeterOpts()",
    "    opts.min_db = float(min_db)",
    "    arr = (c_float * n)(*levels)",
    "    return bool(self._lib.cui_level_meter_ex(self._ctx, id, arr, n, opts))",
]
BLAME_OF_LINE = [0, 0, 1, 1, 2, 2]
BLAME_COMMITS = [
    {"hash": "7629d5f", "author": "sara", "summary": "document linear meter levels", "time": 0},
    {"hash": "12f746a", "author": "yapps", "summary": "sync CUI 1.4.0", "time": 0},
    {"hash": "0a91c44", "author": "sara", "summary": "instrument cluster bindings", "time": 0},
]

KEYMAP = [
    {"action": "Command palette", "combo": {"key": "K", "mods": "ctrl"}, "category": 0},
    {"action": "Quick open file", "combo": {"key": "P", "mods": "ctrl"}, "category": 0},
    {"action": "Run tests", "combo": {"key": "F5", "mods": "ctrl"}, "category": 1},
    {"action": "Rebuild native core", "combo": {"key": "F7", "mods": "ctrl"}, "category": 1},
    {"action": "Toggle problems", "combo": {"key": "M", "mods": "ctrl+shift"}, "category": 2},
]

FRAMES = [
    {"function": "draw", "file": "examples/devtools.py", "line": 188,
     "source": ["with ctx.row(gap=16):", "    with ctx.card(...):", "        ctx.trace_view(...)"], "source_first": 186},
    {"function": "trace_view", "file": "src/nexa/widgets/devtools.py", "line": 512,
     "source": ["def trace_view(self, id, tracks, spans, ...):", "    out = CuiTraceResult()"]},
    {"function": "nexa_trace_view_ex", "file": "csrc/nexa_bridge_extra.c", "line": 64, "external": True},
]

SERVICES = [
    {"name": "api", "days": [1.0, 0.999, 1.0, 0.4, 1.0, 0.998, 1.0, 1.0, 0.92, 1.0, 1.0, 1.0]},
    {"name": "renderer", "days": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.99, 1.0, 1.0, 1.0, 0.999, 1.0]},
    {"name": "docs", "days": [0.98, 1.0, 0.97, 1.0, 1.0, 0.88, 1.0, 1.0, 1.0, 0.95, 1.0, 1.0]},
]

HISTOGRAM = [
    {"name": "200", "counts": [8, 14, 22, 9, 31, 44, 12, 6, 3, 11, 26, 38], "tone": ui.Tone.SUCCESS},
    {"name": "500", "counts": [0, 1, 0, 2, 3, 6, 1, 0, 0, 1, 2, 4], "tone": ui.Tone.DANGER},
    {"name": "p99", "counts": [1, 2, 3, 1, 4, 9, 2, 1, 0, 2, 5, 7], "tone": ui.Tone.WARNING},
]

QUERY_FIELDS = [
    {"name": "status", "type": "choice", "choices": ["open", "closed", "flaky"]},
    {"name": "duration", "type": "number"},
    {"name": "owner", "type": "text"},
    {"name": "quarantined", "type": "bool"},
]


def main() -> None:
    # NEXA_DEVTOOLS_TAB=1..3 opens the example on another tab (handy for screenshots)
    tab = int(os.environ.get("NEXA_DEVTOOLS_TAB", "0")) % len(TABS)
    kv_pairs = [
        {"key": "NEXA_MINIMAL", "value": "0"},
        {"key": "NEXA_TEXT_SHAPING", "value": "1"},
        {"key": "NEXA_LTO", "value": "1"},
    ]
    cron = "0 9 * * 1-5"
    method, url = 0, "https://api.dev/v1/builds?limit=20"
    query_nodes = [
        {"depth": 0, "group": True, "any": False},
        {"depth": 1, "field": 0, "op": 0, "value": "flaky"},
        {"depth": 1, "field": 1, "op": 3, "value": "90"},
    ]
    started = time.time()

    def draw(ctx: ui.UI) -> None:
        nonlocal tab, kv_pairs, cron, method, url, query_nodes

        elapsed = time.time() - started

        with ctx.column(width=ui.FILL, height=ui.FILL, bg=ui.Color.BACKGROUND, pad=20, gap=14):
            with ctx.row(align=ui.Align.CENTER, width=ui.FILL):
                ctx.heading("DevTools Studio", level=2)
                ctx.badge("CUI 1.3", tone=ui.Tone.INFO)
                ctx.spacer()
                ctx.text(f"frame {int(elapsed * 60)}", size=12, color=ui.Color.TEXT_MUTED)
            tab = ctx.tabs("dev_tabs", TABS, tab, full_width=False)

            with ctx.scroll("dev_body", width=ui.FILL, height=ui.FILL, gap=14, fade_edges=True):
                if tab == 0:
                    with ctx.row(gap=14, width=ui.FILL, align=ui.Align.START):
                        with ctx.card(width=ui.GROW(2), min_width=300, pad=16, gap=10):
                            ctx.secondary("Pipeline")
                            ctx.pipeline("pipeline", STAGES, JOBS, selected=-1)
                        with ctx.column(width=ui.GROW(2), gap=14):
                            with ctx.card(width=ui.FILL, pad=16, gap=10):
                                ctx.secondary("Problems")
                                problems = ctx.problems("problems", DIAGNOSTICS, height=230.0, width=ui.FILL)
                                ctx.badge(f"{problems.shown} diagnostics", tone=ui.Tone.WARNING)
                            with ctx.card(width=ui.FILL, pad=16, gap=10):
                                ctx.secondary("Test explorer")
                                tests = ctx.test_explorer("tests", TESTS, height=200.0, width=ui.FILL)
                                ctx.text(
                                    f"{tests.passed} passed · {tests.failed} failed",
                                    size=12,
                                    color=ui.Color.TEXT_SECONDARY,
                                )
                        with ctx.card(width=ui.GROW(3), min_width=360, pad=16, gap=10):
                            ctx.secondary("Coverage")
                            ctx.coverage("coverage", COVERAGE, height=560.0, width=ui.FILL)

                elif tab == 1:
                    with ctx.row(gap=14, width=ui.FILL, align=ui.Align.START):
                        with ctx.card(width=ui.GROW(3), min_width=430, pad=16, gap=10):
                            ctx.secondary("Trace")
                            trace = ctx.trace_view("trace", TRACKS, SPANS, height=210.0, width=ui.FILL)
                            ctx.text(
                                f"selected span {trace.selected} · hovered {trace.hovered}",
                                size=12,
                                color=ui.Color.TEXT_SECONDARY,
                            )
                        with ctx.card(width=ui.GROW(2), min_width=320, pad=16, gap=10):
                            ctx.secondary("Dependency graph")
                            graph = ctx.graph_view("graph", NODES, EDGES, height=210.0, width=ui.FILL)
                            ctx.text(f"hovered node {graph.hovered}", size=12, color=ui.Color.TEXT_SECONDARY)
                    with ctx.card(width=ui.FILL, pad=16, gap=10):
                        ctx.secondary("Waterfall")
                        ctx.waterfall("waterfall", REQUESTS, height=170.0, width=ui.FILL)
                    with ctx.row(gap=14, width=ui.FILL):
                        with ctx.card(width=ui.GROW(2), min_width=360, pad=16, gap=12):
                            ctx.secondary("Request")
                            bar = ctx.request_bar("bar", method, url)
                            method, url = bar.method, bar.url
                            ctx.text(
                                f"{ui.http_method_name(method)} · {ui.http_reason(200)}",
                                size=12,
                                color=ui.Color.TEXT_SECONDARY,
                            )
                        with ctx.card(width=ui.GROW(3), min_width=380, pad=16, gap=10):
                            ctx.secondary("API explorer")
                            ctx.api_explorer("api", ENDPOINTS, height=180.0, width=ui.FILL)

                elif tab == 2:
                    with ctx.row(gap=14, width=ui.FILL, align=ui.Align.START):
                        with ctx.card(width=ui.GROW(2), min_width=300, pad=16, gap=10):
                            ctx.secondary("Key / value")
                            kv = ctx.kv_editor("kv", kv_pairs)
                            kv_pairs = kv.pairs
                        with ctx.card(width=ui.GROW(3), min_width=380, pad=16, gap=10):
                            ctx.secondary("Query builder")
                            query = ctx.query_builder("query", QUERY_FIELDS, query_nodes)
                            query_nodes = query.nodes
                            text = ui.widgets.devtools.query_text(QUERY_FIELDS, query_nodes)
                            ctx.text(text or "(empty)", size=12, color=ui.Color.TEXT_SECONDARY)
                    with ctx.row(gap=14, width=ui.FILL):
                        with ctx.card(width=ui.GROW(3), min_width=400, pad=16, gap=10):
                            ctx.secondary("Feature flags")
                            flags = ctx.feature_flags("flags", FLAGS, ENVS, height=200.0, width=ui.FILL)
                            ctx.text(
                                f"flag {flags.flag} · env {flags.env}",
                                size=12,
                                color=ui.Color.TEXT_SECONDARY,
                            )
                        with ctx.card(width=ui.GROW(2), min_width=320, pad=16, gap=12):
                            ctx.secondary("Schedule")
                            schedule = ctx.schedule_picker("schedule", cron)
                            cron = schedule.cron
                            ctx.text(
                                f"next run {time.strftime('%a %H:%M', time.localtime(schedule.next)) if schedule.next else '—'}",
                                size=12,
                                color=ui.Color.TEXT_SECONDARY,
                            )
                    with ctx.row(gap=14, width=ui.FILL):
                        with ctx.card(width=ui.GROW(2), min_width=340, pad=16, gap=10):
                            ctx.secondary("Regex tester")
                            regex = ctx.regex_tester("regex", r"(?<level>\w+)\s+(\d+)", "info 42 warning 7")
                            state = "valid" if regex.valid else (regex.error or "invalid")
                            ctx.text(f"{state} · {regex.matches} matches", size=12, color=ui.Color.TEXT_SECONDARY)
                        with ctx.card(width=ui.GROW(3), min_width=400, pad=16, gap=10):
                            ctx.secondary("Response time histogram")
                            ctx.time_histogram("hist", started, 60.0, HISTOGRAM, height=140.0, width=ui.FILL)

                else:
                    with ctx.row(gap=14, width=ui.FILL, align=ui.Align.START):
                        with ctx.card(width=ui.GROW(3), min_width=430, pad=16, gap=10):
                            ctx.secondary("Commit graph")
                            commits = ctx.commit_graph("commits", COMMITS, height=220.0, width=ui.FILL)
                            ctx.text(
                                f"hovered {commits.hovered} · selected {commits.selected}",
                                size=12,
                                color=ui.Color.TEXT_SECONDARY,
                            )
                        with ctx.card(width=ui.GROW(2), min_width=320, pad=16, gap=10):
                            ctx.secondary("Uptime (12 days)")
                            uptime = ctx.uptime_bars("uptime", SERVICES)
                            ctx.text(
                                f"service {uptime.service} · day {uptime.day}",
                                size=12,
                                color=ui.Color.TEXT_SECONDARY,
                            )
                            ctx.secondary("Keymap")
                            ctx.keymap("keymap", KEYMAP, categories=["Navigation", "Run", "Panels"], width=ui.FILL)
                    with ctx.row(gap=14, width=ui.FILL):
                        with ctx.card(width=ui.GROW(3), min_width=430, pad=16, gap=10):
                            ctx.secondary("Blame")
                            ctx.blame("blame", BLAME_LINES, BLAME_OF_LINE, BLAME_COMMITS, height=160.0, width=ui.FILL)
                        with ctx.card(width=ui.GROW(2), min_width=320, pad=16, gap=10):
                            ctx.secondary("Stack trace")
                            ctx.stack_trace("stack", FRAMES, title="AssertionError", message="expected -6 dB", width=ui.FILL)

    with ui.App(
        "DevTools Studio — nexa", width=1280, height=1000, theme=ui.ThemeMode.DARK, accent=ui.Accent.BLUE
    ) as app:
        app.run(draw)


if __name__ == "__main__":
    main()
