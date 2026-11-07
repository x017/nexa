"""OOP Settings Application demonstrating Application, Router, View & Component (port of settings.c)."""

from __future__ import annotations

import nexa as ui


class SectionRow(ui.Component):
    """Reusable two-column labelled form section component."""

    def __init__(self, key: str, title: str, description: str) -> None:
        super().__init__(key)
        self.title = title
        self.description = description

    def build(self, ctx: ui.UI) -> None:
        with ctx.column(width=220, gap=3):
            ctx.label(self.title)
            ctx.secondary(self.description)


class ProfileView(ui.View):
    title = "Profile"
    icon = ui.Icon.USER

    def __init__(self, state: dict) -> None:
        super().__init__("profile")
        self.s = state

    def build(self, ctx: ui.UI) -> None:
        s = self.s
        with ctx.card(gap=20, pad=24, width=ui.FILL):
            with ctx.row(gap=16, align=ui.Align.CENTER):
                ctx.avatar(f"{s['first']} {s['last']}", size=60, status="online")
                with ctx.column(gap=6, width=ui.FILL):
                    ctx.heading(f"{s['first']} {s['last']}", level=3)
                    ctx.secondary(f"@{s['username']}  ·  {s['email']}")

            ctx.separator()
            with ctx.grid(columns=2, min_column_width=220, gap=16, width=ui.FILL):
                s["first"] = ctx.input("first", s["first"], label="First name")
                s["last"] = ctx.input("last", s["last"], label="Last name")
                s["email"] = ctx.input("email", s["email"], label="Email", icon=ui.Icon.MAIL)
                err = "Cannot contain spaces" if " " in s["username"] else None
                s["username"] = ctx.input("user", s["username"], label="Username", icon=ui.Icon.AT_SIGN, error=err)

            s["bio"] = ctx.textarea("bio", s["bio"], label="Bio", height=88, hint="Displayed on your team profile.")
            s["skills"] = ctx.tag_input("skills", s["skills"], label="Skills & Interests", placeholder="Add tag...")

            with ctx.grid(columns=2, min_column_width=220, gap=16, width=ui.FILL):
                zones = ["Amsterdam (UTC+1)", "London (UTC+0)", "New York (UTC-5)", "Tehran (UTC+3:30)", "Tokyo (UTC+9)"]
                s["tz"] = ctx.combobox("tz", zones, s["tz"], label="Time zone")
                langs = ["English", "Nederlands", "Deutsch", "Français", "Español"]
                s["lang"] = ctx.select("lang", langs, s["lang"], label="Language")


class AppearanceView(ui.View):
    title = "Appearance"
    icon = ui.Icon.PALETTE

    def __init__(self, state: dict) -> None:
        super().__init__("appearance")
        self.s = state
        self.theme_hdr = SectionRow("hdr_theme", "Theme & Accent", "Customize surfaces and highlight hues.")
        self.scale_hdr = SectionRow("hdr_scale", "Typography & Motion", "Adjust interface scale and spring motion.")

    def build(self, ctx: ui.UI) -> None:
        s = self.s
        with ctx.card(gap=20, pad=24, width=ui.FILL):
            with ctx.row(gap=24, wrap=True, width=ui.FILL):
                self.theme_hdr(ctx)
                with ctx.column(gap=14, width=ui.FILL):
                    s["theme_mode"] = ctx.theme_switcher(s["theme_mode"])
                    accents = [ui.accent_name(a).capitalize() for a in ui.Accent]
                    new_acc = ctx.segmented("accent", accents, int(ctx.accent))
                    if new_acc != int(ctx.accent):
                        ctx.accent = ui.Accent(new_acc)

            ctx.separator()
            with ctx.row(gap=24, wrap=True, width=ui.FILL):
                self.scale_hdr(ctx)
                with ctx.column(gap=14, width=ui.FILL):
                    scale = ctx.slider("Font scale", ctx.font_scale, 0.85, 1.35, step=0.05, show_value=True, format="%.2fx")
                    if abs(scale - ctx.font_scale) > 1e-4:
                        ctx.font_scale = scale
                    s["reduced_motion"] = ctx.switch(
                        "Reduced motion", s["reduced_motion"],
                        description="Snap transitions instead of spring animations.",
                    )
                    ctx.set_reduced_motion(s["reduced_motion"])


class SecurityView(ui.View):
    title = "Security"
    icon = ui.Icon.SHIELD

    def __init__(self, state: dict) -> None:
        super().__init__("security")
        self.s = state

    def build(self, ctx: ui.UI) -> None:
        s = self.s
        with ctx.card(gap=18, pad=24, width=ui.FILL):
            ctx.heading("Authentication & Shortcuts", level=3)
            s["password"] = ctx.input("pw", s["password"], label="New password", password=True, clearable=True)
            ctx.password_strength(s["password"])

            ctx.label("Two-factor verification code")
            s["otp"], completed = ctx.otp_input("otp", s["otp"], 6)
            if completed:
                ctx.toast("2FA code verified", tone=ui.Tone.SUCCESS)

            ctx.label("Quick-lock shortcut")
            s["shortcut"] = ctx.shortcut_recorder("lock_key", s["shortcut"])

            ctx.separator()
            if ctx.confirm_button("Revoke active sessions", variant=ui.ButtonVariant.DANGER, icon=ui.Icon.LOG_OUT):
                ctx.toast("All other sessions revoked", tone=ui.Tone.WARNING)


class SettingsApp(ui.Application):
    title = "Settings — nexa OOP"
    width = 980
    height = 680

    def setup(self) -> None:
        self.state = {
            "first": "Maya",
            "last": "Okafor",
            "email": "maya@larkspur.dev",
            "username": "maya_okafor",
            "bio": "Systems & interface engineer working on fast desktop tools.",
            "skills": ["Python", "C99", "UI", "OpenGL"],
            "tz": 0,
            "lang": 0,
            "theme_mode": 0,
            "reduced_motion": False,
            "password": "correct-horse-battery",
            "otp": "4829",
            "shortcut": ui.KeyCombo(ui.Mod.PRIMARY | ui.Mod.SHIFT, ui.Key.L),
        }
        self.sections = [
            ("profile", ProfileView(self.state)),
            ("appearance", AppearanceView(self.state)),
            ("security", SecurityView(self.state)),
        ]
        for route_id, view in self.sections:
            self.router.register(route_id, view)

    def build(self, ctx: ui.UI) -> None:
        with ctx.row(width=ui.FILL, height=ui.FILL, bg=ui.Color.BACKGROUND):
            with ctx.column(width=230, height=ui.FILL, bg=ui.Color.SURFACE_MUTED, pad=14, gap=4):
                ctx.heading("Settings", level=3)
                ctx.gap(8)
                for route_id, view in self.sections:
                    if ctx.nav_item(
                        view.title,
                        icon=view.icon,
                        selected=(self.router.current_name == route_id),
                        group="settings_nav",
                    ):
                        self.router.push(route_id)
                ctx.spacer()
                if ctx.button("Save changes", icon=ui.Icon.CHECK, variant=ui.ButtonVariant.PRIMARY, full_width=True):
                    ctx.toast("Preferences saved", description="Synced across devices.", tone=ui.Tone.SUCCESS)

            with ctx.scroll("settings_body", width=ui.FILL, height=ui.FILL, pad=28, gap=20):
                self.router.render(ctx)


if __name__ == "__main__":
    SettingsApp().run()
