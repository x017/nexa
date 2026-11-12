"""Build static HTML documentation & Wiki pages in `docs/` from `docs/*.md` (pure stdlib).

Generates:
1. Pre-rendered standalone static HTML pages in `docs/` (`wiki.html`, `tutorials.html`,
   `guide.html`, `components.html`, `changelog.html`, and all 8 Markdown chapters) so every
   page renders instantaneously with zero large JS bundle dependency.
2. Compact `docs/assets/search-index.js` (~18 KB) for instant `Ctrl+K` client-side search.
3. Optional `--export-wiki <dir>` output (`Home.md`, `_Sidebar.md`, `_Footer.md`, + 8 chapters)
   formatted for the GitHub repository Wiki (`https://github.com/x017/nexa/wiki`).
"""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import struct


DOCS_DIR = pathlib.Path(__file__).resolve().parent
ASSET_VER = "1.2.0"

# (slug, sidebar_title, sidebar_group, md_filename, wiki_page_name, top_nav_key)
CHAPTERS = [
    ("zero-to-hero", "0 to Hero: Full Tutorial", "Start Here", "zero-to-hero.md", "Zero-to-Hero", "tutorials"),
    ("getting-started", "Getting Started", "Start Here", "getting-started.md", "Getting-Started", "guide"),
    ("tutorial-functional", "Functional & Procedural", "Tutorials", "tutorial-functional.md", "Functional-and-Procedural", "tutorials"),
    ("tutorial-oop", "Object-Oriented (OOP)", "Tutorials", "tutorial-oop.md", "Object-Oriented-Architecture", "tutorials"),
    ("theming-and-styling", "Theming, Accents & Icons", "Tutorials", "theming-and-styling.md", "Theming-Accents-and-Icons", "tutorials"),
    ("concurrency-and-async", "Concurrency & Asyncio", "Tutorials", "concurrency-and-async.md", "Concurrency-and-Asyncio", "tutorials"),
    ("advanced-rendering-and-packaging", "Canvas, GPU & Packaging", "Tutorials", "advanced-rendering-and-packaging.md", "Canvas-GPU-and-Packaging", "tutorials"),
    ("components-reference", "190+ Components Reference", "API Reference", "components-reference.md", "Components-Reference", "components"),
]

TUTORIAL_TRACK = [
    {
        "num": "00",
        "slug": "zero-to-hero",
        "short": "0 → Hero",
        "fullTitle": "Zero to Hero: The Complete nexa Masterclass",
        "time": "45 min",
        "tag": "Full 11-Module Course",
        "desc": "End-to-end masterclass from your first 15-line window through layouts, forms, chrome, 50k data grids, studio canvases, OOP, OKLCH, async workers & building Pulse Studio.",
    },
    {
        "num": "01",
        "slug": "getting-started",
        "short": "Start",
        "fullTitle": "Getting Started & Mental Model",
        "time": "5 min",
        "tag": "Core Model",
        "desc": "Install nexa-ui, open your first native window, and learn value-returning widgets, IDs, and scopes.",
    },
    {
        "num": "02",
        "slug": "tutorial-functional",
        "short": "Functional",
        "fullTitle": "Functional & Procedural Coding",
        "time": "12 min",
        "tag": "ui.run & ctx",
        "desc": "Build concise closures with ui.run(draw), decompose procedural helpers, and create a complete Budget Tracker.",
    },
    {
        "num": "03",
        "slug": "tutorial-oop",
        "short": "OOP",
        "fullTitle": "Object-Oriented Architecture",
        "time": "15 min",
        "tag": "Component & Store",
        "desc": "Scale multi-screen apps with Application, auto-scoped Component classes, Router, View, and reactive Store[T].",
    },
    {
        "num": "04",
        "slug": "theming-and-styling",
        "short": "Theming",
        "fullTitle": "Theming, OKLCH Accents & Icons",
        "time": "8 min",
        "tag": "8 OKLCH Accents",
        "desc": "Master Light & Dark modes, all 8 perceptual OKLCH accents, 34 semantic tokens, custom .ttf fonts & 168 Lucide icons.",
    },
    {
        "num": "05",
        "slug": "concurrency-and-async",
        "short": "Async & Threads",
        "fullTitle": "Concurrency, Asyncio & Networking",
        "time": "10 min",
        "tag": "GIL-Free",
        "desc": "Run worker pools, token streams, thread-safe Channel[T], LogBuffer, and cooperative asyncio without dropping 60fps.",
    },
    {
        "num": "06",
        "slug": "advanced-rendering-and-packaging",
        "short": "GPU & Packaging",
        "fullTitle": "Vector Canvas, Custom GPU & Packaging",
        "time": "10 min",
        "tag": "CI & Freezing",
        "desc": "Vector canvas drawing, headless pytest screenshot verification, custom GPU backends, --rtl shaping & PyInstaller/Nuitka.",
    },
]

