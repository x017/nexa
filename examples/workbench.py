"""Developer & Creative Workbench (CUI 1.1): Dockspace, TreeTable, PathBar, CodeEditor, Diff, Markdown, Hex, Flame, Curves & Timeline."""

from __future__ import annotations

import nexa as ui


OLD_KERNEL = """\
def schedule_frame(tasks: list[str], budget_ms: float = 16.6) -> int:
    ran = 0
    elapsed = 0.0
    for name in tasks:
        if elapsed > budget_ms:
            break
        elapsed += 1.8
        ran += 1
    return ran
"""

NEW_KERNEL = """\
def schedule_frame(tasks: list[str], budget_ms: float = 8.33) -> tuple[int, float]:
    ran = 0
    elapsed = 0.0
    for name in tasks:
        cost = 0.95 if name.startswith("fast:") else 1.45
        if elapsed + cost > budget_ms:
            break
        elapsed += cost
        ran += 1
    return ran, round(elapsed, 2)
"""

RELEASE_NOTES_MD = """\
### Release Checklist — `nexa` 1.1

- [x] Sync native CUI 1.1 C99 core (`dockspace`, `tree_table`, `code_editor`, `diff_view`)
- [x] Bind zero-copy `hex_view`, `flame_graph`, `curve_editor`, `gradient_editor` & `timeline_editor`
- [ ] Run frame-time flame profiler across 4K viewports

> [!TIP]
> Drag any panel tab out of its strip to split or stack panes interactively, or click **Save Layout** in the toolbar.
"""


