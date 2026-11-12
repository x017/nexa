"""Studio فارسی — a right-to-left studio with a local font, calendar, terminal & files.

Shows the CUI 1.2–1.4 pieces that make a Persian/Arabic app feel native:

* ``direction=ui.TextDirection.RTL`` on the layout (and ``AUTO`` for mixed lines)
* ``ctx.use_rtl_font()`` — installs an Arabic-capable *system* font for the whole UI
  (build with ``python -m nexa.build --rtl`` for real glyph shaping)
* ``ctx.set_strings(...)`` — localized month and weekday names
* ``month_calendar``, ``terminal``, ``file_browser``, ``candlestick``,
  ``image_viewer``, ``cropper``, ``emoji_picker`` and a guided ``tour``

    python examples/rtl.py

Runs headless with ``NEXA_HEADLESS=1 CUI_SCREENSHOT=out.png``; without an
Arabic font or a shaping build it still runs, just with unshaped/fallback text.
"""

from __future__ import annotations

import math
import time

import nexa as ui
from nexa import fonts

MONTHS = [
    "ژانویه", "فوریه", "مارس", "آپریل", "مه", "ژوئن",
    "ژوئیه", "اوت", "سپتامبر", "اکتبر", "نوامبر", "دسامبر",
]
WEEKDAYS = ["یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه"]

EVENTS = [
    ui.MonthEvent("بازبینی طراحی", ui.Date(2026, 11, 3), tone=ui.Tone.INFO),
    ui.MonthEvent("انتشار نسخهٔ ۱٫۴", ui.Date(2026, 11, 12), tone=ui.Tone.SUCCESS),
    ui.MonthEvent("جلسهٔ تیم", ui.Date(2026, 11, 16), ui.Date(2026, 11, 18), tone=ui.Tone.VIOLET),
    ui.MonthEvent("پشتیبان‌گیری", ui.Date(2026, 11, 24), time=3.5, tone=ui.Tone.WARNING),
]

# -- a 24 h price series for the candlestick card -----------------------------
def make_candles(count: int = 28) -> list[ui.Candle]:
    out = []
    price = 96.0
    for i in range(count):
        drift = math.sin(i * 0.55) * 1.7 + math.cos(i * 0.21) * 1.1
        open_ = price
        close = open_ + drift
        high = max(open_, close) + abs(math.sin(i * 1.3)) * 0.9
        low = min(open_, close) - abs(math.cos(i * 0.9)) * 0.9
        out.append(ui.Candle(open_, high, low, close, 40 + 30 * abs(math.sin(i * 0.7))))
        price = close
    return out