CATALOG_ITEMS = [
    {"name": "dockspace", "sig": "ui.dockspace(id, *, layout=None, width=None, height=None)", "domain": "Chrome & Dock", "isNew": True, "desc": "Multi-split tabbed docking workspace with interactive drag-to-dock drop targets and layout DSL."},
    {"name": "dock_panel", "sig": "ui.dock_panel(title, is_open=None, *, icon=None, dirty=False)", "domain": "Chrome & Dock", "isNew": True, "desc": "Closable, dirty-aware dockable panel inside an active dockspace; pairs with dock_save() and dock_load()."},
    {"name": "tree_table", "sig": "ui.tree_table(id, columns, nodes, *, sort=None, guides=True, labels=None)", "domain": "Data & Code", "isNew": True, "desc": "Virtualized multi-column hierarchical tree-grid with lazy child loading, indent guides, and type-ahead search."},
    {"name": "path_bar", "sig": "ui.path_bar(id, segments, *, icon=None, menus=False) -> PathBarResult", "domain": "Chrome & Dock", "isNew": True, "desc": "Editable file-manager / IDE breadcrumb address bar with click-to-edit path input and segment popup menus."},
    {"name": "markdown", "sig": "ui.markdown(id, text, *, streaming=False, compact=False) -> MarkdownResult", "domain": "Data & Code", "isNew": True, "desc": "CommonMark + GFM renderer with headings, tables, fenced syntax blocks, GitHub alerts, and interactive task checkboxes."},
    {"name": "code_editor", "sig": "ui.code_editor(id, text, *, lang=None, height=320) -> CodeEditorResult", "domain": "Data & Code", "isNew": True, "desc": "Multi-line source editor with syntax highlighting, undo/redo history, bracket matching, and Ctrl+F find bar."},
    {"name": "diff_view", "sig": "ui.diff_view(id, old_text, new_text, *, mode=DiffMode.SPLIT) -> DiffResult", "domain": "Data & Code", "isNew": True, "desc": "Side-by-side or unified inline diff viewer with intraline word highlights, hunk folding, and headless diff_compute()."},
    {"name": "hex_view", "sig": "ui.hex_view(id, data, selection=None, *, ranges=None, editable=False) -> HexResult", "domain": "Tools & Studio", "isNew": True, "desc": "Virtualized binary hex + ASCII inspector with colored tone annotations and zero-copy bytearray nibble editing."},
    {"name": "flame_graph", "sig": "ui.flame_graph(id, spans, *, view=None, selected=None) -> FlameResult", "domain": "Tools & Studio", "isNew": True, "desc": "Interactive profiler flame / icicle chart with wheel zoom, drag pan, span selection, and C99 flame_sort()."},
    {"name": "curve_editor", "sig": "ui.curve_editor(id, keys, *, show_playhead=False) -> CurveResult", "domain": "Tools & Studio", "isNew": True, "desc": "2D cubic Bezier, linear & step keyframe curve editor with tangent handles and standalone curve_eval()."},
    {"name": "gradient_editor", "sig": "ui.gradient_editor(id, stops, *, selected=None) -> GradientResult", "domain": "Tools & Studio", "isNew": True, "desc": "Perceptual OKLab multi-stop color ramp editor with stop color/location/opacity controls and gradient_eval()."},
    {"name": "timeline_editor", "sig": "ui.timeline_editor(id, tracks, time, *, start=0, end=10, fps=30) -> TimelineEditorResult", "domain": "Tools & Studio", "isNew": True, "desc": "Multi-track keyframe dope sheet and NLE clip timeline with playhead scrubbing, mute/lock toggles, and clip trimming."},
    {"name": "row / column / grid / stack", "sig": "ui.row(**box_opts) / ui.column(**box_opts) / ui.grid(columns=...)", "domain": "Layout", "isNew": False, "desc": "Sub-quarter-millisecond Flexbox & responsive CSS-Grid containers supporting FIT, FILL, GROW, PX, and PCT sizing."},
    {"name": "split & scroll", "sig": "ui.split(id, ratio, *, vertical=False) / ui.scroll(id, *, sticky_bottom=False)", "domain": "Layout", "isNew": False, "desc": "Interactive draggable split panes and smooth virtualizable scroll containers with optional edge fades."},
    {"name": "menu_bar / toolbar / status_bar / doc_tabs", "sig": "ui.menu_bar() / ui.toolbar() / ui.status_bar() / ui.doc_tabs(...)", "domain": "Chrome & Dock", "isNew": False, "desc": "Complete desktop application chrome with keyboard mnemonics, toggle tools, progress items, and reorderable dirty tabs."},
    {"name": "data_grid", "sig": "ui.data_grid(id, columns, row_count, *, hide_checkboxes=False, anchor=None)", "domain": "Data & Code", "isNew": False, "desc": "Spreadsheet-grade virtualized grid with column priority auto-hiding, range selection, sorting, and inline cell editing."},
    {"name": "virtual_list & table", "sig": "ui.virtual_list(id, count, row_h) / ui.table(id, columns, ...)", "domain": "Data & Code", "isNew": False, "desc": "O(visible) 1,000,000-row virtual list scope and striped sortable data tables."},
    {"name": "code_block & json_view", "sig": "ui.code_block(id, code, *, lang='python') / ui.json_view(id, json_text)", "domain": "Data & Code", "isNew": False, "desc": "Read-only syntax-highlighted source blocks with copy header and interactive collapsible JSON tree inspector."},
    {"name": "node_editor & canvas", "sig": "ui.node_editor(id, view) / ui.canvas(id, width, height)", "domain": "Tools & Studio", "isNew": False, "desc": "Pan/zoom Bezier node graph editor with minimap and immediate SDF vector drawing canvas (lines, arcs, polygons, text)."},
    {"name": "inspector & log_view", "sig": "ui.inspector(id) / ui.prop_float(...) / ui.log_view(id, LogBuffer)", "domain": "Tools & Studio", "isNew": False, "desc": "Typed property inspector (float, int, vec2/3/4, enum, color, bool) and thread-safe C ring-buffer log console."},
    {"name": "line_chart / bar_chart / scatter_chart", "sig": "ui.line_chart(...) / ui.bar_chart(...) / ui.scatter_chart(...)", "domain": "Charts", "isNew": False, "desc": "Smooth cubic area/line charts, stacked/grouped/horizontal bars, and bubble scatter plots with hover crosshairs."},
    {"name": "donut / radar / treemap / sankey / heatmap", "sig": "ui.donut_chart(...) / ui.treemap(...) / ui.sankey(...) / ui.heatmap(...)", "domain": "Charts", "isNew": False, "desc": "16 native chart widgets including gauges, funnels, waffles, split bars, activity rings, sparklines, and GitHub calendar heatmaps."},
    {"name": "kanban / gantt / week_calendar", "sig": "ui.kanban(id) / ui.gantt(id, tasks, ...) / ui.week_calendar(...)", "domain": "Planning", "isNew": False, "desc": "Drag-and-drop Kanban boards with WIP limits, interactive Gantt timelines, and 7-day week event schedules."},
    {"name": "chat_composer / reasoning / tool_call / voice_orb", "sig": "ui.chat_composer(...) / ui.reasoning(...) / ui.voice_orb(...)", "domain": "AI & Social", "isNew": False, "desc": "Streaming AI interfaces: markdown chat bubbles, model picker, token context ring, agent plans, citations & reactive voice orb."},
    {"name": "button / input / select / command_palette / dialog", "sig": "ui.button(...) / ui.input(...) / ui.command_palette(...) / ui.dialog(...)", "domain": "Controls & Overlays", "isNew": False, "desc": "60+ tactile form controls, date/color pickers, OTP/money inputs, sheets, popovers, toasts, and Ctrl+K command palette."},
    {"name": "knob", "sig": "ui.knob(id, value, min=0, max=1, *, label=None, unit=None, bipolar=False) -> float", "domain": "Instruments", "isNew": True, "desc": "Rotary dial with drag/wheel input, dB or linear scale, and the value it returns on change; double-click resets."},
    {"name": "fader", "sig": "ui.fader(id, value, min=0, max=1, *, ticks=(), meter=None, horizontal=False) -> float", "domain": "Instruments", "isNew": True, "desc": "Console fader with tick marks and an optional dB meter strip beside the track."},
    {"name": "level_meter", "sig": "ui.level_meter(id, levels, *, min_db=-48, max_db=6, segmented=True) -> bool", "domain": "Instruments", "isNew": True, "desc": "Multi-channel segmented dB meter with peak hold and decay."},
    {"name": "radial_gauge", "sig": "ui.radial_gauge(id, value, *, min=0, max=100, bands=(), target=None)", "domain": "Instruments", "isNew": True, "desc": "Sweeping arc gauge with tone bands and an optional target needle."},
    {"name": "readout", "sig": "ui.readout(label, value, *, unit=None, detail=None, tone=Tone.NEUTRAL, accent=False)", "domain": "Instruments", "isNew": True, "desc": "Big-number instrument readout with a unit suffix and a small detail line."},
    {"name": "dot_display", "sig": "ui.dot_display(text, *, pitch=0, accent=False, marquee=False)", "domain": "Instruments", "isNew": True, "desc": "Dot-matrix style display for clock and hardware readouts."},
    {"name": "dot_chart", "sig": "ui.dot_chart(id, series, *, x_units='number', annotations=()) -> DotChartResult", "domain": "Instruments", "isNew": True, "desc": "Dot/heatmap chart for sparse event data over a day, with hover readout and annotations."},
    {"name": "event_track", "sig": "ui.event_track(id, times, *, capacity=256, min=0, max=24) -> EventTrackResult", "domain": "Instruments", "isNew": True, "desc": "Timeline strip of point events the user can add, drag and delete."},
    {"name": "candlestick", "sig": "ui.candlestick(id, candles, *, labels=None, overlays=(), ohlc=False) -> int", "domain": "Charts", "isNew": True, "desc": "Financial OHLC candlestick chart with an optional volume strip and overlays; returns the hovered index."},
    {"name": "image_viewer", "sig": "ui.image_viewer(id, texture, image_width, image_height, view) -> ImageView", "domain": "Media", "isNew": True, "desc": "Zoomable, pannable image viewer with a toolbar and checkerboard transparency."},
    {"name": "cropper", "sig": "ui.cropper(id, texture, image_width, image_height, crop, *, aspect=0) -> (Rect, bool)", "domain": "Media", "isNew": True, "desc": "Crop rectangle editor with handles, aspect lock, and a round-mask preview."},
    {"name": "emoji", "sig": "ui.emoji(text, *, size=16)", "domain": "Media", "isNew": True, "desc": "Draw an emoji glyph from the embedded color-emoji table."},
    {"name": "emoji_picker", "sig": "ui.emoji_picker(id, *, height=280, recent='', no_search=False) -> str | None", "domain": "Media", "isNew": True, "desc": "Searchable emoji grid grouped by category; returns the picked emoji."},
    {"name": "terminal", "sig": "ui.terminal(id, buffer, *, height=320, prompt=None, no_input=False) -> TerminalResult", "domain": "Text & Code", "isNew": True, "desc": "Terminal panel over a TerminalBuffer: scrollback, ANSI colours and a command line."},
    {"name": "month_calendar", "sig": "ui.month_calendar(id, month, events=(), *, selected=None, cell_height=104) -> MonthResult", "domain": "Planning", "isNew": True, "desc": "Month grid with multi-day events, day selection, and month navigation."},
    {"name": "tour", "sig": "ui.tour(id, steps, step, *, padding=6, block_target=False) -> (int, str)", "domain": "Controls & Overlays", "isNew": True, "desc": "Guided product tour: a card anchored to any widget id with next/back/done actions."},
    {"name": "file_browser", "sig": "ui.file_browser(id, path, *, filter=None, folders_only=False) -> FileBrowserResult", "domain": "Files", "isNew": True, "desc": "Real-directory browser with sorting, filter, places sidebar and history; returns the updated folder."},
    {"name": "file_picker", "sig": "ui.file_picker(id, path, *, save=False, folders=False, filter=None) -> FilePickerResult", "domain": "Files", "isNew": True, "desc": "Open/save dialog over the file browser with a filename field and filter."},
    {"name": "fs_list", "sig": "ui.fs_list(path='.', *, hidden=False) -> list[FileEntry]", "domain": "Files", "isNew": True, "desc": "Headless directory listing behind the browser, usable outside a frame."},
    {"name": "problems", "sig": "ui.problems(id, diagnostics, *, no_toolbar=False) -> ProblemsResult", "domain": "Dev Tools", "isNew": True, "desc": "Filterable build and lint problems panel with severity icons and jump-to-line."},
    {"name": "pipeline", "sig": "ui.pipeline(id, stages, jobs=(), *, selected=-1) -> PipelineResult", "domain": "Dev Tools", "isNew": True, "desc": "CI/CD pipeline of stage columns with job badges, durations and retries."},
    {"name": "schedule_picker", "sig": "ui.schedule_picker(id, cron='0 9 * * *') -> ScheduleResult", "domain": "Dev Tools", "isNew": True, "desc": "Cron builder with presets, a plain-language description and the next run times."},
    {"name": "keymap", "sig": "ui.keymap(id, bindings, *, categories=()) -> KeymapResult", "domain": "Dev Tools", "isNew": True, "desc": "Searchable keyboard-shortcut cheatsheet with conflict detection."},
    {"name": "commit_graph", "sig": "ui.commit_graph(id, commits, *, height=280) -> CommitGraphResult", "domain": "Dev Tools", "isNew": True, "desc": "Git history graph with branch lanes, refs, merges and author/date columns."},
    {"name": "graph_view", "sig": "ui.graph_view(id, nodes, edges=(), *, top_down=True) -> GraphResult", "domain": "Dev Tools", "isNew": True, "desc": "Node/edge dependency graph with pan, zoom and selection."},
    {"name": "waterfall", "sig": "ui.waterfall(id, requests, *, dom_loaded=-1, loaded=-1) -> WaterfallResult", "domain": "Dev Tools", "isNew": True, "desc": "Network waterfall with request phases, sizes and DOMContentLoaded/load markers."},
    {"name": "trace_view", "sig": "ui.trace_view(id, tracks, spans, view=None, selected=-1) -> TraceResult", "domain": "Dev Tools", "isNew": True, "desc": "Timeline trace viewer with nested tracks, zoom/pan, markers and span selection."},
    {"name": "regex_tester", "sig": "ui.regex_tester(id, pattern='', text='') -> RegexTesterResult", "domain": "Dev Tools", "isNew": True, "desc": "Live regular-expression playground with match highlighting and error text."},
    {"name": "test_explorer", "sig": "ui.test_explorer(id, items) -> TestExplorerResult", "domain": "Dev Tools", "isNew": True, "desc": "Test tree with pass/fail/skip badges, durations, messages and run buttons."},
    {"name": "stack_trace", "sig": "ui.stack_trace(id, frames, *, title='', message='') -> StackTraceResult", "domain": "Dev Tools", "isNew": True, "desc": "Crash report with expandable source excerpts and file/line links."},
    {"name": "request_bar", "sig": "ui.request_bar(id, method=0, url='') -> RequestBarResult", "domain": "Dev Tools", "isNew": True, "desc": "HTTP method picker, URL field and Send button for API clients."},
    {"name": "api_explorer", "sig": "ui.api_explorer(id, endpoints) -> ApiExplorerResult", "domain": "Dev Tools", "isNew": True, "desc": "Browsable API reference with method badges, params and a try-it button."},
    {"name": "feature_flags", "sig": "ui.feature_flags(id, flags, envs=()) -> FeatureFlagsResult", "domain": "Dev Tools", "isNew": True, "desc": "Flag table with per-environment switches and rollout percentages."},
    {"name": "uptime_bars", "sig": "ui.uptime_bars(id, services) -> UptimeResult", "domain": "Dev Tools", "isNew": True, "desc": "Status-page uptime bars with per-day health and tooltips."},
    {"name": "time_histogram", "sig": "ui.time_histogram(id, start, bucket_seconds, series) -> TimeHistogramResult", "domain": "Dev Tools", "isNew": True, "desc": "Stacked histogram over time with a draggable brush selection."},
    {"name": "coverage", "sig": "ui.coverage(id, files, *, low=0.5, high=0.8) -> CoverageResult", "domain": "Dev Tools", "isNew": True, "desc": "Coverage report with per-file line, branch and function heat bars."},
    {"name": "blame", "sig": "ui.blame(id, lines, line_commit, commits) -> BlameResult", "domain": "Dev Tools", "isNew": True, "desc": "git blame view: source lines tinted by commit with author and age gutters."},
    {"name": "kv_editor", "sig": "ui.kv_editor(id, pairs=(), *, capacity=32) -> KvEditorResult", "domain": "Dev Tools", "isNew": True, "desc": "Editable key/value rows with enable toggles and secret masking."},
    {"name": "query_builder", "sig": "ui.query_builder(id, fields, nodes=()) -> QueryBuilderResult", "domain": "Dev Tools", "isNew": True, "desc": "Nested AND/OR rule builder over typed fields, with query_text() and query_match() helpers."},
]

