# Getting Started & Core Mental Model

Welcome to **nexa**—a Python port of [CUI](https://github.com/yappologistic/CUI)! Whether you have built desktop UIs with Tkinter, PyQt, Dear ImGui, or React—or this is your very first Python GUI library—this guide walks you from zero to building fast, polished desktop tools in minutes.

---

## 1. Installation & Requirements

Install `nexa-ui` from PyPI (imported in Python as `import nexa as ui`):

```bash
pip install nexa-ui
```

> **Important:** Install **`nexa-ui`** (`pip install nexa-ui` or `uv add nexa-ui`), **not** `nexa` (an unrelated package on PyPI), and avoid naming your own local folder `nexa/` or file `nexa.py` so Python resolves the installed library cleanly.

Or install from a local git checkout:

```bash
pip install -e .
```

### What you need (and what you *don't* need)
- **Python 3.9+** (zero third-party runtime Python packages—pure standard library).
- **Any C99 compiler** when installing from source (`gcc` or `clang` on Linux/macOS, MSVC `cl` or MinGW `gcc` on Windows).
- **No `python3-dev` headers, no CMake, and no `libx11-dev` packages required!** On Linux, `nexa` dynamically loads `libX11.so.6` via `dlopen` at runtime, and automatically falls back to its built-in multi-threaded CPU `SoftwareRenderer` when running on headless servers or CI.

To manually rebuild the native shared library (`libnexa_cui.so` / `.dylib` / `.dll`) at any time:

```bash
python3 -m nexa.build
```

---

## 2. Your First 15-Line Window

Create a file named `first_app.py` and run `python3 first_app.py`:

```python
import nexa as ui

count = 0
name = "world"

def draw() -> None:
    global count, name
    with ui.column(width=ui.FILL, height=ui.FILL, pad=24, gap=14, bg=ui.Color.BACKGROUND):
        ui.heading(f"Hello, {name or 'stranger'}!", level=1)
        name = ui.input("name_field", name, label="Your name", clearable=True)

        with ui.row(gap=10, align=ui.Align.CENTER):
            if ui.button("Increment", variant=ui.ButtonVariant.PRIMARY, icon=ui.Icon.PLUS):
                count += 1
            ui.badge(f"Clicked {count}x", tone=ui.Tone.ACCENT)

ui.run(draw, title="My First nexa Window", width=520, height=300)
```

### Headless Screenshot Mode (Servers, Containers & CI)
Don't have a display attached right now? Every `nexa` app can render pixel-identical frames off-screen and save a PNG screenshot via environment variables:

```bash
NEXA_HEADLESS=1 CUI_SCREENSHOT=preview.png CUI_SCREENSHOT_FRAMES=10 python3 first_app.py
```

---

## 3. How `nexa` Thinks: Value-Returning Immediate Mode

Traditional retained-mode toolkits (Tkinter, Qt, GTK) force you to keep **two copies of your state** synchronized:
1. Your Python data (`user.name`), and
2. Hidden state inside widget objects (`name_entry.setText(...)`, `on_text_changed` callbacks, signals/slots).

`nexa` uses an **event-driven, value-returning immediate-mode** architecture:

1. **Your Python variables are the single source of truth.** You pass the current value into a widget, and the widget returns the new value:
   ```python
   # Text input: str -> str
   query = ui.search("q", query, placeholder="Filter...")

   # Switch / Checkbox: bool -> bool
   dark = ui.switch("Dark mode", dark)

   # Slider: float -> float
   volume = ui.slider("Volume", volume, 0.0, 1.0, show_value=True)

   # Button: returns True on the exact frame it was clicked!
   if ui.button("Save", variant=ui.ButtonVariant.PRIMARY):
       save_to_disk()
   ```
2. **UI is just plain Python control flow.** Want to hide an input unless `advanced` is enabled? Use a regular `if`:
   ```python
   advanced = ui.checkbox("Show advanced options", advanced)
   if advanced:
       port = int(ui.number("port", port, 1024, 65535, step=1, decimals=0))
   ```
   Want to render a list of items? Use a regular `for` loop!
3. **0% CPU when idle, 60–120 fps spring physics when active.** Unlike game-engine immediate-mode GUIs that burn 100% of a core spinning in `while True`, `nexa` blocks inside the OS event loop (`select` / `GetMessageW` / `NSApp`) consuming **0% CPU** until mouse/keyboard input arrives, a spring animation is in flight, or a background thread calls `app.wake()`.

---

## 4. Widget Identity (`id` & `id_scope`)

To animate hover states, track keyboard focus, and remember scroll offsets across frames, `nexa` hashes an ID string for every interactive widget:

- **Controls with a unique key parameter** (`input("email", ...)`, `tabs("main_tabs", ...)`, `slider("Volume", ...)`) hash that first string argument.
- **Buttons & toggles** (`button("Save")`, `checkbox("Agree", ...)`) hash their label string.
- **`label##hidden_id` syntax**: Just like Dear ImGui / CUI, everything from `##` onward contributes to the ID hash *without* being drawn on screen!
  - `"Delete##row_1"` and `"Delete##row_2"` both display **`Delete`**, while having completely distinct IDs.
  - `"##search"` has an empty visible label and hashes `"##search"`.
- **Loops & Reusable Blocks (`id_scope`)**: Whenever you render widgets inside a `for` loop, wrap each iteration in `with ui.id_scope(item_id):` (or `with ctx.id_scope(i):`) so every iteration gets its own isolated ID namespace:

```python
for idx, task in enumerate(tasks):
    with ui.id_scope(idx):
        with ui.row(gap=8, align=ui.Align.CENTER):
            task["done"] = ui.checkbox(task["title"], task["done"])
            ui.spacer()
            if ui.button("Delete", size=ui.ControlSize.SM, variant=ui.ButtonVariant.GHOST):
                tasks.pop(idx)
                break
```

> **Tip:** When using the OOP API (`ui.Component`), `nexa` pushes `component.key` onto the ID stack **automatically**—you don't even need manual `id_scope` calls between component instances!

---

## 5. Unconditional vs. Conditional `with` Scopes

`nexa` uses Python `with` statements so you can never forget a `*_end()` call. There are two kinds of scopes:

### A. Unconditional Layout Scopes (always render children)
Containers that always open and close cleanly:
- `box`, `row`, `column`, `stack`, `grid`, `card`, `scroll`, `split`
- `id_scope`, `disabled_scope`, `clip_scope`
- `button_group`, `swipe_item`, `spotlight`, `dock`, `carousel`, `card_stack`, `kanban`, `virtual_list`, `reorder`
- `menu_bar`, `toolbar`, `status_bar`, `dialog_footer`

```python
with ui.card(pad=20, gap=12):
    ui.heading("Always rendered", level=3)
    ui.secondary("Card body")
```

### B. Conditional Scopes (check `if scope:` before rendering children!)
Overlays, disclosures, menus, and popups only build their children when open or visible. Always bind `as s:` and check `if s:`:
- Overlays & Menus: `dialog`, `sheet`, `popover`, `hover_card`, `menu`, `context_menu`, `user_menu`, `menu_bar_menu`
- Disclosures & Trees: `accordion`, `expandable_card`, `tree`, `reasoning`
- Structured Views: `table`, `data_grid`, `inspector`, `node_editor`

```python
# Declare `is_open = False` OUTSIDE `draw()`, with `nonlocal is_open` inside `draw()`:
with ui.dialog("Confirm Reset", is_open, description="Reset all settings to defaults?") as dlg:
    if dlg:
        with ui.dialog_footer():
            if ui.button("Cancel", variant=ui.ButtonVariant.GHOST):
                dlg.open = False
            if ui.button("Reset", variant=ui.ButtonVariant.DANGER):
                reset_all()
                dlg.open = False
is_open = dlg.open  # Syncs Cancel/Reset, header X, Escape key & backdrop click!
```

---

## 6. Inspecting Transitions (`changed`, `submitted`, `focused`, `blurred`) & Rects

Even though widgets return updated values directly, you often want to know *how* a widget transitioned on the current frame (for example, running a search when the user presses **Enter** inside `ui.input`):

```python
query = ui.input("cmd", query, placeholder="Type command and press Enter...")
if ui.changed():
    print("Text edited this frame:", query)
if ui.submitted():
    run_command(query)  # Fired when Enter is pressed!
if ui.focused():
    print("Input just gained focus")
if ui.blurred():
    print("Input just lost focus")
```

On an explicit `ctx: ui.UI` instance, these are properties: `ctx.changed`, `ctx.submitted`, `ctx.focused`, `ctx.blurred`.

### Widget Hit Rectangles (`last_id`, `last_rect`, `get_rect`)
Because CUI computes flexbox/grid layout in a single pass inside `end_frame()`:
- During `draw()`, `ctx.last_id` gives the `uint32` ID of the widget you just emitted, and `ctx.last_rect` returns its cached `Rect(x, y, w, h)` from the previous frame.
- Immediately after `end_frame()`, `ctx.get_rect(widget_id)` returns the exact newly computed `Rect(x, y, w, h)` for the frame that just finished.

---

## 7. Troubleshooting a Build

Run `make doctor` (or `python tools/doctor.py`) first — it checks the things that
actually break a checkout and prints the exact fix for each. The three that come
up most often:

**`error: Cannot update time stamp of directory 'src/nexa_ui.egg-info'`**

That is setuptools' `egg_info` running `os.utime()` on the egg-info directory and
getting `EACCES`/`ENOENT`: the directory is not yours, is on a read-only mount, or
is a dangling symlink — typically left behind by a Docker build or a `sudo` run.

```bash
ls -ld src/*.egg-info src/nexa/_native      # who owns the leftovers?
sudo rm -rf src/*.egg-info build dist        # or: sudo chown -R "$(id -u):$(id -g)" .
uv sync --extra dev                          # or: make install-dev
```

**`uv add nexa-ui --dev` inside the nexa checkout**

Don't: that adds the project to itself as a development dependency, and uv then
builds the checkout through the same path that broke above. Syncing the project's
own environment is enough:

```bash
uv sync --extra dev      # or: make sync
uv remove nexa-ui --dev  # undo the self-dependency
```

**`rm: cannot remove 'src/nexa_ui.egg-info/SOURCES.txt': Permission denied` from `make clean`**

Something ran as root in this checkout (`sudo make install`, `sudo uv sync`, a
container build) and left root-owned files behind. `make clean` now removes what
it can and names what is left; hand the tree back and retry:

```bash
make fix-permissions     # sudo chown -R "$(id -u):$(id -g)" .
make clean && make install-dev
```

Do not build as root: `make install`, `make native`, `make test`, `make examples`
and `make dist` refuse when root would create root-owned artifacts in a checkout
owned by someone else, and print the same fix.

**A traceback points at a file that is not in this checkout**

An editable install can point somewhere else entirely — `…/Projects/yapps/src/nexa/widgets/layout.py`
while you edit `…/Projects/nexa`. Confirm and reinstall:

```bash
python -c "import nexa; print(nexa.__file__)"   # which tree am I running?
make doctor                                     # flags "imports nexa-ui from another checkout"
uv pip uninstall nexa-ui && make install-dev    # rebind the environment to this tree
```

**`AttributeError: … undefined symbol: cui_dot_display_ex`**

A compiled library from an older version survived the update (`src/nexa/_native/`
is git-ignored). A source checkout now detects that on import and rebuilds once;
for a forced rebuild, `make native` — or delete `src/nexa/_native/` and import again.

---

## Next Steps

Choose the coding style you want to learn first (most developers read **both**, because they share the exact same widget names and compose together!):

1. **[Functional & Procedural Tutorial →](Functional-and-Procedural)** — Closures, explicit `ctx: ui.UI` helper functions, flexbox/grid layouts, forms, shortcuts, and manual frame loops.
2. **[Object-Oriented (OOP) Tutorial →](Object-Oriented-Architecture)** — `Application`, auto-scoped `Component` classes, multi-screen `Router` & `View`, and reactive `Store`.
3. **[Theming, Accents, Tones & Icons →](Theming-Accents-and-Icons)** — All 8 real `Accent` presets, 9 `Tone`s, custom OKLCH tokens, fonts, and 168 icons.
