"""End-to-end rendering, interaction, and pure-C99 utility tests for CUI v1.1.0 components."""

from __future__ import annotations

import nexa as ui


def test_version_and_pure_c99_utilities() -> None:
    assert ui.__version__ == "1.1.0"
    assert ui.native_version() == "1.1.0"

    # Headless Myers diff & word diff
    old_src = "alpha\nbeta\ngamma\ndelta\n"
    new_src = "alpha\nbeta_v2\ngamma\nepsilon\n"
    hunks, stats = ui.diff_compute(old_src, new_src)
    assert stats.added == 2
    assert stats.removed == 2
    assert stats.hunks >= 1
    assert len(hunks) == stats.hunks

    ok, old_r, new_r = ui.diff_words("return count + 1;", "return count + 42;")
    assert ok
    assert len(old_r) >= 1 and len(new_r) >= 1

    # Tree sibling sort
    names = ["root", "zeta.py", "alpha.py", "mid.py"]
    nodes = [
        ui.TreeNode(parent=-1, first_child=1, next_sibling=-1, flags=ui.TreeFlags.HAS_CHILDREN | ui.TreeFlags.OPEN),
        ui.TreeNode(parent=0, first_child=-1, next_sibling=2),
        ui.TreeNode(parent=0, first_child=-1, next_sibling=3),
        ui.TreeNode(parent=0, first_child=-1, next_sibling=-1),
    ]
    ui.tree_sort(nodes, root=0, key=lambda idx: names[idx])
    order = []
    cur = nodes[0].first_child
    while cur >= 0:
        order.append(names[cur])
        cur = nodes[cur].next_sibling
    assert order == ["alpha.py", "mid.py", "zeta.py"]

    # Flame sort, curve eval, OKLab gradient eval
    spans = [
        ui.FlameSpan("child_b", 5.0, 9.0, depth=1),
        ui.FlameSpan("root", 0.0, 10.0, depth=0),
        ui.FlameSpan("child_a", 1.0, 4.0, depth=1),
    ]
    ui.flame_sort(spans)
    assert [s.name for s in spans] == ["root", "child_a", "child_b"]

    keys = [
        ui.CurveKey(0.0, 0.0, mode=ui.CurveMode.LINEAR),
        ui.CurveKey(1.0, 10.0, mode=ui.CurveMode.LINEAR),
    ]
    assert abs(ui.curve_eval(keys, 0.5) - 5.0) < 1e-3

    stops = [
        ui.GradientStop(0.0, "#000000"),
        ui.GradientStop(1.0, "#ffffff"),
    ]
    mid_col = ui.gradient_eval(stops, 0.5)
    assert 80 < mid_col.r < 200 and mid_col.a == 255


def test_cui_1_1_text_code_and_diff_widgets() -> None:
    md_doc = (
        "# Release 1.1\n\n"
        "- [ ] Ship tree table\n"
        "- [x] Ship diff viewer\n\n"
        "> [!NOTE]\n"
        "> Zero external dependencies — check [docs](https://example.com).\n"
    )
    code_text = "def fib(n: int) -> int:\n    return n if n < 2 else fib(n - 1) + fib(n - 2)\n"

    with ui.SoftwareRenderer() as sw, ui.UI(width=1100, height=900, theme=ui.ThemeMode.DARK, accent=ui.Accent.VIOLET, renderer=sw) as ctx:
        for frame_i in range(2):
            with ctx.frame():
                with ctx.column(width=ui.FILL, height=ui.FILL, pad=16, gap=12):
                    res_pb = ctx.path_bar("pb", ["workspace", "nexa", "src", "ui.py"], icon=ui.Icon.FOLDER, menus=True)
                    assert res_pb.clicked == -1
                    with ctx.path_bar_menu("pb") as m:
                        if m:
                            ctx.menu_item("Open in terminal")

                    md_res = ctx.markdown("md", md_doc, width=ui.FILL)
                    chat_md = ctx.chat_message("**Markdown** in chat!", author="Nexa", markdown=True)
                    assert chat_md is not None
                    if frame_i > 0:
                        assert md_res.height > 0.0
                        assert chat_md.height > 0.0

                    ed_res = ctx.code_editor("ed", code_text, lang="python", width=ui.FILL, height=180)
                    txt, chg = ed_res
                    assert txt == code_text and not chg
                    assert ed_res.line_count == 3

                    ctx.code_editor_goto("ed", 2, 5)
                    ctx.code_editor_find("ed", "fib")

                    df_res = ctx.diff_view(
                        "df",
                        "line1\nold_val = 1\nline3\n",
                        "line1\nnew_val = 2\nline3\nextra\n",
                        language="python",
                        old_title="a/app.py",
                        new_title="b/app.py",
                        width=ui.FILL,
                        height=220,
                    )
                    assert df_res.added >= 1 and df_res.removed >= 1
                    rows = ctx.diff_view_rows("df")
                    assert len(rows) >= 3

        rgba = ctx.render_rgba()
        assert len(rgba) == 1100 * 900 * 4

    # Verify MarkdownResult.apply_task helper
    toggled = ui.MarkdownResult(task_offset=md_doc.index("[ ]") + 1, task_line=3, task_checked=True).apply_task(md_doc)
    assert "- [x] Ship tree table" in toggled


