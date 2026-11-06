# Tutorial: Object-Oriented (OOP) Architecture

When your application grows into multiple views, reusable widget cards, shared state stores, and background workers, `yapps` provides a clean, zero-boilerplate Object-Oriented layer built directly on top of its immediate-mode engine:

- **`ui.Application`** — Top-level application class managing the native `App` window, `Router`, `BackgroundRunner`, and lifecycle (`setup`, `build`, `on_close`).
- **`ui.Component`** — Reusable, stateful or stateless UI building block with **automatic ID-scope isolation** (`on_mount`, `build`, `on_unmount`).
- **`ui.View`** & **`ui.Router`** — Named screens with parameterized navigation (`push`, `replace`, `back`, `forward`) and `on_enter` / `on_leave` hooks.
- **`ui.Store[T]`** — Observable state container with `update()`, `subscribe()`, and automatic native event-loop wakeup.

---

## Functional/Procedural vs. OOP: Side-by-Side

Both paradigms call the **exact same widget methods** and can even be mixed inside the same frame!

| Question | Functional / Procedural (`ui.run` / plain `def`) | Object-Oriented (`Application` / `Component` / `View`) |
|---|---|---|
| **Best for** | Scripts, single-window utilities, data dashboards, quick tools | Multi-screen desktop apps, reusable widget libraries, team codebases |
| **State storage** | Closures (`nonlocal`) or passed `dict` / state objects | Instance attributes (`self.count`) and shared `ui.Store[T]` |
| **Widget ID scoping** | Manual `with ctx.id_scope(key):` in loops | **Automatic**—every `Component(key)` scopes all child widgets! |
| **Screen routing** | `if tab == 0: ... elif tab == 1: ...` | `self.router.push("project", id=42)` + `back()` / `forward()` history |
| **Background workers** | `runner = ui.BackgroundRunner.for_app(app)` | Built-in `self.runner` & lazy `self.async_bridge` on `Application` |

---

## Lesson 1: Subclassing `ui.Application`

You can configure window defaults either as **class attributes** or via **`super().__init__(...)`** arguments:

```python
import yapps as ui

class CounterApp(ui.Application):
    title = "OOP Counter"
    width = 560
    height = 360
    theme = ui.ThemeMode.DARK
    accent = ui.Accent.VIOLET  # Real accents: NEUTRAL, VIOLET, BLUE, GREEN, AMBER, ORANGE, CORAL, ROSE

    def setup(self) -> None:
        # Called automatically at the end of __init__
        self.count = 0
        self.step = 1

    def build(self, ctx: ui.UI) -> None:
        with ctx.column(width=ui.FILL, height=ui.FILL, pad=28, gap=16, bg=ui.Color.BACKGROUND):
            ctx.heading(f"Total: {self.count}", level=1)
            self.step = int(ctx.slider("Step size", self.step, 1, 10, step=1, show_value=True, format="%.0f"))

            with ctx.row(gap=10):
                if ctx.button(f"Add +{self.step}", variant=ui.ButtonVariant.PRIMARY, icon=ui.Icon.PLUS):
                    self.count += self.step
                if ctx.button("Reset", variant=ui.ButtonVariant.GHOST):
                    self.count = 0

    def on_close(self) -> None:
        # Optional cleanup when the window closes
        pass

if __name__ == "__main__":
    CounterApp().run()
```

You can also override `__init__` and pass `title`, `width`, `height`, `theme`, `accent` directly to `super().__init__("Custom Title", width=720, height=420, accent=ui.Accent.GREEN)`.

---

## Lesson 2: Reusable `ui.Component` & Automatic ID Isolation

In raw immediate-mode UIs, rendering two components that both contain `ctx.button("Increment")` would normally collide on the ID `"Increment"`.

`ui.Component` solves this automatically: calling `my_component(ctx)` (or `my_component()` inside a frame) wraps `build(ctx)` inside `with ctx.id_scope(self.key):`—and runs `on_mount(ctx)` once on first render!

Even better: **`build(self, ctx)` can return a value**, so parent views can react to component events naturally!

