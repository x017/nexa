"""Tests for manual frame lifecycle, DrawData, SoftwareRenderer, CustomRenderer, platform & theme."""

from __future__ import annotations

import pathlib

import nexa as ui


def test_software_renderer_and_png_roundtrip(tmp_path: pathlib.Path) -> None:
    with ui.SoftwareRenderer(threads=2) as sw:
        with ui.UI(width=320, height=200, theme=ui.ThemeMode.DARK, accent=ui.Accent.CORAL, renderer=sw) as ctx:
            with ctx.frame(1.0 / 60.0):
                with ctx.column(width=ui.FILL, height=ui.FILL, pad=16, gap=10, bg=ui.Color.BACKGROUND):
                    ctx.heading("Render Test", level=2)
                    ctx.button("Primary Action", variant=ui.ButtonVariant.PRIMARY, icon=ui.Icon.ROCKET)

            dd = ctx.draw_data()
            assert dd.size_px == (320, 200)
            assert dd.vertex_count > 20
            assert dd.index_count > 30
            assert dd.command_count >= 1
            assert len(dd.vertices_bytes()) == dd.vertex_count * 64
            assert len(dd.indices_bytes()) == dd.index_count * 4
            v0 = dd.vertex_at(0)
            assert isinstance(v0.color, ui.Color)
            cmds = dd.commands()
            assert len(cmds) == dd.command_count

            # Render into caller-allocated writable bytearray (zero extra copy)
            buf = bytearray(320 * 200 * 4)
            raw = sw.render(dd, buffer=buf)
            assert len(raw) == 320 * 200 * 4
            assert any(b != 0 for b in buf)

            # Save to PNG & reload via stb_image!
            png_path = tmp_path / "out.png"
            assert ctx.render_to_png(png_path)
            assert png_path.is_file() and png_path.stat().st_size > 500

            tex, iw, ih = ctx.image_load(png_path)
            assert tex > 0 and (iw, ih) == (320, 200)
            ctx.image_destroy(tex)


def test_custom_renderer_callbacks() -> None:
    events: list[tuple] = []
    next_tex = 10

    def on_create(w: int, h: int, fmt: ui.TextureFormat, data: bytes) -> int:
        nonlocal next_tex
        tid = next_tex
        next_tex += 1
        events.append(("create", tid, w, h, fmt, len(data)))
        return tid

    def on_update(tex: int, x: int, y: int, w: int, h: int, data: bytes, stride: int) -> None:
        events.append(("update", tex, w, h))

    def on_destroy(tex: int) -> None:
        events.append(("destroy", tex))

    custom = ui.CustomRenderer(on_create=on_create, on_update=on_update, on_destroy=on_destroy)
    with ui.UI(width=240, height=160, renderer=custom) as ctx:
        tex = ctx.image_create(4, 4, bytes([255, 0, 128, 255] * 16))
        assert tex >= 10
        with ctx.frame():
            ctx.text("Custom GPU Atlas Upload")
            ctx.image(tex, width=32, height=32)
        ctx.image_destroy(tex)

    kinds = [e[0] for e in events]
    assert "create" in kinds
    assert "destroy" in kinds


def test_platform_callbacks_and_clipboard() -> None:
    clip_store = {"text": "pasted_value"}
    cursors: list[ui.Cursor] = []

    with ui.UI(width=400, height=200) as ctx:
        ctx.set_platform(
            set_clipboard=lambda s: clip_store.__setitem__("text", s),
            get_clipboard=lambda: clip_store["text"],
            set_cursor=lambda c: cursors.append(c),
        )
        # Render a copy button; layout runs on end_frame(), so get_rect(wid) has exact bounds!
        with ctx.frame():
            ctx.copy_button("cp1", "hello clipboard!")
            cp_id = ctx.last_id
        r = ctx.get_rect(cp_id)
        assert r.w > 0 and r.h > 0

        ctx.input_click(r.x + r.w * 0.5, r.y + r.h * 0.5)
        with ctx.frame():
            clicked = ctx.copy_button("cp1", "hello clipboard!")
        ctx.input_mouse_button(ui.MouseButton.LEFT, False)
        with ctx.frame():
            clicked |= ctx.copy_button("cp1", "hello clipboard!")

        assert clicked
        assert clip_store["text"] == "hello clipboard!"


def test_theme_oklch_dates_and_icons() -> None:
    c1 = ui.oklch(0.65, 0.18, 250.0)
    c2 = ui.Color.hex("#ff5500")
    mixed = ui.mix_colors(c1, c2, 0.5)
    faded = ui.with_alpha(mixed, 0.5)
    assert 0 <= faded.a <= 140

    d = ui.Date(2026, 11, 6)
    assert ui.Date.from_days(d.to_days()) == d
    assert ui.Date.today().year >= 2026

    assert ui.Icon.get("sparkles") == ui.Icon.SPARKLES
    assert ui.Icon.get("CUI_ICON_ARROW_RIGHT") == ui.Icon.ARROW_RIGHT

    with ui.UI(width=300, height=200) as ctx:
        ctx.theme[ui.Token.ACCENT] = ui.Color.hex("#10b981")
        assert ctx.theme[ui.Token.ACCENT] == ui.Color(0x10, 0xB9, 0x81, 255)
        ctx.theme.radius_control = 10.0
        assert ctx.theme.radius_control == 10.0
        m = ctx.measure_text("Hello world", size=14.0)
        assert m.width > 30.0 and m.height > 10.0