EXAMPLES_LIST = [
    ("zero_to_hero.py", "Pulse Studio (0→Hero Capstone)", "OOP Application + Store, dockspace, tree_table, code_editor, diff_view, GFM checklist, charts & flame profiler."),
    ("workbench.py", "Workbench Studio 1.1", "All 12 CUI 1.1 components: dockspace, path_bar, tree_table, code_editor, diff_view, hex_view, flame_graph, curves, gradients & NLE timeline."),
    ("gallery.py", "Nodes & Studio Gallery", "Menu bar, toolbar, dirty document tabs, pan/zoom Bezier node graph, typed property inspector & C-backed log console."),
    ("dashboard.py", "Larkspur Analytics", "Animated rolling KPIs, sparklines, cubic area chart, donut breakdown, filter bar & virtualized data grid."),
    ("tracker.py", "Project Tracker", "Light-mode drag-and-drop Kanban board, interactive Gantt timeline, 7-day week schedule & live presence rings."),
    ("assistant.py", "Muse AI Copilot", "BackgroundRunner token streaming, model picker, context ring meter, execution plan & reactive voice orb."),
    ("finance.py", "Market Terminal", "Live scrolling market ticker, rolling odometer counter, Treemap, split bar, Sankey diagram & trading heatmap."),
    ("settings.py", "OOP Settings & 8 Accents", "Multi-route Application + Router + View + Component architecture showcasing all 8 OKLCH accents."),
    ("async_network.py", "Asyncio & Worker Pools", "Cooperative asyncio loop, AsyncBridge, BackgroundRunner HTTP JSON fetch & non-blocking progress."),
    ("mail.py", "Desktop Mail Client", "Three-pane resizable split layout, virtualized message list, search filter & rich thread preview."),
    ("music.py", "Audio Deck", "Transport controls, waveform/equalizer visualization, playlists & smooth spring animations."),
    ("notes.py", "Markdown Notes", "Live CommonMark + GFM task list preview alongside multi-line editing and tag filtering."),
    ("hello.py", "Minimal Starter", "Smallest 15-line interactive native window using ui.run(draw)."),
]

PY_KW = {
    "import", "from", "as", "def", "class", "return", "if", "elif", "else",
    "for", "in", "while", "with", "try", "finally", "except", "raise",
    "True", "False", "None", "and", "or", "not", "nonlocal", "global",
    "async", "await", "yield", "lambda", "pass", "break", "continue", "assert",
}

TOKEN_RE = re.compile(
    r"(?P<com>#[^\n]*)"
    r"|(?P<str>\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''|\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*')"
    r"|(?P<num>\b\d+(?:\.\d+)?\b)"
    r"|(?P<id>\b[A-Za-z_][A-Za-z0-9_]*\b)"
)


def highlight_code(code: str, lang: str) -> str:
    if lang not in ("python", "py"):
        return html.escape(code)

    out: list[str] = []
    pos = 0
    for m in TOKEN_RE.finditer(code):
        if m.start() > pos:
            out.append(html.escape(code[pos:m.start()]))
        tok = m.group(0)
        esc = html.escape(tok)
        if m.lastgroup == "com":
            out.append(f'<span class="tok-com">{esc}</span>')
        elif m.lastgroup == "str":
            out.append(f'<span class="tok-str">{esc}</span>')
        elif m.lastgroup == "num":
            out.append(f'<span class="tok-num">{esc}</span>')
        elif m.lastgroup == "id":
            if tok in PY_KW:
                out.append(f'<span class="tok-kw">{esc}</span>')
            elif tok[0].isupper():
                out.append(f'<span class="tok-cls">{esc}</span>')
            else:
                out.append(esc)
        pos = m.end()
    if pos < len(code):
        out.append(html.escape(code[pos:]))
    return "".join(out)


def slugify(text: str) -> str:
    clean = re.sub(r"`([^`]+)`", r"\1", text)
    clean = re.sub(r"[^a-zA-Z0-9]+", "-", clean.lower()).strip("-")
    return clean or "section"


def render_inline(text: str) -> str:
    stashed: list[str] = []

    def _stash(fragment: str) -> str:
        idx = len(stashed)
        stashed.append(fragment)
        return f"\x00TOK{idx}\x00"

    s = re.sub(r"`([^`]+)`", lambda m: _stash(f"<code>{html.escape(m.group(1))}</code>"), text)
    s = html.escape(s)

    def _format_emph(val: str) -> str:
        val = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", val)
        val = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<em>\1</em>", val)
        return val

    def _link_sub(m: re.Match[str]) -> str:
        lbl, url = _format_emph(m.group(1)), m.group(2)
        if url.endswith(".md"):
            chap_slug = pathlib.Path(url).stem
            return _stash(f'<a href="{chap_slug}.html">{lbl}</a>')
        if ".md#" in url:
            md_part, anchor_part = url.split("#", 1)
            chap_slug = pathlib.Path(md_part).stem
            return _stash(f'<a href="{chap_slug}.html#{anchor_part}">{lbl}</a>')
        return _stash(f'<a href="{url}" target="_blank" rel="noopener">{lbl}</a>')

    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _link_sub, s)
    s = _format_emph(s)
    return re.sub(r"\x00TOK(\d+)\x00", lambda m: stashed[int(m.group(1))], s)


def markdown_to_html(md: str) -> tuple[str, list[dict[str, str]], list[dict[str, str]]]:
    lines = md.splitlines()
    i = 0
    n = len(lines)
    html_parts: list[str] = []
    toc: list[dict[str, str]] = []
    sections_index: list[dict[str, str]] = []
    current_h = "Overview"
    current_slug = ""
    current_text: list[str] = []

    def _flush_section() -> None:
        if current_text:
            sections_index.append({
                "heading": current_h,
                "anchor": current_slug,
                "snippet": " ".join(current_text)[:240],
            })
            current_text.clear()

    while i < n:
        line = lines[i]

        if line.strip().startswith("```"):
            lang = line.strip()[3:].strip() or "text"
            i += 1
            buf: list[str] = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            raw_code = "\n".join(buf)
            hl = highlight_code(raw_code, lang)
            label = "python" if lang in ("python", "py") else lang
            html_parts.append(
                f'<div class="code-panel">'
                f'<div class="code-header"><span>{html.escape(label)}</span>'
                f'<button class="copy-mini" data-copy-code="1" type="button">Copy</button></div>'
                f"<pre><code>{hl}</code></pre></div>"
            )
            continue

        if re.match(r"^\s*---+\s*$", line):
            html_parts.append("<hr />")
            i += 1
            continue

        img_m = re.match(r"^\s*!\[([^\]]*)\]\(([^)]+)\)\s*$", line)
        if img_m:
            alt_txt = html.escape(img_m.group(1).strip())
            raw_src = img_m.group(2).strip()
            src_url = html.escape(raw_src)
            dims_attr = ""
            img_path = DOCS_DIR / raw_src.split("?")[0]
            if img_path.is_file() and img_path.suffix.lower() == ".png":
                hdr = img_path.read_bytes()[:24]
                if len(hdr) == 24 and hdr[:8] == b"\x89PNG\r\n\x1a\n":
                    w, h = struct.unpack(">II", hdr[16:24])
                    dims_attr = f' width="{w}" height="{h}"'
            html_parts.append(
                f'<figure class="doc-figure">'
                f'<div class="window-frame">'
                f'<div class="window-bar"><div class="window-dots"><i></i><i></i><i></i></div>'
                f'<span>{alt_txt}</span><span style="width: 42px;"></span></div>'
                f'<img src="{src_url}" alt="{alt_txt}"{dims_attr} loading="lazy" decoding="async" />'
                f"</div></figure>"
            )
            i += 1
            continue

        hm = re.match(r"^(#{1,4})\s+(.+)$", line)
        if hm:
            _flush_section()
            lvl = len(hm.group(1))
            raw_title = hm.group(2).strip()
            slug = slugify(raw_title)
            current_h = re.sub(r"`([^`]+)`", r"\1", raw_title)
            current_h = re.sub(r"\*\*([^*]+)\*\*", r"\1", current_h)
            current_h = re.sub(r"\*([^*]+)\*", r"\1", current_h)
            current_slug = slug if lvl > 1 else ""
            if lvl == 2:
                toc.append({"title": current_h, "id": slug})
            html_parts.append(f'<h{lvl} id="{slug}">{render_inline(raw_title)}</h{lvl}>')
            i += 1
            continue

        if "|" in line and i + 1 < n and re.match(r"^\s*\|?[\s:-]+\|[\s|:-]*$", lines[i + 1]):
            headers = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows: list[list[str]] = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            th_html = "".join(f"<th>{render_inline(h)}</th>" for h in headers)
            tr_html = "".join(
                "<tr>" + "".join(f"<td>{render_inline(c)}</td>" for c in r) + "</tr>"
                for r in rows
            )
            html_parts.append(f"<table><thead><tr>{th_html}</tr></thead><tbody>{tr_html}</tbody></table>")
            continue

        if line.lstrip().startswith(">"):
            q_lines: list[str] = []
            while i < n and lines[i].lstrip().startswith(">"):
                q_lines.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            q_body = " ".join(x.strip() for x in q_lines if x.strip())
            current_text.append(q_body)
            cls_attr = ""
            if q_body.startswith("**Pitfall") or q_body.startswith("**Important"):
                cls_attr = ' class="callout-warn"'
            elif q_body.startswith("**Pro Tip"):
                cls_attr = ' class="callout-tip"'
            html_parts.append(f"<blockquote{cls_attr}><p>{render_inline(q_body)}</p></blockquote>")
            continue

        ul_m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.+)$", line)
        if ul_m:
            ordered = ul_m.group(2).endswith(".")
            tag = "ol" if ordered else "ul"
            items_html: list[str] = []
            while i < n:
                m_it = re.match(r"^(\s*)([-*]|\d+\.)\s+(.+)$", lines[i])
                if not m_it:
                    break
                item_txt = m_it.group(3).strip()
                current_text.append(re.sub(r"`([^`]+)`", r"\1", item_txt))
                i += 1
                sub_items: list[str] = []
                while i < n and re.match(r"^\s{2,}[-*]\s+(.+)$", lines[i]):
                    sub_txt = re.sub(r"^\s{2,}[-*]\s+", "", lines[i]).strip()
                    current_text.append(re.sub(r"`([^`]+)`", r"\1", sub_txt))
                    sub_items.append(f"<li>{render_inline(sub_txt)}</li>")
                    i += 1
                sub_ul = f"<ul>{''.join(sub_items)}</ul>" if sub_items else ""
                items_html.append(f"<li>{render_inline(item_txt)}{sub_ul}</li>")
            html_parts.append(f"<{tag}>{''.join(items_html)}</{tag}>")
            continue

        if not line.strip():
            i += 1
            continue

        p_lines: list[str] = []
        while i < n and lines[i].strip() and not re.match(r"^(#{1,4}\s|```|---|\s*!\[|\s*[-*]\s|\s*\d+\.\s|\s*>)", lines[i]):
            p_lines.append(lines[i].strip())
            i += 1
        para = " ".join(p_lines)
        current_text.append(re.sub(r"`([^`]+)`", r"\1", para))
        html_parts.append(f"<p>{render_inline(para)}</p>")

    _flush_section()
    return "\n".join(html_parts), toc, sections_index