```python
import yapps as ui

class PipelineCard(ui.Component):
    def __init__(self, key: str, title: str, initial_rpm: int = 120) -> None:
        super().__init__(key)  # Pushes `key` onto CUI's ID stack every render!
        self.title = title
        self.rpm = initial_rpm
        self.enabled = True

    def on_mount(self, ctx: ui.UI) -> None:
        # Runs once before the very first build()
        pass

    def build(self, ctx: ui.UI) -> bool:
        """Render the card and return True if the 'Restart' button was clicked."""
        restarted = False
        with ctx.card(pad=18, gap=12, width=ui.GROW(1)):
            with ctx.row(align=ui.Align.CENTER):
                ctx.heading(self.title, level=4)
                ctx.spacer()
                # Notice both cards have a switch & buttons with the SAME labels—zero collision!
                self.enabled = ctx.switch("##on", self.enabled)

            with ctx.disabled_scope(not self.enabled):
                self.rpm = int(ctx.slider("Target RPM", self.rpm, 0, 500, step=10, show_value=True, format="%.0f"))
                with ctx.row(gap=8):
                    if ctx.button("Boost +50", icon=ui.Icon.ZAP, size=ui.ControlSize.SM):
                        self.rpm = min(500, self.rpm + 50)
                    if ctx.button("Restart", variant=ui.ButtonVariant.OUTLINE, size=ui.ControlSize.SM):
                        restarted = True
        return restarted

class DualPipelineApp(ui.Application):
    def __init__(self) -> None:
        super().__init__("Dual Pipelines", width=760, height=380, theme=ui.ThemeMode.DARK, accent=ui.Accent.GREEN)

    def setup(self) -> None:
        self.left = PipelineCard("pipe_a", "Ingestion Cluster", 180)
        self.right = PipelineCard("pipe_b", "Inference Workers", 320)

    def build(self, ctx: ui.UI) -> None:
        with ctx.row(width=ui.FILL, height=ui.FILL, pad=24, gap=18, bg=ui.Color.BACKGROUND):
            if self.left(ctx):
                ctx.toast("Restarted Ingestion Cluster", tone=ui.Tone.INFO)
            if self.right(ctx):
                ctx.toast("Restarted Inference Workers", tone=ui.Tone.INFO)

if __name__ == "__main__":
    DualPipelineApp().run()
```

---

## Lesson 3: Multi-Screen Navigation with `ui.View` & `ui.Router`

Every `ui.Application` comes with `self.router` pre-wired to wake the window on navigation:

- **`self.router.register("route_name", MyView(...))`** — Register a `View` instance (the first registered route becomes active automatically).
- **`self.router.push("detail", item_id=42)`** — Navigate forward, passing arbitrary keyword parameters to `DetailView.on_enter(params)`.
- **`self.router.replace("login")`** — Replace the current history entry without growing the back stack.
- **`self.router.back()` / `self.router.forward()`** — Navigate browser-style history (`can_go_back`, `can_go_forward`).
- **`self.router.render(ctx)`** — Render whichever `View` is currently active.

```python
class ProjectDetailView(ui.View):
    title = "Project Detail"

    def __init__(self, router: ui.Router) -> None:
        super().__init__("detail")
        self.router = router
        self.project_id: int = -1

    def on_enter(self, params: dict) -> None:
        self.project_id = params.get("project_id", 1)

    def on_leave(self) -> None:
        pass

    def build(self, ctx: ui.UI) -> None:
        with ctx.column(gap=12):
            if ctx.button("Back", icon=ui.Icon.ARROW_LEFT, variant=ui.ButtonVariant.GHOST):
                self.router.back()
            ctx.heading(f"Inspecting Project #{self.project_id}", level=2)
```

---

## Lesson 4: Reactive State with `ui.Store[T]`

In multi-view OOP apps, passing raw dicts between 6 views can get messy. `ui.Store[T]` holds shared state, notifies subscribers on change, and automatically wakes the UI window when mutated:

```python
store = ui.Store({"Filter": "", "incidents": []}, wake=self.wake)

# Read current state
items = store.value["incidents"]

# Mutate in-place OR return a new value — both notify subscribers and wake the window!
store.update(lambda s: s["incidents"].append({"id": 1, "title": "API spike"}))
```

> **Thread-safety tip:** When updating a `Store` from a background worker thread, marshal the mutation via `self.call_soon(lambda: store.update(...))` (or `on_done=` in `self.runner.submit(...)`) so state only mutates between UI frames!

