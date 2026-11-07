"""Comprehensive widget parity & interaction tests covering all ~150 nexa components."""

from __future__ import annotations

import nexa as ui


def test_interactive_widget_value_returns_and_events() -> None:
    """Verify synthetic mouse clicks, text entry, keyboard shortcuts & file drops update Python values."""
    with ui.SoftwareRenderer() as sw, ui.UI(width=600, height=500, renderer=sw) as ctx:
        # 1. Button & Switch click interaction (layout resolves on end_frame())
        flag = False
        with ctx.frame():
            with ctx.column(pad=16, gap=12):
                flag = ctx.switch("Enable feature", flag)
                sw_id = ctx.last_id
                ctx.button("Run")
                btn_id = ctx.last_id
        sw_rect = ctx.get_rect(sw_id)
        btn_rect = ctx.get_rect(btn_id)
        assert sw_rect.w > 0 and btn_rect.w > 0

        ctx.input_click(sw_rect.x + 12, sw_rect.y + sw_rect.h * 0.5)
        with ctx.frame():
            with ctx.column(pad=16, gap=12):
                flag = ctx.switch("Enable feature", flag)
                ctx.button("Run")
        ctx.input_mouse_button(ui.MouseButton.LEFT, False)
        with ctx.frame():
            with ctx.column(pad=16, gap=12):
                flag = ctx.switch("Enable feature", flag)
                ctx.button("Run")
        assert flag is True

        # Click the button
        ctx.input_click(btn_rect.x + 10, btn_rect.y + 10)
        with ctx.frame():
            with ctx.column(pad=16, gap=12):
                flag = ctx.switch("Enable feature", flag)
                fired = ctx.button("Run")
        ctx.input_mouse_button(ui.MouseButton.LEFT, False)
        with ctx.frame():
            with ctx.column(pad=16, gap=12):
                flag = ctx.switch("Enable feature", flag)
                fired |= ctx.button("Run")
        assert fired is True

        # 2. Text input focus + UTF-8 typing + Enter submit
        val = ""
        with ctx.frame():
            val = ctx.input("username", val, autofocus=True)
        assert ctx.wants_keyboard

        ctx.input_text("kaya_42")
        ctx.input_key(ui.Key.ENTER, True)
        with ctx.frame():
            val = ctx.input("username", val)
            was_changed = ctx.changed
            was_submitted = ctx.submitted
        ctx.input_key(ui.Key.ENTER, False)
        assert val == "kaya_42"
        assert was_changed is True
        assert was_submitted is True

        # 3. OS File drop onto dropzone
        with ctx.frame():
            dropped, _ = ctx.dropzone("dz", accept="png;pdf")
            dz_id = ctx.last_id
        dz_rect = ctx.get_rect(dz_id)
        assert dropped == [] and dz_rect.w > 0

        ctx.input_file_drop(["/tmp/report.pdf", "/tmp/ignore.exe", "/tmp/chart.png"], dz_rect.x + 20, dz_rect.y + 20)
        with ctx.frame():
            dropped, _ = ctx.dropzone("dz", accept="png;pdf")
        assert dropped == ["/tmp/report.pdf", "/tmp/chart.png"]


