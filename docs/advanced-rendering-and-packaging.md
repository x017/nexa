# Custom Canvas, Headless Testing, Custom GPU & Packaging

Beyond its 150+ built-in components, `nexa` exposes every low-level primitive of the underlying C99 engine so you can build custom vector instruments, write deterministic CI tests, plug into Vulkan/Metal/Direct3D/`wgpu`, or ship tiny standalone binaries.

---

## 1. Custom Vector `canvas` & Persistent `state_buffer`

Reserve layout space with `ctx.canvas(id, width, height, paint_fn)`—`nexa` runs flexbox layout first, then invokes `paint_fn(ctx, rect)` with the resolved screen `Rect(x, y, w, h)` and returns a `CanvasResult` (`rect`, `mouse`, `hovered`, `pressed`, `clicked`):

```python
import math
import nexa as ui

def main() -> None:
    def draw(ctx: ui.UI) -> None:
        with ctx.column(width=ui.FILL, height=ui.FILL, pad=20, bg=ui.Color.BACKGROUND):
            def paint_scope(c: ui.UI, r: ui.Rect) -> None:
                with c.clip_scope(r):
                    c.draw_rect_gradient(r, "#0f172a", "#1e293b", radius=12)
                    pts = [
                        (r.x + (i / 80.0) * r.w, r.y + r.h * 0.5 + math.sin(c.time * 4.0 + i * 0.2) * (r.h * 0.3))
                        for i in range(81)
                    ]
                    c.draw_polyline(pts, ui.Color.hex("#53dca6"), thickness=2.2)
                    c.draw_text("Live SDF Oscilloscope", (r.x + 16, r.y + 14), "#e2e8f0", size=13)

            res = ctx.canvas("osc", ui.FILL, ui.FILL, paint_scope)
            if res.hovered:
                ctx.request_redraw()  # Animate continuously while hovered

    with ui.App("Custom Canvas", width=640, height=360, theme=ui.ThemeMode.DARK) as app:
        app.run(draw)

if __name__ == "__main__":
    main()
```

Need C-managed per-widget byte storage for a custom control? `mv = ctx.state_buffer("my_knob", 16)` returns a zero-initialized writable `memoryview` persisted in CUI's widget state hash table (automatically garbage-collected if the widget stops rendering).

---

## 2. Automated Headless UI Testing & PNG Snapshots

You can test **every click, keystroke, text edit, and file drop** in `pytest` at thousands of frames per second without opening an OS window:

```python
import nexa as ui

def test_login_form(tmp_path):
    with ui.SoftwareRenderer(threads=2) as sw, ui.UI(width=480, height=320, renderer=sw) as ctx:
        username = ""
        submitted = False

        # Frame 1: Render & locate widget rectangles
        with ctx.frame():
            with ctx.column(pad=24, gap=12):
                username = ctx.input("user", username, autofocus=True)
                if ctx.button("Sign In", variant=ui.ButtonVariant.PRIMARY):
                    submitted = True
                btn_id = ctx.last_id

        btn_rect = ctx.get_rect(btn_id)

        # Frame 2: Type UTF-8 text into focused input
        ctx.input_text("ada_lovelace")
        with ctx.frame():
            with ctx.column(pad=24, gap=12):
                username = ctx.input("user", username)
                ctx.button("Sign In", variant=ui.ButtonVariant.PRIMARY)
        assert username == "ada_lovelace"

        # Frame 3 & 4: Click the Sign In button (press + release)
        ctx.input_click(btn_rect.x + 10, btn_rect.y + 10)
        with ctx.frame():
            with ctx.column(pad=24, gap=12):
                username = ctx.input("user", username)
                submitted |= ctx.button("Sign In", variant=ui.ButtonVariant.PRIMARY)
        ctx.input_mouse_button(ui.MouseButton.LEFT, False)
        with ctx.frame():
            with ctx.column(pad=24, gap=12):
                username = ctx.input("user", username)
                submitted |= ctx.button("Sign In", variant=ui.ButtonVariant.PRIMARY)

        assert submitted is True
        assert ctx.render_to_png(tmp_path / "login_verified.png")
```

---

## 3. Custom GPU Backends (`CustomRenderer` & `DrawData`)

Want to render `nexa` inside your own **Vulkan**, **Metal**, **Direct3D 12**, **`wgpu`**, or **`moderngl`** swapchain?

1. Supply texture atlas callbacks via `ui.CustomRenderer(on_create=..., on_update=..., on_destroy=...)`.
2. Call `ctx.set_viewport(w, h, dpi_scale)`, inject OS events via `ctx.input_*`, and run `dd = ctx.end_frame()`.
3. Upload `dd.vertices_bytes()` (`64` bytes per `cui_vertex` SDF primitive) and `dd.indices_bytes()` (`uint32`), then iterate `for cmd in dd.commands():` (`clip`, `texture`, `index_offset`, `index_count`).

---

## 4. Minimal Stripped Builds & Single-File Executables

Compile a stripped custom shared library removing unused subsystems via CLI or environment variables:

```bash
# Default full build (~652 KB: SW + GL 3.3 + OS Windowing + Embedded Fonts + PNG/JPEG)
python3 -m nexa.build

# Minimal LTO build with Software Renderer (~499 KB)
python3 -m nexa.build --minimal --lto

# Ultra-minimal Core-Only LTO build for custom GPU engines (~487 KB)
python3 -m nexa.build --minimal --no-sw --lto
```

### Freezing with PyInstaller or Nuitka

`nexa` registers an automatic PyInstaller hook (`nexa._pyinstaller`) that bundles `libnexa_cui` and excludes build-time compiler helpers (`nexa.build`, `setuptools`, `distutils`):

```bash
# PyInstaller single-file binary
pyinstaller --onefile $(python3 -c "import nexa.build as b; print(' '.join(b.freeze_flags('pyinstaller')))") app.py

# Nuitka standalone native compilation
python3 -m nuitka --onefile $(python3 -c "import nexa.build as b; print(' '.join(b.freeze_flags('nuitka')))") app.py
```
