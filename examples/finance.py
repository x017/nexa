"""Finance & Portfolio Terminal: ticker, odometer, money input, Sankey, Treemap & calendar heatmap (port of finance.c)."""

from __future__ import annotations

import nexa as ui


def main() -> None:
    amount = 1250.00
    tab = 0
    net_worth = 184_920.50

    tickers = [
        ui.TickerItem("AAPL", "$229.40", 1.84),
        ui.TickerItem("NVDA", "$141.12", 3.12),
        ui.TickerItem("MSFT", "$428.50", -0.45),
        ui.TickerItem("BTC", "$91,420", 4.60),
        ui.TickerItem("US10Y", "4.18%", -0.06, lower_is_better=True),
    ]

    allocations = [
        ui.VizItem("Global Equities", 98400),
        ui.VizItem("Short-Term Treasuries", 42100),
        ui.VizItem("Venture & Private", 24800),
        ui.VizItem("Cash Reserve", 19620),
    ]

    sankey_nodes = ["Salary", "Dividends", "Consulting", "Taxes", "Living", "Savings", "Equities"]
    sankey_links = [
        ui.SankeyLink(0, 3, 2800),
        ui.SankeyLink(0, 4, 3400),
        ui.SankeyLink(0, 5, 2800),
        ui.SankeyLink(1, 5, 650),
        ui.SankeyLink(2, 3, 450),
        ui.SankeyLink(2, 5, 1350),
        ui.SankeyLink(5, 6, 4800),
    ]

    daily_returns = [float(((d * 11 + 3) % 9)) for d in range(120)]

    def draw(ctx: ui.UI) -> None:
        nonlocal amount, tab, net_worth

        with ctx.column(width=ui.FILL, height=ui.FILL, bg=ui.Color.BACKGROUND):
            ctx.ticker("mkt_ticker", tickers, height=34)
            ctx.separator()

            with ctx.row(width=ui.FILL, pad_x=24, pad_y=14, gap=16, align=ui.Align.CENTER):
                with ctx.column(gap=2):
                    ctx.secondary("Total Net Worth")
                    ctx.counter("nw_counter", net_worth, format="$%.2f", size=28, font=ui.FontRole.DISPLAY)
                ctx.spacer()
                tab = ctx.tabs("fin_tabs", ["Allocation", "Cashflow Sankey", "Transfer"], tab, variant=ui.TabsVariant.PILL)
                ctx.theme_toggle()

            ctx.separator()

            with ctx.scroll("fin_body", width=ui.FILL, height=ui.FILL, pad=24, gap=20):
                if tab == 0:
                    with ctx.card(pad=20, gap=12, width=ui.FILL):
                        ctx.heading("Portfolio Treemap", level=4)
                        ctx.treemap("alloc_tree", allocations, height=220, format="$%.0f")
                    with ctx.card(pad=20, gap=12, width=ui.FILL):
                        ctx.heading("Asset Share", level=4)
                        ctx.split_bar("alloc_split", allocations, format="$%.0f")
                    with ctx.card(pad=20, gap=12, width=ui.FILL):
                        ctx.heading("Trading Consistency", level=4)
                        ctx.calendar_heatmap("trade_cal", ui.Date(2026, 7, 1), daily_returns, unit="trades")

                elif tab == 1:
                    with ctx.card(pad=20, gap=12, width=ui.FILL):
                        ctx.heading("Monthly Cashflow Sankey", level=4)
                        ctx.sankey("cash_sankey", sankey_nodes, sankey_links, height=320, format="$%.0f")

                else:
                    with ctx.card(pad=24, gap=16, max_width=440):
                        ctx.heading("Instant Deposit", level=3)
                        amount = ctx.money_input("dep_amt", amount, label="Transfer amount", symbol="$", code="USD")
                        if ctx.hold_button("Hold to execute transfer", icon=ui.Icon.SEND, variant=ui.ButtonVariant.PRIMARY):
                            net_worth += amount
                            ctx.toast("Transfer executed", description=f"Added ${amount:,.2f} to Cash Reserve.", tone=ui.Tone.SUCCESS)

    with ui.App("Finance — nexa", width=1080, height=720, theme=ui.ThemeMode.DARK, accent=ui.Accent.GREEN) as app:
        app.run(draw)


if __name__ == "__main__":
    main()