def test_all_150_components_full_render_and_keepalive() -> None:
    """Exercise every widget family across multiple frames and rasterize with SoftwareRenderer.

    Specifically stresses deferred layout/paint pointer lifetimes (Table, DataGrid,
    Charts, Canvas, NodeEditor, Kanban, Inspector, LogView) to ensure zero dangling pointers.
    """
    log = ui.LogBuffer(max_lines=128)
    log.trace("trace msg")
    log.debug("debug msg")
    log.info("info msg")
    log.warn("warn msg")
    log.error("error msg")
    assert len(log) == 5
    assert log.get_line(2)[2] == "info msg"

    canvas_rects: list[ui.Rect] = []

    with ui.SoftwareRenderer(threads=2) as sw, ui.UI(width=1280, height=2400, renderer=sw) as ctx:
        tex = ctx.image_create(8, 8, bytes([80, 140, 240, 255] * 64))

        for frame_idx in range(3):
            with ctx.frame(1.0 / 60.0):
                # Chrome
                with ctx.menu_bar():
                    with ctx.menu_bar_menu("File") as mbm:
                        if mbm:
                            ctx.menu_item("New", shortcut="Ctrl N")
                            ctx.menu_separator()
                            ctx.menu_label("Recent")
                with ctx.toolbar():
                    ctx.toolbar_button(ui.Icon.PLAY, label="Run")
                    ctx.toolbar_toggle(True, ui.Icon.GRID_3X3, tooltip="Grid")
                    ctx.toolbar_separator()
                    ctx.toolbar_spacer()

                ctx.doc_tabs("dtabs", [ui.DocTab("a.py", dirty=True), ui.DocTab("b.py")], 0)

                with ctx.scroll("mega_scroll", width=ui.FILL, height=ui.FILL, pad=16, gap=14):
                    def _on_paint(c: ui.UI, r: ui.Rect) -> None:
                        canvas_rects.append(r)
                        with c.clip_scope(r):
                            c.draw_rect(r, ui.Color(30, 40, 60), radius=8)
                            c.draw_rect_border(r, ui.Color.TRANSPARENT, ui.Color.ACCENT, 1.5, radius=8)
                            c.draw_line((r.x, r.y), (r.x + r.w, r.y + r.h), ui.Color.SUCCESS, 2.0)
                            c.draw_circle((r.x + 40, r.y + 40), 14.0, ui.Color.WARNING)
                            c.draw_arc((r.x + 90, r.y + 40), 14.0, 0.0, 3.14, ui.Color.INFO, 2.0)
                            c.draw_polyline([(r.x + 10, r.y + 10), (r.x + 50, r.y + 20)], ui.Color.DANGER)
                            c.draw_polygon([(r.x + 120, r.y + 10), (r.x + 150, r.y + 10), (r.x + 135, r.y + 40)], ui.Color.ACCENT)
                            c.draw_text("Canvas OK", (r.x + 12, r.y + 56), ui.Color(255, 255, 255))

                    ctx.canvas("cv1", 260, 90, _on_paint)

                    # Text & Typography
                    ctx.heading("Heading", level=1)
                    ctx.text("Body text", selectable=True)
                    ctx.label("Label")
                    ctx.secondary("Secondary")
                    ctx.muted("Muted")
                    ctx.code("x = 42")
                    ctx.kbd("Ctrl K")
                    ctx.link("https://example.org")
                    ctx.icon(ui.Icon.STAR, 18)

                    # Actions
                    with ctx.row(gap=8, wrap=True):
                        ctx.button("Default")
                        ctx.icon_button(ui.Icon.PLUS, tooltip="Add")
                        with ctx.button_group():
                            ctx.button("Left")
                            ctx.button("Right")
                        ctx.copy_button("cp", "copied")
                        ctx.hold_button("Hold")
                        ctx.confirm_button("Delete")
                        ctx.status_button("Save", ui.Status.BUSY)
                        ctx.split_button("Deploy", ["Staging", "Prod"])
                        ctx.segmented("seg", ["One", "Two", "Three"], 1)
                        ctx.toggle_group("tg", ["B", "I", "U"], [True, False, True])
                        ctx.reactions("react", [ui.Reaction(ui.Icon.THUMBS_UP, 4, True)])
                        ctx.speed_dial("sd", [ui.SpeedAction(ui.Icon.PLUS, "Create")])
                        ctx.theme_switcher(0)
                        ctx.theme_toggle()

                    with ctx.swipe_item("sw_row", right=[ui.SwipeAction("Delete", tone=ui.Tone.DANGER)]):
                        ctx.list_item("Swipeable Row", subtitle="Subtitle", trailing="Now")

                    # Selection
                    ctx.checkbox("Check", True, description="Desc")
                    ctx.switch("Switch", False)
                    ctx.radio("Radio A", 0, 0)
                    ctx.radio_group("rg", ["A", "B"], 1)
                    ctx.radio_cards("rc", [ui.Choice("Pro", description="$12/mo", badge="Popular")], 0)
                    ctx.slider("Slider", 0.4, 0.0, 1.0, show_value=True)
                    ctx.range_slider("Range", 0.2, 0.8, 0.0, 1.0)
                    ctx.rating("Stars", 4, 5)
                    ctx.chip("Filter", True, icon=ui.Icon.CHECK)
                    ctx.control_tile("Wi-Fi", True, icon=ui.Icon.WIFI, detail="Connected")

                    # Inputs & Pickers
                    ctx.input("in1", "hello", label="Input", prefix="@")
                    ctx.search("srch", "query")
                    ctx.textarea("ta", "multi\nline", height=64)
                    ctx.number("num", 42.0, 0.0, 100.0, step=1.0)
                    ctx.scrub("Scrub", 50.0, 0.0, 100.0, suffix="px")
                    ctx.money_input("money", 199.95)
                    ctx.inline_edit("iedit", "Editable Title")
                    assert ctx.tag_input("tags_list", ["alpha", "beta"]) == ["alpha", "beta"]
                    assert isinstance(ctx.tag_input("tags_str", "alpha, beta"), str)
                    ctx.otp_input("otp", "123", 6)
                    ctx.password_strength("Tr0ub4dor&3!")
                    ctx.shortcut_recorder("srec", ui.KeyCombo(ui.Mod.PRIMARY, ui.Key.S))
                    ctx.signature_pad("sig", height=80)
                    ctx.dropzone("dz_all", compact=True)

                    ctx.select("sel", ["Red", "Green", "Blue"], 1)
                    ctx.combobox("cbo", ["Python", "C99", "Rust"], 0)
                    ctx.multi_select("msel", ["Read", "Write", "Admin"], [True, True, False])
                    ctx.calendar("cal", ui.Date(2026, 11, 6))
                    ctx.date_picker("dp", ui.Date(2026, 11, 6))
                    dr = ui.DateRange(ui.Date(2026, 11, 1), ui.Date(2026, 11, 10))
                    ctx.range_calendar("rcal", dr, months=1)
                    ctx.date_range_picker("drp", dr)
                    ctx.time_picker("tp", 14, 30)
                    ctx.time_dial("tdial", 9, 15, size=140)
                    ctx.wheel_picker("wheel", ["00", "15", "30", "45"], 2)
                    ctx.ruler_slider("Ruler", 25.0, 0.0, 100.0, unit="mm")
                    ctx.histogram_slider("Hist", [1, 4, 8, 6, 3, 2], 10.0, 80.0, 0.0, 100.0)
                    ctx.color_picker("cpick", ui.Color.hex("#3b82f6"))

                    # Navigation & Overlays
                    ctx.tabs("nav_tabs", ["Tab 1", "Tab 2"], 0)
                    ctx.nav_section("Section")
                    ctx.nav_item("Home", icon=ui.Icon.HOUSE, selected=True)
                    ctx.breadcrumb(["Root", "Child", "Leaf"])
                    ctx.pagination("pag", 1, 10)
                    ctx.stepper(["Cart", "Shipping", "Pay"], 1)
                    ctx.tab_bar("tbar", [ui.TabBarItem(ui.Icon.HOUSE, "Home", badge=2)], 0)
                    with ctx.dock("dock"):
                        ctx.dock_item(ui.Icon.TERMINAL, "Terminal", running=True)
                        ctx.dock_separator()
                        ctx.dock_item(ui.Icon.FOLDER, "Files")

                    ctx.button("Anchor")
                    ctx.tooltip("Helpful tooltip")
                    with ctx.popover("pop") as pop:
                        if pop:
                            ctx.text("Inside popover")
                    with ctx.hover_card("hcard") as hc:
                        if hc:
                            ctx.text("Hover card")
                    ctx.confirm_popover("cpop", title="Sure?")
                    with ctx.menu("Actions") as mn:
                        if mn:
                            ctx.menu_item("Edit")
                    with ctx.context_menu("ctxm") as cm:
                        if cm:
                            ctx.menu_item("Copy")
                    with ctx.user_menu("Ada Lovelace", detail="ada@analytical.engine") as um:
                        if um:
                            ctx.menu_item("Sign out")
                    with ctx.accordion("Details", True) as acc:
                        if acc:
                            ctx.text("Expanded content")
                    with ctx.expandable_card("Card Details", True, badge="v1") as ec:
                        if ec:
                            ctx.text("Inside expandable card")
                    ctx.expandable_text("etext", "Line 1\nLine 2\nLine 3\nLine 4", lines=2)

                    # Feedback
                    if frame_idx == 0:
                        th = ctx.toast("Saved", description="All good", action="Undo")
                        assert not ctx.toast_action_clicked(th)
                    ctx.alert("Notice", description="Inline alert", tone=ui.Tone.INFO)
                    ctx.banner("Release v1.0 is live", True, action="Read")
                    ctx.progress(0.65, show_value=True)
                    ctx.progress_ring("CPU", 0.72, size=64)
                    ctx.spinner(16)
                    ctx.loader(style=ui.LoaderStyle.ORBIT)
                    ctx.skeleton(120, 16)
                    ctx.badge("Active", tone=ui.Tone.SUCCESS, dot=True)
                    ctx.avatar("Grace Hopper", status="online")
                    ctx.avatar_group(["Ada", "Grace", "Margaret", "Barbara", "Katherine"])
                    ctx.avatar_upload("av_up", "Grace", size=56)
                    ctx.empty_state("Nothing here", icon=ui.Icon.INBOX, action="Add")
                    ctx.metric("Latency", "4.2 ms", delta=-12.5, spark=[6, 5, 5, 4.2], lower_is_better=True)
                    ctx.meter("Disk", 42.0, 100.0, "GB")
                    ctx.countdown("cdown", 90061.0)
                    ctx.checklist("chklist", [ui.CheckStep("Step 1", done=True), ui.CheckStep("Step 2", action="Go")])

                    # Data, Virtual List (1M rows!), Table & DataGrid (100K rows!)
                    with ctx.tree("src", True) as tr:
                        if tr:
                            with ctx.tree("main.py", leaf=True):
                                pass
                    with ctx.virtual_list("vlist_1m", 1_000_000, 28.0, 140.0) as vl:
                        for idx in vl.indices:
                            ctx.text(f"Virtual row #{idx}")
                    with ctx.reorder("reord", [0, 1, 2]) as ro:
                        for p in range(3):
                            with ro.item(p):
                                ctx.text(f"Item {ro.order[p]}")
                    ctx.timeline_item("Deployed", time="12:00", description="Production rollout", last=True)

                    with ctx.table(
                        "tbl",
                        [ui.TableColumn("Name", sortable=True), ui.TableColumn("Score", align=ui.TextAlign.RIGHT)],
                        sort=ui.TableSort(0, False),
                        height=120,
                        striped=True,
                    ) as tbl:
                        if tbl:
                            for name_s, sc in (("Alice", "98"), ("Bob", "91")):
                                tbl.row()
                                tbl.cell_text(name_s)
                                tbl.cell_text(sc)

                    with ctx.data_grid(
                        "dgrid",
                        [ui.GridColumn("ID", width=80, sortable=True), ui.GridColumn("Value", width=160)],
                        1000,
                        height=160,
                        selected=[False] * 1000,
                        sort=ui.TableSort(0, False),
                        cursor=0,
                    ) as dg:
                        if dg:
                            for r in dg.rows:
                                dg.row(r)
                                dg.cell_text(f"#{r}")
                                dg.edit(f"val_{r}")

                    ctx.filter_bar("fbar", [ui.FilterField("Kind", ["Bug", "Feat"])], [1], "")
                    ctx.code_block("cb", "def add(a: int, b: int) -> int:\n    return a + b\n", lang="python", line_numbers=True)
                    assert ctx.json_view("jv", '{"ok": true, "items": [1, 2, 3]}')

                    # All 16 Charts
                    ser = [ui.Series("S1", [10, 25, 18, 32])]
                    viz = [ui.VizItem("A", 40), ui.VizItem("B", 35), ui.VizItem("C", 25)]
                    ctx.line_chart("lc", ser, height=120, smooth=True, area=True)
                    ctx.bar_chart("bc", ser, height=120)
                    ctx.donut_chart("dc", [60, 40], ["Used", "Free"], height=120)
                    ctx.sparkline([3, 7, 5, 9, 8])
                    ctx.gauge("Load", 0.68, size=100)
                    ctx.heatmap("hm", [1, 2, 3, 4, 5, 6], 2, 3, row_labels=["R1", "R2"], col_labels=["C1", "C2", "C3"])
                    ctx.calendar_heatmap("chm", ui.Date(2026, 10, 1), [1, 3, 0, 4, 2, 5, 1] * 4)
                    ctx.treemap("tmap", viz, height=120)
                    ctx.radar_chart("rad", [ui.Series("P1", [8, 7, 9, 6])], ["Speed", "Size", "DX", "Safety"], size=140)
                    ctx.funnel("fun", viz, height=120)
                    ctx.sankey("snk", ["In", "Mid", "Out"], [ui.SankeyLink(0, 1, 10), ui.SankeyLink(1, 2, 10)], height=120)
                    ctx.waffle("waf", viz)
                    ctx.split_bar("sbar", viz)
                    ctx.bar_list("blist", viz)
                    ctx.activity_rings("rings", [ui.VizItem("Move", 0.85), ui.VizItem("Stand", 0.6)], size=110, legend=True)
                    ctx.scatter_chart("scat", [ui.ScatterSeries("Pts", [(1, 2), (3, 5), (4, 4)], sizes=[6, 10, 8])], height=120)

                    # Planning, AI, Social, Media, Motion
                    with ctx.kanban("kb") as kb:
                        with kb.column("Todo", 1):
                            with kb.card(1):
                                ctx.text("Ship nexa")
                    ctx.week_calendar("wcal", ui.Date(2026, 11, 2), [ui.CalEvent("Sync", 0, 9.0, 10.0)], height=180)
                    ctx.gantt("gnt", [ui.GanttTask("Build", 0, 5, 0.5)], ui.Date(2026, 11, 2), 10, height=140)

                    with ctx.reasoning("reas", thinking=True, seconds=1.5) as rs:
                        if rs:
                            ctx.text("Reasoning trace...")
                    ctx.tool_call("tc1", "bash", input_text='{"cmd": "pytest"}', output_text='{"rc": 0}')
                    ctx.agent_plan("aplan", [ui.PlanStep("Step A", status=ui.TaskStatus.DONE)])
                    ctx.agent_status("Working", seconds=2.0)
                    ctx.source_list("slist", [ui.Source("Doc", "https://example.com", "Snippet")])
                    ctx.citation(1, ui.Source("Ref", "https://example.com"))
                    ctx.context_meter("cmeter", 2048, 8192)
                    ctx.response_actions("racts", copy_text="hello")
                    ctx.prompt_suggestions("psug", [ui.PromptSuggestion("Try me")])
                    ctx.model_picker("mpick", [ui.Model("Atlas")], 0)
                    ctx.chat_composer("ccomp", "draft")
                    ctx.voice_orb("vorb", ui.VoiceState.LISTENING, 0.5, size=56)

                    ctx.chat_divider("Today")
                    ctx.chat_message("Hello there!", author="Sam", time="10:00")
                    ctx.typing_indicator("Sam")
                    ctx.comment("cmt1", "Sam", "Nice work!", likes=2)
                    ctx.presence("pres1", [ui.PresenceUser("Sam")])

                    ctx.image(tex, width=32, height=32, radius=6)
                    with ctx.carousel("car1", 2, 0, height=100) as car:
                        for s_i in range(2):
                            with car.slide():
                                ctx.text(f"Slide {s_i}")
                    ctx.image_compare("icmp", tex, tex, 0.5, height=100)
                    with ctx.card_stack("cstack", 2, height=100) as cs:
                        for d_i in range(2):
                            with cs.item(d_i):
                                ctx.text(f"Card {d_i}")
                    ctx.waveform("wf1", [0.2, 0.6, 0.9, 0.4], 0.5, height=48)
                    ctx.now_playing("np1", ui.NowPlaying("Song", "Artist", position=12.0, duration=180.0, playing=True))
                    ctx.counter("cnt1", 12345.67)
                    ctx.ticker("tkr1", [ui.TickerItem("NEXA", "1.0.0", 100.0)])

                    ctx.shimmer_text("Shimmer")
                    ctx.typewriter("tw1", "Typed text")
                    ctx.text_reveal("tr1", "Revealed words")
                    ctx.word_rotate("wr1", ["Fast", "Small"], 1.5)
                    ctx.number_roll("nr1", "$9,420")
                    ctx.gradient_text("Gradient", from_color=ui.Color.ACCENT, to_color=ui.Color.DANGER)
                    with ctx.spotlight("spot1", pad=12):
                        ctx.text("Spotlight")
                    _ = ctx.animate("anim1", 1.0)
                    _ = ctx.animate_spring("anim2", 1.0)

                    # Tools, Node Editor & Custom Canvas
                    with ctx.inspector("insp1") as ins:
                        if ins:
                            vis, _ = ctx.inspector_group("Props", True)
                            if vis:
                                ctx.prop_float("F", 1.5)
                                ctx.prop_int("I", 3)
                                ctx.prop_text("T", "abc")
                                ctx.prop_bool("B", True)
                                ctx.prop_enum("E", ["X", "Y"], 0)
                                ctx.prop_color("C", ui.Color.ACCENT)
                                ctx.prop_vec2("V2", (1.0, 2.0))
                                ctx.prop_vec3("V3", (1.0, 2.0, 3.0))
                                ctx.prop_vec4("V4", (1.0, 2.0, 3.0, 4.0))
                    ctx.log_view("lview", log, height=120, timestamps=True)

                    with ctx.node_editor("ned", ui.NodeView(0, 0, 1.0), height=200) as ned:
                        if ned:
                            with ned.node(1, 20, 20, "Source"):
                                ned.output(10, "Out")
                        with ned.node(2, 240, 20, "Sink"):
                            ned.input(20, "In")
                        ned.link(100, 10, 20)

                    st_mv = ctx.state_buffer("custom_widget_state", 16)
                    st_mv[0] = 77
                    assert st_mv[0] == 77

                # Overlays at root level
                with ctx.dialog("Modal", frame_idx == 1) as dlg:
                    if dlg:
                        ctx.text("Dialog body")
                        with ctx.dialog_footer():
                            ctx.button("Close")
                with ctx.sheet("Drawer", frame_idx == 2) as sh:
                    if sh:
                        ctx.text("Sheet body")

                with ctx.status_bar():
                    ctx.status_bar_text("OK")
                    ctx.status_bar_spacer()
                    ctx.status_bar_progress(0.5, label="Indexing")
                    ctx.status_bar_item("Ln 1")

            pixels = ctx.render_rgba()
            assert len(pixels) == 1280 * 2400 * 4

        ctx.image_destroy(tex)

    assert len(canvas_rects) == 3
    assert canvas_rects[-1].w == 260.0 and canvas_rects[-1].h == 90.0
    log.close()