def render_sidebar_html(current_slug: str, parsed_chapters: list[dict]) -> str:
    groups: list[tuple[str, list[dict]]] = []
    for ch in parsed_chapters:
        found = False
        for gname, gitems in groups:
            if gname == ch["group"]:
                gitems.append(ch)
                found = True
                break
        if not found:
            groups.append((ch["group"], [ch]))

    special_links = [
        ("wiki", "wiki.html", 'Docs Wiki <span class="badge-new">WIKI</span>'),
        ("tutorials", "tutorials.html", "All Tutorials Overview"),
        ("components", "components.html", 'Component Explorer <span class="badge-new">1.4</span>'),
        ("changelog", "changelog.html", "Changelog"),
    ]
    special_html = '<div class="sidebar-group-title">Explore</div>' + "".join(
        f'<a class="sidebar-link{" active" if current_slug == s_slug else ""}" href="{s_href}">{s_label}</a>'
        for s_slug, s_href, s_label in special_links
    )

    chapters_html_parts: list[str] = []
    for gname, gitems in groups:
        chapters_html_parts.append(f'<div class="sidebar-group-title">{html.escape(gname)}</div>')
        for ch in gitems:
            is_act = ch["slug"] == current_slug
            badge = ' <span class="badge-new">FULL</span>' if ch["slug"] == "zero-to-hero" else ""
            sub_html = ""
            if is_act and ch["toc"]:
                sub_links = "".join(
                    f'<a class="sidebar-sublink" href="#{html.escape(t["id"])}" data-anchor="{html.escape(t["id"])}">{html.escape(t["title"])}</a>'
                    for t in ch["toc"]
                )
                sub_html = f'<div class="sidebar-sublinks">{sub_links}</div>'
            chapters_html_parts.append(
                f'<a class="sidebar-link{" active" if is_act else ""}" href="{ch["slug"]}.html">'
                f'{html.escape(ch["title"])}{badge}</a>{sub_html}'
            )

    return special_html + "".join(chapters_html_parts)


def render_tutorial_track_html(current_slug: str) -> str:
    if not any(t["slug"] == current_slug for t in TUTORIAL_TRACK):
        return ""
    steps = "".join(
        f'<a class="track-step{" active" if t["slug"] == current_slug else ""}" href="{t["slug"]}.html">'
        f'<span class="track-step-num">{t["num"]}</span>'
        f'<span>{html.escape(t["short"])}</span></a>'
        for t in TUTORIAL_TRACK
    )
    return f'<div class="tutorial-track" aria-label="Tutorial curriculum"><span class="tutorial-track-label">Tutorials</span>{steps}</div>'


def build_tutorials_hub_html(hero_toc: list[dict[str, str]]) -> str:
    syntax_toc = next((t for t in hero_toc if "syntax guide" in t["title"].lower()), None)
    pills: list[str] = []
    if syntax_toc:
        pills.append(
            f'<a class="module-jump-pill" href="zero-to-hero.html#{html.escape(syntax_toc["id"])}">Syntax &amp; Sections Guide</a>'
        )
    for t in hero_toc:
        if re.match(r"^Module\s+\d+", t["title"], re.IGNORECASE):
            short_lbl = t["title"].split(":")[0].replace("Module ", "M").strip()
            pills.append(
                f'<a class="module-jump-pill" href="zero-to-hero.html#{html.escape(t["id"])}">{html.escape(short_lbl)}</a>'
            )
    pills_html = f'<div class="module-jump-strip">{"".join(pills)}</div>' if pills else ""

    cards_html = "".join(
        f'<a class="tutorial-hub-card" href="{t["slug"]}.html">'
        f'<div class="tutorial-hub-top">'
        f'<span class="tutorial-hub-num">CHAPTER {t["num"]} · {html.escape(t["tag"])}</span>'
        f'<span class="tutorial-hub-meta">{html.escape(t["time"])}</span>'
        f"</div>"
        f'<h3>{html.escape(t["fullTitle"])}</h3>'
        f'<p>{html.escape(t["desc"])}</p>'
        f"</a>"
        for t in TUTORIAL_TRACK
        if t["slug"] != "zero-to-hero"
    )

    return f"""<h1 id="step-by-step-tutorials">Step-by-Step Tutorials</h1>
<p>Every tutorial in <code>nexa</code> contains complete, standalone Python programs tested automatically in CI. Start with the comprehensive <strong>0 → Hero Full Tutorial</strong> below, browse the <a href="wiki.html">Documentation Wiki</a>, or dive into a focused topic guide.</p>
<div class="hero-course-banner">
  <div class="tutorial-hub-top">
    <span class="tutorial-hub-num">FEATURED FULL COURSE · 11 MODULES · 11 RUNNABLE APPS</span>
    <span class="badge-new">0 → Hero</span>
  </div>
  <h2><a href="zero-to-hero.html">Zero to Hero: The Complete <code>nexa</code> Masterclass →</a></h2>
  <p>Go from installing <code>nexa-ui</code> and opening your first 15-line native window all the way to building, testing, and freezing <strong>Pulse Studio</strong>—a multi-pane OOP desktop IDE &amp; telemetry workbench with docking, 50k virtualized grids, code &amp; diff editors, GFM checklists, live charts, flame profilers, and worker streams.</p>
  {pills_html}
  <div style="margin-top: 4px;">
    <a class="btn btn-primary" href="zero-to-hero.html">Start 0 → Hero Full Tutorial →</a>
  </div>
</div>
<h2 id="focused-deep-dive-guides">Focused Deep-Dive Guides</h2>
<div class="tutorials-hub-grid">{cards_html}</div>
<div class="changelog-entry" style="margin-top: 24px;">
  <h2 id="looking-for-widget-signatures">Looking for widget signatures or the Wiki index?</h2>
  <p>Browse the <a href="wiki.html">nexa Documentation Wiki</a>, filter widgets in the <a href="components.html">160+ Component Explorer</a>, or read the single-page <a href="components-reference.html">Complete API Reference</a>.</p>
</div>"""


