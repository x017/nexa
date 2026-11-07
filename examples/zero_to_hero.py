"""Pulse Studio — Complete 0-to-Hero Capstone App (nexa v1.1).

Demonstrates how to combine nexa's OOP architecture (Application, Component, Store),
multi-split dockspace, editable path_bar, hierarchical tree_table, syntax code_editor,
split/inline diff_view, interactive GFM markdown checklist, live line_chart + KPIs,
profiler flame_graph, thread-safe BackgroundRunner + LogBuffer, command_palette,
confirmation dialog, and OKLCH theming in one cohesive desktop workbench.
"""

from __future__ import annotations

import dataclasses
import math
import time
from typing import Dict, List

import nexa as ui


BASELINE_SOURCE = """\
def evaluate_slo(latencies_ms: list[float], budget_ms: float = 12.0) -> bool:
    if not latencies_ms:
        return True
    peak = max(latencies_ms)
    return peak <= budget_ms
"""

ACTIVE_SOURCE = """\
def evaluate_slo(latencies_ms: list[float], budget_ms: float = 8.5) -> tuple[bool, float]:
    if not latencies_ms:
        return True, 0.0
    ordered = sorted(latencies_ms)
    p99_idx = min(len(ordered) - 1, int(len(ordered) * 0.99))
    p99 = round(ordered[p99_idx], 2)
    return p99 <= budget_ms, p99
"""

GATEWAY_SOURCE = """\
def route_request(path: str, circuit_open: bool = False) -> tuple[int, str]:
    if circuit_open:
        return 503, "circuit-breaker: fallback cache"
    if path.startswith("/v1/stream"):
        return 200, "sse-worker-pool"
    return 200, "edge-router"
"""

RUNBOOK_MD = """\
### Incident Remediation Playbook

- [x] Isolate `edge-gateway` tail-latency spike in profiler flame graph
- [x] Tighten p99 SLO threshold from `12.0 ms` to `8.5 ms` in `slo_guard.py`
- [ ] Run background canary verification across **eu-central** workers
- [ ] Snapshot verified multi-pane dock layout for on-call handoff

> **Tip:** Toggle tasks above directly—`ui.markdown` returns clicked checklist indices so your Python state updates in place!
"""

DEFAULT_DOCK_LAYOUT = (
    "h0.22([*Services],v0.63(h0.57([*Editor,Diff,Runbook],[*Telemetry]),[*Profiler,Logs]))"
)


@dataclasses.dataclass
class StudioState:
    selected_node: int = 2
    path_segments: List[str] = dataclasses.field(
        default_factory=lambda: ["pulse-studio", "services", "slo_guard.py"]
    )
    files: Dict[str, str] = dataclasses.field(
        default_factory=lambda: {
            "slo_guard.py": ACTIVE_SOURCE,
            "gateway.py": GATEWAY_SOURCE,
            "runbook.md": RUNBOOK_MD,
        }
    )
    active_file: str = "slo_guard.py"
    diff_mode: ui.DiffMode = ui.DiffMode.SPLIT
    rate_limit_rps: float = 2400.0
    worker_pool: int = 8
    circuit_breaker: bool = True
    region_idx: int = 0
    audit_running: bool = False
    audit_progress: float = 1.0
    throughput_hist: List[float] = dataclasses.field(
        default_factory=lambda: [1820.0, 1940.0, 2080.0, 2190.0, 2310.0, 2280.0, 2410.0, 2490.0]
    )
    latency_hist: List[float] = dataclasses.field(
        default_factory=lambda: [9.4, 8.9, 8.2, 7.8, 7.4, 7.1, 6.8, 6.4]
    )
    cursor_line: int = 1
    cursor_col: int = 1