---

## Lesson 5: Complete OOP Capstone — Incident Response Console

Here is a complete, 100% standalone multi-view OOP application combining **`Application`**, **`Store`**, **`Router`**, **two `View` screens (`OverviewView` & `DetailView`)**, **reusable `IncidentCard` `Component`s**, **live accent switching**, and **background diagnostics via `self.runner`**:

```python
"""Complete OOP Capstone: Multi-View Incident Response Console."""

from __future__ import annotations
import time
import yapps as ui


class IncidentCard(ui.Component):
    """Reusable incident summary card with automatic ID scoping."""

    def __init__(self, incident_id: int) -> None:
        super().__init__(f"inc_{incident_id}")
        self.incident_id = incident_id

    def build(self, ctx: ui.UI, item: dict) -> str | None:
        action: str | None = None
        tone = ui.Tone.SUCCESS if item["resolved"] else ui.Tone.DANGER
        with ctx.card(pad=16, gap=10, width=ui.FILL):
            with ctx.row(align=ui.Align.CENTER, gap=10):
                ctx.badge("Resolved" if item["resolved"] else "Open", tone=tone, dot=True)
                ctx.text(item["title"], font=ui.FontRole.MEDIUM, size=15)
                ctx.spacer()
                ctx.muted(f"#{item['id']} · {item['service']}")

            with ctx.row(gap=8):
                if ctx.button("Inspect", icon=ui.Icon.ARROW_RIGHT, size=ui.ControlSize.SM):
                    action = "inspect"
                if not item["resolved"]:
                    if ctx.button("Resolve", icon=ui.Icon.CHECK, size=ui.ControlSize.SM, variant=ui.ButtonVariant.PRIMARY):
                        action = "resolve"
        return action


class OverviewView(ui.View):
    title = "Incidents"
    icon = ui.Icon.ACTIVITY

    def __init__(self, store: ui.Store[dict], router: ui.Router) -> None:
        super().__init__("overview")
        self.store = store
        self.router = router
        self.cards: dict[int, IncidentCard] = {}
        self.new_title = ""
        self.new_service = 0

    def _create_incident(self, title: str, service: str) -> None:
        def _mutate(s: dict) -> None:
            s["incidents"].insert(0, {
                "id": s["next_id"],
                "title": title,
                "service": service,
                "resolved": False,
                "notes": "Investigating root cause.",
            })
            s["next_id"] += 1

        self.store.update(_mutate)

    def build(self, ctx: ui.UI) -> None:
        services = ["Auth API", "Edge Gateway", "Billing DB", "Search Index"]
        items = self.store.value["incidents"]
        open_cnt = sum(1 for x in items if not x["resolved"])

        with ctx.column(width=ui.FILL, gap=18):
            with ctx.grid(columns=2, min_column_width=220, gap=14, width=ui.FILL):
                with ctx.card(pad=16, gap=4):
                    ctx.secondary("Active Incidents")
                    ctx.heading(str(open_cnt), level=2)
                with ctx.card(pad=16, gap=4):
                    ctx.secondary("Total Logged")
                    ctx.heading(str(len(items)), level=2)

            with ctx.card(pad=16, gap=12, width=ui.FILL):
                ctx.label("Report New Incident")
                with ctx.row(gap=10, align=ui.Align.END, wrap=True):
                    self.new_title = ctx.input("title", self.new_title, placeholder="Describe issue...", width=ui.GROW(2))
                    self.new_service = ctx.select("svc", services, self.new_service, width=160)
                    if ctx.button("Create", icon=ui.Icon.PLUS, variant=ui.ButtonVariant.PRIMARY):
                        if self.new_title.strip():
                            self._create_incident(self.new_title.strip(), services[self.new_service])
                            self.new_title = ""

            for item in items:
                iid = item["id"]
                card = self.cards.setdefault(iid, IncidentCard(iid))
                # Invoke Component.build inside its automatic ID scope!
                with ctx.id_scope(card.key):
                    act = card.build(ctx, item)
                if act == "inspect":
                    self.router.push("detail", id=iid)
                elif act == "resolve":
                    self.store.update(lambda s, target=iid: next(
                        x.__setitem__("resolved", True) for x in s["incidents"] if x["id"] == target
                    ))
                    ctx.toast(f"Incident #{iid} marked resolved", tone=ui.Tone.SUCCESS)


class DetailView(ui.View):
    title = "Detail"
    icon = ui.Icon.FILE_TEXT

    def __init__(self, store: ui.Store[dict], router: ui.Router, runner: ui.BackgroundRunner) -> None:
        super().__init__("detail")
        self.store = store
        self.router = router
        self.runner = runner
        self.current_id = -1
        self.diag_task: ui.TaskHandle | None = None

    def on_enter(self, params: dict) -> None:
        self.current_id = params.get("id", -1)
        self.diag_task = None

    def build(self, ctx: ui.UI) -> None:
        item = next((x for x in self.store.value["incidents"] if x["id"] == self.current_id), None)
        if item is None:
            ctx.empty_state("Incident not found", icon=ui.Icon.INBOX)
            return

        with ctx.column(width=ui.FILL, gap=16):
            with ctx.row(align=ui.Align.CENTER, gap=10):
                if ctx.button("Back to list", icon=ui.Icon.ARROW_LEFT, variant=ui.ButtonVariant.GHOST):
                    self.router.back()
                ctx.spacer()
                status = self.diag_task.button_status if self.diag_task else ui.Status.IDLE
                if ctx.status_button("Run Diagnostics", status, icon=ui.Icon.TERMINAL):
                    self.diag_task = self.runner.submit(
                        lambda: (time.sleep(0.35), "Latency p99=14ms, 0 packet drops")[1],
                        on_done=lambda report: self.store.update(
                            lambda _s: item.__setitem__("notes", item["notes"] + f"\n[Diag] {report}")
                        ),
                    )

            with ctx.card(pad=20, gap=12, width=ui.FILL):
                ctx.heading(f"#{item['id']} — {item['title']}", level=2)
                ctx.secondary(f"Service: {item['service']}")
                item["notes"] = ctx.textarea("notes", item["notes"], label="Runbook Notes", height=160)


class IncidentConsoleApp(ui.Application):
    title = "Incident Console — yapps OOP"
    width = 960
    height = 660
    theme = ui.ThemeMode.DARK
    accent = ui.Accent.CORAL

    def setup(self) -> None:
        self.store = ui.Store(
            {
                "next_id": 103,
                "incidents": [
                    {"id": 102, "title": "Elevated TLS handshake latency in EU-West", "service": "Edge Gateway", "resolved": False, "notes": "Checking upstream edge pop."},
                    {"id": 101, "title": "Read replica lag cleared after compaction", "service": "Billing DB", "resolved": True, "notes": "Auto-compaction finished in 18s."},
                ],
            },
            wake=self.wake,
        )
        self.router.register("overview", OverviewView(self.store, self.router))
        self.router.register("detail", DetailView(self.store, self.router, self.runner))

    def build(self, ctx: ui.UI) -> None:
        with ctx.column(width=ui.FILL, height=ui.FILL, bg=ui.Color.BACKGROUND):
            with ctx.row(width=ui.FILL, pad_x=24, pad_y=12, gap=12, align=ui.Align.CENTER):
                ctx.icon(ui.Icon.SHIELD, 18, ui.Color.ACCENT)
                ctx.text("Incident Console", font=ui.FontRole.MEDIUM, size=16)
                ctx.spacer()
                accents = [ui.accent_name(a).capitalize() for a in ui.Accent]
                picked = ctx.select("acc_sel", accents, int(ctx.accent), width=130)
                if picked != int(ctx.accent):
                    ctx.accent = ui.Accent(picked)
                ctx.theme_toggle()

            ctx.separator()
            with ctx.scroll("main_scroll", width=ui.FILL, height=ui.FILL, pad=24):
                self.router.render(ctx)


if __name__ == "__main__":
    IncidentConsoleApp().run()
```

---

## Next Steps

- Learn every detail of **Accents, Tones, OKLCH Color Tokens, Custom Fonts, and Icons** in **[Theming & Styling →](theming-and-styling.md)**.
- Add **async HTTP APIs, streaming LLMs, and multi-threaded workers** in **[Concurrency & Async →](concurrency-and-async.md)**.