def main() -> None:
    view = ui.ImageView()
    crop = ui.Rect(0.0)
    month = ui.Date(2026, 11, 12)
    selected_day = ui.Date(2026, 11, 12)
    terminal = ui.TerminalBuffer(text_capacity=32_768, line_capacity=128)
    terminal.write("nexa ~ $ help\n")
    terminal.write("سلام! این شبیه‌ساز ترمینال است.\n")
    terminal.write("دستورها: help · status · clear\n")
    tour_step = -1
    emoji_choice: str | None = None
    picked_file: str | None = None
    candles = make_candles()
    started = time.time()

    # Procedural texture so image_viewer / cropper have something to show.
    tex_w, tex_h = 240, 160
    pixels = bytearray(tex_w * tex_h * 4)
    for y in range(tex_h):
        for x in range(tex_w):
            i = (y * tex_w + x) * 4
            pixels[i] = min(255, max(0,int(120 + 120 * math.sin(x * 0.05))))
            pixels[i + 1] = min(255, max(0,int(90 + 120 * math.cos(y * 0.06))))
            pixels[i + 2] = min(255, max(0,int(180 + 60 * math.sin((x + y) * 0.02))))
            pixels[i + 3] = 255

    ctx_ref: list[ui.UI] = []
    setup: dict[str, object] = {"rtl_font": False, "texture": 0}

    def configure(ctx: ui.UI) -> None:
        """Fonts, localized names and the procedural texture are set up once."""
        ctx_ref.append(ctx)
        try:
            ctx.use_rtl_font()          # whole-UI Persian/Arabic font (system font)
            setup["rtl_font"] = True
        except FileNotFoundError:
            setup["rtl_font"] = False   # falls back to the embedded faces
        ctx.set_strings(months=MONTHS, weekdays=WEEKDAYS, today="امروز")
        setup["texture"] = ctx.image_create(tex_w, tex_h, bytes(pixels))

    def draw(ctx: ui.UI) -> None:
        nonlocal view, crop, month, selected_day, tour_step, emoji_choice, picked_file

        ctx.request_redraw()
        texture = int(setup["texture"])  # type: ignore[arg-type]
        has_rtl_font = bool(setup["rtl_font"])

        with ctx.column(
            width=ui.FILL,
            height=ui.FILL,
            bg=ui.Color.BACKGROUND,
            pad=20,
            gap=14,
            direction=ui.TextDirection.RTL,
        ):
            with ctx.row(align=ui.Align.CENTER, width=ui.FILL):
                ctx.heading("استودیو فارسی", level=2)
                ctx.badge(
                    "شکل‌دهی فعال" if fonts.supports_text_shaping() else "بدون شکل‌دهی",
                    tone=ui.Tone.SUCCESS if fonts.supports_text_shaping() else ui.Tone.WARNING,
                    dot=True,
                )
                if not has_rtl_font:
                    ctx.badge("فونت فارسی پیدا نشد", tone=ui.Tone.DANGER)
                ctx.spacer()
                if ctx.button("تور راهنما", variant=ui.ButtonVariant.SECONDARY, size=ui.ControlSize.SM):
                    tour_step = 0
                tour_id = ctx.last_id
                ctx.text("۱۲ نوامبر ۲۰۲۶", size=12, color=ui.Color.TEXT_MUTED)

            with ctx.scroll("rtl_body", width=ui.FILL, height=ui.FILL, gap=14, fade_edges=True):
                # ---- calendar + terminal ------------------------------------
                with ctx.row(gap=14, width=ui.FILL, align=ui.Align.START):
                    with ctx.card(width=ui.GROW(3), min_width=420, pad=16, gap=10):
                        ctx.secondary("تقویم ماهانه")
                        cal = ctx.month_calendar(
                            "calendar",
                            month,
                            EVENTS,
                            selected=selected_day,
                            cell_height=80.0,
                            month_names=MONTHS,
                            day_names=WEEKDAYS,
                        )
                        month = cal.month
                        if cal.day_clicked >= 0:
                            selected_day = ui.Date(month.year, month.month, cal.day_clicked + 1)
                        ctx.text(
                            f"روز انتخاب‌شده: {selected_day.year}/{selected_day.month:02d}/{selected_day.day:02d}"
                            f" · رویدادها: {len(EVENTS)}",
                            size=12,
                            color=ui.Color.TEXT_SECONDARY,
                        )

                    with ctx.card(width=ui.GROW(2), min_width=360, pad=16, gap=10):
                        ctx.secondary("ترمینال")
                        term = ctx.terminal(
                            "terminal", terminal, height=250.0, prompt="nexa ~ $", size=13.0, width=ui.FILL
                        )
                        if term.command:
                            command = term.command.strip()
                            terminal.printf("nexa ~ $ %s\n", command)
                            if command in ("help", "راهنما"):
                                terminal.write("  help · status · clear\n")
                                terminal.write("  تایپ کنید و Enter بزنید.\n")
                            elif command == "status":
                                terminal.printf("  %d خط در حافظه · هستهٔ CUI 1.4\n", terminal.line_count)
                            elif command == "clear":
                                terminal.clear()
                            elif command:
                                terminal.printf("  دستور ناشناخته: %s\n", command)
                        if term.interrupt:
                            terminal.write("^C\n")

                # ---- chart + files -----------------------------------------
                with ctx.row(gap=14, width=ui.FILL, align=ui.Align.START):
                    with ctx.card(width=ui.GROW(3), min_width=430, pad=16, gap=10):
                        ctx.secondary("نمودار شمعی — ۲۸ کندل")
                        hovered = ctx.candlestick(
                            "candles",
                            candles,
                            height=210.0,
                            width=ui.FILL,
                            labels=[f"{i:02d}" for i in range(len(candles))],
                            overlays=[
                                ui.Series(
                                    "میانگین ۷",
                                    [
                                        sum(c.close for c in candles[max(0, i - 6) : i + 1])
                                        / len(candles[max(0, i - 6) : i + 1])
                                        for i in range(len(candles))
                                    ],
                                )
                            ],
                        )
                        ctx.text(
                            f"کندل زیر نشانگر: {hovered if hovered >= 0 else '—'}",
                            size=12,
                            color=ui.Color.TEXT_SECONDARY,
                        )

                    with ctx.card(width=ui.GROW(2), min_width=360, pad=16, gap=10):
                        ctx.secondary("مرورگر فایل")
                        browser = ctx.file_browser(
                            "files", picked_file or ".", height=260.0, width=ui.FILL, filter="*.py,*.md"
                        )
                        picked_file = browser.path
                        if browser.picked:
                            ctx.badge(f"انتخاب: {browser.picked.split('/')[-1]}", tone=ui.Tone.INFO)
                        elif browser.error:
                            ctx.badge(browser.error, tone=ui.Tone.DANGER)
                        else:
                            row = browser.selected or -1
                            label = "هیچ موردی انتخاب نشده" if row < 0 else f"ردیف {row}"
                            ctx.text(label, size=12, color=ui.Color.TEXT_SECONDARY)

                # ---- images + emoji ----------------------------------------
                with ctx.row(gap=14, width=ui.FILL, align=ui.Align.START):
                    with ctx.card(width=ui.GROW(2), min_width=330, pad=16, gap=10):
                        ctx.secondary("نمایش تصویر")
                        view = ctx.image_viewer(
                            "image", texture, tex_w, tex_h, view, width=300.0, height=190.0
                        )
                        ctx.text(f"بزرگ‌نمایی {view.zoom:.0%}", size=12, color=ui.Color.TEXT_SECONDARY)
                    with ctx.card(width=ui.GROW(2), min_width=330, pad=16, gap=10):
                        ctx.secondary("برش تصویر")
                        crop, changed = ctx.cropper(
                            "crop", texture, tex_w, tex_h, crop, width=300.0, height=190.0, aspect=0.0
                        )
                        ctx.text(
                            f"برش {crop.w:.0f}×{crop.h:.0f}" + ("  (تغییر کرد)" if changed else ""),
                            size=12,
                            color=ui.Color.TEXT_SECONDARY,
                        )
                    with ctx.card(width=ui.GROW(2), min_width=300, pad=16, gap=10):
                        ctx.secondary("ایموجی")
                        if ctx.load_emoji_font():
                            picked = ctx.emoji_picker("emoji", width=ui.FILL, height=190.0)
                            if picked:
                                emoji_choice = picked
                        else:
                            ctx.text("فونت ایموجی نصب نیست", size=12, color=ui.Color.TEXT_MUTED)
                            ctx.text("ctx.load_emoji_font(path)", size=11, color=ui.Color.TEXT_MUTED)
                        ctx.text(
                            f"انتخاب: {emoji_choice or '—'}", size=13, color=ui.Color.TEXT_SECONDARY
                        )
                        ctx.emoji("🚀 🎨 📅", size=22)

            # ---- guided tour (overlay, so it lives outside the scroll) ------
            if tour_step >= 0:
                steps = [
                    ui.TourStep(tour_id, "تور راهنما", "این دکمه تور را دوباره اجرا می‌کند."),
                    ui.TourStep(0, "پایان", "راست‌به‌چپ، فونت فارسی و تقویم محلی آماده‌اند."),
                ]
                tour_step, action = ctx.tour("tour", steps, tour_step)
                if action in ("done", "skipped"):
                    tour_step = -1

    with ui.App(
        "استودیو فارسی — nexa", width=1280, height=1080, theme=ui.ThemeMode.DARK, accent=ui.Accent.ROSE
    ) as app:
        configure(app.ui)
        app.run(draw)


if __name__ == "__main__":
    main()