def test_dialog_close_interactions() -> None:
    with ui.SoftwareRenderer() as sw, ui.UI(width=600, height=400, renderer=sw) as ctx:
        is_open = True
        force_close = False
        close_btn_id = 0

        def step() -> None:
            nonlocal is_open, force_close, close_btn_id
            with ctx.frame():
                with ctx.dialog("Confirm", is_open) as dlg:
                    if dlg:
                        if ctx.button("Close") or force_close:
                            dlg.open = False
                            force_close = False
                        close_btn_id = ctx.last_id
                is_open = dlg.open

        # 1. Close via inner "Close" button click
        for _ in range(30):
            step()
        r = ctx.get_rect(close_btn_id)
        ctx.input_click(r.x + r.w * 0.5, r.y + r.h * 0.5)
        step()
        ctx.input_mouse_button(ui.MouseButton.LEFT, False)
        step()
        assert is_open is False

        # 2. Close via single-frame trackpad tap on backdrop scrim
        is_open = True
        for _ in range(30):
            step()
        ctx.input_mouse_move(10.0, 10.0)
        ctx.input_mouse_button(ui.MouseButton.LEFT, True)
        ctx.input_mouse_button(ui.MouseButton.LEFT, False)
        step()
        assert is_open is False

        # 3. Close via Escape key
        is_open = True
        for _ in range(30):
            step()
        ctx.input_key(ui.Key.ESCAPE, True)
        step()
        ctx.input_key(ui.Key.ESCAPE, False)
        assert is_open is False

        # 4. Programmatic dlg.open = False on an idle settled frame schedules redraw
        is_open = True
        for _ in range(120):
            step()
        assert ctx.needs_redraw is False
        force_close = True
        step()
        assert is_open is False
        assert ctx.needs_redraw is True

