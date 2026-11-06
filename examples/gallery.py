"""Master IDE & Component Gallery: Chrome, Node Editor, Property Inspector, Log Console & Vector Canvas."""

from __future__ import annotations

import math

import yapps as ui


def main() -> None:
    tabs = [
        ui.DocTab("shader_graph.yapps", icon=ui.Icon.GIT_BRANCH, dirty=True),
        ui.DocTab("vector_canvas.py", icon=ui.Icon.PALETTE),
        ui.DocTab("motion_fx.py", icon=ui.Icon.SPARKLES),
    ]
    active_tab = 0
    show_grid = True
    snap_nodes = False

    node_view = ui.NodeView(40.0, 30.0, 1.0)
    nodes = [
        {"id": 1, "title": "UV Coordinates", "x": 40.0, "y": 60.0, "icon": ui.Icon.GRID_3X3, "in": [], "out": [(11, "UV", 1)]},
        {"id": 2, "title": "Simplex Noise", "x": 290.0, "y": 50.0, "icon": ui.Icon.ACTIVITY, "in": [(21, "Coords", 1)], "out": [(22, "Height", 2)]},
        {"id": 3, "title": "PBR Surface", "x": 560.0, "y": 80.0, "icon": ui.Icon.LAYERS, "in": [(31, "Displacement", 2)], "out": []},
    ]
    links = [[1, 11, 21], [2, 22, 31]]
    next_link_id = 3

    # Inspector state
    grp_xform = True
    grp_style = True
    pos3 = (0.0, 1.25, -4.0)
    roughness = 0.35
    octaves = 4
    tint = ui.Color.hex("#3b82f6")
    blend_mode = 0

    log = ui.LogBuffer(max_lines=1024)
    log.info("Initialized yapps Studio workspace")
    log.debug("Loaded embedded Inter, Geist & Lucide font atlases")
    log.warn("Shader graph has unsaved edits")

    def draw(ctx: ui.UI) -> None:
        nonlocal active_tab, show_grid, snap_nodes, node_view, next_link_id
        nonlocal grp_xform, grp_style, pos3, roughness, octaves, tint, blend_mode

        with ctx.column(width=ui.FILL, height=ui.FILL, bg=ui.Color.BACKGROUND):
            # Desktop Menu Bar
            with ctx.menu_bar():
                with ctx.menu_bar_menu("File") as m:
                    if m:
                        if ctx.menu_item("Compile Graph", icon=ui.Icon.PLAY, shortcut="F5"):
                            log.info("Compiled 3 shader nodes in 1.4 ms")
                        ctx.menu_separator()
                        if ctx.menu_item("Clear Console", icon=ui.Icon.TRASH):
                            log.clear()
                with ctx.menu_bar_menu("View") as m:
                    if m:
                        if ctx.menu_item("Toggle Grid", checked=show_grid):
                            show_grid = not show_grid
                        if ctx.menu_item("Toggle Dark Mode", icon=ui.Icon.MOON):
                            ctx.theme_mode = (
                                ui.ThemeMode.LIGHT if ctx.theme_mode == ui.ThemeMode.DARK else ui.ThemeMode.DARK
                            )

            # Toolbar
            with ctx.toolbar():
                if ctx.toolbar_button(ui.Icon.PLAY, label="Build", tooltip="Compile shader graph"):
                    log.info(f"Built shader (roughness={roughness:.2f}, octaves={octaves})")
                ctx.toolbar_separator()
                show_grid = ctx.toolbar_toggle(show_grid, ui.Icon.GRID_3X3, tooltip="Show canvas grid")
                snap_nodes = ctx.toolbar_toggle(snap_nodes, ui.Icon.TARGET, tooltip="Snap to grid")
                ctx.toolbar_spacer()
                ctx.theme_toggle()

            # Document Tabs
            if tabs:
                res = ctx.doc_tabs("docs", tabs, active_tab, shortcuts=True)
                active_tab = res.apply_to(tabs)

            # Central Workspace + Right Property Inspector
            with ctx.row(width=ui.FILL, height=ui.FILL):
                with ctx.column(width=ui.GROW(3), height=ui.FILL):
                    cur_title = tabs[active_tab].title if tabs else ""
                    if "shader_graph" in cur_title:
                        with ctx.node_editor(
                            "shader_ed", node_view, width=ui.FILL, height=ui.FILL, no_grid=not show_grid
                        ) as ed:
                            if ed:
                                for nd in nodes:
                                    with ed.node(nd["id"], nd["x"], nd["y"], nd["title"], icon=nd["icon"]) as ns:
                                        for pid, plbl, ptype in nd["in"]:
                                            ed.input(pid, plbl, pin_type=ptype)
                                        if nd["id"] == 2:
                                            with ed.content():
                                                roughness = ctx.slider("##r", roughness, 0.0, 1.0)
                                        for pid, plbl, ptype in nd["out"]:
                                            ed.output(pid, plbl, pin_type=ptype)
                                    nd["x"], nd["y"] = ns.x, ns.y
                                for lid, fp, tp in links:
                                    ed.link(lid, fp, tp)
                        node_view = ed.view
                        for fp, tp in ed.created_links:
                            links.append([next_link_id, fp, tp])
                            log.info(f"Connected pin {fp} -> {tp}")
                            next_link_id += 1
                        for r_id in ed.removed_links:
                            links[:] = [l for l in links if l[0] != r_id]
                            log.warn(f"Removed link #{r_id}")

                    elif "vector_canvas" in cur_title:
                        def paint_art(c: ui.UI, r: ui.Rect) -> None:
                            c.draw_rect_gradient(r, ui.Color(18, 24, 38), ui.Color(30, 41, 59), radius=12)
                            cx, cy = r.x + r.w * 0.5, r.y + r.h * 0.5
                            t = c.time
                            pts = [
                                (
                                    cx + math.cos(t + k * 0.52) * (60 + 25 * math.sin(t * 2 + k)),
                                    cy + math.sin(t + k * 0.52) * (60 + 25 * math.sin(t * 2 + k)),
                                )
                                for k in range(12)
                            ]
                            c.draw_polyline(pts, tint, thickness=2.5, closed=True)
                            c.draw_circle((cx, cy), 18 + 6 * math.sin(t * 3), tint)
                            c.draw_text("60fps Custom SDF Vector Canvas", (r.x + 18, r.y + 18), ui.Color(255, 255, 255), size=14)

                        with ctx.box(width=ui.FILL, height=ui.FILL, pad=16):
                            res_c = ctx.canvas("art_canvas", ui.FILL, ui.FILL, paint_art)
                            if res_c.hovered:
                                ctx.request_redraw()

                    else:
                        with ctx.column(width=ui.FILL, height=ui.FILL, pad=28, gap=18):
                            ctx.gradient_text(
                                "Perceptual OKLab Motion & Shimmer Typography",
                                from_color=ui.Color.hex("#6366f1"),
                                to_color=ui.Color.hex("#ec4899"),
                                size=24, font=ui.FontRole.DISPLAY, animate=True,
                            )
                            ctx.shimmer_text("Synthesizing immediate-mode GPU draw batches...", size=15)
                            ctx.word_rotate("rot", ["Zero-Bloat", "Value-Returning", "Thread-Safe", "652 KB Native"], 1.8, size=18)
                            with ctx.spotlight("spot_demo", width=ui.FILL, pad=20, gap=8, beam=True):
                                ctx.heading("Spotlight Border Beam Card", level=4)
                                ctx.secondary("Move the pointer across this card to illuminate its border.")

                    # Bottom Log Console
                    ctx.log_view("studio_log", log, width=ui.FILL, height=175, timestamps=True)

                # Right Property Inspector
                with ctx.column(width=290, height=ui.FILL, bg=ui.Color.SURFACE_MUTED, pad=10):
                    with ctx.inspector("props", width=ui.FILL) as insp:
                        if insp:
                            vis, grp_xform = ctx.inspector_group("Transform", grp_xform)
                            if vis:
                                pos3 = ctx.prop_vec3("Position", pos3, step=0.05)
                                octaves = ctx.prop_int("Octaves", octaves, min=1, max=8)
                            vis2, grp_style = ctx.inspector_group("Material", grp_style)
                            if vis2:
                                roughness = ctx.prop_float("Roughness", roughness, min=0.0, max=1.0, step=0.01)
                                tint = ctx.prop_color("Base Tint", tint)
                                blend_mode = ctx.prop_enum("Blend", ["Opaque", "Additive", "Multiply"], blend_mode)

            # Status Bar
            with ctx.status_bar():
                ctx.status_bar_text("Ready", icon=ui.Icon.CIRCLE_CHECK, tone=ui.Tone.SUCCESS)
                ctx.status_bar_spacer()
                ctx.status_bar_text(f"Nodes: {len(nodes)}  Links: {len(links)}")
                ctx.status_bar_item("UTF-8")

    with ui.App("Gallery & Studio — yapps", width=1200, height=780, theme=ui.ThemeMode.DARK) as app:
        app.run(draw)
    log.close()


if __name__ == "__main__":
    main()
