# nexa (`nexa-ui`)

**nexa** (`pip install nexa-ui`) is a Python port of [CUI](https://github.com/yappologistic/CUI)—a lightweight, zero-dependency C99 immediate-mode desktop UI library with spring motion, Flexbox/Grid layout, and crisp SDF rendering.

![nexa Workbench Studio — Dockspace, TreeTable, CodeEditor, FlameGraph & Timeline](https://raw.githubusercontent.com/x017/nexa/main/docs/assets/screenshots/workbench.png)

- **Just over a megabyte native core**: **1.1 MB** stripped shared library (`libnexa_cui`) including embedded **Inter**, **Geist Mono**, **168 Lucide icons**, a color **emoji font** path, OpenGL 3.3 + multi-threaded CPU software rasterizer, PNG/JPEG loader, **BiDi & Arabic OpenType text shaping** on by default (`--no-rtl` drops it), and OS windowing (**956 KB** in minimal LTO builds).
- **Zero runtime Python dependencies**: Pure Python standard library (`ctypes` ABI releasing the GIL on every native call, `__slots__` value types, ~48 ms warm import).
- **190+ components across 22 domains (synced with CUI v1.4.0)**: Flexbox & grid layouts, multi-split **docking workspaces** (`dockspace`), hierarchical **`tree_table`** & **`path_bar`**, rich CommonMark/GFM **`markdown`**, multi-line **`code_editor`**, side-by-side **`diff_view`**, **`hex_view`**, profiler **`flame_graph`**, **`curve_editor`**, OKLab **`gradient_editor`**, NLE **`timeline_editor`**, virtualized 1M-row lists & editable data grids, 16 chart types, Kanban/Gantt/week calendars, AI agent/chat widgets, media, motion text, property inspector, Bezier node editor, and custom vector canvas.
- **CUI 1.2–1.4 additions, all exposed to Python**: right-to-left layout (`direction=`), **terminal** with a real scrollback buffer, **emoji** + color-emoji font and an emoji picker, **file browser**/**file picker**, **image viewer**, **cropper**, **candlestick** charts with **chart annotations**, **month calendar**, app **tour**, and the **instrument cluster** — `knob`, `fader`, `level_meter`, `radial_gauge`, `readout`, `dot_display`, `dot_chart`, `event_track`. CUI 1.3's **developer tools** ride along: `problems`, `pipeline`, `trace_view`, `waterfall`, `graph_view`, `commit_graph`, `keymap`, `test_explorer`, `stack_trace`, `blame`, `coverage`, `regex_tester`, `request_bar`, `api_explorer`, `feature_flags`, `uptime_bars`, `time_histogram`, `kv_editor`, `query_builder`, and `schedule_picker`. Context-free helpers (`regex_search`, `cron_next`/`cron_describe`, `url_params`/`url_set_params`, `http_reason`) come from the same C core.
- **Value-returning Pythonic API with full control**: Widgets accept and return plain Python values (`str`, `bool`, `int`, `float`, `Color`, `Date`) while exposing transition flags (`changed`, `submitted`, `focused`, `blurred`), hit rects, persistent `state_buffer`, custom `Platform` hooks, and `CustomRenderer` GPU callbacks.
- **Functional, Procedural, and OOP styles**: Write concise scripts with `import nexa as ui`, modular procedural apps with `ctx: ui.UI`, or multi-screen architectures with `Application`, `Router`, `View`, `Component`, and `Store`.
- **First-class Concurrency, `asyncio`, & Networking**: 0%-CPU idle sleep with OS-level cross-thread `app.wake()`, `BackgroundRunner` (`submit`, `stream`, `fetch_json`, `fetch_bytes`), MPSC `Channel`, cooperative `await app.run_async(...)`, and threaded `AsyncBridge`.

---

## Documentation & Step-by-Step Guides

Read the interactive documentation at **[parsa.x017.ir/nexa](http://parsa.x017.ir/nexa/)**, explore the **[Documentation Wiki](http://parsa.x017.ir/nexa/wiki.html)** (also mirrored to the **[GitHub Wiki](https://github.com/x017/nexa/wiki)**), or browse [`docs/`](https://github.com/x017/nexa/tree/main/docs):

0. **[Zero to Hero: The Complete `nexa` Full Tutorial](https://github.com/x017/nexa/blob/main/docs/zero-to-hero.md)** — Comprehensive 11-module masterclass taking you from your first 15-line native window through Flexbox/Grid layouts, forms & pickers, desktop chrome, 50k virtualized grids, code & diff editors, studio canvases, OOP architecture, OKLCH theming, async worker streams, headless `pytest`, and building **Pulse Studio** (`examples/zero_to_hero.py`).
1. **[Getting Started & Core Mental Model](https://github.com/x017/nexa/blob/main/docs/getting-started.md)** — Installation, value-returning immediate mode, widget IDs & `id_scope`, conditional vs. unconditional `with` scopes, and transition flags.
2. **[Tutorial: Functional & Procedural Coding](https://github.com/x017/nexa/blob/main/docs/tutorial-functional.md)** — Top-level `ui.run(draw)`, flexbox/grid sizing (`FIT`, `FILL`, `GROW`, `PX`, `PCT`), procedural helper decomposition, manual `while app.frame():` loops, and a complete Budget Tracker project.
3. **[Tutorial: Object-Oriented (OOP) Architecture](https://github.com/x017/nexa/blob/main/docs/tutorial-oop.md)** — `Application`, reusable auto-ID-scoped `Component`s, multi-view `Router` & `View` navigation, reactive `Store[T]`, and a complete Incident Console project.
4. **[Theming, Accents, Tones, Colors & Typography](https://github.com/x017/nexa/blob/main/docs/theming-and-styling.md)** — All **8 built-in `Accent` palettes**, **9 semantic `Tone`s**, custom OKLCH/hex `Token` overrides, `.ttf` font loading, and **168 `Icon` constants**.
5. **[Concurrency, Multithreading, `asyncio`, & Networking](https://github.com/x017/nexa/blob/main/docs/concurrency-and-async.md)** — `BackgroundRunner`, token streaming, `Channel`, `LogBuffer`, `await app.run_async(...)`, and `AsyncBridge`.
6. **[Complete 160+ Component Reference](https://github.com/x017/nexa/blob/main/docs/components-reference.md)** — Signatures and usage across all 20 widget domains.
7. **[Custom Canvas, Headless Testing, Custom GPU & Packaging](https://github.com/x017/nexa/blob/main/docs/advanced-rendering-and-packaging.md)** — Vector `canvas`, automated `pytest` UI testing, Vulkan/Metal/`wgpu` `DrawData`, minimal LTO builds, and PyInstaller/Nuitka freezing.

---

## Installation

Install prebuilt wheels from PyPI (imported in Python as `import nexa as ui`):

```bash
pip install nexa-ui
```

> **Note:** Make sure to install **`nexa-ui`** (`pip install nexa-ui` or `uv add nexa-ui`), **not** `nexa` (which is an unrelated package on PyPI). Once installed, import it in Python as `import nexa as ui`.

Or install directly from a local git checkout:

```bash
pip install -e .
```

Only a C99 compiler (`gcc`, `clang`, or MSVC `cl`) is required when building from source—**no `python3-dev` headers, CMake, or `libx11-dev` packages are needed** (`libX11.so.6` is loaded dynamically via `dlopen` on Linux, with automatic headless `SoftwareRenderer` fallback on CI/servers without a display).

> **Upgrading a dev checkout?** `src/nexa/_native/` is git-ignored, so a library built by the previous version survives a `git pull`/`git switch`. It is detected automatically: every build writes a `libnexa_cui.so.stamp` (CUI version + source fingerprint), and on import a mismatched stamp — or a library that lacks the current sentinel symbols — triggers a one-time recompile (about 20 s). You can also force one with `python -m nexa.build`. If you point `NEXA_LIB_PATH` at a stale library yourself, nexa raises a clear error instead of the raw `undefined symbol: cui_…_ex` from `ctypes`.

---

## Quickstart: Functional, OOP, & Headless Styles

Every snippet below is 100% standalone and runnable as-is.

### 1. Functional / Procedural Style

```python
import nexa as ui

def main() -> None:
    count = 0
    name = "world"

    def draw() -> None:
        nonlocal count, name
        with ui.column(width=ui.FILL, height=ui.FILL, pad=24, gap=14, bg=ui.Color.BACKGROUND):
            ui.heading(f"Hello, {name or 'stranger'}!", level=1)
            name = ui.input("name", name, placeholder="Type your name...", clearable=True)
            with ui.row(gap=10, align=ui.Align.CENTER):
                if ui.button("Increment", variant=ui.ButtonVariant.PRIMARY, icon=ui.Icon.PLUS):
                    count += 1
                ui.badge(f"Count: {count}", tone=ui.Tone.ACCENT)

    ui.run(draw, title="Hello — nexa", width=560, height=340, accent=ui.Accent.BLUE)

if __name__ == "__main__":
    main()
```

### 2. Object-Oriented Style (`Application`, `Router`, `View`, `Component`, `Store`)

```python
import nexa as ui

class CounterCard(ui.Component):
    def __init__(self, key: str, title: str) -> None:
        super().__init__(key)
        self.title = title
        self.count = 0

    def build(self, ctx: ui.UI) -> None:
        # Automatic ID-scope isolation: multiple instances never collide!
        with ctx.card(pad=18, gap=10, width=ui.GROW(1)):
            ctx.heading(self.title, level=4)
            if ctx.button("Increment", icon=ui.Icon.PLUS, variant=ui.ButtonVariant.PRIMARY):
                self.count += 1
            ctx.secondary(f"Value: {self.count}")

class DashboardApp(ui.Application):
    def __init__(self) -> None:
        super().__init__("OOP Demo", width=720, height=380, theme=ui.ThemeMode.DARK, accent=ui.Accent.GREEN)

    def setup(self) -> None:
        self.left = CounterCard("left", "Pipeline A")
        self.right = CounterCard("right", "Pipeline B")

    def build(self, ctx: ui.UI) -> None:
        with ctx.row(width=ui.FILL, height=ui.FILL, pad=24, gap=16, bg=ui.Color.BACKGROUND):
            self.left(ctx)
            self.right(ctx)

if __name__ == "__main__":
    DashboardApp().run()
```

### 3. Explicit Headless / Custom GPU Control

```python
import nexa as ui

with ui.SoftwareRenderer(threads=4) as sw:
    with ui.UI(width=800, height=450, theme=ui.ThemeMode.DARK, accent=ui.Accent.VIOLET, renderer=sw) as ctx:
        with ctx.frame(dt=1 / 60):
            with ctx.column(width=ui.FILL, height=ui.FILL, pad=24, gap=12, bg=ui.Color.BACKGROUND):
                ctx.metric("Throughput", "124,800 req/s", delta=14.2, spark=[82, 91, 96, 110, 124])

        # Save directly to PNG or inspect raw 64-byte SDF vertices & draw commands
        ctx.render_to_png("snapshot.png")
        dd = ctx.draw_data()
        print(dd.vertex_count, dd.index_count, len(dd.commands()))
```

---

## Built-In Theme Accents (`ui.Accent`)

`nexa` includes **8 perceptually balanced OKLCH accents** (`ThemeMode.LIGHT` & `ThemeMode.DARK`):

| Accent Enum | Dark Hex | Light Hex |
|---|---|---|
| `ui.Accent.NEUTRAL` | `#e8e8e8` | `#1d1d1d` |
| `ui.Accent.VIOLET` | `#a78bff` | `#7747ff` |
| `ui.Accent.BLUE` *(default)* | `#6ba3ff` | `#0562ef` |
| `ui.Accent.GREEN` | `#53dca6` | `#00864b` |
| `ui.Accent.AMBER` | `#ffcb62` | `#f3ad20` |
| `ui.Accent.ORANGE` | `#ffad5e` | `#c25300` |
| `ui.Accent.CORAL` | `#ff9386` | `#d1403a` |
| `ui.Accent.ROSE` | `#ff8bc5` | `#d23286` |

Need a custom hex or OKLCH brand accent? Set `ctx.theme[ui.Token.ACCENT] = ui.Color.hex("#14b8a6")` at any time—see **[Theming & Styling](https://github.com/x017/nexa/blob/main/docs/theming-and-styling.md)**.

---

## Concurrency, `asyncio`, & Background Streaming

### Cooperative Single-Thread `asyncio`

```python
import asyncio
import nexa as ui

async def main() -> None:
    status = "Connecting..."
    app = ui.App("Async Demo", width=640, height=320, theme=ui.ThemeMode.DARK, accent=ui.Accent.VIOLET)

    async def worker() -> None:
        nonlocal status
        await asyncio.sleep(0.2)
        status = "Live stream active"
        app.wake()

    task = asyncio.create_task(worker())
    try:
        await app.run_async(lambda ctx: ctx.heading(status, level=2))
    finally:
        task.cancel()
        app.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Background Worker Pool & Token Streaming (`BackgroundRunner`)

```python
import time
import nexa as ui

def main() -> None:
    app = ui.App("Streaming Demo", width=640, height=320, theme=ui.ThemeMode.DARK)
    runner = ui.BackgroundRunner.for_app(app)
    chunks: list[str] = []

    def generate_tokens():
        for word in ["Zero-bloat", "native", "UI", "streaming", "in", "Python!"]:
            time.sleep(0.05)
            yield word

    def draw(ctx: ui.UI) -> None:
        with ctx.column(width=ui.FILL, height=ui.FILL, pad=24, gap=14, bg=ui.Color.BACKGROUND):
            if ctx.button("Stream Response", icon=ui.Icon.SPARKLES, variant=ui.ButtonVariant.PRIMARY):
                chunks.clear()
                runner.stream(generate_tokens, on_item=chunks.append)
            ctx.text(" ".join(chunks) or "Click Stream Response to begin.")

    try:
        app.run(draw)
    finally:
        runner.close()
        app.close()

if __name__ == "__main__":
    main()
```

---

## Examples & Tests

Run any of the **16 complete example apps** in [`examples/`](https://github.com/x017/nexa/tree/main/examples):

| Example | Highlights |
|---|---|
| [`examples/zero_to_hero.py`](https://github.com/x017/nexa/blob/main/examples/zero_to_hero.py) | **0-to-Hero Capstone (*Pulse Studio*)**: OOP `Application` + `Component` + `Store`, `dockspace`, `path_bar`, `tree_table`, `code_editor`, `diff_view`, GFM `markdown`, `line_chart`, `flame_graph`, `BackgroundRunner` & `command_palette` |
| [`examples/workbench.py`](https://github.com/x017/nexa/blob/main/examples/workbench.py) | **New in 1.1**: Multi-split `dockspace`, `path_bar`, `tree_table`, `code_editor`, `diff_view`, `markdown`, `flame_graph`, `curve_editor`, `gradient_editor`, `timeline_editor` & `hex_view` |
| [`examples/hello.py`](https://github.com/x017/nexa/blob/main/examples/hello.py) | Functional quickstart, `input`, `switch`, `toast`, `theme_toggle` |
| [`examples/notes.py`](https://github.com/x017/nexa/blob/main/examples/notes.py) | Split-view notes editor, search, tags, `dialog`, `command_palette` (`Ctrl+K`) |
| [`examples/settings.py`](https://github.com/x017/nexa/blob/main/examples/settings.py) | OOP `Application` + `Router` + `View` + `Component` + all 8 `Accent` presets |
| [`examples/dashboard.py`](https://github.com/x017/nexa/blob/main/examples/dashboard.py) | KPI `number_roll`, `sparkline`, `line_chart`, `donut_chart`, 250-row `data_grid` |
| [`examples/assistant.py`](https://github.com/x017/nexa/blob/main/examples/assistant.py) | AI workspace + `BackgroundRunner.stream`, `reasoning`, `tool_call`, `voice_orb` |
| [`examples/tracker.py`](https://github.com/x017/nexa/blob/main/examples/tracker.py) | Drag-and-drop `kanban` board, `gantt` timeline, `week_calendar`, `presence` |
| [`examples/finance.py`](https://github.com/x017/nexa/blob/main/examples/finance.py) | Live `ticker`, odometer `counter`, `treemap`, `sankey`, `money_input` |
| [`examples/mail.py`](https://github.com/x017/nexa/blob/main/examples/mail.py) | `swipe_item` inbox, `chip` filters, `comment`, `dropzone`, slide-over `sheet` |
| [`examples/music.py`](https://github.com/x017/nexa/blob/main/examples/music.py) | `carousel`, `now_playing` transport, scrubbable `waveform`, `reorder` queue |
| [`examples/gallery.py`](https://github.com/x017/nexa/blob/main/examples/gallery.py) | IDE `menu_bar`/`toolbar`/`doc_tabs`, Bezier `node_editor`, `canvas`, `inspector`, `LogBuffer` |
| [`examples/async_network.py`](https://github.com/x017/nexa/blob/main/examples/async_network.py) | Cooperative `await app.run_async` + loopback HTTP server + `Channel` |
| [`examples/instruments.py`](https://github.com/x017/nexa/blob/main/examples/instruments.py) | **New in 1.4**: `knob`, `fader`, `level_meter`, `radial_gauge`, `readout`, `dot_display`, `dot_chart` & `event_track` — a live reactor console |
| [`examples/devtools.py`](https://github.com/x017/nexa/blob/main/examples/devtools.py) | **New in 1.4**: all 20 CUI 1.3 dev tools — `pipeline`, `problems`, `test_explorer`, `coverage`, `trace_view`, `waterfall`, `api_explorer`, `feature_flags`, `schedule_picker`, `blame`, `commit_graph`… |
| [`examples/rtl.py`](https://github.com/x017/nexa/blob/main/examples/rtl.py) | **New in 1.4**: Persian RTL studio — system font install, shaped text, `month_calendar`, `terminal`, `file_browser`, `candlestick`, `image_viewer`/`cropper`, `emoji_picker`, `tour` |

<p align="center">
  <img src="docs/assets/screenshots/instruments.png" width="49%" alt="Reactor Console — knobs, faders, meters, dot chart" />
  <img src="docs/assets/screenshots/devtools.png" width="49%" alt="DevTools Studio — pipeline, problems, coverage, traces" />
</p>
<p align="center">
  <img src="docs/assets/screenshots/rtl.png" width="66%" alt="Studio فارسی — right-to-left Persian UI with a system font" />
</p>

Render headless screenshots on any machine or CI runner:

```bash
NEXA_HEADLESS=1 CUI_SCREENSHOT=dashboard.png CUI_SCREENSHOT_FRAMES=12 python3 examples/dashboard.py
```

Run the test suite:

```bash
pytest -v
```

---

## Development

```bash
git clone https://github.com/x017/nexa && cd nexa

# with uv — no pip in the environment, the Makefile uses `uv pip` / `uv venv`
uv sync --extra dev                    # or: make sync
# …or with pip
python3 -m pip install -e ".[dev]"

make test                              # builds the native library on first run, then pytest
make examples                          # headless screenshots of all 16 examples → build/screenshots/
```

The installer is picked automatically: if `uv` is on `PATH` the Makefile uses
`uv venv` + `uv pip install --python <interpreter>` (uv virtualenvs ship without
pip), otherwise `python -m venv` + `python -m pip`. Force one explicitly with
`make INSTALLER=pip …` or `make INSTALLER=uv …`; `make help` prints which
installer and interpreter are in effect. `uv run make test` works too, since
`uv` keeps the project environment in sync.

`make` on its own lists every task:

| Task | What it does |
|---|---|
| `make native` | compile the C99 engine (`RTL=0`, `LTO=1`, `MINIMAL=1`, `DEBUG=1`, `OUT=…`; a shapeless build at the default path is replaced on next import, so pair `RTL=0` with `OUT=` + `NEXA_LIB_PATH`) |
| `make native-info` | which library is loaded, its build stamp and whether shaping is on |
| `make test` / `make test-quick` | full pytest suite / everything but the slow example + packaging tests |
| `make examples` / `make example EXAMPLE=rtl` | render every example headless / run one |
| `make docs` | rebuild the HTML + wiki bundle from `README.md` and `docs/*.md` |
| `make bridge-check` / `make abi` | verify or regenerate the generated ctypes/C bridge code |
| `make dist` / `make check` | sdist + wheel into `dist/`, then `twine check --strict` |
| `make testpypi` / `make publish PUBLISH=yes` | upload to TestPyPI / PyPI |
| `make ci` | build + test + docs + generated-code check |

## License

MIT License. Bundled fonts (Inter, Geist Mono, Lucide) and single-header libraries (`stb_*`) are permissive open-source; see [`LICENSE`](https://github.com/x017/nexa/blob/main/LICENSE), [`THIRD_PARTY.md`](https://github.com/x017/nexa/blob/main/THIRD_PARTY.md), and [`RELEASING.md`](https://github.com/x017/nexa/blob/main/RELEASING.md).