class TelemetryPanel(ui.Component):
    """Reusable OOP Component (auto-pushes its `key` onto CUI's ID stack)."""

    REGIONS = ["eu-central-1", "us-east-1", "ap-northeast-1"]

    def __init__(self, key: str, store: ui.Store[StudioState]) -> None:
        super().__init__(key)
        self.store = store

    def build(self, ctx: ui.UI) -> None:
        st = self.store.value
        with ctx.scroll("tel_scroll", width=ui.FILL, height=ui.FILL, pad=10, gap=10):
            with ctx.grid(columns=2, min_column_width=150, gap=8, width=ui.FILL):
                ctx.metric(
                    "Throughput",
                    f"{st.throughput_hist[-1] / 1000.0:.2f}k",
                    delta=6.8,
                    spark=st.throughput_hist,
                )
                ctx.metric(
                    "p99 Latency",
                    f"{st.latency_hist[-1]:.1f}ms",
                    delta=-11.4,
                    lower_is_better=True,
                    spark=st.latency_hist,
                )

            ctx.line_chart(
                "rps_chart",
                [
                    ui.Series("RPS (x100)", [v / 100.0 for v in st.throughput_hist], "#53dca6"),
                    ui.Series("p99 (ms)", st.latency_hist, "#6ba3ff"),
                ],
                labels=["T-7", "T-6", "T-5", "T-4", "T-3", "T-2", "T-1", "Now"],
                width=ui.FILL,
                height=132,
                area=True,
                smooth=True,
            )

            ctx.muted("RUNTIME CONTROLS")
            with ctx.inspector("runtime_inspector", width=ui.FILL, label_width=108) as insp:
                if insp:
                    st.rate_limit_rps = ctx.prop_float(
                        "Rate Limit", st.rate_limit_rps, min=200.0, max=5000.0, step=50.0, format="%.0f rps"
                    )
                    st.worker_pool = ctx.prop_int("Workers", st.worker_pool, min=1, max=32)
                    st.circuit_breaker = ctx.prop_bool("Circuit Guard", st.circuit_breaker)
                    st.region_idx = ctx.prop_enum("Active Region", self.REGIONS, st.region_idx)