def test_cui_1_1_treetable_dockspace_and_creative_tools() -> None:
    nodes = [
        ui.TreeNode(-1, 1, -1, ui.TreeFlags.HAS_CHILDREN | ui.TreeFlags.OPEN),
        ui.TreeNode(0, -1, 2, ui.TreeFlags.SELECTED),
        ui.TreeNode(0, -1, -1, ui.TreeFlags.NONE),
    ]
    names = ["src", "ui.py", "build.py"]
    sizes = ["—", "14 KB", "12 KB"]
    cols = [
        ui.GridColumn("Name", width=220, sortable=True),
        ui.GridColumn("Size", width=90, align=ui.TextAlign.RIGHT, priority=1),
    ]

    payload = bytearray(b"\x7fELF\x02\x01\x01\x00NexaBinaryPayload0123456789ABCDEF")
    hex_sel = ui.HexSelection(0, 4, 0)
    hex_ranges = [ui.HexRange(0, 4, tone=ui.Tone.ACCENT, label="ELF Magic")]

    flame_spans = [
        ui.FlameSpan("frame", 0.0, 16.6, depth=0),
        ui.FlameSpan("layout", 0.4, 5.2, depth=1),
        ui.FlameSpan("raster", 5.4, 14.8, depth=1),
    ]
    flame_view = ui.FlameView(0.0, 16.6, 0.0)

    curve_keys = [
        ui.CurveKey(0.0, 0.0, out_dx=0.25, out_dy=0.0, mode=ui.CurveMode.SMOOTH),
        ui.CurveKey(1.0, 1.0, in_dx=-0.25, in_dy=0.0, mode=ui.CurveMode.SMOOTH),
    ]
    grad_stops = [
        ui.GradientStop(0.0, "#7747ff"),
        ui.GradientStop(0.5, "#0562ef"),
        ui.GradientStop(1.0, "#53dca6"),
    ]
    tracks = [
        ui.TimelineTrack(
            "Camera FOV",
            icon=ui.Icon.VIDEO,
            keys=[ui.CurveKey(0.0, 60.0), ui.CurveKey(2.5, 75.0), ui.CurveKey(5.0, 60.0)],
        ),
        ui.TimelineTrack(
            "Main Clip",
            icon=ui.Icon.SPARKLES,
            clips=[ui.TimelineClip(0.5, 4.2, name="intro.mp4", selected=True)],
        ),
    ]
    playhead = 1.25
    inspector_open = True

    with ui.SoftwareRenderer() as sw, ui.UI(width=1280, height=920, theme=ui.ThemeMode.DARK, accent=ui.Accent.BLUE, renderer=sw) as ctx:
        for _ in range(3):
            with ctx.frame():
                with ctx.dockspace(
                    "wb_dock",
                    layout="h0.32([*Explorer],v0.55([*Tools,Curves],[*Timeline]))",
                    width=ui.FILL,
                    height=ui.FILL,
                ):
                    with ctx.dock_panel("Explorer", icon=ui.Icon.FOLDER) as p_exp:
                        if p_exp:
                            with ctx.tree_table("tt", cols, nodes, height=240, labels=names) as tt:
                                for idx in tt.rows():
                                    tt.name(names[idx], icon=ui.Icon.FOLDER if nodes[idx].has_children else ui.Icon.FILE)
                                    tt.cell_text(sizes[idx])

                            with ctx.data_grid(
                                "dg", cols, 3, height=160, hide_checkboxes=True, cursor=0, anchor=0
                            ) as dg:
                                if dg:
                                    for r in dg.rows:
                                        dg.row(r)
                                        dg.cell_text(names[r])
                                        dg.cell_text(sizes[r])

                    with ctx.dock_panel("Tools", is_open=inspector_open, icon=ui.Icon.TERMINAL) as p_tools:
                        inspector_open = p_tools.open
                        if p_tools:
                            hx = ctx.hex_view(
                                "hx", payload, hex_sel, height=140, ranges=hex_ranges, editable=True
                            )
                            assert hx.selection.length == 4
                            fg = ctx.flame_graph("fg", flame_spans, view=flame_view, height=130)
                            assert fg.selected == -1

                    with ctx.dock_panel("Curves", icon=ui.Icon.SLIDERS_HORIZONTAL) as p_curves:
                        if p_curves:
                            cv = ctx.curve_editor("cv", curve_keys, height=150, show_playhead=True, playhead=0.4)
                            assert len(cv.keys) == 2
                            gr = ctx.gradient_editor("gr", grad_stops)
                            assert len(gr.stops) == 3

                    with ctx.dock_panel("Timeline", icon=ui.Icon.CLOCK) as p_tl:
                        if p_tl:
                            tl = ctx.timeline_editor("tl", tracks, playhead, start=0.0, end=6.0, height=180)
                            playhead = tl.time

                saved_layout = ctx.dock_save("wb_dock")
                assert "Explorer" in saved_layout and "Timeline" in saved_layout

        assert ctx.dock_load("wb_dock", saved_layout)
        rgba = ctx.render_rgba()
        assert len(rgba) == 1280 * 920 * 4