def build_wiki_hub_html(hero_toc: list[dict[str, str]]) -> tuple[str, list[dict[str, str]]]:
    module_chips = "".join(
        f'<a class="wiki-chip-link" href="zero-to-hero.html#{html.escape(t["id"])}">{html.escape(t["title"].split(":")[0])}</a>'
        for t in hero_toc
        if re.match(r"^Module\s+\d+", t["title"], re.IGNORECASE)
    )

    examples_rows = "".join(
        f'<tr><td><a href="https://github.com/x017/nexa/blob/main/examples/{fname}" target="_blank" rel="noopener"><code>examples/{fname}</code></a></td>'
        f"<td><strong>{html.escape(label)}</strong></td>"
        f"<td>{html.escape(desc)}</td></tr>"
        for fname, label, desc in EXAMPLES_LIST
    )

    toc = [
        {"title": "Quick Jump & Installation", "id": "quick-jump-installation"},
        {"title": "Knowledge Base by Topic", "id": "knowledge-base-by-topic"},
        {"title": "UI Paradigms Matrix", "id": "ui-paradigms-matrix"},
        {"title": "Widget Domains Directory", "id": "widget-domains-directory"},
        {"title": "13 Runnable Examples", "id": "runnable-examples"},
    ]

    wiki_html = f"""<h1 id="nexa-documentation-wiki"><code>nexa</code> Documentation Wiki</h1>
<p>Central knowledge base for <strong><code>nexa</code></strong> (<code>pip install nexa-ui</code>, imported as <code>import nexa as ui</code>)—a zero-dependency Python port of <a href="https://github.com/yappologistic/CUI" target="_blank" rel="noopener">CUI</a> with 160+ native C99 desktop components, OpenGL 3.3 + multi-threaded SIMD software rendering, and 0% idle CPU.</p>

<div class="wiki-quick-bar" id="quick-jump-installation">
  <a class="wiki-pill primary" href="zero-to-hero.html">0 → Hero Full Course (11 Modules)</a>
  <a class="wiki-pill" href="getting-started.html">Quickstart (5 min)</a>
  <a class="wiki-pill" href="tutorials.html">All Tutorials Hub</a>
  <a class="wiki-pill" href="components.html">160+ Component Explorer</a>
  <a class="wiki-pill" href="components-reference.html">Full API Signatures</a>
  <a class="wiki-pill" href="https://github.com/x017/nexa/wiki" target="_blank" rel="noopener">GitHub Repo Wiki ↗</a>
</div>

<div class="code-panel">
  <div class="code-header"><span>bash · install &amp; verify</span><button class="copy-mini" data-copy-code="1" type="button">Copy</button></div>
  <pre><code>pip install nexa-ui
python3 -c "import nexa as ui; print(ui.__version__)"</code></pre>
</div>

<blockquote class="callout-warn"><p><strong>Important:</strong> Always install <strong><code>nexa-ui</code></strong> from PyPI (<code>pip install nexa-ui</code> or <code>uv add nexa-ui</code>), <strong>not</strong> the unrelated <code>nexa</code> package, and avoid naming a local file <code>nexa.py</code> or folder <code>nexa/</code>.</p></blockquote>

<h2 id="knowledge-base-by-topic">Knowledge Base by Topic</h2>
<div class="wiki-grid">
  <div class="wiki-card">
    <h3><span>Core Mental Model</span> <span class="badge-new">Start</span></h3>
    <p>Value-returning immediate mode, stable widget IDs (<code>label##id</code> &amp; <code>id_scope</code>), unconditional vs. conditional <code>with</code> scopes, and focus/submit transitions.</p>
    <div class="wiki-card-links">
      <a class="wiki-chip-link" href="getting-started.html#3-how-nexa-thinks-value-returning-immediate-mode">Value-Returning Model</a>
      <a class="wiki-chip-link" href="getting-started.html#4-widget-identity-id-id-scope">IDs &amp; Scopes</a>
      <a class="wiki-chip-link" href="getting-started.html#5-unconditional-vs-conditional-with-scopes">with Scopes</a>
    </div>
  </div>

  <div class="wiki-card">
    <h3><span>0 → Hero Masterclass</span> <span class="badge-new">11 Modules</span></h3>
    <p>Progressive 4-stage curriculum building 11 runnable desktop apps culminating in <strong>Pulse Studio</strong> (<code>examples/zero_to_hero.py</code>).</p>
    <div class="wiki-card-links">
      <a class="wiki-chip-link" href="zero-to-hero.html#how-this-tutorial-is-organized-complete-syntax-guide">Syntax Guide</a>
      {module_chips}
    </div>
  </div>

  <div class="wiki-card">
    <h3><span>Layouts, Docking &amp; Chrome</span> <span class="badge-new">v1.1</span></h3>
    <p>Sub-0.25ms Flexbox (<code>row</code>/<code>column</code>), CSS Grid, <code>FIT</code>/<code>FILL</code>/<code>GROW</code>/<code>PX</code>/<code>PCT</code>, draggable splits, multi-split <code>dockspace</code>, menu bars, toolbars &amp; path bars.</p>
    <div class="wiki-card-links">
      <a class="wiki-chip-link" href="zero-to-hero.html#module-1-layout-mastery-flexbox-responsive-grids-scroll-split-panes">Flex &amp; Grid</a>
      <a class="wiki-chip-link" href="zero-to-hero.html#module-3-desktop-chrome-menus-tabs-dialogs-sheets-command-palette">Menus &amp; Overlays</a>
      <a class="wiki-chip-link" href="zero-to-hero.html#module-5-studio-creative-tools-dockspace-node-graphs-curves-timelines-custom-sdf-canvas">Dockspace</a>
    </div>
  </div>

  <div class="wiki-card">
    <h3><span>Data Grids, Editors &amp; Charts</span> <span class="badge-new">1M+ Rows</span></h3>
    <p>Virtualized <code>data_grid</code>, hierarchical <code>tree_table</code>, syntax <code>code_editor</code>, Myers <code>diff_view</code>, CommonMark/GFM <code>markdown</code>, and 16 native chart types.</p>
    <div class="wiki-card-links">
      <a class="wiki-chip-link" href="zero-to-hero.html#module-4-high-density-data-markdown-code-editor-diffs-charts">Data &amp; Code Lab</a>
      <a class="wiki-chip-link" href="components-reference.html#10-data-virtual-lists-tables-grids-code-nexa-widgets-data">Data Signatures</a>
      <a class="wiki-chip-link" href="components-reference.html#11-charts-data-visualization-nexa-widgets-charts">16 Charts</a>
    </div>
  </div>

  <div class="wiki-card">
    <h3><span>OKLCH Theming, Fonts &amp; BiDi</span> <span class="badge-new">8 Accents</span></h3>
    <p>Smooth Light/Dark cross-fading, 8 perceptual OKLCH accents, 9 semantic tones, 34 live-editable theme tokens, custom <code>.ttf</code> fonts, 168 Lucide icons &amp; <code>--rtl</code> shaping.</p>
    <div class="wiki-card-links">
      <a class="wiki-chip-link" href="theming-and-styling.html#2-the-8-built-in-ui-accent-palettes">8 OKLCH Accents</a>
      <a class="wiki-chip-link" href="theming-and-styling.html#4-custom-brand-colors-live-token-overrides-perceptual-oklch">34 Tokens</a>
      <a class="wiki-chip-link" href="theming-and-styling.html#5-typography-custom-ttf-fonts-international-fallback">Fonts &amp; Icons</a>
    </div>
  </div>

  <div class="wiki-card">
    <h3><span>Async, Threads, Testing &amp; Shipping</span> <span class="badge-new">GIL-Free</span></h3>
    <p>Non-blocking <code>BackgroundRunner</code>, <code>Channel[T]</code>, <code>LogBuffer</code>, <code>AsyncBridge</code>, headless <code>pytest</code> PNG verification, custom GPU backends &amp; PyInstaller/Nuitka.</p>
    <div class="wiki-card-links">
      <a class="wiki-chip-link" href="concurrency-and-async.html">Workers &amp; Asyncio</a>
      <a class="wiki-chip-link" href="advanced-rendering-and-packaging.html#2-automated-headless-ui-testing-png-snapshots">Headless pytest</a>
      <a class="wiki-chip-link" href="advanced-rendering-and-packaging.html#4-minimal-stripped-builds-single-file-executables">Freeze Binaries</a>
    </div>
  </div>
</div>

<h2 id="ui-paradigms-matrix">UI Paradigms Matrix</h2>
<table>
  <thead>
    <tr><th>Paradigm</th><th>Entry Point</th><th>Best For</th><th>Guide</th></tr>
  </thead>
  <tbody>
    <tr><td><strong>Functional Closure</strong></td><td><code>ui.run(draw, ...)</code></td><td>Scripts, prototypes &amp; compact utilities (15–120 lines)</td><td><a href="tutorial-functional.html#lesson-1-top-level-functional-basics">Functional Lesson 1 →</a></td></tr>
    <tr><td><strong>Procedural Context</strong></td><td><code>with ui.App(...) as app:</code></td><td>Explicit frame loops, multi-module helpers &amp; interactive tests</td><td><a href="tutorial-functional.html#lesson-3-procedural-decomposition-plain-functions-state-dict">Procedural Lesson 3 →</a></td></tr>
    <tr><td><strong>Object-Oriented</strong></td><td><code>Application</code>, <code>Component</code>, <code>Router</code>, <code>Store</code></td><td>Large multi-view desktop studios with automatic ID isolation</td><td><a href="tutorial-oop.html">OOP Architecture →</a></td></tr>
    <tr><td><strong>Headless / BYO GPU</strong></td><td><code>SoftwareRenderer</code> / <code>CustomRenderer</code></td><td>CI screenshot testing, server PNG generation &amp; Vulkan/Metal/DX12</td><td><a href="advanced-rendering-and-packaging.html">GPU &amp; Headless →</a></td></tr>
  </tbody>
</table>

<h2 id="widget-domains-directory">Widget Domains Directory (160+ Components)</h2>
<table>
  <thead>
    <tr><th>Domain</th><th>Representative Widgets</th><th>Reference Section</th></tr>
  </thead>
  <tbody>
    <tr><td><strong>Layout &amp; Containers</strong></td><td><code>row</code>, <code>column</code>, <code>grid</code>, <code>stack</code>, <code>card</code>, <code>scroll</code>, <code>split</code></td><td><a href="components-reference.html#1-layout-containers-nexa-widgets-layout">§1 Layout →</a></td></tr>
    <tr><td><strong>Typography &amp; Actions</strong></td><td><code>heading</code>, <code>label</code>, <code>code</code>, <code>kbd</code>, <code>button</code>, <code>icon_button</code>, <code>button_group</code></td><td><a href="components-reference.html#2-text-typography-nexa-widgets-text">§2–3 Text &amp; Buttons →</a></td></tr>
    <tr><td><strong>Selection, Inputs &amp; Pickers</strong></td><td><code>checkbox</code>, <code>switch</code>, <code>slider</code>, <code>select</code>, <code>combobox</code>, <code>input</code>, <code>money_input</code>, <code>date_picker</code>, <code>color_picker</code></td><td><a href="components-reference.html#4-selection-controls-nexa-widgets-selection">§4–6 Controls &amp; Pickers →</a></td></tr>
    <tr><td><strong>Navigation, Overlays &amp; Feedback</strong></td><td><code>tabs</code>, <code>nav_item</code>, <code>dialog</code>, <code>sheet</code>, <code>popover</code>, <code>context_menu</code>, <code>command_palette</code>, <code>toast</code>, <code>badge</code>, <code>metric</code></td><td><a href="components-reference.html#7-navigation-nexa-widgets-navigation">§7–9 Overlays &amp; Status →</a></td></tr>
    <tr><td><strong>Data Grids, Markdown, Code &amp; Diff</strong></td><td><code>virtual_list</code>, <code>table</code>, <code>data_grid</code>, <code>tree_table</code>, <code>markdown</code>, <code>code_editor</code>, <code>diff_view</code>, <code>json_view</code></td><td><a href="components-reference.html#10-data-virtual-lists-tables-grids-code-nexa-widgets-data">§10 Data &amp; Code →</a></td></tr>
    <tr><td><strong>Charts &amp; Visualization</strong></td><td><code>line_chart</code>, <code>bar_chart</code>, <code>scatter_chart</code>, <code>donut_chart</code>, <code>radar_chart</code>, <code>treemap</code>, <code>sankey</code>, <code>heatmap</code>, <code>sparkline</code></td><td><a href="components-reference.html#11-charts-data-visualization-nexa-widgets-charts">§11 Charts →</a></td></tr>
    <tr><td><strong>Studio, Docking, Planning &amp; AI</strong></td><td><code>dockspace</code>, <code>path_bar</code>, <code>hex_view</code>, <code>flame_graph</code>, <code>curve_editor</code>, <code>gradient_editor</code>, <code>timeline_editor</code>, <code>node_editor</code>, <code>kanban</code>, <code>gantt</code>, <code>chat_composer</code>, <code>voice_orb</code></td><td><a href="components-reference.html#12-19-planning-ai-social-media-motion-chrome-tools-node-canvas">§12–19 Studio, AI &amp; Chrome →</a></td></tr>
  </tbody>
</table>

<h2 id="runnable-examples">13 Runnable Examples (<code>examples/</code>)</h2>
<p>Run any example locally with <code>python3 examples/&lt;name&gt;.py</code>:</p>
<table>
  <thead>
    <tr><th>File</th><th>Application</th><th>Highlights</th></tr>
  </thead>
  <tbody>
    {examples_rows}
  </tbody>
</table>"""
    return wiki_html, toc


