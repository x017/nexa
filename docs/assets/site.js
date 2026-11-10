/* ==========================================================================
   nexa Interactive Theme, Accent, Topographic Woodcut & Docs Portal Controller
   ========================================================================== */

(function () {
  "use strict";

  // Exact 8 built-in CUI OKLCH Accent palettes (0..7)
  const ACCENTS = [
    { key: "NEUTRAL", id: 0, label: "Neutral", dark: "#e8e8e8", darkFg: "#111215", light: "#1d1d1d", lightFg: "#ffffff" },
    { key: "VIOLET",  id: 1, label: "Violet",  dark: "#a78bff", darkFg: "#13092b", light: "#7747ff", lightFg: "#ffffff" },
    { key: "BLUE",    id: 2, label: "Blue",    dark: "#6ba3ff", darkFg: "#071428", light: "#0562ef", lightFg: "#ffffff" },
    { key: "GREEN",   id: 3, label: "Green",   dark: "#53dca6", darkFg: "#052216", light: "#00864b", lightFg: "#ffffff" },
    { key: "AMBER",   id: 4, label: "Amber",   dark: "#ffcb62", darkFg: "#261800", light: "#f3ad20", lightFg: "#1c1200" },
    { key: "ORANGE",  id: 5, label: "Orange",  dark: "#ffad5e", darkFg: "#261000", light: "#c25300", lightFg: "#ffffff" },
    { key: "CORAL",   id: 6, label: "Coral",   dark: "#ff9386", darkFg: "#280906", light: "#d1403a", lightFg: "#ffffff" },
    { key: "ROSE",    id: 7, label: "Rose",    dark: "#ff8bc5", darkFg: "#280718", light: "#d23286", lightFg: "#ffffff" },
  ];

  const ICON_SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>';
  const ICON_MOON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>';

  const SHOWCASES = [
    {
      id: "zero_to_hero",
      label: "Pulse Studio (0→Hero)",
      title: "Pulse Studio — 0-to-Hero Capstone (1240×820)",
      img: "assets/screenshots/zero_to_hero.png",
      caption: "Built step-by-step in the 0→Hero Full Tutorial: OOP Application + Store, multi-split dockspace, tree table, code & diff editors, GFM runbook, live telemetry & profiler.",
      file: "examples/zero_to_hero.py",
    },
    {
      id: "workbench",
      label: "Workbench 1.1",
      title: "Workbench Studio — nexa 1.1 (1240×855)",
      img: "assets/screenshots/workbench.png",
      caption: "New in 1.1: Multi-split dockspace, path bar, tree table, syntax code editor, diff viewer, profiler flame graph, Bezier curve & OKLab gradient editors, and NLE timeline.",
      file: "examples/workbench.py",
    },
    {
      id: "gallery",
      label: "Nodes & Canvas",
      title: "Gallery & Studio — nexa (1200×780)",
      img: "assets/screenshots/gallery.png",
      caption: "Desktop menu bar, toolbar, dirty document tabs, Bezier node graph, typed property inspector & C-backed log console.",
      file: "examples/gallery.py",
    },
    {
      id: "dashboard",
      label: "Data & Analytics",
      title: "Larkspur Analytics — nexa (1140×740)",
      img: "assets/screenshots/dashboard.png",
      caption: "Animated rolling KPIs, sparklines, smooth cubic area chart, donut breakdown, filter bar & 250-row virtualized data grid.",
      file: "examples/dashboard.py",
    },
    {
      id: "tracker",
      label: "Planning",
      title: "Tracker — nexa (1100×700)",
      img: "assets/screenshots/tracker.png",
      caption: "Light-mode drag-and-drop Kanban board, interactive Gantt timeline, 7-day week schedule & live team presence rings.",
      file: "examples/tracker.py",
    },
    {
      id: "assistant",
      label: "AI & Streaming",
      title: "Muse AI — nexa (1160×740)",
      img: "assets/screenshots/assistant.png",
      caption: "Non-blocking BackgroundRunner token streaming, model picker, context ring meter, execution plan & procedural voice orb.",
      file: "examples/assistant.py",
    },
    {
      id: "finance",
      label: "Charts & Finance",
      title: "Finance — nexa (1080×720)",
      img: "assets/screenshots/finance.png",
      caption: "Live scrolling market ticker, rolling odometer counter, proportional Treemap, split bar, Sankey diagram & trading heatmap.",
      file: "examples/finance.py",
    },
    {
      id: "settings",
      label: "OOP & 8 Accents",
      title: "Settings — nexa OOP (980×680)",
      img: "assets/screenshots/settings.png",
      caption: "Object-oriented Application + Router + View + Component architecture showcasing all 8 built-in OKLCH Accent presets.",
      file: "examples/settings.py",
    },
  ];

  const TUTORIAL_TRACK = [
    { num: "00", slug: "zero-to-hero", short: "0 → Hero", fullTitle: "Zero to Hero: The Complete nexa Masterclass", time: "45 min", tag: "Full 11-Module Course", desc: "End-to-end masterclass from your first 15-line window through layouts, forms, chrome, 50k data grids, studio canvases, OOP, OKLCH, async workers & building Pulse Studio." },
    { num: "01", slug: "getting-started", short: "Start", fullTitle: "Getting Started & Mental Model", time: "5 min", tag: "Core Model", desc: "Install nexa, open your first native window, and learn value-returning widgets, IDs, and scopes." },
    { num: "02", slug: "tutorial-functional", short: "Functional", fullTitle: "Functional & Procedural Coding", time: "12 min", tag: "ui.run & ctx", desc: "Build concise closures with ui.run(draw), decompose procedural helpers, and create a complete Budget Tracker." },
    { num: "03", slug: "tutorial-oop", short: "OOP", fullTitle: "Object-Oriented Architecture", time: "15 min", tag: "Component & Store", desc: "Scale multi-screen apps with Application, auto-scoped Component classes, Router, View, and reactive Store[T]." },
    { num: "04", slug: "theming-and-styling", short: "Theming", fullTitle: "Theming, OKLCH Accents & Icons", time: "8 min", tag: "8 OKLCH Accents", desc: "Master Light & Dark modes, all 8 perceptual OKLCH accents, 34 semantic tokens, custom .ttf fonts & 168 Lucide icons." },
    { num: "05", slug: "concurrency-and-async", short: "Async & Threads", fullTitle: "Concurrency, Asyncio & Networking", time: "10 min", tag: "GIL-Free", desc: "Run worker pools, token streams, thread-safe Channel[T], LogBuffer, and cooperative asyncio without dropping 60fps." },
    { num: "06", slug: "advanced-rendering-and-packaging", short: "GPU & Packaging", fullTitle: "Vector Canvas, Custom GPU & Packaging", time: "10 min", tag: "CI & Freezing", desc: "Vector canvas drawing, headless pytest screenshot verification, custom GPU backends, --rtl shaping & PyInstaller/Nuitka." },
  ];

  // Interactive Component Catalog items (highlights + full coverage across all 20 domains)
  const CATALOG_ITEMS = [
    // New in 1.1
    { name: "dockspace", sig: "ui.dockspace(id, *, layout=None, width=None, height=None)", domain: "Chrome & Dock", isNew: true, desc: "Multi-split tabbed docking workspace with interactive drag-to-dock drop targets and layout DSL." },
    { name: "dock_panel", sig: "ui.dock_panel(title, is_open=None, *, icon=None, dirty=False)", domain: "Chrome & Dock", isNew: true, desc: "Closable, dirty-aware dockable panel inside an active dockspace; pairs with dock_save() and dock_load()." },
    { name: "tree_table", sig: "ui.tree_table(id, columns, nodes, *, sort=None, guides=True, labels=None)", domain: "Data & Code", isNew: true, desc: "Virtualized multi-column hierarchical tree-grid with lazy child loading, indent guides, and type-ahead search." },
    { name: "path_bar", sig: "ui.path_bar(id, segments, *, icon=None, menus=False) -> PathBarResult", domain: "Chrome & Dock", isNew: true, desc: "Editable file-manager / IDE breadcrumb address bar with click-to-edit path input and segment popup menus." },
    { name: "markdown", sig: "ui.markdown(id, text, *, streaming=False, compact=False) -> MarkdownResult", domain: "Data & Code", isNew: true, desc: "CommonMark + GFM renderer with headings, tables, fenced syntax blocks, GitHub alerts, and interactive task checkboxes." },
    { name: "code_editor", sig: "ui.code_editor(id, text, *, lang=None, height=320) -> CodeEditorResult", domain: "Data & Code", isNew: true, desc: "Multi-line source editor with syntax highlighting, undo/redo history, bracket matching, and Ctrl+F find bar." },
    { name: "diff_view", sig: "ui.diff_view(id, old_text, new_text, *, mode=DiffMode.SPLIT) -> DiffResult", domain: "Data & Code", isNew: true, desc: "Side-by-side or unified inline diff viewer with intraline word highlights, hunk folding, and headless diff_compute()." },
    { name: "hex_view", sig: "ui.hex_view(id, data, selection=None, *, ranges=None, editable=False) -> HexResult", domain: "Tools & Studio", isNew: true, desc: "Virtualized binary hex + ASCII inspector with colored tone annotations and zero-copy bytearray nibble editing." },
    { name: "flame_graph", sig: "ui.flame_graph(id, spans, *, view=None, selected=None) -> FlameResult", domain: "Tools & Studio", isNew: true, desc: "Interactive profiler flame / icicle chart with wheel zoom, drag pan, span selection, and C99 flame_sort()." },
    { name: "curve_editor", sig: "ui.curve_editor(id, keys, *, show_playhead=False) -> CurveResult", domain: "Tools & Studio", isNew: true, desc: "2D cubic Bezier, linear & step keyframe curve editor with tangent handles and standalone curve_eval()." },
    { name: "gradient_editor", sig: "ui.gradient_editor(id, stops, *, selected=None) -> GradientResult", domain: "Tools & Studio", isNew: true, desc: "Perceptual OKLab multi-stop color ramp editor with stop color/location/opacity controls and gradient_eval()." },
    { name: "timeline_editor", sig: "ui.timeline_editor(id, tracks, time, *, start=0, end=10, fps=30) -> TimelineEditorResult", domain: "Tools & Studio", isNew: true, desc: "Multi-track keyframe dope sheet and NLE clip timeline with playhead scrubbing, mute/lock toggles, and clip trimming." },
    // Core Layout, Chrome, Data, Charts, Planning, AI, Controls & Overlays
    { name: "row / column / grid / stack", sig: "ui.row(**box_opts) / ui.column(**box_opts) / ui.grid(columns=...)", domain: "Layout", isNew: false, desc: "Sub-quarter-millisecond Flexbox & responsive CSS-Grid containers supporting FIT, FILL, GROW, PX, and PCT sizing." },
    { name: "split & scroll", sig: "ui.split(id, ratio, *, vertical=False) / ui.scroll(id, *, sticky_bottom=False)", domain: "Layout", isNew: false, desc: "Interactive draggable split panes and smooth virtualizable scroll containers with optional edge fades." },
    { name: "menu_bar / toolbar / status_bar / doc_tabs", sig: "ui.menu_bar() / ui.toolbar() / ui.status_bar() / ui.doc_tabs(...)", domain: "Chrome & Dock", isNew: false, desc: "Complete desktop application chrome with keyboard mnemonics, toggle tools, progress items, and reorderable dirty tabs." },
    { name: "data_grid", sig: "ui.data_grid(id, columns, row_count, *, hide_checkboxes=False, anchor=None)", domain: "Data & Code", isNew: false, desc: "Spreadsheet-grade virtualized grid with column priority auto-hiding, range selection, sorting, and inline cell editing." },
    { name: "virtual_list & table", sig: "ui.virtual_list(id, count, row_h) / ui.table(id, columns, ...)", domain: "Data & Code", isNew: false, desc: "O(visible) 1,000,000-row virtual list scope and striped sortable data tables." },
    { name: "code_block & json_view", sig: "ui.code_block(id, code, *, lang='python') / ui.json_view(id, json_text)", domain: "Data & Code", isNew: false, desc: "Read-only syntax-highlighted source blocks with copy header and interactive collapsible JSON tree inspector." },
    { name: "node_editor & canvas", sig: "ui.node_editor(id, view) / ui.canvas(id, width, height)", domain: "Tools & Studio", isNew: false, desc: "Pan/zoom Bezier node graph editor with minimap and immediate SDF vector drawing canvas (lines, arcs, polygons, text)." },
    { name: "inspector & log_view", sig: "ui.inspector(id) / ui.prop_float(...) / ui.log_view(id, LogBuffer)", domain: "Tools & Studio", isNew: false, desc: "Typed property inspector (float, int, vec2/3/4, enum, color, bool) and thread-safe C ring-buffer log console." },
    { name: "line_chart / bar_chart / scatter_chart", sig: "ui.line_chart(...) / ui.bar_chart(...) / ui.scatter_chart(...)", domain: "Charts", isNew: false, desc: "Smooth cubic area/line charts, stacked/grouped/horizontal bars, and bubble scatter plots with hover crosshairs." },
    { name: "donut / radar / treemap / sankey / heatmap", sig: "ui.donut_chart(...) / ui.treemap(...) / ui.sankey(...) / ui.heatmap(...)", domain: "Charts", isNew: false, desc: "16 native chart widgets including gauges, funnels, waffles, split bars, activity rings, sparklines, and GitHub calendar heatmaps." },
    { name: "kanban / gantt / week_calendar", sig: "ui.kanban(id) / ui.gantt(id, tasks, ...) / ui.week_calendar(...)", domain: "Planning", isNew: false, desc: "Drag-and-drop Kanban boards with WIP limits, interactive Gantt timelines, and 7-day week event schedules." },
    { name: "chat_composer / reasoning / tool_call / voice_orb", sig: "ui.chat_composer(...) / ui.reasoning(...) / ui.voice_orb(...)", domain: "AI & Social", isNew: false, desc: "Streaming AI interfaces: markdown chat bubbles, model picker, token context ring, agent plans, citations & reactive voice orb." },
    { name: "button / input / select / command_palette / dialog", sig: "ui.button(...) / ui.input(...) / ui.command_palette(...) / ui.dialog(...)", domain: "Controls & Overlays", isNew: false, desc: "60+ tactile form controls, date/color pickers, OTP/money inputs, sheets, popovers, toasts, and Ctrl+K command palette." },
  ];

  const PARADIGMS = {
    functional: {
      file: "hello_functional.py",
      guideLink: "guide.html#tutorial-functional",
      guideLabel: "Read Functional Tutorial →",
      code: `<span class="tok-kw">import</span> <span class="tok-cls">nexa</span> <span class="tok-kw">as</span> ui

<span class="tok-kw">def</span> main() -> <span class="tok-kw">None</span>:
    count = <span class="tok-num">0</span>
    name = <span class="tok-str">"world"</span>

    <span class="tok-kw">def</span> draw() -> <span class="tok-kw">None</span>:
        <span class="tok-kw">nonlocal</span> count, name
        <span class="tok-kw">with</span> ui.column(width=ui.<span class="tok-cls">FILL</span>, height=ui.<span class="tok-cls">FILL</span>, pad=<span class="tok-num">24</span>, gap=<span class="tok-num">14</span>, bg=ui.<span class="tok-cls">Color</span>.<span class="tok-cls">BACKGROUND</span>):
            ui.heading(<span class="tok-str">f"Hello, {name or 'stranger'}!"</span>, level=<span class="tok-num">1</span>)
            name = ui.input(<span class="tok-str">"name"</span>, name, label=<span class="tok-str">"Your name"</span>, clearable=<span class="tok-kw">True</span>)

            <span class="tok-kw">with</span> ui.row(gap=<span class="tok-num">10</span>, align=ui.<span class="tok-cls">Align</span>.<span class="tok-cls">CENTER</span>):
                <span class="tok-kw">if</span> ui.button(<span class="tok-str">"Increment"</span>, variant=ui.<span class="tok-cls">ButtonVariant</span>.<span class="tok-cls">PRIMARY</span>, icon=ui.<span class="tok-cls">Icon</span>.<span class="tok-cls">PLUS</span>):
                    count += <span class="tok-num">1</span>
                ui.badge(<span class="tok-str">f"Count: {count}"</span>, tone=ui.<span class="tok-cls">Tone</span>.<span class="tok-cls">ACCENT</span>)

    ui.run(draw, title=<span class="tok-str">"Functional Quickstart"</span>, width=<span class="tok-num">540</span>, height=<span class="tok-num">320</span>, accent=ui.<span class="tok-cls">Accent</span>.<span class="tok-cls">BLUE</span>)

<span class="tok-kw">if</span> __name__ == <span class="tok-str">"__main__"</span>:
    main()`,
    },
    procedural: {
      file: "ledger_procedural.py",
      guideLink: "guide.html#tutorial-functional",
      guideLabel: "Read Procedural Guide →",
      code: `<span class="tok-kw">import</span> <span class="tok-cls">nexa</span> <span class="tok-kw">as</span> ui

<span class="tok-kw">def</span> render_sidebar(ctx: ui.<span class="tok-cls">UI</span>, st: dict) -> <span class="tok-kw">None</span>:
    <span class="tok-kw">with</span> ctx.column(width=<span class="tok-num">210</span>, height=ui.<span class="tok-cls">FILL</span>, bg=ui.<span class="tok-cls">Color</span>.<span class="tok-cls">SURFACE_MUTED</span>, pad=<span class="tok-num">12</span>, gap=<span class="tok-num">4</span>):
        <span class="tok-kw">for</span> i, label <span class="tok-kw">in</span> enumerate([<span class="tok-str">"Overview"</span>, <span class="tok-str">"Metrics"</span>, <span class="tok-str">"Logs"</span>]):
            <span class="tok-kw">if</span> ctx.nav_item(label, selected=(st[<span class="tok-str">"tab"</span>] == i), group=<span class="tok-str">"nav"</span>):
                st[<span class="tok-str">"tab"</span>] = i

<span class="tok-kw">def</span> render_main(ctx: ui.<span class="tok-cls">UI</span>, st: dict) -> <span class="tok-kw">None</span>:
    <span class="tok-kw">with</span> ctx.column(width=ui.<span class="tok-cls">FILL</span>, height=ui.<span class="tok-cls">FILL</span>, pad=<span class="tok-num">24</span>, gap=<span class="tok-num">14</span>):
        st[<span class="tok-str">"query"</span>] = ctx.search(<span class="tok-str">"q"</span>, st[<span class="tok-str">"query"</span>], placeholder=<span class="tok-str">"Filter metrics..."</span>)
        ctx.metric(<span class="tok-str">"Throughput"</span>, <span class="tok-str">"124,800 req/s"</span>, delta=<span class="tok-num">14.2</span>, spark=[<span class="tok-num">82</span>, <span class="tok-num">95</span>, <span class="tok-num">108</span>, <span class="tok-num">124</span>])

<span class="tok-kw">def</span> main() -> <span class="tok-kw">None</span>:
    state = {<span class="tok-str">"tab"</span>: <span class="tok-num">0</span>, <span class="tok-str">"query"</span>: <span class="tok-str">""</span>}
    <span class="tok-kw">with</span> ui.<span class="tok-cls">App</span>(<span class="tok-str">"Procedural App"</span>, width=<span class="tok-num">820</span>, height=<span class="tok-num">480</span>, theme=ui.<span class="tok-cls">ThemeMode</span>.<span class="tok-cls">DARK</span>) <span class="tok-kw">as</span> app:
        <span class="tok-kw">while</span> app.frame(wait=<span class="tok-kw">True</span>):
            <span class="tok-kw">with</span> app.ui.row(width=ui.<span class="tok-cls">FILL</span>, height=ui.<span class="tok-cls">FILL</span>, bg=ui.<span class="tok-cls">Color</span>.<span class="tok-cls">BACKGROUND</span>):
                render_sidebar(app.ui, state)
                render_main(app.ui, state)

<span class="tok-kw">if</span> __name__ == <span class="tok-str">"__main__"</span>:
    main()`,
    },
    oop: {
      file: "studio_oop.py",
      guideLink: "guide.html#tutorial-oop",
      guideLabel: "Read OOP Architecture Tutorial →",
      code: `<span class="tok-kw">import</span> <span class="tok-cls">nexa</span> <span class="tok-kw">as</span> ui

<span class="tok-kw">class</span> <span class="tok-cls">PipelineCard</span>(ui.<span class="tok-cls">Component</span>):
    <span class="tok-kw">def</span> __init__(self, key: str, title: str) -> <span class="tok-kw">None</span>:
        super().__init__(key)  <span class="tok-com"># Auto-pushes ID scope — zero collisions!</span>
        self.title = title
        self.count = <span class="tok-num">0</span>

    <span class="tok-kw">def</span> build(self, ctx: ui.<span class="tok-cls">UI</span>) -> <span class="tok-kw">None</span>:
        <span class="tok-kw">with</span> ctx.card(pad=<span class="tok-num">18</span>, gap=<span class="tok-num">10</span>, width=ui.<span class="tok-cls">GROW</span>(<span class="tok-num">1</span>)):
            ctx.heading(self.title, level=<span class="tok-num">4</span>)
            <span class="tok-kw">if</span> ctx.button(<span class="tok-str">"Increment"</span>, icon=ui.<span class="tok-cls">Icon</span>.<span class="tok-cls">PLUS</span>, variant=ui.<span class="tok-cls">ButtonVariant</span>.<span class="tok-cls">PRIMARY</span>):
                self.count += <span class="tok-num">1</span>
            ctx.secondary(<span class="tok-str">f"Completed jobs: {self.count}"</span>)

<span class="tok-kw">class</span> <span class="tok-cls">StudioApp</span>(ui.<span class="tok-cls">Application</span>):
    <span class="tok-kw">def</span> __init__(self) -> <span class="tok-kw">None</span>:
        super().__init__(<span class="tok-str">"OOP Studio"</span>, width=<span class="tok-num">760</span>, height=<span class="tok-num">380</span>, theme=ui.<span class="tok-cls">ThemeMode</span>.<span class="tok-cls">DARK</span>, accent=ui.<span class="tok-cls">Accent</span>.<span class="tok-cls">GREEN</span>)

    <span class="tok-kw">def</span> setup(self) -> <span class="tok-kw">None</span>:
        self.left = <span class="tok-cls">PipelineCard</span>(<span class="tok-str">"pipe_a"</span>, <span class="tok-str">"Ingestion Cluster"</span>)
        self.right = <span class="tok-cls">PipelineCard</span>(<span class="tok-str">"pipe_b"</span>, <span class="tok-str">"Inference Workers"</span>)

    <span class="tok-kw">def</span> build(self, ctx: ui.<span class="tok-cls">UI</span>) -> <span class="tok-kw">None</span>:
        <span class="tok-kw">with</span> ctx.row(width=ui.<span class="tok-cls">FILL</span>, height=ui.<span class="tok-cls">FILL</span>, pad=<span class="tok-num">24</span>, gap=<span class="tok-num">16</span>, bg=ui.<span class="tok-cls">Color</span>.<span class="tok-cls">BACKGROUND</span>):
            self.left(ctx)
            self.right(ctx)

<span class="tok-kw">if</span> __name__ == <span class="tok-str">"__main__"</span>:
    <span class="tok-cls">StudioApp</span>().run()`,
    },
  };

  function hexToRgba(hex, alpha) {
    const h = hex.replace("#", "");
    const r = parseInt(h.slice(0, 2), 16);
    const g = parseInt(h.slice(2, 4), 16);
    const b = parseInt(h.slice(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function storageGet(key) {
    try {
      return localStorage.getItem(key);
    } catch (e) {
      return null;
    }
  }

  function storageSet(key, val) {
    try {
      localStorage.setItem(key, val);
    } catch (e) {}
  }

  const savedTheme = storageGet("nexa_theme");
  let currentTheme =
    savedTheme === "dark" || savedTheme === "light"
      ? savedTheme
      : matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  let currentAccent = storageGet("nexa_accent") || "VIOLET";
  if (!ACCENTS.some((a) => a.key === currentAccent)) currentAccent = "BLUE";

  function applyThemeAndAccent() {
    document.documentElement.setAttribute("data-theme", currentTheme);
    document.documentElement.setAttribute("data-accent", currentAccent);
    const acc = ACCENTS.find((a) => a.key === currentAccent) || ACCENTS[2];
    const hex = currentTheme === "dark" ? acc.dark : acc.light;
    const fg = currentTheme === "dark" ? acc.darkFg : acc.lightFg;
    const root = document.documentElement.style;
    root.setProperty("--accent", hex);
    root.setProperty("--accent-fg", fg);
    root.setProperty("--accent-subtle", hexToRgba(hex, currentTheme === "dark" ? 0.15 : 0.10));
    root.setProperty("--accent-ring", hexToRgba(hex, currentTheme === "dark" ? 0.35 : 0.26));

    const themeBtn = document.getElementById("theme-toggle-btn");
    if (themeBtn) {
      themeBtn.innerHTML = currentTheme === "dark" ? ICON_SUN : ICON_MOON;
      themeBtn.title = currentTheme === "dark" ? "Switch to light mode" : "Switch to dark mode";
    }

    document.querySelectorAll(".accent-dot").forEach((el) => {
      const a = ACCENTS.find((x) => x.key === el.dataset.accent);
      if (a) {
        el.style.backgroundColor = currentTheme === "dark" ? a.dark : a.light;
        el.classList.toggle("active", a.key === currentAccent);
      }
    });

    document.querySelectorAll(".accent-card").forEach((el) => {
      const a = ACCENTS.find((x) => x.key === el.dataset.accent);
      if (a) {
        const curHex = currentTheme === "dark" ? a.dark : a.light;
        el.classList.toggle("active", a.key === currentAccent);
        const sw = el.querySelector(".swatch-pill");
        const hexEl = el.querySelector(".accent-hex");
        if (sw) sw.style.backgroundColor = curHex;
        if (hexEl) hexEl.textContent = `ui.Accent.${a.key} · ${curHex}`;
      }
    });

    const liveCodeEl = document.getElementById("active-accent-code");
    if (liveCodeEl) {
      liveCodeEl.textContent = `accent=ui.Accent.${acc.key}  # ${hex} (${currentTheme} mode)`;
    }
  }

  function initHeaderAndScrollChrome() {
    const strip = document.getElementById("header-accent-strip");
    if (strip) {
      strip.innerHTML = ACCENTS.map(
        (a) =>
          `<button class="accent-dot" type="button" data-accent="${a.key}" title="ui.Accent.${a.key} (${a.label})" aria-label="${a.label}"></button>`
      ).join("");
      strip.addEventListener("click", (ev) => {
        const btn = ev.target.closest(".accent-dot");
        if (!btn) return;
        currentAccent = btn.dataset.accent;
        storageSet("nexa_accent", currentAccent);
        applyThemeAndAccent();
      });
    }

    const themeBtn = document.getElementById("theme-toggle-btn");
    if (themeBtn) {
      themeBtn.addEventListener("click", () => {
        currentTheme = currentTheme === "dark" ? "light" : "dark";
        storageSet("nexa_theme", currentTheme);
        applyThemeAndAccent();
      });
    }

    const progressEl = document.getElementById("read-progress");
    let scrollScheduled = false;
    const updateScroll = () => {
      scrollScheduled = false;
      document.body.classList.toggle("scrolled", window.scrollY > 6);
      if (progressEl) {
        const max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
        const ratio = Math.min(1, Math.max(0, window.scrollY / max));
        progressEl.style.transform = `scaleX(${ratio.toFixed(4)})`;
      }
    };
    window.addEventListener(
      "scroll",
      () => {
        if (!scrollScheduled) {
          scrollScheduled = true;
          requestAnimationFrame(updateScroll);
        }
      },
      { passive: true }
    );
    updateScroll();
  }

  // Pointer spotlight tracking on bento & guide cards
  function initCardSpotlights() {
    document.querySelectorAll(".bento-card, .guide-card").forEach((card) => {
      card.addEventListener(
        "pointermove",
        (ev) => {
          const r = card.getBoundingClientRect();
          card.style.setProperty("--mx", `${(ev.clientX - r.left).toFixed(1)}px`);
          card.style.setProperty("--my", `${(ev.clientY - r.top).toFixed(1)}px`);
        },
        { passive: true }
      );
    });
  }

  // Mount Procedural 3D Topographic Woodcut & Stipple Engraving
  function initDitherBackgrounds() {
    if (typeof window.ditherArt !== "function") return;

    const homeHeroArt = document.getElementById("home-hero-art");
    if (homeHeroArt) {
      const heroDither = window.ditherArt({
        scene: "horizon",
        loop: true,
        maxScrollY: 820,
      });
      homeHeroArt.appendChild(heroDither);

      if (!matchMedia("(prefers-reduced-motion: reduce)").matches) {
        let ticking = false;
        window.addEventListener(
          "scroll",
          () => {
            if (ticking) return;
            ticking = true;
            requestAnimationFrame(() => {
              ticking = false;
              const y = Math.min(window.scrollY, 860);
              heroDither.style.transform = `translate3d(0, ${(y * 0.32).toFixed(1)}px, 0)`;
              heroDither.style.opacity = String(Math.max(0, 1 - y / 760).toFixed(3));
            });
          },
          { passive: true }
        );
      }
    }

    const homeCtaBand = document.getElementById("home-cta-band");
    if (homeCtaBand) {
      homeCtaBand.prepend(
        window.ditherArt({
          scene: "basin",
          reveal: "view",
          loop: true,
        })
      );
    }

    // On guide.html, static woodcut render uses 0% background CPU while reading tutorials
    const docsHeroArt = document.getElementById("docs-hero-art");
    if (docsHeroArt) {
      docsHeroArt.appendChild(
        window.ditherArt({
          scene: "horizon",
          loop: false,
        })
      );
    }

    const docsCtaBand = document.getElementById("docs-cta-band");
    if (docsCtaBand) {
      docsCtaBand.prepend(
        window.ditherArt({
          scene: "basin",
          reveal: "view",
          loop: false,
        })
      );
    }
  }

  function copyTextToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text).catch(() => fallbackCopyText(text));
    }
    return fallbackCopyText(text);
  }

  function fallbackCopyText(text) {
    return new Promise((resolve, reject) => {
      try {
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.setAttribute("readonly", "");
        ta.style.position = "fixed";
        ta.style.top = "-9999px";
        ta.style.left = "-9999px";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        const ok = document.execCommand("copy");
        document.body.removeChild(ta);
        if (ok) resolve();
        else reject(new Error("execCommand copy failed"));
      } catch (err) {
        reject(err);
      }
    });
  }

  function bindCopyButtons(scope) {
    (scope || document).querySelectorAll("[data-copy-text], [data-copy-code]").forEach((btn) => {
      if (btn.dataset.boundCopy) return;
      btn.dataset.boundCopy = "1";
      btn.addEventListener("click", () => {
        let text = btn.dataset.copyText || "";
        if (!text && btn.dataset.copyCode) {
          const panel = btn.closest(".code-panel");
          const codeEl = panel && panel.querySelector("pre code");
          text = codeEl ? codeEl.textContent : "";
        }
        if (!text) return;
        copyTextToClipboard(text)
          .then(() => {
            const prev = btn.dataset.origLabel || btn.textContent;
            btn.dataset.origLabel = prev;
            btn.textContent = "Copied";
            setTimeout(() => {
              btn.textContent = prev;
            }, 1400);
          })
          .catch(() => {});
      });
    });
  }

  // ---- Landing Page Initializer ----
  function initLandingPage() {
    const tabsRoot = document.getElementById("showcase-tabs");
    const imgEl = document.getElementById("showcase-img");
    const winTitle = document.getElementById("showcase-win-title");
    const capText = document.getElementById("showcase-caption-text");
    const capLink = document.getElementById("showcase-source-link");

    if (tabsRoot && imgEl) {
      const preloaded = new Set();
      function warmImage(url) {
        if (!url || preloaded.has(url)) return;
        preloaded.add(url);
        const im = new Image();
        im.decoding = "async";
        im.src = url;
      }

      function selectShowcase(id) {
        const item = SHOWCASES.find((s) => s.id === id) || SHOWCASES[0];
        imgEl.src = item.img;
        imgEl.alt = item.label;
        if (winTitle) winTitle.textContent = item.title;
        if (capText) capText.textContent = item.caption;
        if (capLink) {
          capLink.textContent = `Source: ${item.file} →`;
          capLink.href = `https://github.com/x017/nexa/blob/main/${item.file}`;
        }
        tabsRoot.querySelectorAll(".tab-pill").forEach((b) => {
          b.classList.toggle("active", b.dataset.showcase === item.id);
        });
      }

      tabsRoot.innerHTML = SHOWCASES.map(
        (s) => `<button class="tab-pill" type="button" data-showcase="${s.id}">${s.label}</button>`
      ).join("");
      tabsRoot.addEventListener("click", (ev) => {
        const b = ev.target.closest(".tab-pill");
        if (b) selectShowcase(b.dataset.showcase);
      });
      tabsRoot.addEventListener(
        "pointerover",
        (ev) => {
          const b = ev.target.closest(".tab-pill");
          if (!b) return;
          const s = SHOWCASES.find((x) => x.id === b.dataset.showcase);
          if (s) warmImage(s.img);
        },
        { passive: true }
      );
      selectShowcase("workbench");
    }

    const pSelector = document.getElementById("paradigm-selector");
    const pCode = document.getElementById("paradigm-code");
    const pFile = document.getElementById("paradigm-filename");
    const pGuideLink = document.getElementById("paradigm-guide-link");

    if (pSelector && pCode) {
      function setParadigm(key) {
        const p = PARADIGMS[key] || PARADIGMS.functional;
        pCode.innerHTML = p.code;
        if (pFile) pFile.textContent = p.file;
        if (pGuideLink) {
          pGuideLink.href = p.guideLink;
          pGuideLink.textContent = p.guideLabel;
        }
        pSelector.querySelectorAll(".paradigm-card").forEach((c) => {
          c.classList.toggle("active", c.dataset.paradigm === key);
        });
      }
      pSelector.addEventListener("click", (ev) => {
        const card = ev.target.closest(".paradigm-card");
        if (card) setParadigm(card.dataset.paradigm);
      });
      setParadigm("functional");
    }

    const accGrid = document.getElementById("accents-interactive-grid");
    if (accGrid) {
      accGrid.innerHTML = ACCENTS.map(
        (a) => `<button class="accent-card" type="button" data-accent="${a.key}">
          <span class="swatch-pill"></span>
          <span class="accent-meta">
            <strong>${a.label}</strong>
            <code class="accent-hex">ui.Accent.${a.key}</code>
          </span>
        </button>`
      ).join("");
      accGrid.addEventListener("click", (ev) => {
        const card = ev.target.closest(".accent-card");
        if (!card) return;
        currentAccent = card.dataset.accent;
        storageSet("nexa_accent", currentAccent);
        applyThemeAndAccent();
      });
    }
  }

  // ---- Special Views for `guide.html` (#tutorials, #components, #changelog) ----
  function buildTutorialsHubHtml(docsData) {
    const heroChapter = docsData && Array.isArray(docsData.chapters) ? docsData.chapters.find((c) => c.slug === "zero-to-hero") : null;
    const syntaxToc =
      heroChapter && Array.isArray(heroChapter.toc)
        ? heroChapter.toc.find((t) => t.title.toLowerCase().includes("syntax guide"))
        : null;
    const syntaxPill = syntaxToc
      ? `<a class="module-jump-pill" href="#zero-to-hero--${escapeHtml(syntaxToc.id)}">Syntax &amp; Sections Guide</a>`
      : "";
    const modulePills =
      heroChapter && Array.isArray(heroChapter.toc)
        ? syntaxPill +
          heroChapter.toc
            .filter((t) => /^Module\s+\d+/i.test(t.title))
            .map((t) => {
              const shortLbl = t.title.split(":")[0].replace("Module ", "M").trim();
              return `<a class="module-jump-pill" href="#zero-to-hero--${escapeHtml(t.id)}">${escapeHtml(shortLbl)}</a>`;
            })
            .join("")
        : "";

    const cards = TUTORIAL_TRACK.filter((t) => t.slug !== "zero-to-hero")
      .map(
        (t) => `<a class="tutorial-hub-card" href="#${t.slug}" data-doc-link="${t.slug}">
        <div class="tutorial-hub-top">
          <span class="tutorial-hub-num">CHAPTER ${t.num} · ${escapeHtml(t.tag)}</span>
          <span class="tutorial-hub-meta">${escapeHtml(t.time)}</span>
        </div>
        <h3>${escapeHtml(t.fullTitle)}</h3>
        <p>${escapeHtml(t.desc)}</p>
      </a>`
      )
      .join("");

    return `
      <h1>Step-by-Step Tutorials</h1>
      <p>Every tutorial in <code>nexa</code> contains complete, standalone Python programs tested automatically in CI. Start with the comprehensive <strong>0 → Hero Full Tutorial</strong> below, or dive into a focused topic guide.</p>
      <div class="hero-course-banner">
        <div class="tutorial-hub-top">
          <span class="tutorial-hub-num">FEATURED FULL COURSE · 11 MODULES · 11 RUNNABLE APPS</span>
          <span class="badge-new">0 → Hero</span>
        </div>
        <h2><a href="#zero-to-hero" data-doc-link="zero-to-hero" style="color: inherit; text-decoration: none;">Zero to Hero: The Complete <code>nexa</code> Masterclass →</a></h2>
        <p>Go from installing <code>nexa</code> and opening your first 15-line native window all the way to building, testing, and freezing <strong>Pulse Studio</strong>—a multi-pane OOP desktop IDE &amp; telemetry workbench with docking, 50k virtualized grids, code &amp; diff editors, GFM checklists, live charts, flame profilers, and worker streams.</p>
        ${modulePills ? `<div class="module-jump-strip">${modulePills}</div>` : ""}
        <div style="margin-top: 4px;">
          <a class="btn btn-primary" href="#zero-to-hero" data-doc-link="zero-to-hero">Start 0 → Hero Full Tutorial →</a>
        </div>
      </div>
      <h2>Focused Deep-Dive Guides</h2>
      <div class="tutorials-hub-grid">${cards}</div>
      <div class="changelog-entry" style="margin-top: 24px;">
        <h2>Looking for widget signatures?</h2>
        <p>Explore the interactive <a href="#components" data-doc-link="components">160+ Component Explorer</a> (including all 12 new CUI 1.1 components) or read the single-page <a href="#components-reference" data-doc-link="components-reference">Complete API Reference</a>.</p>
      </div>
    `;
  }

  function buildComponentCatalogHtml() {
    const domains = ["All", "New in 1.1", "Layout", "Chrome & Dock", "Data & Code", "Tools & Studio", "Charts", "Planning", "AI & Social", "Controls & Overlays"];
    return `
      <h1>Interactive Component Explorer <span class="badge-new">160+ Widgets</span></h1>
      <p>Filter across all 20 native C99 widget domains, inspect Pythonic signatures, or jump to the full <a href="#components-reference" data-doc-link="components-reference">Markdown Signature Reference →</a></p>
      <div class="catalog-controls">
        <div class="catalog-search-row">
          <input id="catalog-filter-input" type="search" placeholder="Search dockspace, tree_table, diff_view, flame_graph, kanban, charts…" autocomplete="off" />
          <span class="catalog-count" id="catalog-count-label"></span>
        </div>
        <div class="catalog-filter-row" id="catalog-domain-chips">
          ${domains
            .map(
              (d, i) =>
                `<button class="catalog-chip${i === 0 ? " active" : ""}" type="button" data-domain="${escapeHtml(d)}">${escapeHtml(d)}</button>`
            )
            .join("")}
        </div>
      </div>
      <div class="catalog-grid" id="catalog-cards-grid"></div>
    `;
  }

  function mountCatalogInteractivity(root) {
    const input = root.querySelector("#catalog-filter-input");
    const chips = root.querySelector("#catalog-domain-chips");
    const grid = root.querySelector("#catalog-cards-grid");
    const countLbl = root.querySelector("#catalog-count-label");
    if (!input || !chips || !grid) return;

    let activeDomain = "All";
    function update() {
      const q = input.value.trim().toLowerCase();
      const filtered = CATALOG_ITEMS.filter((it) => {
        if (activeDomain === "New in 1.1" && !it.isNew) return false;
        if (activeDomain !== "All" && activeDomain !== "New in 1.1" && it.domain !== activeDomain) return false;
        if (!q) return true;
        return (
          it.name.toLowerCase().includes(q) ||
          it.sig.toLowerCase().includes(q) ||
          it.desc.toLowerCase().includes(q) ||
          it.domain.toLowerCase().includes(q)
        );
      });

      if (countLbl) countLbl.textContent = `${filtered.length} shown`;
      grid.innerHTML = filtered
        .map(
          (it) => `<div class="catalog-card">
            <div class="catalog-card-head">
              <span class="catalog-card-sig">${escapeHtml(it.name)} ${it.isNew ? '<span class="badge-new">1.1</span>' : ""}</span>
              <span class="catalog-card-domain">${escapeHtml(it.domain)}</span>
            </div>
            <code>${escapeHtml(it.sig)}</code>
            <p>${escapeHtml(it.desc)}</p>
          </div>`
        )
        .join("");
    }

    input.addEventListener("input", update);
    chips.addEventListener("click", (ev) => {
      const btn = ev.target.closest(".catalog-chip");
      if (!btn) return;
      activeDomain = btn.dataset.domain || "All";
      chips.querySelectorAll(".catalog-chip").forEach((b) => b.classList.toggle("active", b === btn));
      update();
    });
    update();
  }

  function buildChangelogHtml() {
    return `
      <h1>Changelog</h1>
      <p>Release history for <code>nexa</code> and its vendored C99 <a href="https://github.com/yappologistic/CUI" target="_blank" rel="noopener">CUI</a> core.</p>
      <div class="changelog-entry">
        <h2>v1.1.0 <span class="badge-new">Latest · CUI 1.1 Sync</span></h2>
        <ul>
          <li><strong>Multi-split Docking Workspaces</strong>: Added <code>ui.dockspace</code>, <code>ui.dock_panel</code>, <code>ui.dock_save</code>, and <code>ui.dock_load</code> with interactive tab dragging, split previews, and layout serialization.</li>
          <li><strong>Tree Table &amp; Editable Path Bar</strong>: Added virtualized multi-column <code>ui.tree_table</code> + <code>ui.tree_sort</code> and breadcrumb/editable <code>ui.path_bar</code> + <code>ui.path_bar_menu</code>.</li>
          <li><strong>Rich Markdown, Source Code Editor &amp; Diff Viewer</strong>: Added CommonMark/GFM <code>ui.markdown</code> (with interactive task checkboxes and <code>chat_message(..., markdown=True)</code>), multi-line syntax-highlighted <code>ui.code_editor</code>, and side-by-side/inline <code>ui.diff_view</code> + headless <code>ui.diff_compute</code> &amp; <code>ui.diff_words</code>.</li>
          <li><strong>Systems &amp; Creative Studio Widgets</strong>: Added binary <code>ui.hex_view</code>, profiler <code>ui.flame_graph</code> + <code>ui.flame_sort</code>, Bezier <code>ui.curve_editor</code> + <code>ui.curve_eval</code>, perceptual OKLab <code>ui.gradient_editor</code> + <code>ui.gradient_eval</code>, and multi-track <code>ui.timeline_editor</code>.</li>
          <li><strong>Optional Bidirectional &amp; Arabic Shaping</strong>: Build with <code>python3 -m nexa.build --rtl</code> (or <code>NEXA_TEXT_SHAPING=1</code>) for UAX #9 BiDi paragraphs and Arabic-script OpenType glyph shaping.</li>
          <li><strong>New Flagship Example</strong>: Added <code>examples/workbench.py</code> combining all 1.1 studio &amp; developer widgets.</li>
        </ul>
      </div>
      <div class="changelog-entry">
        <h2>v1.0.0</h2>
        <ul>
          <li>Initial C99 + Python zero-dependency architecture covering 150+ immediate-mode components, OpenGL 3.3 + multi-threaded SIMD software renderer, Functional/Procedural/OOP paradigms, 8 OKLCH accents, and GIL-free <code>BackgroundRunner</code> / <code>asyncio</code> integration.</li>
        </ul>
      </div>
    `;
  }

  // ---- Documentation Portal (`guide.html`) Initializer ----
  function initDocsPortal() {
    const docsData = window.NEXA_DOCS || window.YAPPS_DOCS;
    const navRoot = document.getElementById("docs-sidebar-nav");
    const articleRoot = document.getElementById("docs-article");
    const tocRoot = document.getElementById("docs-toc-links");
    const searchInput = document.getElementById("docs-search-input");
    const searchResults = document.getElementById("docs-search-results");
    if (!navRoot || !articleRoot) return;

    document.body.classList.add("guide-mode");
    if (!docsData || !Array.isArray(docsData.chapters)) {
      articleRoot.innerHTML = `<h1>Documentation Bundle Unavailable</h1><p>Run <code>python3 docs/build_docs_bundle.py</code> to build <code>docs/assets/docs-data.js</code>.</p>`;
      return;
    }

    const chapters = docsData.chapters;
    const SPECIAL_SLUGS = new Set(["tutorials", "components", "changelog"]);
    let activeSlug = "";

    function updateTopbarActive(slug) {
      document.querySelectorAll(".topbar .nav-link").forEach((a) => {
        const navKey = a.dataset.nav || "";
        let isAct = false;
        if (navKey === "guide") isAct = slug === "getting-started";
        else if (navKey === "tutorials")
          isAct =
            slug === "zero-to-hero" ||
            slug === "tutorials" ||
            slug === "tutorial-functional" ||
            slug === "tutorial-oop" ||
            slug === "theming-and-styling" ||
            slug === "concurrency-and-async" ||
            slug === "advanced-rendering-and-packaging";
        else if (navKey === "components") isAct = slug === "components" || slug === "components-reference";
        else if (navKey === "changelog") isAct = slug === "changelog";
        a.classList.toggle("active", isAct);
      });
    }

    function renderSidebar(currentSlug) {
      const groups = [];
      chapters.forEach((ch) => {
        let g = groups.find((x) => x.name === ch.group);
        if (!g) {
          g = { name: ch.group, items: [] };
          groups.push(g);
        }
        g.items.push(ch);
      });

      const specialHtml =
        `<div class="sidebar-group-title">Explore</div>` +
        `<a class="sidebar-link${currentSlug === "tutorials" ? " active" : ""}" href="#tutorials" data-chapter="tutorials">All Tutorials Overview</a>` +
        `<a class="sidebar-link${currentSlug === "components" ? " active" : ""}" href="#components" data-chapter="components">Component Explorer <span class="badge-new">1.1</span></a>` +
        `<a class="sidebar-link${currentSlug === "changelog" ? " active" : ""}" href="#changelog" data-chapter="changelog">Changelog</a>`;

      const chaptersHtml = groups
        .map(
          (g) =>
            `<div class="sidebar-group-title">${escapeHtml(g.name)}</div>` +
            g.items
              .map((ch) => {
                const isAct = ch.slug === currentSlug;
                const subHtml =
                  isAct && ch.toc && ch.toc.length
                    ? `<div class="sidebar-sublinks">${ch.toc
                        .map(
                          (t) =>
                            `<a class="sidebar-sublink" href="#${ch.slug}--${t.id}" data-anchor="${t.id}">${escapeHtml(t.title)}</a>`
                        )
                        .join("")}</div>`
                    : "";
                const badgeHtml = ch.slug === "zero-to-hero" ? ' <span class="badge-new">FULL</span>' : "";
                return `<a class="sidebar-link${isAct ? " active" : ""}" href="#${ch.slug}" data-chapter="${ch.slug}">${escapeHtml(ch.title)}${badgeHtml}</a>${subHtml}`;
              })
              .join("")
        )
        .join("");

      navRoot.innerHTML = specialHtml + chaptersHtml;
    }

    function buildTutorialTrackBar(currentSlug) {
      if (!TUTORIAL_TRACK.some((t) => t.slug === currentSlug)) return "";
      return `<div class="tutorial-track" aria-label="Tutorial curriculum">
        <span class="tutorial-track-label">Tutorials</span>
        ${TUTORIAL_TRACK.map(
          (t) =>
            `<a class="track-step${t.slug === currentSlug ? " active" : ""}" href="#${t.slug}" data-doc-link="${t.slug}">
              <span class="track-step-num">${t.num}</span>
              <span>${escapeHtml(t.short)}</span>
            </a>`
        ).join("")}
      </div>`;
    }

    function renderChapter(slug, anchorId) {
      if (SPECIAL_SLUGS.has(slug)) {
        activeSlug = slug;
        renderSidebar(slug);
        updateTopbarActive(slug);
        if (slug === "tutorials") {
          articleRoot.innerHTML = buildTutorialsHubHtml(docsData);
          document.title = "Tutorials — nexa Documentation";
          if (tocRoot) tocRoot.innerHTML = TUTORIAL_TRACK.map((t) => `<a class="toc-link" href="#${t.slug}" data-doc-link="${t.slug}">${t.num}. ${escapeHtml(t.short)}</a>`).join("");
        } else if (slug === "components") {
          articleRoot.innerHTML = buildComponentCatalogHtml();
          document.title = "160+ Component Explorer — nexa Documentation";
          mountCatalogInteractivity(articleRoot);
          if (tocRoot) tocRoot.innerHTML = `<a class="toc-link" href="#components-reference" data-doc-link="components-reference">Full Markdown Signatures →</a>`;
        } else {
          articleRoot.innerHTML = buildChangelogHtml();
          document.title = "Changelog — nexa Documentation";
          if (tocRoot) tocRoot.innerHTML = "";
        }
        window.scrollTo({ top: 0, behavior: "auto" });
        return;
      }

      const idx = chapters.findIndex((c) => c.slug === slug);
      const ch = idx >= 0 ? chapters[idx] : chapters[0];
      const realIdx = idx >= 0 ? idx : 0;

      if (activeSlug !== ch.slug) {
        activeSlug = ch.slug;
        renderSidebar(ch.slug);
        updateTopbarActive(ch.slug);

        const prev = realIdx > 0 ? chapters[realIdx - 1] : null;
        const next = realIdx < chapters.length - 1 ? chapters[realIdx + 1] : null;
        const trackHtml = buildTutorialTrackBar(ch.slug);

        const pagerHtml = `<div class="pager-nav">
          ${
            prev
              ? `<a class="pager-card prev" href="#${prev.slug}" data-doc-link="${prev.slug}">
                   <span>← Previous</span><strong>${escapeHtml(prev.title)}</strong>
                 </a>`
              : `<div></div>`
          }
          ${
            next
              ? `<a class="pager-card next" href="#${next.slug}" data-doc-link="${next.slug}">
                   <span>Next →</span><strong>${escapeHtml(next.title)}</strong>
                 </a>`
              : `<div></div>`
          }
        </div>`;

        articleRoot.innerHTML = trackHtml + ch.html + pagerHtml;
        document.title = `${ch.title} — nexa Documentation`;

        if (tocRoot) {
          tocRoot.innerHTML = ch.toc
            .map(
              (t) =>
                `<a class="toc-link" href="#${ch.slug}--${t.id}" data-anchor="${t.id}">${escapeHtml(t.title)}</a>`
            )
            .join("");
        }

        bindCopyButtons(articleRoot);
      }

      if (anchorId) {
        const target = document.getElementById(anchorId);
        if (target) {
          target.scrollIntoView({ behavior: "smooth", block: "start" });
          return;
        }
      }
      window.scrollTo({ top: 0, behavior: "auto" });
    }

    function updateActiveTocOnScroll() {
      const headings = Array.from(articleRoot.querySelectorAll("h2[id]"));
      if (!headings.length) return;
      let activeId = headings[0].id;
      const threshold = 130;
      for (let i = 0; i < headings.length; i++) {
        if (headings[i].getBoundingClientRect().top <= threshold) {
          activeId = headings[i].id;
        } else {
          break;
        }
      }
      if (tocRoot) {
        tocRoot.querySelectorAll(".toc-link[data-anchor]").forEach((el) => {
          el.classList.toggle("active", el.dataset.anchor === activeId);
        });
      }
      navRoot.querySelectorAll(".sidebar-sublink[data-anchor]").forEach((el) => {
        el.classList.toggle("active", el.dataset.anchor === activeId);
      });
    }

    let spyTicking = false;
    window.addEventListener(
      "scroll",
      () => {
        if (!spyTicking) {
          spyTicking = true;
          requestAnimationFrame(() => {
            spyTicking = false;
            updateActiveTocOnScroll();
          });
        }
      },
      { passive: true }
    );

    function syncFromHash() {
      const raw = (window.location.hash || "").replace(/^#/, "");
      if (!raw) {
        renderChapter(chapters[0].slug, "");
        updateActiveTocOnScroll();
        return;
      }
      const sep = raw.indexOf("--");
      const slug = sep >= 0 ? raw.slice(0, sep) : raw;
      const anchor = sep >= 0 ? raw.slice(sep + 2) : "";
      renderChapter(slug, anchor);
      updateActiveTocOnScroll();
    }

    window.addEventListener("hashchange", syncFromHash);

    document.addEventListener("click", (ev) => {
      const docLink = ev.target.closest("[data-doc-link], [data-chapter]");
      if (docLink) {
        ev.preventDefault();
        const slug = docLink.dataset.docLink || docLink.dataset.chapter;
        const targetHash = `#${slug}`;
        if (window.location.hash !== targetHash) {
          window.location.hash = targetHash;
        } else {
          renderChapter(slug, "");
          updateActiveTocOnScroll();
        }
        return;
      }
      const anchorLink = ev.target.closest("[data-anchor]");
      if (anchorLink) {
        ev.preventDefault();
        const aid = anchorLink.dataset.anchor;
        history.replaceState(null, "", `#${activeSlug}--${aid}`);
        const el = document.getElementById(aid);
        if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });

    if (searchInput && searchResults) {
      searchInput.addEventListener("input", () => {
        const q = searchInput.value.trim().toLowerCase();
        if (q.length < 2) {
          searchResults.classList.remove("open");
          searchResults.innerHTML = "";
          return;
        }
        const docHits = docsData.search
          .filter(
            (item) =>
              item.heading.toLowerCase().includes(q) ||
              item.text.toLowerCase().includes(q) ||
              item.chapter.toLowerCase().includes(q)
          )
          .slice(0, 8)
          .map((h) => ({
            href: h.anchor ? `#${h.slug}--${h.anchor}` : `#${h.slug}`,
            title: `${h.chapter} · ${h.heading}`,
            sub: `${h.text.slice(0, 95)}…`,
          }));

        const catHits = CATALOG_ITEMS.filter(
          (it) => it.name.toLowerCase().includes(q) || it.sig.toLowerCase().includes(q)
        )
          .slice(0, 4)
          .map((it) => ({
            href: "#components",
            title: `Widget · ${it.name}${it.isNew ? " (1.1)" : ""}`,
            sub: it.sig,
          }));

        const allHits = [...catHits, ...docHits].slice(0, 10);

        if (!allHits.length) {
          searchResults.innerHTML = `<div class="search-hit"><span>No matches for "${escapeHtml(q)}"</span></div>`;
        } else {
          searchResults.innerHTML = allHits
            .map(
              (h) => `<a class="search-hit" href="${h.href}">
                <strong>${escapeHtml(h.title)}</strong>
                <span>${escapeHtml(h.sub)}</span>
              </a>`
            )
            .join("");
        }
        searchResults.classList.add("open");
      });

      searchResults.addEventListener("click", () => {
        searchResults.classList.remove("open");
        searchInput.value = "";
      });

      window.addEventListener("keydown", (ev) => {
        if (
          (ev.key === "/" || ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === "k")) &&
          document.activeElement !== searchInput &&
          document.activeElement &&
          document.activeElement.tagName !== "INPUT"
        ) {
          ev.preventDefault();
          searchInput.focus();
        } else if (ev.key === "Escape" && document.activeElement === searchInput) {
          searchInput.blur();
          searchResults.classList.remove("open");
        }
      });
    }

    syncFromHash();
  }

  document.addEventListener("DOMContentLoaded", () => {
    initHeaderAndScrollChrome();
    applyThemeAndAccent();
    initDitherBackgrounds();
    bindCopyButtons(document);
    initLandingPage();
    initDocsPortal();
    initCardSpotlights();
  });
})();
