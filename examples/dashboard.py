"""Analytics Dashboard: KPIs, rolling numbers, charts, filter bar & virtualized data grid (port of dashboard.c)."""

from __future__ import annotations

import yapps as ui


def main() -> None:
    nav = 0
    period = 1
    search = ""
    filter_masks = [0, 0]
    grid_sort = ui.TableSort(0, False)
    grid_selected = [False] * 250
    grid_cursor = 0

    orders = [
        (f"#{3100 + i}", name, email, status, tone, round(49.5 + (i * 37.8) % 940.0, 2))
        for i, (name, email, status, tone) in enumerate(
            [
                ("Nora Lindqvist", "nora@lindqvist.se", "Paid", ui.Tone.SUCCESS),
                ("Kwame Asante", "kwame@asante.co", "Pending", ui.Tone.WARNING),
                ("Hana Novak", "hana@novak.cz", "Paid", ui.Tone.SUCCESS),
                ("Felix Moreau", "felix@moreau.fr", "Refunded", ui.Tone.DANGER),
                ("Iris Coleman", "iris@coleman.org", "Paid", ui.Tone.SUCCESS),
                ("Ravi Shah", "ravi@shah.in", "Paid", ui.Tone.SUCCESS),
            ]
            * 42
        )
    ][:250]

    rev_series = [
        [42, 48, 51, 49, 62, 68, 74],
        [180, 210, 195, 240, 268, 302, 329],
        [720, 810, 890, 940, 1020, 1150, 1284],
    ]
    kpis = [
        ("$18,420", "$84,910", "$342,800"),
        ("412", "1,894", "7,612"),
        ("2.8%", "3.4%", "3.9%"),
    ]

    filter_fields = [
        ui.FilterField("Status", ["Paid", "Pending", "Refunded"], icon=ui.Icon.FILTER),
        ui.FilterField("Region", ["EU", "NA", "APAC"], icon=ui.Icon.GLOBE),
    ]
    grid_cols = [
        ui.GridColumn("Order", width=95, sortable=True),
        ui.GridColumn("Customer", width=180, sortable=True),
        ui.GridColumn("Email", width=210),
        ui.GridColumn("Status", width=115),
        ui.GridColumn("Amount", width=110, align=ui.TextAlign.RIGHT, sortable=True),
    ]

    def draw(ctx: ui.UI) -> None:
        nonlocal nav, period, search, filter_masks, grid_sort, grid_selected, grid_cursor

        with ctx.row(width=ui.FILL, height=ui.FILL, bg=ui.Color.BACKGROUND):
            # Sidebar
            with ctx.column(width=224, height=ui.FILL, bg=ui.Color.SURFACE_MUTED, pad=12, gap=3):
                with ctx.row(gap=10, pad_x=8, pad_y=8, align=ui.Align.CENTER):
                    with ctx.box(
                        width=26, height=26, radius=7, bg=ui.Color.ACCENT,
                        dir=ui.Direction.STACK, align=ui.Align.CENTER, justify=ui.Justify.CENTER,
                    ):
                        ctx.text("L", font=ui.FontRole.DISPLAY, size=14, color=ui.Color.ACCENT_FOREGROUND)
                    ctx.text("Larkspur Analytics", font=ui.FontRole.MEDIUM, size=15)

                nav_defs = [
                    ("Overview", ui.Icon.LAYOUT_DASHBOARD, None),
                    ("Orders", ui.Icon.SHOPPING_CART, "250"),
                    ("Funnels", ui.Icon.TRENDING_UP, None),
                ]
                for idx, (lbl, ic, bdg) in enumerate(nav_defs):
                    if ctx.nav_item(lbl, icon=ic, badge=bdg, selected=(nav == idx), group="dash_nav"):
                        nav = idx

                ctx.spacer()
                ctx.meter("Monthly quota", 74.2, 100.0, "GB")

            # Main workspace
            with ctx.column(width=ui.FILL, height=ui.FILL):
                with ctx.row(width=ui.FILL, pad_x=24, pad_y=12, gap=12, align=ui.Align.CENTER):
                    ctx.breadcrumb(["Workspace", ["Overview", "Orders", "Funnels"][nav]])
                    ctx.spacer()
                    period = ctx.segmented("period", ["7d", "30d", "90d"], period, size=ui.ControlSize.SM)
                    ctx.theme_toggle()

                ctx.separator()

                if nav == 0:
                    with ctx.scroll("dash_scroll", width=ui.FILL, height=ui.FILL, pad=24, gap=20):
                        with ctx.grid(columns=3, min_column_width=200, gap=16, width=ui.FILL):
                            with ctx.card(pad=18, gap=6):
                                ctx.secondary("Net revenue")
                                ctx.number_roll("kpi_rev", kpis[0][period], font=ui.FontRole.DISPLAY, size=26)
                                ctx.sparkline(rev_series[period], width=ui.FILL, height=32)
                            with ctx.card(pad=18, gap=6):
                                ctx.secondary("Completed orders")
                                ctx.number_roll("kpi_ord", kpis[1][period], font=ui.FontRole.DISPLAY, size=26)
                                ctx.badge("+12.4% vs prior", tone=ui.Tone.SUCCESS)
                            with ctx.card(pad=18, gap=6):
                                ctx.secondary("Conversion rate")
                                ctx.number_roll("kpi_cvr", kpis[2][period], font=ui.FontRole.DISPLAY, size=26)
                                ctx.badge("+0.3pp", tone=ui.Tone.INFO)

                        with ctx.row(gap=16, width=ui.FILL, wrap=True):
                            with ctx.card(width=ui.GROW(2), min_width=360, pad=18, gap=10):
                                ctx.heading("Revenue trajectory", level=4)
                                ctx.line_chart(
                                    "rev_chart",
                                    [ui.Series("Revenue ($k)", rev_series[period])],
                                    labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                                    height=210, area=True, smooth=True,
                                )
                            with ctx.card(width=ui.GROW(1), min_width=260, pad=18, gap=10):
                                ctx.heading("Channel mix", level=4)
                                ctx.donut_chart(
                                    "channels",
                                    [48, 29, 15, 8],
                                    ["Direct", "Search", "Referral", "Social"],
                                    height=210,
                                )

                elif nav == 1:
                    with ctx.column(width=ui.FILL, height=ui.FILL, pad=24, gap=12):
                        filter_masks, search = ctx.filter_bar("ord_filter", filter_fields, filter_masks, search)
                        with ctx.data_grid(
                            "orders_grid", grid_cols, len(orders),
                            width=ui.FILL, height=ui.FILL,
                            selected=grid_selected, sort=grid_sort, striped=True, cursor=grid_cursor,
                        ) as grid:
                            if grid:
                                for r in grid.rows:
                                    oid, cust, mail, st, tone, amt = orders[r]
                                    grid.row(r)
                                    grid.cell_text(oid)
                                    grid.cell_text(cust)
                                    grid.cell_text(mail)
                                    grid.cell()
                                    ctx.badge(st, tone=tone, dot=True, size=ui.ControlSize.SM)
                                    grid.cell_text(f"${amt:,.2f}")
                        if grid.selected is not None:
                            grid_selected = grid.selected
                        if grid.sort is not None:
                            grid_sort = grid.sort
                        grid_cursor = grid.cursor

                else:
                    with ctx.scroll("funnel_scroll", width=ui.FILL, height=ui.FILL, pad=24, gap=20):
                        with ctx.card(pad=20, gap=12, width=ui.FILL):
                            ctx.heading("Checkout conversion funnel", level=4)
                            ctx.funnel(
                                "checkout_funnel",
                                [
                                    ui.VizItem("Visited store", 12400),
                                    ui.VizItem("Viewed product", 6820),
                                    ui.VizItem("Added to cart", 2490),
                                    ui.VizItem("Completed purchase", 1410),
                                ],
                                height=220,
                            )
                        with ctx.card(pad=20, gap=12, width=ui.FILL):
                            ctx.heading("Hourly activity heatmap", level=4)
                            vals = [float(((r * 7 + c * 13) % 19) + 2) for r in range(5) for c in range(12)]
                            ctx.heatmap(
                                "hr_heat", vals, 5, 12,
                                row_labels=["Mon", "Tue", "Wed", "Thu", "Fri"],
                                col_labels=[f"{h * 2:02d}h" for h in range(12)],
                            )

    with ui.App("Dashboard — yapps", width=1140, height=740, theme=ui.ThemeMode.DARK) as app:
        app.run(draw)


if __name__ == "__main__":
    main()