def build_components_explorer_html() -> str:
    domains = [
        "All", "New in 1.1", "Layout", "Chrome & Dock", "Data & Code",
        "Tools & Studio", "Charts", "Planning", "AI & Social", "Controls & Overlays",
    ]
    chips_html = "".join(
        f'<button class="catalog-chip{" active" if idx == 0 else ""}" type="button" data-domain="{html.escape(d)}">{html.escape(d)}</button>'
        for idx, d in enumerate(domains)
    )
    badge_11 = ' <span class="badge-new">1.1</span>'
    cards_html = "".join(
        f'<div class="catalog-card" data-card-domain="{html.escape(it["domain"])}" data-card-new="{"1" if it["isNew"] else "0"}">'
        f'<div class="catalog-card-head">'
        f'<span class="catalog-card-sig">{html.escape(it["name"])}{badge_11 if it["isNew"] else ""}</span>'
        f'<span class="catalog-card-domain">{html.escape(it["domain"])}</span>'
        f"</div>"
        f'<code>{html.escape(it["sig"])}</code>'
        f'<p>{html.escape(it["desc"])}</p>'
        f"</div>"
        for it in CATALOG_ITEMS
    )
    return f"""<h1 id="interactive-component-explorer">Interactive Component Explorer <span class="badge-new">190+ Widgets</span></h1>
<p>Filter across all 22 native C99 widget domains, inspect Pythonic signatures, or jump to the full <a href="components-reference.html">Markdown Signature Reference →</a></p>
<div class="catalog-controls">
  <div class="catalog-search-row">
    <input id="catalog-filter-input" type="search" placeholder="Search dockspace, tree_table, diff_view, flame_graph, kanban, charts…" autocomplete="off" />
    <span class="catalog-count" id="catalog-count-label">{len(CATALOG_ITEMS)} shown</span>
  </div>
  <div class="catalog-filter-row" id="catalog-domain-chips">{chips_html}</div>
</div>
<div class="catalog-grid" id="catalog-cards-grid">{cards_html}</div>"""


def build_changelog_html() -> str:
    return """<h1 id="changelog">Changelog</h1>
<p>Release history for <code>nexa</code> (<code>nexa-ui</code> on PyPI) and its vendored C99 <a href="https://github.com/yappologistic/CUI" target="_blank" rel="noopener">CUI</a> core.</p>
<div class="changelog-entry">
  <h2 id="v1-4-0">v1.4.0 <span class="badge-new">Latest · CUI 1.4 Sync</span></h2>
  <ul>
    <li><strong>Instrument cluster</strong>: Added <code>ui.knob</code>, <code>ui.fader</code>, <code>ui.level_meter</code>, <code>ui.radial_gauge</code>, <code>ui.readout</code>, <code>ui.dot_display</code>, <code>ui.dot_chart</code>, and <code>ui.event_track</code> — every one returns the value the user dialed in.</li>
    <li><strong>Text, media &amp; files</strong>: Right-to-left layout and text (<code>direction=ui.TextDirection.RTL</code>), embedded <strong>emoji</strong> with <code>ui.emoji_picker</code> and color-emoji font loading, a scrollback-backed <code>ui.terminal</code> via <code>ui.TerminalBuffer</code>, <code>ui.file_browser</code> / <code>ui.file_picker</code> for real directories (with an in-tree <code>ui.fs_list</code>), <code>ui.image_viewer</code>, and <code>ui.cropper</code>.</li>
    <li><strong>Charts &amp; calendars</strong>: <code>ui.candlestick</code> for OHLC data plus <code>annotations=</code> on every chart (<code>ui.ChartAnnotation</code>), <code>ui.month_calendar</code> with events, and <code>ui.tour</code> guided app walks.</li>
    <li><strong>Developer tools (CUI 1.3)</strong>: <code>ui.problems</code>, <code>ui.pipeline</code>, <code>ui.trace_view</code>, <code>ui.waterfall</code>, <code>ui.graph_view</code>, <code>ui.commit_graph</code>, <code>ui.keymap</code>, <code>ui.test_explorer</code>, <code>ui.stack_trace</code>, <code>ui.blame</code>, <code>ui.coverage</code>, <code>ui.regex_tester</code>, <code>ui.request_bar</code>, <code>ui.api_explorer</code>, <code>ui.feature_flags</code>, <code>ui.uptime_bars</code>, <code>ui.time_histogram</code>, <code>ui.kv_editor</code>, <code>ui.query_builder</code>, and <code>ui.schedule_picker</code> — data in as plain dicts, results out as named tuples.</li>
    <li><strong>Context-free utilities</strong>: <code>ui.regex_search</code> (CUI's RE2-style engine with named groups), <code>ui.cron_next</code> / <code>ui.cron_describe</code>, <code>ui.url_params</code> / <code>ui.url_set_params</code>, <code>ui.http_reason</code> / <code>ui.http_method_name</code>, plus <code>ui.UI.request_wakeup</code>, <code>set_strings</code>/<code>get_strings</code>, <code>response_status</code>, and <code>is_software</code>.</li>
    <li><strong>Engine re-sync &amp; ABI hardening</strong>: <code>csrc/</code> moved to CUI <strong>v1.4.0</strong> (434 → 501 public functions, 208 → 304 structs); <code>tools/gen_abi.py</code> regenerates the ctypes mirrors from <code>cui.h</code> and an audit proves every mirrored struct matches the compiler's <code>sizeof</code>/offsets; <code>tools/gen_devtools_bridge.py</code> generates the struct-returning bridges so ctypes never passes a struct by value.</li>
  </ul>
</div>
<div class="changelog-entry">
  <h2 id="v1-1-0">v1.1.0 <span class="badge">CUI 1.1 Sync</span></h2>
  <ul>
    <li><strong>Multi-split Docking Workspaces</strong>: Added <code>ui.dockspace</code>, <code>ui.dock_panel</code>, <code>ui.dock_save</code>, and <code>ui.dock_load</code> with interactive tab dragging, split previews, and layout serialization.</li>
    <li><strong>Tree Table &amp; Editable Path Bar</strong>: Added virtualized multi-column <code>ui.tree_table</code> + <code>ui.tree_sort</code> and breadcrumb/editable <code>ui.path_bar</code> + <code>ui.path_bar_menu</code>.</li>
    <li><strong>Rich Markdown, Source Code Editor &amp; Diff Viewer</strong>: Added CommonMark/GFM <code>ui.markdown</code> (with interactive task checkboxes and <code>ui.markdown_apply_task</code>), multi-line syntax-highlighted <code>ui.code_editor</code>, and side-by-side/inline <code>ui.diff_view</code> + headless <code>ui.diff_compute</code> &amp; <code>ui.diff_words</code>.</li>
    <li><strong>Systems &amp; Creative Studio Widgets</strong>: Added binary <code>ui.hex_view</code>, profiler <code>ui.flame_graph</code> + <code>ui.flame_sort</code>, Bezier <code>ui.curve_editor</code> + <code>ui.curve_eval</code>, perceptual OKLab <code>ui.gradient_editor</code> + <code>ui.gradient_eval</code>, and multi-track <code>ui.timeline_editor</code>.</li>
    <li><strong>PyPI Distribution &amp; Complete Exports</strong>: Published as <code>pip install nexa-ui</code> with 505 typed top-level exports in <code>nexa.__all__</code>, cross-platform wheel builds, and optional <code>--rtl</code> BiDi + Arabic shaping.</li>
  </ul>
</div>
<div class="changelog-entry">
  <h2 id="v1-0-0">v1.0.0</h2>
  <ul>
    <li>Initial C99 + Python zero-dependency architecture covering 150+ immediate-mode components, OpenGL 3.3 + multi-threaded SIMD software renderer, Functional/Procedural/OOP paradigms, 8 OKLCH accents, and GIL-free <code>BackgroundRunner</code> / <code>asyncio</code> integration.</li>
  </ul>
</div>"""


