# Tutorial: Functional & Procedural Coding

`nexa` lets you write clean, Pythonic desktop applications **without a single class** when you want speed, simplicity, and direct data flow.

In fact, `nexa` supports **two closely related non-OOP styles**:
1. **Top-Level Functional Style** (`import nexa as ui` + `ui.heading(...)`, `ui.button(...)`): Uses a lightweight `contextvars.ContextVar` under the hood so you don't even pass a context parameter around. Ideal for scripts, prototypes, and single-file tools.
2. **Explicit Procedural Style** (`def render_sidebar(ctx: ui.UI, state: dict)`): Passes `ctx: ui.UI` explicitly as the first argument to plain Python functions. Ideal for larger procedural codebases, multi-window tools, and unit-tested UI modules.

Let's master both step by step!

---

## Lesson 1: Top-Level Functional Basics

With `ui.run(draw)`, your `draw` function takes **0 arguments** (or 1 `ctx: ui.UI` argument—`ui.run` inspects its signature automatically!).

```python
import nexa as ui

def main() -> None:
    celsius = 22.0

    def draw() -> None:
        nonlocal celsius
        fahrenheit = celsius * 9.0 / 5.0 + 32.0

        with ui.column(
            width=ui.FILL, height=ui.FILL, pad=28, gap=16,
            align=ui.Align.CENTER, justify=ui.Justify.CENTER, bg=ui.Color.BACKGROUND,
        ):
            with ui.card(width=380, pad=24, gap=14):
                with ui.row(align=ui.Align.CENTER):
                    ui.heading("Thermostat", level=2)
                    ui.spacer()
                    ui.theme_toggle()

                celsius = ui.slider("Temperature", celsius, -10.0, 45.0, step=0.5, show_value=True, format="%.1f °C")
                ui.metric("Fahrenheit", f"{fahrenheit:.1f} °F", delta=celsius - 20.0)

                with ui.row(gap=8):
                    if ui.button("Eco (19 °C)", icon=ui.Icon.CHECK):
                        celsius = 19.0
                    if ui.button("Comfort (22 °C)", variant=ui.ButtonVariant.PRIMARY):
                        celsius = 22.0

    ui.run(draw, title="Thermostat", width=500, height=380, accent=ui.Accent.CORAL)

if __name__ == "__main__":
    main()
```

Wait—notice how clean `nonlocal celsius` is for 1–3 variables. What when you have 10+ state fields? In procedural Python, put your state in a plain `dict` (or custom state object) so you never need `global` or `nonlocal`!

---

## Lesson 2: Mastering Flexbox, Sizing & Grids

Every container in `nexa` (`box`, `row`, `column`, `stack`, `grid`, `card`, `scroll`) uses the same single-pass constraint layout system.

### The 5 Sizing Primitives

| Sizing Spec | Meaning |
|---|---|
| `ui.FIT` *(or `None`)* | Shrink-wrap to fit child content |
| `ui.FILL` | Stretch to 100% of available parent space |
| `ui.GROW(weight)` | Flex-grow proportionally along a `row` or `column` (`GROW(2)` takes 2x space of `GROW(1)`) |
| `240` or `ui.PX(240)` | Exact logical pixel size (automatically scaled by HiDPI `ctx.scale`) |
| `ui.PCT(50)` | Percentage (`0..100`) of parent dimension |

### Classic Desktop Shell Recipe (Sidebar + Header + Scrollable Content + Status Bar)

```python
import nexa as ui

def main() -> None:
    state = {"nav": 0, "search": ""}

    def draw(ctx: ui.UI) -> None:
        with ctx.column(width=ui.FILL, height=ui.FILL, bg=ui.Color.BACKGROUND):
            # Main horizontal body (GROW(1) fills everything above the status bar)
            with ctx.row(width=ui.FILL, height=ui.GROW(1)):
                # Fixed 220px sidebar
                with ctx.column(width=220, height=ui.FILL, bg=ui.Color.SURFACE_MUTED, pad=12, gap=4):
                    ctx.heading("Workspace", level=4)
                    for i, (label, icon) in enumerate([
                        ("Overview", ui.Icon.LAYOUT_DASHBOARD),
                        ("Activity", ui.Icon.ACTIVITY),
                        ("Settings", ui.Icon.SETTINGS),
                    ]):
                        if ctx.nav_item(label, icon=icon, selected=(state["nav"] == i), group="main"):
                            state["nav"] = i

                # Flexible right content pane
                with ctx.column(width=ui.FILL, height=ui.FILL):
                    # Top header bar
                    with ctx.row(width=ui.FILL, pad_x=20, pad_y=12, gap=12, align=ui.Align.CENTER):
                        ctx.breadcrumb(["Workspace", ["Overview", "Activity", "Settings"][state["nav"]]])
                        ctx.spacer()  # Pushes everything after it to the right!
                        state["search"] = ctx.search("q", state["search"], width=220, size=ui.ControlSize.SM)
                        ctx.theme_toggle()

                    ctx.separator()

                    # Responsive auto-wrapping card grid inside a scroll container
                    with ctx.scroll("body_scroll", width=ui.FILL, height=ui.FILL, pad=20, gap=16):
                        with ctx.grid(columns=3, min_column_width=180, gap=14, width=ui.FILL):
                            for k in range(6):
                                with ctx.card(pad=16, gap=6):
                                    ctx.secondary(f"Node #{k + 1}")
                                    ctx.heading(f"{94 + k}.2%", level=3)
                                    ctx.badge("Healthy", tone=ui.Tone.SUCCESS, dot=True)

            # Bottom status bar
            with ctx.status_bar():
                ctx.status_bar_text("Connected", icon=ui.Icon.CIRCLE_CHECK, tone=ui.Tone.SUCCESS)
                ctx.status_bar_spacer()
                ctx.status_bar_item("60 FPS")

    with ui.App("Layout Recipe", width=960, height=620, theme=ui.ThemeMode.DARK, accent=ui.Accent.BLUE) as app:
        app.run(draw)

if __name__ == "__main__":
    main()
```