def test_added_helpers_and_aliases_work_end_to_end(tmp_path) -> None:
    assert ui.TabsVariant.LINE == ui.TabsVariant.UNDERLINE
    assert ui.TreeScope is ui.OpenStateScope
    assert ui.SwipeItemScope is ui.SwipeScope

    md_res = ui.MarkdownResult(task_offset=3, task_line=1, task_checked=True)
    assert ui.markdown_apply_task("- [ ] Ship release", md_res) == "- [x] Ship release"

    png_path = tmp_path / "tiny.png"
    ui.write_png(png_path, bytes([40, 120, 220, 255] * 16), 4, 4)
    png_bytes = png_path.read_bytes()

    with ui.SoftwareRenderer() as sw, ui.Context(width=320, height=200, renderer=sw) as ctx:
        tex, w, h = ctx.image_load_bytes(png_bytes)
        assert tex != 0 and (w, h) == (4, 4)
        with ctx.frame():
            with ctx.tree("Root", is_open=True) as tr:
                assert tr.expanded is True
                if tr:
                    ctx.label("Child")
            ctx.button("Delete")
            ctx.confirm_popover_open("del_pop")
            ctx.confirm_popover("del_pop", title="Sure?", danger=True)
            ctx.canvas(
                "bez_cv",
                120,
                60,
                lambda c, r: c.draw_bezier(
                    (r.x, r.y),
                    (r.x + 40, r.y),
                    (r.x + 80, r.y + 50),
                    (r.x + 120, r.y + 50),
                    ui.Color.ACCENT,
                    2.0,
                ),
            )
            ctx.image(tex, width=16, height=16)
        ctx.image_destroy(tex)