def render_page_shell(
    *,
    page_title: str,
    meta_desc: str,
    active_nav: str,
    sidebar_html: str,
    article_html: str,
    toc_html: str,
    extra_head_script: str = "",
) -> str:
    def _nav_cls(key: str) -> str:
        return "nav-link active" if active_nav == key else "nav-link"

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(page_title)}</title>
  <meta name="description" content="{html.escape(meta_desc)}" />
  <link rel="icon" type="image/svg+xml" href="assets/favicon.svg?v={ASSET_VER}" />
  <link rel="stylesheet" href="assets/styles.css?v={ASSET_VER}" />
  <script>
    try {{
      const saved = localStorage.getItem("nexa_theme");
      const dark = saved ? saved === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
      document.documentElement.dataset.theme = dark ? "dark" : "light";
    }} catch (e) {{}}
  </script>{extra_head_script}
</head>
<body class="guide-mode">
  <!-- Sticky Top Bar with Reading Progress Hairline -->
  <header class="topbar">
    <div class="topbar-inner">
      <a class="brand" href="index.html">
        <svg class="brand-mark-svg" viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false">
          <path d="M12 3.4 L20.6 12 L12 20.6 L3.4 12 Z" stroke="currentColor" stroke-opacity="0.34" stroke-width="1.35" stroke-linejoin="round"/>
          <path fill-rule="evenodd" clip-rule="evenodd"
                d="M12 5.2 C12 9.4 14.6 12 18.8 12 C14.6 12 12 14.6 12 18.8 C12 14.6 9.4 12 5.2 12 C9.4 12 12 9.4 12 5.2 Z M12 9.8 L14.2 12 L12 14.2 L9.8 12 Z"
                fill="currentColor"/>
          <circle cx="12" cy="3.4" r="1.9" fill="var(--accent)"/>
          <circle cx="20.6" cy="12" r="1.7" fill="currentColor"/>
          <circle cx="12" cy="20.6" r="1.7" fill="currentColor"/>
          <circle cx="3.4" cy="12" r="1.7" fill="currentColor"/>
        </svg>
        <span>nexa</span>
        <span class="brand-badge">Docs</span>
      </a>
      <nav class="nav-links" aria-label="Primary">
        <a class="nav-link" href="index.html">Overview</a>
        <a class="{_nav_cls('wiki')}" data-nav="wiki" href="wiki.html">Wiki</a>
        <a class="{_nav_cls('guide')}" data-nav="guide" href="getting-started.html">Guide</a>
        <a class="{_nav_cls('tutorials')}" data-nav="tutorials" href="tutorials.html">Tutorials</a>
        <a class="{_nav_cls('components')}" data-nav="components" href="components.html">Components</a>
        <a class="{_nav_cls('changelog')}" data-nav="changelog" href="changelog.html">Changelog</a>
      </nav>
      <div class="topbar-right">
        <div class="accent-strip" id="header-accent-strip" title="Switch live OKLCH accent"></div>
        <a class="icon-btn" href="https://github.com/x017/nexa" target="_blank" rel="noopener" aria-label="Source on GitHub" title="Source on GitHub">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>
        </a>
        <button class="icon-btn" id="theme-toggle-btn" type="button" aria-label="Switch theme"></button>
      </div>
    </div>
    <div class="read-progress" id="read-progress"></div>
  </header>

  <!-- Documentation Layout Shell -->
  <div class="docs-shell">
    <!-- Left Chapter Navigation + Instant Filter -->
    <aside class="docs-sidebar" aria-label="Documentation chapters">
      <div class="search-box">
        <input id="docs-search-input" type="search" placeholder="Filter wiki, tutorials &amp; widgets…" autocomplete="off" />
        <span class="search-kbd">Ctrl K</span>
      </div>
      <div class="search-results" id="docs-search-results"></div>
      <nav id="docs-sidebar-nav">{sidebar_html}</nav>
    </aside>

    <!-- Main Content Area with Procedural Topographic Backdrop -->
    <div class="docs-content-grid docs-main-wrap">
      <div class="docs-art" id="docs-hero-art"></div>

      <div class="docs-page-inner">
        <main class="docs-main">
          <article class="prose" id="docs-article">
{article_html}
          </article>

          <!-- Subtle Closing Procedural Topographic Band -->
          <section class="home-cta compact" id="docs-cta-band">
            <div class="home-cta-body">
              <h2>Explore the 13 runnable examples</h2>
              <p>Every tutorial &amp; 1.1 studio pattern—including the complete <code>zero_to_hero.py</code> Pulse Studio capstone—is ready to run inside <code>examples/</code>.</p>
              <div class="hero-actions">
                <a class="btn btn-primary" href="https://github.com/x017/nexa/tree/main/examples" target="_blank" rel="noopener">Browse examples/ →</a>
                <a class="btn" href="wiki.html">Open Docs Wiki</a>
                <a class="btn" href="index.html">Back to Overview</a>
              </div>
            </div>
          </section>
        </main>

        <!-- Right Table of Contents -->
        <aside class="docs-toc" aria-label="On this page">
          <div class="toc-title">On this page</div>
          <nav id="docs-toc-links">{toc_html}</nav>
        </aside>
      </div>
    </div>
  </div>

  <script src="assets/search-index.js?v={ASSET_VER}" defer></script>
  <script src="assets/dither.js?v={ASSET_VER}" defer></script>
  <script src="assets/site.js?v={ASSET_VER}" defer></script>