class PulseStudioApp(ui.Application):
    title = "Pulse Studio — nexa 0-to-Hero Capstone"
    width = 1240
    height = 820
    theme = ui.ThemeMode.DARK
    accent = ui.Accent.BLUE

    ACCENT_CYCLE = [
        ui.Accent.BLUE,
        ui.Accent.VIOLET,
        ui.Accent.GREEN,
        ui.Accent.AMBER,
        ui.Accent.CORAL,
        ui.Accent.ROSE,
    ]

    def setup(self) -> None:
        self.store = ui.Store(StudioState(), wake=self.app.wake)
        self.logs = ui.LogBuffer(max_lines=1024)
        self.logs.info("[boot] Pulse Studio v1.1 initialized (OpenGL / SIMD SW ready)")
        self.logs.info("[mesh] Connected to eu-central-1 telemetry ring")
        self.logs.debug("[slo] p99 guard active at 8.50 ms budget")

        self.telemetry_panel = TelemetryPanel("telemetry", self.store)
        self.saved_layout = ""
        self.palette_open = False
        self.confirm_reset_open = False
        self.filter_query = ""
        self.accent_idx = 0

        self.node_names = [
            "pulse-studio",
            "services",
            "slo_guard.py",
            "gateway.py",
            "docs",
            "runbook.md",
        ]
        self.node_status = ["Workspace", "Folder", "Healthy", "Healthy", "Folder", "Playbook"]
        self.node_p99 = ["—", "—", "6.4 ms", "4.1 ms", "—", "4 tasks"]
        self.tree_nodes = [
            ui.TreeNode(parent=-1, first_child=1, next_sibling=-1, flags=ui.TreeFlags.HAS_CHILDREN | ui.TreeFlags.OPEN),
            ui.TreeNode(parent=0, first_child=2, next_sibling=4, flags=ui.TreeFlags.HAS_CHILDREN | ui.TreeFlags.OPEN),
            ui.TreeNode(parent=1, first_child=-1, next_sibling=3, flags=ui.TreeFlags.SELECTED),
            ui.TreeNode(parent=1, first_child=-1, next_sibling=-1),
            ui.TreeNode(parent=0, first_child=5, next_sibling=-1, flags=ui.TreeFlags.HAS_CHILDREN | ui.TreeFlags.OPEN),
            ui.TreeNode(parent=4, first_child=-1, next_sibling=-1),
        ]
        self.tree_cols = [
            ui.GridColumn("Artifact", width=165, sortable=True),
            ui.GridColumn("State", width=70, priority=1),
        ]
        self.tree_sort = ui.TableSort(0, False)

        self.flame_spans = ui.flame_sort([
            ui.FlameSpan("edge.handle_request", 0.0000, 0.00640, depth=0, color_key=1),
            ui.FlameSpan("auth.verify_jwt", 0.0002, 0.00145, depth=1, color_key=2),
            ui.FlameSpan("ed25519_verify", 0.00035, 0.00120, depth=2, color_key=3),
            ui.FlameSpan("router.dispatch", 0.00155, 0.00510, depth=1, color_key=4),
            ui.FlameSpan("slo_guard.evaluate", 0.00175, 0.00330, depth=2, color_key=5),
            ui.FlameSpan("upstream.stream", 0.00340, 0.00495, depth=2, color_key=6),
            ui.FlameSpan("telemetry.flush", 0.00520, 0.00630, depth=1, color_key=7),
        ])
        self.flame_view = ui.FlameView(0.0, 0.00640, 0.0)
        self.selected_span = 4

        self.commands = [
            ui.Command("Run Canary Health Audit", icon=ui.Icon.PLAY, group="Diagnostics", shortcut="Ctrl+R"),
            ui.Command("Toggle Split / Inline Diff Mode", icon=ui.Icon.GIT_BRANCH, group="Editor", shortcut="Ctrl+D"),
            ui.Command("Save Current Dock Layout", icon=ui.Icon.SAVE, group="Workspace", shortcut="Ctrl+S"),
            ui.Command("Reset Dock Layout to Default", icon=ui.Icon.ROTATE_CCW, group="Workspace"),
            ui.Command("Cycle OKLCH Accent Preset", icon=ui.Icon.PALETTE, group="Appearance"),
            ui.Command("Reset Modified Source Files…", icon=ui.Icon.TRASH_2, group="Workspace"),
        ]

    def trigger_canary_audit(self) -> None:
        st = self.store.value
        if st.audit_running:
            return
        st.audit_running = True
        st.audit_progress = 0.0
        self.logs.info("[canary] Starting background audit across worker pool...")

        def worker_stream():
            steps = [
                (0.25, 2460.0, 6.6, "[canary] Probing edge-gateway TLS handshake... OK"),
                (0.55, 2530.0, 6.2, "[canary] Verifying slo_guard p99 <= 8.5 ms... PASS"),
                (0.85, 2590.0, 5.9, "[canary] Rebalancing 8 worker queues... OK"),
                (1.00, 2640.0, 5.7, "[canary] Canary audit passed with 0 regressions."),
            ]
            for prog, rps, p99, msg in steps:
                time.sleep(0.08)
                self.logs.info(msg)
                yield (prog, rps, p99)

        def on_chunk(item: tuple[float, float, float]) -> None:
            prog, rps, p99 = item
            s = self.store.value
            s.audit_progress = prog
            s.throughput_hist = [*s.throughput_hist[1:], rps]
            s.latency_hist = [*s.latency_hist[1:], p99]

        def on_done() -> None:
            self.store.value.audit_running = False

        self.runner.stream(worker_stream, on_item=on_chunk, on_done=on_done)

    def execute_command(self, ctx: ui.UI, cmd_idx: int) -> None:
        st = self.store.value
        if cmd_idx == 0:
            self.trigger_canary_audit()
        elif cmd_idx == 1:
            st.diff_mode = ui.DiffMode.INLINE if st.diff_mode == ui.DiffMode.SPLIT else ui.DiffMode.SPLIT
        elif cmd_idx == 2:
            self.saved_layout = ctx.dock_save("pulse_dock")
            ctx.toast("Workspace layout saved", tone=ui.Tone.SUCCESS)
        elif cmd_idx == 3:
            ctx.dock_load("pulse_dock", self.saved_layout or DEFAULT_DOCK_LAYOUT)
            ctx.toast("Restored dock layout", tone=ui.Tone.INFO)
        elif cmd_idx == 4:
            self.accent_idx = (self.accent_idx + 1) % len(self.ACCENT_CYCLE)
            ctx.accent = self.ACCENT_CYCLE[self.accent_idx]
        elif cmd_idx == 5:
            self.confirm_reset_open = True

    def build(self, ctx: ui.UI) -> None:
        st = self.store.value

        # Global Keyboard Shortcuts
        if ctx.shortcut(ui.Mod.CTRL, ui.Key.K):
            self.palette_open = not self.palette_open
        if ctx.shortcut(ui.Mod.CTRL, ui.Key.R):
            self.trigger_canary_audit()

        with ctx.column(width=ui.FILL, height=ui.FILL, bg=ui.Color.BACKGROUND):
            # 1. Native Desktop Menu Bar
            with ctx.menu_bar("main_menu"):
                with ctx.menu_bar_menu("File") as m:
                    if m:
                        if ctx.menu_item("Save Layout Snapshot", icon=ui.Icon.SAVE, shortcut="Ctrl+S"):
                            self.execute_command(ctx, 2)
                        if ctx.menu_item("Reset Source Files…", icon=ui.Icon.ROTATE_CCW, danger=True):
                            self.confirm_reset_open = True
                with ctx.menu_bar_menu("Diagnostics") as m:
                    if m:
                        if ctx.menu_item("Run Canary Audit", icon=ui.Icon.PLAY, shortcut="Ctrl+R"):
                            self.trigger_canary_audit()
                        if ctx.menu_item("Command Palette…", icon=ui.Icon.SEARCH, shortcut="Ctrl+K"):
                            self.palette_open = True

            # 2. Action Toolbar + Editable Breadcrumb Path Bar
            with ctx.toolbar("main_toolbar"):
                if ctx.toolbar_button(
                    ui.Icon.PLAY,
                    label="Run Audit",
                    tooltip="Run non-blocking BackgroundRunner canary check (Ctrl+R)",
                    disabled=st.audit_running,
                ):
                    self.trigger_canary_audit()
                if ctx.toolbar_button(ui.Icon.SAVE, label="Save Dock"):
                    self.execute_command(ctx, 2)
                if ctx.toolbar_button(ui.Icon.ROTATE_CCW, label="Reset Dock"):
                    self.execute_command(ctx, 3)
                ctx.toolbar_separator()

                pb = ctx.path_bar("studio_path", st.path_segments, icon=ui.Icon.FOLDER_OPEN, width=360)
                if pb.clicked >= 0:
                    del st.path_segments[pb.clicked + 1 :]
                elif pb.submitted:
                    parts = [seg for seg in pb.submitted.strip("/").split("/") if seg]
                    if parts:
                        st.path_segments = parts

                ctx.toolbar_spacer()
                if ctx.toolbar_button(ui.Icon.SEARCH, label="Ctrl+K", tooltip="Open Command Palette"):
                    self.palette_open = True
                if ctx.toolbar_button(ui.Icon.PALETTE, tooltip="Cycle OKLCH Accent"):
                    self.execute_command(ctx, 4)
                ctx.theme_toggle()

            # 3. Multi-Split Interactive Dockspace
            with ctx.dockspace("pulse_dock", layout=DEFAULT_DOCK_LAYOUT, width=ui.FILL, height=ui.GROW(1)):
                # Left Dock Panel: Hierarchical Service Tree
                with ctx.dock_panel("Services", icon=ui.Icon.FOLDER) as p:
                    if p:
                        with ctx.column(width=ui.FILL, height=ui.FILL, pad=8, gap=8):
                            self.filter_query = ctx.search(
                                "svc_q", self.filter_query, placeholder="Filter files…", size=ui.ControlSize.SM
                            )
                            with ctx.tree_table(
                                "svc_tree",
                                self.tree_cols,
                                self.tree_nodes,
                                width=ui.FILL,
                                height=ui.FILL,
                                sort=self.tree_sort,
                                labels=self.node_names,
                            ) as tree:
                                for idx in tree.rows():
                                    name = self.node_names[idx]
                                    if self.filter_query and self.filter_query.lower() not in name.lower() and idx >= 2:
                                        continue
                                    is_dir = bool(self.tree_nodes[idx].flags & ui.TreeFlags.HAS_CHILDREN)
                                    ico = ui.Icon.FOLDER if is_dir else ui.Icon.FILE_TEXT
                                    tree.name(name, icon=ico)
                                    tree.cell_text(self.node_status[idx])
                            if tree.sort is not None:
                                self.tree_sort = tree.sort
                            if tree.events.activated >= 0:
                                clicked_name = self.node_names[tree.events.activated]
                                if clicked_name in st.files:
                                    st.active_file = clicked_name
                                    folder = "docs" if clicked_name.endswith(".md") else "services"
                                    st.path_segments = ["pulse-studio", folder, clicked_name]

                # Center Panel 1: Syntax-Highlighted Code Editor
                is_dirty = st.files["slo_guard.py"] != BASELINE_SOURCE
                with ctx.dock_panel("Editor", icon=ui.Icon.CODE, dirty=is_dirty) as p:
                    if p:
                        with ctx.column(width=ui.FILL, height=ui.FILL, pad=8, gap=6):
                            with ctx.row(align=ui.Align.CENTER, gap=8):
                                ctx.badge(st.active_file, tone=ui.Tone.ACCENT, icon=ui.Icon.FILE_TEXT)
                                ctx.muted("Ctrl+F Find · Undo/Redo")
                                ctx.spacer()
                                for label_short, fname in (("SLO Guard", "slo_guard.py"), ("Gateway", "gateway.py")):
                                    if ctx.button(
                                        label_short,
                                        size=ui.ControlSize.SM,
                                        variant=ui.ButtonVariant.SECONDARY if st.active_file == fname else ui.ButtonVariant.GHOST,
                                    ):
                                        st.active_file = fname
                            lang = "markdown" if st.active_file.endswith(".md") else "python"
                            ed = ctx.code_editor(
                                "main_code_editor",
                                st.files[st.active_file],
                                lang=lang,
                                width=ui.FILL,
                                height=360,
                            )
                            st.files[st.active_file] = ed.text
                            st.cursor_line = ed.line
                            st.cursor_col = ed.column

                # Center Panel 2: Side-by-Side / Inline Myers Diff Viewer
                with ctx.dock_panel("Diff", icon=ui.Icon.GIT_BRANCH) as p:
                    if p:
                        with ctx.column(width=ui.FILL, height=ui.FILL, pad=8, gap=6):
                            _, stats = ui.diff_compute(BASELINE_SOURCE, st.files["slo_guard.py"])
                            with ctx.row(align=ui.Align.CENTER, gap=8):
                                mode_idx = 0 if st.diff_mode == ui.DiffMode.SPLIT else 1
                                mode_idx = ctx.segmented("diff_seg", ["Split", "Inline"], mode_idx, size=ui.ControlSize.SM)
                                st.diff_mode = ui.DiffMode.SPLIT if mode_idx == 0 else ui.DiffMode.INLINE
                                ctx.badge(f"+{stats.added} / -{stats.removed}", tone=ui.Tone.SUCCESS)
                                ctx.spacer()
                                ctx.muted("slo_guard.py (baseline vs. working copy)")
                            ctx.diff_view(
                                "slo_diff",
                                BASELINE_SOURCE,
                                st.files["slo_guard.py"],
                                mode=st.diff_mode,
                                language="python",
                                old_title="slo_guard.py (main)",
                                new_title="slo_guard.py (working)",
                                width=ui.FILL,
                                height=345,
                            )

                # Center Panel 3: Interactive GFM Markdown Playbook
                with ctx.dock_panel("Runbook", icon=ui.Icon.LIST_CHECKS) as p:
                    if p:
                        with ctx.scroll("runbook_scroll", width=ui.FILL, height=ui.FILL, pad=14):
                            md_res = ctx.markdown("runbook_md", st.files["runbook.md"], width=ui.FILL)
                            if md_res.task_toggled:
                                st.files["runbook.md"] = md_res.apply_task(st.files["runbook.md"])

                # Right Panel: Reusable OOP Telemetry Component
                with ctx.dock_panel("Telemetry", icon=ui.Icon.ACTIVITY) as p:
                    if p:
                        self.telemetry_panel(ctx)

                # Bottom Panel 1: Interactive Trace Flame Graph
                with ctx.dock_panel("Profiler", icon=ui.Icon.CPU) as p:
                    if p:
                        with ctx.column(width=ui.FILL, height=ui.FILL, pad=8, gap=6):
                            fl = ctx.flame_graph(
                                "req_flame",
                                self.flame_spans,
                                view=self.flame_view,
                                selected=self.selected_span,
                                width=ui.FILL,
                                height=195,
                            )
                            self.selected_span = fl.selected
                            if 0 <= fl.selected < len(self.flame_spans):
                                sp = self.flame_spans[fl.selected]
                                dur_ms = (sp.end - sp.start) * 1000.0
                                ctx.muted(f"Selected span: {sp.name} ({dur_ms:.2f} ms) — wheel to zoom, drag to pan")

                # Bottom Panel 2: Zero-GIL C Ring-Buffer Log Console
                with ctx.dock_panel("Logs", icon=ui.Icon.TERMINAL) as p:
                    if p:
                        ctx.log_view("studio_logs", self.logs, width=ui.FILL, height=ui.FILL, timestamps=True)

            # 4. Bottom Status Bar
            with ctx.status_bar("studio_status"):
                if st.audit_running:
                    ctx.status_bar_text("Running Canary Audit…", icon=ui.Icon.LOADER_CIRCLE, tone=ui.Tone.WARNING)
                    ctx.status_bar_progress(st.audit_progress, width=110)
                else:
                    ctx.status_bar_text(
                        f"Region: {TelemetryPanel.REGIONS[st.region_idx]}",
                        icon=ui.Icon.CIRCLE_CHECK,
                        tone=ui.Tone.SUCCESS,
                    )
                ctx.status_bar_spacer()
                ctx.status_bar_item(f"Limit: {math.floor(st.rate_limit_rps)} rps")
                ctx.status_bar_item(f"Ln {st.cursor_line}, Col {st.cursor_col}")
                ctx.status_bar_item(f"Accent: {ctx.accent.name}")

        # 5. Ctrl+K Command Palette & Confirmation Modal
        self.palette_open, chosen = ctx.command_palette(self.palette_open, self.commands)
        if chosen >= 0:
            self.execute_command(ctx, chosen)

        with ctx.dialog(
            "Reset Working Changes?",
            self.confirm_reset_open,
            description="Restore slo_guard.py to its baseline implementation?",
        ) as dlg:
            if dlg:
                with ctx.dialog_footer():
                    if ctx.button("Cancel", variant=ui.ButtonVariant.GHOST):
                        dlg.open = False
                    if ctx.button("Restore Baseline", variant=ui.ButtonVariant.DANGER):
                        st.files["slo_guard.py"] = BASELINE_SOURCE
                        self.logs.warn("[git] Restored slo_guard.py to baseline")
                        ctx.toast("Restored baseline slo_guard.py", tone=ui.Tone.WARNING)
                        dlg.open = False
        self.confirm_reset_open = dlg.open


if __name__ == "__main__":
    PulseStudioApp().run()