---

## Lesson 3: Procedural Decomposition (Plain Functions + State Dict)

As a procedural app grows beyond ~100 lines, split your UI into plain functions that accept `(ctx: ui.UI, state: dict)`. Notice how readable, modular, and testable this is—no inheritance required:

```python
def draw_toolbar(ctx: ui.UI, state: dict) -> None:
    with ctx.toolbar():
        if ctx.toolbar_button(ui.Icon.PLUS, label="New Item", tooltip="Ctrl+N"):
            state["items"].append({"title": "Untitled", "done": False})
        ctx.toolbar_separator()
        state["hide_done"] = ctx.toolbar_toggle(state["hide_done"], ui.Icon.FILTER, tooltip="Hide completed")
        ctx.toolbar_spacer()
        ctx.theme_toggle()

def draw_item_list(ctx: ui.UI, state: dict) -> None:
    with ctx.scroll("items", width=ui.FILL, height=ui.FILL, pad=20, gap=8):
        for idx, item in enumerate(state["items"]):
            if state["hide_done"] and item["done"]:
                continue
            with ctx.id_scope(idx):
                with ctx.card(pad=12):
                    with ctx.row(align=ui.Align.CENTER, gap=10):
                        item["done"] = ctx.checkbox("##chk", item["done"])
                        item["title"] = ctx.inline_edit("title", item["title"], width=ui.FILL)
                        if ctx.icon_button(ui.Icon.TRASH, tooltip="Remove"):
                            state["items"].pop(idx)
                            break
```

---

## Lesson 4: Manual Frame Loop (`while app.frame():`)

`app.run(draw)` is simply a convenience loop around `app.frame()`. Whenever you want explicit per-frame control—for example, draining a network queue, stepping a physics simulation, or driving custom frame timing—write the `while app.frame():` loop directly:

```python
import nexa as ui

with ui.App("Manual Loop", width=520, height=320, theme=ui.ThemeMode.DARK, accent=ui.Accent.AMBER) as app:
    ctx = app.ui
    clicks = 0

    while app.frame(wait=True):
        if ctx.shortcut(ui.Mod.PRIMARY, ui.Key.Q):
            app.quit()

        with ctx.column(width=ui.FILL, height=ui.FILL, pad=24, gap=12, bg=ui.Color.BACKGROUND):
            ctx.heading(f"Frame #{ctx.frame_count}", level=2)
            ctx.secondary(f"Delta time: {ctx.dt * 1000:.2f} ms  ·  Scale: {ctx.scale:.1f}x")
            if ctx.button("Trigger Toast", icon=ui.Icon.BELL, variant=ui.ButtonVariant.PRIMARY):
                clicks += 1
                ctx.toast(f"Notification #{clicks}", description="Dispatched from manual loop", tone=ui.Tone.INFO)
```

---

## Lesson 5: Complete Procedural Project — Expense & Budget Tracker

Below is a complete, 100% standalone procedural application combining **split panes**, **forms & money input**, **keyboard shortcuts (`Ctrl+K` command palette)**, **donut chart**, and **sortable table**:

```python
"""Complete procedural project: Personal Expense & Budget Tracker."""

from __future__ import annotations
import nexa as ui

CATEGORIES = ["Housing", "Food", "Transport", "Software"]
CAT_TONES = [ui.Tone.VIOLET, ui.Tone.SUCCESS, ui.Tone.INFO, ui.Tone.WARNING]

def draw_form_pane(ctx: ui.UI, st: dict) -> None:
    with ctx.column(width=ui.FILL, height=ui.FILL, bg=ui.Color.SURFACE_MUTED, pad=18, gap=14):
        with ctx.row(align=ui.Align.CENTER):
            ctx.heading("Add Expense", level=3)
            ctx.spacer()
            ctx.theme_toggle()

        st["title"] = ctx.input("exp_title", st["title"], label="Description", placeholder="e.g. Cloud hosting")
        st["amount"] = ctx.money_input("exp_amt", st["amount"], label="Amount", symbol="$", code="USD")
        st["cat"] = ctx.select("exp_cat", CATEGORIES, st["cat"], label="Category")

        err = st["error"]
        if err:
            ctx.alert(err, tone=ui.Tone.DANGER)

        if ctx.button("Record Expense", icon=ui.Icon.PLUS, variant=ui.ButtonVariant.PRIMARY, full_width=True):
            if not st["title"].strip():
                st["error"] = "Please enter a description."
            elif st["amount"] <= 0:
                st["error"] = "Amount must be greater than $0.00."
            else:
                st["error"] = ""
                st["rows"].append((st["title"].strip(), st["cat"], round(st["amount"], 2)))
                ctx.toast("Expense added", description=st["title"].strip(), tone=ui.Tone.SUCCESS)
                st["title"] = ""

        ctx.separator()
        totals = [sum(r[2] for r in st["rows"] if r[1] == c) for c in range(len(CATEGORIES))]
        ctx.secondary("Category Breakdown")
        ctx.donut_chart("cat_donut", totals, CATEGORIES, height=180, format="$%.0f")

def draw_ledger_pane(ctx: ui.UI, st: dict) -> None:
    total = sum(r[2] for r in st["rows"])
    budget = 2500.0

    with ctx.column(width=ui.FILL, height=ui.FILL, bg=ui.Color.BACKGROUND, pad=24, gap=16):
        with ctx.row(gap=16, width=ui.FILL):
            with ctx.card(width=ui.GROW(1), pad=16, gap=6):
                ctx.secondary("Total Spent")
                ctx.number_roll("spent_roll", f"${total:,.2f}", font=ui.FontRole.DISPLAY, size=24)
            with ctx.card(width=ui.GROW(1), pad=16, gap=8):
                ctx.meter("Monthly Budget", total, budget, "USD")

        cols = [
            ui.TableColumn("Description", width=ui.GROW(2), sortable=True),
            ui.TableColumn("Category", width=130),
            ui.TableColumn("Amount", width=110, align=ui.TextAlign.RIGHT, sortable=True),
        ]
        rows = list(st["rows"])
        if st["sort"].column == 0:
            rows.sort(key=lambda r: r[0].lower(), reverse=st["sort"].descending)
        elif st["sort"].column == 2:
            rows.sort(key=lambda r: r[2], reverse=st["sort"].descending)

        with ctx.table("ledger_tbl", cols, sort=st["sort"], height=ui.FILL, striped=True) as tbl:
            if tbl:
                for desc, cat_idx, amt in rows:
                    tbl.row()
                    tbl.cell_text(desc)
                    tbl.cell()
                    ctx.badge(CATEGORIES[cat_idx], tone=CAT_TONES[cat_idx], size=ui.ControlSize.SM)
                    tbl.cell_text(f"${amt:,.2f}")
        if tbl.sort is not None:
            st["sort"] = tbl.sort

def main() -> None:
    state = {
        "title": "",
        "amount": 49.00,
        "cat": 3,
        "error": "",
        "split": 0.34,
        "palette": False,
        "sort": ui.TableSort(2, True),
        "rows": [
            ("Apartment Rent", 0, 1250.00),
            ("Weekly Groceries", 1, 142.80),
            ("Metro Pass", 2, 65.00),
            ("Dev Server & Domains", 3, 38.50),
        ],
    }
    commands = [
        ui.Command("Clear all expenses", icon=ui.Icon.TRASH, group="Ledger"),
        ui.Command("Toggle Dark/Light Theme", icon=ui.Icon.MOON, group="View", shortcut="Ctrl D"),
    ]

    def draw(ctx: ui.UI) -> None:
        if ctx.shortcut(ui.Mod.PRIMARY, ui.Key.K):
            state["palette"] = True

        with ctx.split("root_split", state["split"], min_first=290, min_second=420, width=ui.FILL, height=ui.FILL) as sp:
            draw_form_pane(ctx, state)
            sp.next()
            draw_ledger_pane(ctx, state)
        state["split"] = sp.ratio

        state["palette"], picked = ctx.command_palette(state["palette"], commands)
        if picked == 0:
            state["rows"].clear()
        elif picked == 1:
            ctx.theme_mode = ui.ThemeMode.LIGHT if ctx.theme_mode == ui.ThemeMode.DARK else ui.ThemeMode.DARK

    with ui.App("Budget Ledger — nexa", width=1020, height=660, theme=ui.ThemeMode.DARK, accent=ui.Accent.GREEN) as app:
        app.run(draw)

if __name__ == "__main__":
    main()
```

---

## Next Steps

Ready to scale up to multi-screen applications with reusable custom components, routing history, and reactive stores? Continue to **[Object-Oriented (OOP) Architecture →](Object-Oriented-Architecture)**.