</body>
</html>
"""


def build_bundle() -> None:
    parsed_chapters: list[dict] = []
    search_index: list[dict[str, str]] = []

    for slug, title, group, filename, wiki_name, nav_key in CHAPTERS:
        md_path = DOCS_DIR / filename
        raw_md = md_path.read_text(encoding="utf-8")
        rendered_html, toc, sections = markdown_to_html(raw_md)
        parsed_chapters.append({
            "slug": slug,
            "title": title,
            "group": group,
            "source": f"docs/{filename}",
            "wiki_name": wiki_name,
            "nav_key": nav_key,
            "html": rendered_html,
            "toc": toc,
        })
        for sec in sections:
            search_index.append({
                "page": f"{slug}.html",
                "chapter": title,
                "heading": sec["heading"],
                "anchor": sec["anchor"],
                "text": sec["snippet"],
            })

    # Add Wiki page sections to instant search index
    search_index.insert(0, {
        "page": "wiki.html",
        "chapter": "Docs Wiki",
        "heading": "Knowledge Base, Paradigms Matrix & 13 Examples",
        "anchor": "",
        "text": "Central nexa documentation wiki: installation, quickstart, paradigms matrix, 20 widget domains, and all 13 runnable examples.",
    })

    # 1. Write compact search-index.js
    search_js_path = DOCS_DIR / "assets" / "search-index.js"
    search_payload = json.dumps(search_index, ensure_ascii=False)
    search_js_path.write_text(
        "/* Auto-generated search index from docs/*.md by docs/build_docs_bundle.py */\n"
        f"window.NEXA_SEARCH = {search_payload};\n",
        encoding="utf-8",
    )

    # 2. Write each standalone pre-rendered Markdown chapter page (`<slug>.html`)
    for idx, ch in enumerate(parsed_chapters):
        prev_ch = parsed_chapters[idx - 1] if idx > 0 else None
        next_ch = parsed_chapters[idx + 1] if idx + 1 < len(parsed_chapters) else None
        track_html = render_tutorial_track_html(ch["slug"])
        prev_html = (
            f'<a class="pager-card prev" href="{prev_ch["slug"]}.html">'
            f'<span>← Previous</span><strong>{html.escape(prev_ch["title"])}</strong></a>'
            if prev_ch else "<div></div>"
        )
        next_html = (
            f'<a class="pager-card next" href="{next_ch["slug"]}.html">'
            f'<span>Next →</span><strong>{html.escape(next_ch["title"])}</strong></a>'
            if next_ch else "<div></div>"
        )
        pager_html = f'<div class="pager-nav">{prev_html}{next_html}</div>'
        toc_html = "".join(
            f'<a class="toc-link" href="#{html.escape(t["id"])}" data-anchor="{html.escape(t["id"])}">{html.escape(t["title"])}</a>'
            for t in ch["toc"]
        )
        page_html = render_page_shell(
            page_title=f"{ch['title']} — nexa Documentation",
            meta_desc=f"{ch['title']} — step-by-step guide and runnable Python examples for nexa (nexa-ui).",
            active_nav=ch["nav_key"],
            sidebar_html=render_sidebar_html(ch["slug"], parsed_chapters),
            article_html=track_html + ch["html"] + pager_html,
            toc_html=toc_html,
        )
        (DOCS_DIR / f"{ch['slug']}.html").write_text(page_html, encoding="utf-8")

    # 3. Write special static hub pages: `wiki.html`, `tutorials.html`, `components.html`, `changelog.html`, and `guide.html`
    hero_toc = parsed_chapters[0]["toc"]

    wiki_article, wiki_toc = build_wiki_hub_html(hero_toc)
    wiki_toc_html = "".join(
        f'<a class="toc-link" href="#{html.escape(t["id"])}" data-anchor="{html.escape(t["id"])}">{html.escape(t["title"])}</a>'
        for t in wiki_toc
    )
    (DOCS_DIR / "wiki.html").write_text(
        render_page_shell(
            page_title="Documentation Wiki — nexa",
            meta_desc="Complete nexa Documentation Wiki: installation, UI paradigms matrix, 11-module 0-to-Hero map, 20 widget domains, and 13 runnable Python examples.",
            active_nav="wiki",
            sidebar_html=render_sidebar_html("wiki", parsed_chapters),
            article_html=wiki_article,
            toc_html=wiki_toc_html,
        ),
        encoding="utf-8",
    )

    tutorials_article = build_tutorials_hub_html(hero_toc)
    tutorials_toc_html = "".join(
        f'<a class="toc-link" href="{t["slug"]}.html">{t["num"]}. {html.escape(t["short"])}</a>'
        for t in TUTORIAL_TRACK
    )
    (DOCS_DIR / "tutorials.html").write_text(
        render_page_shell(
            page_title="Tutorials — nexa Documentation",
            meta_desc="Step-by-step nexa Python UI tutorials: 11-module 0-to-Hero masterclass, Functional/Procedural closures, OOP Application/Router/Store, OKLCH theming, and asyncio.",
            active_nav="tutorials",
            sidebar_html=render_sidebar_html("tutorials", parsed_chapters),
            article_html=tutorials_article,
            toc_html=tutorials_toc_html,
        ),
        encoding="utf-8",
    )

    (DOCS_DIR / "components.html").write_text(
        render_page_shell(
            page_title="160+ Component Explorer — nexa Documentation",
            meta_desc="Interactive explorer for all 160+ native C99 desktop UI components in nexa across 20 widget domains.",
            active_nav="components",
            sidebar_html=render_sidebar_html("components", parsed_chapters),
            article_html=build_components_explorer_html(),
            toc_html='<a class="toc-link" href="components-reference.html">Full Markdown Signatures →</a>',
        ),
        encoding="utf-8",
    )

    (DOCS_DIR / "changelog.html").write_text(
        render_page_shell(
            page_title="Changelog — nexa Documentation",
            meta_desc="Release history and changelog for nexa (nexa-ui) and its C99 CUI core.",
            active_nav="changelog",
            sidebar_html=render_sidebar_html("changelog", parsed_chapters),
            article_html=build_changelog_html(),
            toc_html='<a class="toc-link" href="#v1-4-0" data-anchor="v1-4-0">v1.4.0</a><a class="toc-link" href="#v1-1-0" data-anchor="v1-1-0">v1.1.0</a><a class="toc-link" href="#v1-0-0" data-anchor="v1-0-0">v1.0.0</a>',
        ),
        encoding="utf-8",
    )

    # 4. `guide.html`: instant `<head>` hash redirector for legacy `guide.html#<slug>[--<anchor>]` URLs
    #    PLUS full pre-rendered Tutorials & Wiki Hub body as zero-JS fallback!
    known_pages = ["wiki", "tutorials", "components", "changelog", *[c["slug"] for c in parsed_chapters]]
    known_pages_json = json.dumps(known_pages)
    legacy_redirect_script = f"""
  <script>
    (function () {{
      var raw = (window.location.hash || "").replace(/^#/, "");
      if (!raw) return;
      var sep = raw.indexOf("--");
      var slug = sep >= 0 ? raw.slice(0, sep) : raw;
      var anchor = sep >= 0 ? raw.slice(sep + 2) : "";
      var pages = {known_pages_json};
      if (pages.indexOf(slug) >= 0) {{
        window.location.replace(slug + ".html" + (anchor ? "#" + anchor : ""));
      }}
    }})();
  </script>"""
    (DOCS_DIR / "guide.html").write_text(
        render_page_shell(
            page_title="Documentation & Tutorials — nexa",
            meta_desc="Complete step-by-step tutorials, Docs Wiki, interactive 160+ component explorer, and API reference for nexa.",
            active_nav="tutorials",
            sidebar_html=render_sidebar_html("tutorials", parsed_chapters),
            article_html=tutorials_article,
            toc_html=tutorials_toc_html,
            extra_head_script=legacy_redirect_script,
        ),
        encoding="utf-8",
    )

    # 5. Always keep committed `wiki/` directory in sync with `docs/*.md`
    export_github_wiki(DOCS_DIR.parent / "wiki")


def export_github_wiki(out_dir: pathlib.Path) -> list[pathlib.Path]:
    """Export GitHub-Wiki-ready Markdown files (`Home.md`, `_Sidebar.md`, `_Footer.md`, + 8 chapters)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    slug_to_wiki = {slug: wiki_name for slug, _, _, _, wiki_name, _ in CHAPTERS}
    written: list[pathlib.Path] = []

    def _rewrite_md_for_wiki(md_text: str) -> str:
        # 1. Rewrite relative screenshot images to raw.githubusercontent.com URLs
        def _img_repl(m: re.Match[str]) -> str:
            alt, src = m.group(1), m.group(2).strip()
            if src.startswith("assets/"):
                src = f"https://raw.githubusercontent.com/x017/nexa/main/docs/{src}"
            return f"![{alt}]({src})"

        out = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _img_repl, md_text)

        # 2. Rewrite internal chapter `.md` links outside fenced/inline code to GitHub Wiki page slugs
        def _lnk_repl(m: re.Match[str]) -> str:
            lbl, target = m.group(1), m.group(2).strip()
            if target.startswith(("http://", "https://", "#")):
                return m.group(0)
            anchor = ""
            if "#" in target:
                target, anchor = target.split("#", 1)
                anchor = f"#{anchor}"
            if target.endswith(".md"):
                stem = pathlib.Path(target).stem
                if stem in slug_to_wiki:
                    return f"[{lbl}]({slug_to_wiki[stem]}{anchor})"
            return m.group(0)

        parts = re.split(r"(```[\s\S]*?```|`[^`\n]+`)", out)
        for idx in range(0, len(parts), 2):
            parts[idx] = re.sub(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)", _lnk_repl, parts[idx])
        return "".join(parts)

    for slug, title, _group, filename, wiki_name, _nav in CHAPTERS:
        raw_md = (DOCS_DIR / filename).read_text(encoding="utf-8")
        p = out_dir / f"{wiki_name}.md"
        p.write_text(_rewrite_md_for_wiki(raw_md), encoding="utf-8")
        written.append(p)

    # Home.md
    examples_md = "\n".join(
        f"| [`examples/{fname}`](https://github.com/x017/nexa/blob/main/examples/{fname}) | **{label}** | {desc} |"
        for fname, label, desc in EXAMPLES_LIST
    )
    home_md = f"""# `nexa` Documentation Wiki

Welcome to the official **`nexa`** Wiki (`pip install nexa-ui`, imported in Python as `import nexa as ui`)—a zero-dependency Python port of [CUI](https://github.com/yappologistic/CUI) delivering **160+ native C99 desktop UI components**, sub-quarter-millisecond Flexbox/CSS-Grid layout, OpenGL 3.3 + multi-threaded SIMD CPU rendering, and **0% idle CPU**.

- **Interactive Web Docs & Wiki**: <http://parsa.x017.ir/nexa/wiki.html>
- **PyPI Package**: <https://pypi.org/project/nexa-ui/>
- **Source Repository**: <https://github.com/x017/nexa>

```bash
pip install nexa-ui
```

> **Important:** Always install **`nexa-ui`** (`pip install nexa-ui` or `uv add nexa-ui`), **not** the unrelated `nexa` package on PyPI, and avoid naming a local folder `nexa/` or script `nexa.py`.

---

## Chapters & Step-by-Step Courses

| # | Wiki Page | Summary |
|---|---|---|
| **00** | **[0 to Hero: Full Tutorial](Zero-to-Hero)** | Complete 11-module masterclass from a 15-line starter window to building **Pulse Studio** (`examples/zero_to_hero.py`). |
| **01** | **[Getting Started](Getting-Started)** | Installation, opening your first native window, value-returning immediate mode, widget IDs (`##`), and `with` scopes. |
| **02** | **[Functional & Procedural](Functional-and-Procedural)** | Closures with `ui.run(draw)`, procedural `ctx: ui.UI` decomposition, manual frame loops & a Budget Tracker app. |
| **03** | **[Object-Oriented Architecture](Object-Oriented-Architecture)** | `Application`, auto-scoped `Component`, `View`, `Router`, reactive `Store[T]` & an Incident Response Console. |
| **04** | **[Theming, Accents & Icons](Theming-Accents-and-Icons)** | Light/Dark modes, all 8 perceptual OKLCH accents, 9 semantic tones, 34 live tokens, `.ttf` fonts & 168 Lucide icons. |
| **05** | **[Concurrency & Asyncio](Concurrency-and-Asyncio)** | GIL-free `BackgroundRunner` threads & token streams, `Channel[T]`, `LogBuffer`, cooperative `asyncio` & `AsyncBridge`. |
| **06** | **[Canvas, GPU & Packaging](Canvas-GPU-and-Packaging)** | SDF vector `canvas`, headless `pytest` PNG verification, `CustomRenderer` GPU integration, `--rtl` shaping & PyInstaller/Nuitka. |
| **API** | **[190+ Components Reference](Components-Reference)** | Complete Python signatures, enum values, result dataclasses, and scope rules across all 20 widget domains. |

---

## 13 Runnable Examples (`examples/`)

| Example | Title | Highlights |
|---|---|---|
{examples_md}
"""
    home_path = out_dir / "Home.md"
    home_path.write_text(home_md, encoding="utf-8")
    written.append(home_path)

    sidebar_md = """### `nexa` Wiki

- **[Home](Home)**
- **[Live Web Wiki ↗](http://parsa.x017.ir/nexa/wiki.html)**

#### Start Here
- **[0 → Hero Full Tutorial](Zero-to-Hero)**
- **[Getting Started (5 min)](Getting-Started)**

#### Step-by-Step Guides
- **[Functional & Procedural](Functional-and-Procedural)**
- **[Object-Oriented (OOP)](Object-Oriented-Architecture)**
- **[Theming, Accents & Icons](Theming-Accents-and-Icons)**
- **[Concurrency & Asyncio](Concurrency-and-Asyncio)**
- **[Canvas, GPU & Packaging](Canvas-GPU-and-Packaging)**

#### API Reference
- **[190+ Components Reference](Components-Reference)**
"""
    sidebar_path = out_dir / "_Sidebar.md"
    sidebar_path.write_text(sidebar_md, encoding="utf-8")
    written.append(sidebar_path)

    footer_md = (
        "`nexa v1.4.0` · `pip install nexa-ui` · "
        "[Web Docs & Wiki](http://parsa.x017.ir/nexa/wiki.html) · "
        "[PyPI](https://pypi.org/project/nexa-ui/) · "
        "[GitHub](https://github.com/x017/nexa)\n"
    )
    footer_path = out_dir / "_Footer.md"
    footer_path.write_text(footer_md, encoding="utf-8")
    written.append(footer_path)

    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Build static docs/wiki HTML pages and optional GitHub Wiki export.")
    parser.add_argument("--export-wiki", type=pathlib.Path, default=None, help="Directory to write GitHub Wiki .md files.")
    args = parser.parse_args()

    build_bundle()
    search_kb = (DOCS_DIR / "assets" / "search-index.js").stat().st_size / 1024.0
    print(f"Built 13 static HTML docs/wiki pages + search-index.js ({search_kb:.1f} KB)")

    if args.export_wiki is not None:
        files = export_github_wiki(args.export_wiki)
        print(f"Exported {len(files)} GitHub Wiki Markdown files to {args.export_wiki}")


if __name__ == "__main__":
    main()
