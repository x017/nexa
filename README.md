# yapps

**yapps** is a lightweight, high-performance immediate-mode desktop UI library for Python, powered by the zero-dependency C99 [CUI](https://github.com/yappologistic/CUI) layout, animation, and SDF rendering engine.

- **Sub-megabyte native core**: **652 KB** stripped shared library (`libyapps_cui`) including embedded **Inter**, **Geist Mono**, and **168 Lucide icons**, OpenGL 3.3 + multi-threaded CPU software rasterizer, PNG/JPEG loader, and OS windowing (**487 KB** in minimal LTO builds).
- **Zero runtime Python dependencies**: Pure stdlib (`ctypes` ABI with GIL release on every native call, `__slots__` value types, lazy `asyncio`/build imports, ~48 ms warm import).
- **150+ components across 19 domains**: Layouts, typography, buttons & actions, inputs, date/time/color pickers, navigation, popovers/dialogs/sheets, virtualized 1M-row lists & editable data grids, 16 chart types, Kanban/Gantt/week calendars, AI agent/chat components, media, motion typography, IDE chrome, property inspector, Bezier node editor, and vector canvas.
- **Value-returning Pythonic API with full control**: Widgets accept and return plain Python values (`str`, `bool`, `int`, `float`, `Color`, `Date`) while exposing transition queries (`changed`, `submitted`, `focused`, `blurred`), hit rects, persistent `state_buffer`, custom `Platform` hooks, raw 64-byte SDF `DrawData` buffers, and `CustomRenderer` GPU callbacks.
- **Idiomatic Functional, Context, and OOP styles**: Write concise scripts with `import yapps as ui`, explicit multi-window/headless contexts with `ui.UI`, or structured apps with `Application`, `Router`, `View`, `Component`, and reactive `Store`.
- **First-class Concurrency, `asyncio`, & Networking**: Cross-thread native event-loop wakeup (`app.wake()`), UI-thread callback marshaling (`app.call_soon_threadsafe()`), `BackgroundRunner` (`submit`, `stream`, `fetch_json`, `fetch_bytes`), MPSC `Channel`, cooperative `await app.run_async(...)`, and threaded `AsyncBridge`.

---

## Installation

```bash
pip install .
```

Only a C99 compiler (`gcc`, `clang`, or MSVC `cl`) is required when building from source—**no `python3-dev` headers, CMake, or `libx11-dev` packages are needed** (`libX11.so.6` is loaded dynamically via `dlopen` on Linux, with automatic headless `SoftwareRenderer` fallback on CI/servers without a display).

---

## Quickstart: Three Python Paradigms

### 1. Functional Style (Zero Boilerplate)

```python
import yapps as ui

count = 0
name = ""

def draw():
    global count, name
    with ui.column(width=ui.FILL, height=ui.FILL, pad=24, gap=14, bg=ui.Color.BACKGROUND):
        ui.heading("Hello from yapps", level=1)
        name = ui.input("name", name, placeholder="Type your name...")
        with ui.row(gap=10, align=ui.Align.CENTER):
            if ui.button("Increment", variant=ui.ButtonVariant.PRIMARY, icon=ui.Icon.PLUS):
                count += 1
            ui.badge(f"Count: {count}", tone=ui.Tone.ACCENT)

ui.run(draw, title="Hello", width=560, height=340)
```

### 2. Object-Oriented Style (`Application`, `Router`, `View`, `Component`, `Store`)

```python
import yapps as ui

class CounterCard(ui.Component):
    def __init__(self, key: str, title: str):
        super().__init__(key)
        self.title = title
        self.count = 0

    def build(self, ctx: ui.UI) -> None:
        # Automatic ID-scope isolation: multiple instances never collide!
        with ctx.card(pad=18, gap=10, width=ui.GROW(1)):
            ctx.heading(self.title, level=4)
            if ctx.button("Increment", icon=ui.Icon.PLUS):
                self.count += 1
            ctx.secondary(f"Value: {self.count}")

class DashboardApp(ui.Application):
    def __init__(self):
        super().__init__("OOP Demo", width=720, height=420, accent=ui.Accent.MINT)
        self.left = CounterCard("left", "Pipeline A")
        self.right = CounterCard("right", "Pipeline B")

    def build(self, ctx: ui.UI) -> None:
        with ctx.row(width=ui.FILL, height=ui.FILL, pad=24, gap=16, bg=ui.Color.BACKGROUND):
            self.left(ctx)
            self.right(ctx)

DashboardApp().run()
```

### 3. Explicit Headless / Custom GPU Control

```python
import yapps as ui

with ui.SoftwareRenderer(threads=4) as sw:
    with ui.UI(width=800, height=450, theme=ui.ThemeMode.DARK, renderer=sw) as ctx:
        with ctx.frame(dt=1 / 60):
            with ctx.column(width=ui.FILL, height=ui.FILL, pad=24, gap=12, bg=ui.Color.BACKGROUND):
                ctx.metric("Throughput", "124,800 req/s", delta=14.2, spark=[82, 91, 96, 110, 124])

        # Save directly to PNG or inspect raw 64-byte vertices & draw commands for Vulkan/Metal/wgpu
        ctx.render_to_png("snapshot.png")
        dd = ctx.draw_data()
        print(dd.vertex_count, dd.index_count, len(dd.commands()))
```

---

## Concurrency, `asyncio`, & Networking

`yapps` sleeps at **0% CPU** when idle and wakes the native OS event loop immediately when background threads or coroutines push updates.

### Cooperative Single-Thread `asyncio`

```python
import asyncio
import yapps as ui

async def main():
    status = "Connecting..."
    app = ui.App("Async Demo", width=640, height=360)

    async def worker():
        nonlocal status
        await asyncio.sleep(0.5)
        status = "Live stream active"
        app.wake()

    task = asyncio.create_task(worker())
    await app.run_async(lambda ctx: ctx.heading(status, level=2))
    await task

asyncio.run(main())
```

### Background Threads, Streaming Generators, & HTTP JSON

```python
runner = ui.BackgroundRunner.for_app(app)

# Run blocking HTTP or CPU work off-thread; callbacks execute safely on the UI thread!
task = runner.fetch_json(
    "https://api.github.com/zen",
    on_done=lambda data: state.update({"quote": data}),
)

# Stream tokens from an LLM or iterator frame-by-frame onto the UI thread
stream_task = runner.stream(generate_tokens(prompt), on_item=chunks.append)
```

For libraries that require a dedicated background `asyncio` event loop alongside a synchronous `app.run(...)` UI thread, use `from yapps.aio import AsyncBridge`.

---

## Minimal Binary Size & Freezing (`PyInstaller` / `Nuitka`)

`yapps` compiles with `-ffunction-sections -fdata-sections -Wl,--gc-sections -fvisibility=hidden` (or `/Gy /OPT:REF /OPT:ICF` on MSVC) and strips unused subsystems at build time:

| Build Configuration | Command / Flags | Stripped Binary Size |
|---|---|---|
| **Full Default** (SW + GL 3.3 + OS Windowing + Fonts + Image Loader) | `python -m yapps.build` | **~652 KB** |
| **Minimal + Software Renderer** (custom fonts, no GL/App/stb_image) | `python -m yapps.build --minimal --lto` | **~499 KB** |
| **Ultra-Minimal Core** (layout + 150 widgets + SDF draw list for custom GPU) | `python -m yapps.build --minimal --no-sw --lto` | **~487 KB** |

Environment variables also work during `pip install .`:
`YAPPS_MINIMAL=1`, `YAPPS_DEFAULT_FONTS=0`, `YAPPS_STB_IMAGE=0`, `YAPPS_IMAGE_ALL=1`, `YAPPS_WITH_GL=0`, `YAPPS_WITH_SW=0`, `YAPPS_WITH_APP=0`, `YAPPS_LTO=1`.

When freezing single-file executables with **PyInstaller** or **Nuitka**, `yapps` includes an automatic PyInstaller hook (`yapps._pyinstaller`) that bundles `libyapps_cui` and excludes build-only modules, plus a CLI helper:

```bash
pyinstaller $(python -c "import yapps.build as b; print(' '.join(b.freeze_flags('pyinstaller')))") my_app.py
```

---

## Examples & Tests

Run any of the **11 complete example apps** in [`examples/`](examples/):

- `examples/hello.py` — Functional API quickstart, theme & accent switcher
- `examples/notes.py` — Split-view Markdown notes app, command palette (`Ctrl+K`), modal dialog
- `examples/settings.py` — OOP `Application` + `Router` + `View` + reusable `Component` cards
- `examples/dashboard.py` — KPI metrics, area & donut charts, filter bar, virtualized 250-row editable `data_grid`
- `examples/assistant.py` — AI agent workspace, streaming `BackgroundRunner`, `reasoning`, `tool_call`, `agent_plan`, `voice_orb`
- `examples/tracker.py` — Drag-and-drop `kanban` board, `gantt` chart, `week_calendar`, `presence`
- `examples/finance.py` — Live `ticker`, rolling `counter`, `treemap`, `sankey`, `money_input`
- `examples/mail.py` — Three-pane mail client with `swipe_item`, `comment`, `dropzone`, slide-over `sheet`
- `examples/music.py` — `carousel`, `now_playing`, scrubbable `waveform`, drag-`reorder` queue
- `examples/gallery.py` — IDE `menu_bar`/`toolbar`/`doc_tabs`, Bezier `node_editor`, custom `canvas`, motion text, `LogBuffer`, `inspector`
- `examples/async_network.py` — Cooperative `asyncio` + loopback HTTP telemetry server + `Channel`

Every example also supports headless screenshot rendering on servers/CI:

```bash
YAPPS_HEADLESS=1 CUI_SCREENSHOT=dashboard.png CUI_SCREENSHOT_FRAMES=12 python3 examples/dashboard.py
```

Run the full test suite (ABI struct layout parity, AST symbol verification, all 150 widgets, OOP/functional/threading/asyncio, minimal builds, and all examples):

```bash
pytest -v
```

---

## License

MIT License. Bundled fonts (Inter, Geist Mono, Lucide) and single-header libraries (`stb_*`) are permissive open-source; see [`LICENSE`](LICENSE) and [`THIRD_PARTY.md`](THIRD_PARTY.md).