def main() -> None:
    segments = ["workspace", "nexa", "src", "scheduler.py"]
    center_mode = 0  # 0 = Code Editor, 1 = Diff Viewer, 2 = Markdown Notes

    # Hierarchical project tree for tree_table
    names = [
        "nexa",
        "src",
        "scheduler.py",
        "render_sw.c",
        "dock_layout.py",
        "assets",
        "lut_ramp.bin",
    ]
    kinds = ["Folder", "Folder", "Python", "C99", "Python", "Folder", "Binary"]
    sizes = ["—", "—", "4.2 KB", "38.6 KB", "9.1 KB", "—", "512 B"]
    tree_nodes = [
        ui.TreeNode(parent=-1, first_child=1, next_sibling=-1, flags=ui.TreeFlags.HAS_CHILDREN | ui.TreeFlags.OPEN),
        ui.TreeNode(parent=0, first_child=2, next_sibling=5, flags=ui.TreeFlags.HAS_CHILDREN | ui.TreeFlags.OPEN),
        ui.TreeNode(parent=1, first_child=-1, next_sibling=3, flags=ui.TreeFlags.SELECTED),
        ui.TreeNode(parent=1, first_child=-1, next_sibling=4),
        ui.TreeNode(parent=1, first_child=-1, next_sibling=-1),
        ui.TreeNode(parent=0, first_child=6, next_sibling=-1, flags=ui.TreeFlags.HAS_CHILDREN | ui.TreeFlags.OPEN),
        ui.TreeNode(parent=5, first_child=-1, next_sibling=-1),
    ]
    tree_cols = [
        ui.GridColumn("Name", width=185, sortable=True),
        ui.GridColumn("Type", width=68, priority=2),
        ui.GridColumn("Size", width=68, align=ui.TextAlign.RIGHT, priority=1),
    ]
    tree_sort = ui.TableSort(0, False)

    source_code = NEW_KERNEL
    markdown_doc = RELEASE_NOTES_MD
    diff_mode = ui.DiffMode.SPLIT

    # Binary packet for hex_view
    packet = bytearray(
        b"\x89NXA\r\n\x1a\n\x00\x01\x01\x00scheduler_lut_v11\x00"
        b"\x00\x10\x20\x30\x40\x55\x68\x7f\x8c\x9a\xb0\xc8\xe0\xff\x00\x42"
    )
    hex_sel = ui.HexSelection(0, 8, 0)
    hex_ranges = [
        ui.HexRange(0, 8, tone=ui.Tone.ACCENT, label="Nexa Magic"),
        ui.HexRange(8, 4, tone=ui.Tone.SUCCESS, label="Version 1.1"),
        ui.HexRange(12, 17, tone=ui.Tone.WARNING, label="Symbol"),
    ]

    # Profiler spans for flame_graph (sorted by depth, start via ui.flame_sort)
    flame_spans = ui.flame_sort([
        ui.FlameSpan("App.frame", 0.0000, 0.00812, depth=0, color_key=1),
        ui.FlameSpan("cui_layout", 0.00015, 0.00150, depth=1, color_key=2),
        ui.FlameSpan("dock + tree", 0.00025, 0.00125, depth=2, color_key=3),
        ui.FlameSpan("code_editor", 0.00155, 0.00380, depth=1, color_key=4),
        ui.FlameSpan("tokenize", 0.00165, 0.00320, depth=2, color_key=5),
        ui.FlameSpan("cui_render_sw", 0.00390, 0.00800, depth=1, color_key=6),
        ui.FlameSpan("glyph_blit", 0.00415, 0.00685, depth=2, color_key=7),
    ])
    flame_view = ui.FlameView(0.0, 0.00812, 0.0)
    selected_span = 2
    selected_key = 1
    selected_stop = 1

    # Easing curve & OKLab color ramp
    curve_keys = [
        ui.CurveKey(0.0, 0.0, out_dx=0.22, out_dy=0.05, mode=ui.CurveMode.SMOOTH),
        ui.CurveKey(0.48, 0.78, in_dx=-0.14, in_dy=-0.18, out_dx=0.16, out_dy=0.14, mode=ui.CurveMode.SMOOTH),
        ui.CurveKey(1.0, 1.0, in_dx=-0.24, in_dy=0.0, mode=ui.CurveMode.SMOOTH),
    ]
    grad_stops = [
        ui.GradientStop(0.0, "#7747ff"),
        ui.GradientStop(0.48, "#0562ef"),
        ui.GradientStop(1.0, "#53dca6"),
    ]

    # Multi-track timeline
    tracks = [
        ui.TimelineTrack(
            "Ease Weight",
            icon=ui.Icon.ACTIVITY,
            color=1,
            keys=[ui.CurveKey(0.0, 0.0), ui.CurveKey(1.8, 1.0), ui.CurveKey(4.2, 0.45), ui.CurveKey(6.0, 1.0)],
        ),
        ui.TimelineTrack(
            "Shader Pass",
            icon=ui.Icon.SPARKLES,
            color=3,
            clips=[
                ui.TimelineClip(0.2, 2.8, name="topo_dither", selected=True),
                ui.TimelineClip(3.0, 5.7, name="composite_hdr"),
            ],
        ),
    ]
    playhead = 1.85
    saved_layout = ""
    editor_line = 1
    editor_col = 1

    default_layout = "h0.27([*Explorer],v0.54([*Editor,Diff,Notes],h0.48([*Profiler,Hex],[*Timeline])))"

    def draw(ctx: ui.UI) -> None:
        nonlocal center_mode, source_code, markdown_doc, diff_mode, selected_span
        nonlocal selected_key, selected_stop, playhead, saved_layout, tree_sort, editor_line, editor_col

        with ctx.column(width=ui.FILL, height=ui.FILL, bg=ui.Color.BACKGROUND):
            # Top Toolbar + Editable Breadcrumb Path Bar
            with ctx.toolbar():
                if ctx.toolbar_button(ui.Icon.SAVE, label="Save Layout", tooltip="Snapshot dock layout"):
                    saved_layout = ctx.dock_save("studio_dock")
                if ctx.toolbar_button(ui.Icon.ROTATE_CCW, label="Reset", tooltip="Restore default panes"):
                    ctx.dock_load("studio_dock", saved_layout or default_layout)
                ctx.toolbar_separator()
                pb = ctx.path_bar("wb_path", segments, icon=ui.Icon.FOLDER_OPEN, width=420, menus=True)
                if pb.clicked >= 0:
                    del segments[pb.clicked + 1 :]
                elif pb.submitted:
                    parts = [p for p in pb.submitted.strip("/").split("/") if p]
                    if parts:
                        segments[:] = parts
                with ctx.path_bar_menu("wb_path") as pm:
                    if pm:
                        ctx.menu_item(f"Copy '{segments[pm.segment]}'")
                        ctx.menu_item("Reveal in Explorer")
                ctx.toolbar_spacer()
                ctx.badge("CUI 1.1", tone=ui.Tone.ACCENT)

            # Multi-split Docking Workspace
            with ctx.box(width=ui.FILL, height=ui.GROW(1), pad=6):
                with ctx.dockspace("studio_dock", layout=default_layout, width=ui.FILL, height=ui.FILL):
                    with ctx.dock_panel("Explorer", icon=ui.Icon.FOLDER) as p_exp:
                        if p_exp:
                            with ctx.column(width=ui.FILL, height=ui.FILL, pad=8, gap=8):
                                with ctx.tree_table(
                                    "proj_tree",
                                    tree_cols,
                                    tree_nodes,
                                    width=ui.FILL,
                                    height=185,
                                    sort=tree_sort,
                                    labels=names,
                                ) as tt:
                                    for idx in tt.rows():
                                        icon = ui.Icon.FOLDER if tree_nodes[idx].has_children else ui.Icon.FILE
                                        tt.name(names[idx], icon=icon)
                                        tt.cell_text(kinds[idx])
                                        tt.cell_text(sizes[idx])
                                if tt.sort is not None:
                                    tree_sort = tt.sort
                                if tt.events.activated >= 0:
                                    segments[-1] = names[tt.events.activated]

                                ctx.separator()
                                ctx.muted("EASING CURVE & OKLAB RAMP")
                                cv = ctx.curve_editor(
                                    "wb_curve",
                                    curve_keys,
                                    width=ui.FILL,
                                    height=130,
                                    selected=selected_key,
                                    show_playhead=True,
                                    playhead=min(1.0, max(0.0, playhead / 6.0)),
                                )
                                selected_key = cv.selected
                                gr = ctx.gradient_editor("wb_grad", grad_stops, width=ui.FILL, selected=selected_stop)
                                selected_stop = gr.selected

                    with ctx.dock_panel("Editor", icon=ui.Icon.CODE, dirty=(source_code != NEW_KERNEL)) as p_ed:
                        if p_ed:
                            with ctx.column(width=ui.FILL, height=ui.FILL, pad=8):
                                ed = ctx.code_editor(
                                    "wb_editor",
                                    source_code,
                                    lang="python",
                                    width=ui.FILL,
                                    height=315,
                                )
                                source_code = ed.text
                                editor_line, editor_col = ed.line, ed.column

                    with ctx.dock_panel("Diff", icon=ui.Icon.GIT_BRANCH) as p_diff:
                        if p_diff:
                            with ctx.column(width=ui.FILL, height=ui.FILL, pad=8, gap=6):
                                with ctx.row(gap=8, align=ui.Align.CENTER):
                                    is_inline = ctx.switch("Unified inline diff", diff_mode == ui.DiffMode.INLINE)
                                    diff_mode = ui.DiffMode.INLINE if is_inline else ui.DiffMode.SPLIT
                                ctx.diff_view(
                                    "wb_diff",
                                    OLD_KERNEL,
                                    source_code,
                                    mode=diff_mode,
                                    language="python",
                                    old_title="a/scheduler.py",
                                    new_title="b/scheduler.py",
                                    width=ui.FILL,
                                    height=280,
                                )

                    with ctx.dock_panel("Notes", icon=ui.Icon.FILE_TEXT) as p_md:
                        if p_md:
                            with ctx.scroll("wb_md_scroll", width=ui.FILL, height=315):
                                with ctx.column(width=ui.FILL, pad=10):
                                    md = ctx.markdown("wb_md", markdown_doc, width=ui.FILL)
                                    if md.task_toggled:
                                        markdown_doc = md.apply_task(markdown_doc)

                    with ctx.dock_panel("Profiler", icon=ui.Icon.ACTIVITY) as p_prof:
                        if p_prof:
                            with ctx.column(width=ui.FILL, height=ui.FILL, pad=8):
                                fg = ctx.flame_graph(
                                    "wb_flame",
                                    flame_spans,
                                    view=flame_view,
                                    selected=selected_span,
                                    width=ui.FILL,
                                    height=230,
                                )
                                selected_span = fg.selected

                    with ctx.dock_panel("Timeline", icon=ui.Icon.CLOCK) as p_tl:
                        if p_tl:
                            with ctx.column(width=ui.FILL, height=ui.FILL, pad=8):
                                tl = ctx.timeline_editor(
                                    "wb_tl",
                                    tracks,
                                    playhead,
                                    start=0.0,
                                    end=6.0,
                                    width=ui.FILL,
                                    height=230,
                                )
                                playhead = tl.time

                    with ctx.dock_panel("Hex", icon=ui.Icon.CPU) as p_hex:
                        if p_hex:
                            with ctx.column(width=ui.FILL, height=ui.FILL, pad=8):
                                ctx.hex_view(
                                    "wb_hex",
                                    packet,
                                    hex_sel,
                                    width=ui.FILL,
                                    height=230,
                                    ranges=hex_ranges,
                                    editable=True,
                                )

            with ctx.status_bar():
                ctx.status_bar_text("nexa 1.1 Workbench", icon=ui.Icon.SPARKLES, tone=ui.Tone.ACCENT)
                ctx.status_bar_spacer()
                ctx.status_bar_text(f"Playhead {playhead:.2f}s")
                ctx.status_bar_text(f"Ln {editor_line}, Col {editor_col}")
                ctx.status_bar_item("C99 + Python")

    with ui.App(
        "Workbench Studio — nexa 1.1",
        width=1240,
        height=855,
        theme=ui.ThemeMode.DARK,
        accent=ui.Accent.VIOLET,
    ) as app:
        app.run(draw)


if __name__ == "__main__":
    main()
