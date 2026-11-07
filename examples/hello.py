"""Minimal functional nexa example (port of CUI's hello.c)."""

from __future__ import annotations

import nexa as ui


def main() -> None:
    name = "world"
    count = 0
    energetic = False

    def view() -> None:
        nonlocal name, count, energetic
        with ui.column(
            width=ui.FILL, height=ui.FILL, align=ui.Align.CENTER,
            justify=ui.Justify.CENTER, pad=32, gap=16, bg=ui.Color.BACKGROUND,
        ):
            with ui.card(width=380, pad=24, gap=16):
                with ui.row(align=ui.Align.CENTER):
                    ui.heading(f"Hello, {name or 'stranger'}{'!' if energetic else '.'}", level=2)
                    ui.spacer()
                    ui.theme_toggle()

                name = ui.input("name", name, label="Your name", placeholder="Type a name...", clearable=True)
                energetic = ui.switch("Exclamation mark", energetic, description="Add extra enthusiasm")

                with ui.row(gap=10, align=ui.Align.CENTER):
                    if ui.button("Greet", icon=ui.Icon.SPARKLES, variant=ui.ButtonVariant.PRIMARY):
                        count += 1
                        ui.toast(f"Hello, {name or 'friend'}!", description=f"Greeted {count} time(s).", tone=ui.Tone.SUCCESS)
                    if count > 0:
                        ui.badge(f"{count}x", tone=ui.Tone.ACCENT)

    ui.run(view, title="Hello — nexa", width=560, height=400)


if __name__ == "__main__":
    main()
