# `nexa` Documentation Wiki

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
| **API** | **[160+ Components Reference](Components-Reference)** | Complete Python signatures, enum values, result dataclasses, and scope rules across all 20 widget domains. |

---

## 13 Runnable Examples (`examples/`)

| Example | Title | Highlights |
|---|---|---|
| [`examples/zero_to_hero.py`](https://github.com/x017/nexa/blob/main/examples/zero_to_hero.py) | **Pulse Studio (0→Hero Capstone)** | OOP Application + Store, dockspace, tree_table, code_editor, diff_view, GFM checklist, charts & flame profiler. |
| [`examples/workbench.py`](https://github.com/x017/nexa/blob/main/examples/workbench.py) | **Workbench Studio 1.1** | All 12 CUI 1.1 components: dockspace, path_bar, tree_table, code_editor, diff_view, hex_view, flame_graph, curves, gradients & NLE timeline. |
| [`examples/gallery.py`](https://github.com/x017/nexa/blob/main/examples/gallery.py) | **Nodes & Studio Gallery** | Menu bar, toolbar, dirty document tabs, pan/zoom Bezier node graph, typed property inspector & C-backed log console. |
| [`examples/dashboard.py`](https://github.com/x017/nexa/blob/main/examples/dashboard.py) | **Larkspur Analytics** | Animated rolling KPIs, sparklines, cubic area chart, donut breakdown, filter bar & virtualized data grid. |
| [`examples/tracker.py`](https://github.com/x017/nexa/blob/main/examples/tracker.py) | **Project Tracker** | Light-mode drag-and-drop Kanban board, interactive Gantt timeline, 7-day week schedule & live presence rings. |
| [`examples/assistant.py`](https://github.com/x017/nexa/blob/main/examples/assistant.py) | **Muse AI Copilot** | BackgroundRunner token streaming, model picker, context ring meter, execution plan & reactive voice orb. |
| [`examples/finance.py`](https://github.com/x017/nexa/blob/main/examples/finance.py) | **Market Terminal** | Live scrolling market ticker, rolling odometer counter, Treemap, split bar, Sankey diagram & trading heatmap. |
| [`examples/settings.py`](https://github.com/x017/nexa/blob/main/examples/settings.py) | **OOP Settings & 8 Accents** | Multi-route Application + Router + View + Component architecture showcasing all 8 OKLCH accents. |
| [`examples/async_network.py`](https://github.com/x017/nexa/blob/main/examples/async_network.py) | **Asyncio & Worker Pools** | Cooperative asyncio loop, AsyncBridge, BackgroundRunner HTTP JSON fetch & non-blocking progress. |
| [`examples/mail.py`](https://github.com/x017/nexa/blob/main/examples/mail.py) | **Desktop Mail Client** | Three-pane resizable split layout, virtualized message list, search filter & rich thread preview. |
| [`examples/music.py`](https://github.com/x017/nexa/blob/main/examples/music.py) | **Audio Deck** | Transport controls, waveform/equalizer visualization, playlists & smooth spring animations. |
| [`examples/notes.py`](https://github.com/x017/nexa/blob/main/examples/notes.py) | **Markdown Notes** | Live CommonMark + GFM task list preview alongside multi-line editing and tag filtering. |
| [`examples/hello.py`](https://github.com/x017/nexa/blob/main/examples/hello.py) | **Minimal Starter** | Smallest 15-line interactive native window using ui.run(draw). |
