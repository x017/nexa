"""Notes app: split view, search, tags, pinning, delete dialog & command palette (port of notes.c)."""

from __future__ import annotations

import yapps as ui

TAGS = ("Personal", "Work", "Ideas")
TAG_TONES = (ui.Tone.TEAL, ui.Tone.INFO, ui.Tone.VIOLET)


class Note:
    __slots__ = ("title", "body", "pinned", "tag")

    def __init__(self, title: str, body: str, tag: int = 0, pinned: bool = False) -> None:
        self.title = title
        self.body = body
        self.tag = tag
        self.pinned = pinned


def main() -> None:
    notes = [
        Note(
            "Spring physics notes",
            "Critically damped springs respond immediately to velocity changes.\n- No fixed duration curves\n- Interruptible mid-flight",
            tag=2,
            pinned=True,
        ),
        Note(
            "Release checklist",
            "- Verify Linux, macOS, and Windows wheels\n- Run headless PNG regression suite\n- Tag v1.0.0 release",
            tag=1,
            pinned=True,
        ),
        Note(
            "Weekend reading",
            " Subpixel glyph positioning and perceptual OKLab color mixing.",
            tag=0,
        ),
    ]
    selected = 0
    query = ""
    tag_filter = 0
    split_ratio = 0.32
    palette_open = False
    confirm_delete = False

    commands = [
        ui.Command("New note", icon=ui.Icon.PLUS, group="Notes", shortcut="Ctrl N"),
        ui.Command("Toggle pin", icon=ui.Icon.STAR, group="Notes", shortcut="Ctrl P"),
        ui.Command("Delete note", icon=ui.Icon.TRASH, group="Notes"),
        ui.Command("Toggle dark theme", icon=ui.Icon.MOON, group="Appearance", shortcut="Ctrl D"),
    ]

    def add_note() -> None:
        nonlocal selected
        notes.append(Note("Untitled note", "", tag=max(0, tag_filter - 1)))
        selected = len(notes) - 1

    def delete_current() -> None:
        nonlocal selected
        if 0 <= selected < len(notes):
            notes.pop(selected)
            selected = min(selected, len(notes) - 1)

    def draw(ctx: ui.UI) -> None:
        nonlocal selected, query, tag_filter, split_ratio, palette_open, confirm_delete

        if ctx.shortcut(ui.Mod.PRIMARY, ui.Key.K):
            palette_open = True
        if ctx.shortcut(ui.Mod.PRIMARY, ui.Key.N):
            add_note()

        with ctx.split("main_split", split_ratio, min_first=240, min_second=340, width=ui.FILL, height=ui.FILL) as sp:
            # Left sidebar
            with ctx.column(width=ui.FILL, height=ui.FILL, bg=ui.Color.SURFACE_MUTED, pad=12, gap=10):
                with ctx.row(gap=8, pad_x=4, align=ui.Align.CENTER):
                    ctx.text("Notes", font=ui.FontRole.MEDIUM, size=16, width=ui.FILL)
                    ctx.theme_toggle()
                    if ctx.icon_button(ui.Icon.PLUS, tooltip="New note", shortcut="Ctrl N"):
                        add_note()

                query = ctx.search("q", query, placeholder="Search notes...", size=ui.ControlSize.SM)
                tag_filter = ctx.segmented(
                    "filter", ["All", "Personal", "Work", "Ideas"], tag_filter,
                    size=ui.ControlSize.SM, full_width=True,
                )

                with ctx.scroll("note_list", width=ui.FILL, height=ui.FILL, gap=4, fade_edges=True):
                    q_low = query.strip().lower()
                    shown = 0
                    for pinned_pass in (True, False):
                        for idx, n in enumerate(notes):
                            if n.pinned != pinned_pass:
                                continue
                            if tag_filter > 0 and n.tag != tag_filter - 1:
                                continue
                            if q_low and q_low not in f"{n.title} {n.body}".lower():
                                continue
                            shown += 1
                            preview = (n.body.strip().splitlines() or ["No content"])[0][:60]
                            with ctx.id_scope(idx):
                                if ctx.list_item(
                                    n.title or "Untitled",
                                    subtitle=preview,
                                    icon=ui.Icon.PIN if n.pinned else ui.Icon.FILE_TEXT,
                                    trailing=TAGS[n.tag],
                                    selected=(idx == selected),
                                ):
                                    selected = idx
                    if shown == 0:
                        if ctx.empty_state("No matching notes", icon=ui.Icon.SEARCH, action="Create note"):
                            add_note()

            sp.next()

            # Right editor pane
            with ctx.column(width=ui.FILL, height=ui.FILL, bg=ui.Color.BACKGROUND, pad=24, gap=14):
                if 0 <= selected < len(notes):
                    cur = notes[selected]
                    with ctx.row(gap=8, align=ui.Align.CENTER):
                        cur.title = ctx.inline_edit("note_title", cur.title, size=22, font=ui.FontRole.DISPLAY, width=ui.FILL)
                        cur.tag = ctx.select("note_tag", TAGS, cur.tag, width=130)
                        if ctx.icon_button(
                            ui.Icon.PIN,
                            selected=cur.pinned,
                            tooltip="Pin note",
                            color=ui.Color.ACCENT if cur.pinned else None,
                        ):
                            cur.pinned = not cur.pinned
                        if ctx.icon_button(ui.Icon.COMMAND, tooltip="Command palette (Ctrl+K)"):
                            palette_open = True
                        if ctx.icon_button(ui.Icon.TRASH, variant=ui.ButtonVariant.GHOST, tooltip="Delete note"):
                            confirm_delete = True

                    ctx.separator()
                    cur.body = ctx.textarea(
                        "note_body", cur.body,
                        placeholder="Write something...",
                        width=ui.FILL, height=-1,
                    )
                else:
                    if ctx.empty_state(
                        "Select or create a note",
                        description="Press Ctrl+N to start writing.",
                        icon=ui.Icon.FILE_TEXT,
                        action="New note",
                    ):
                        add_note()
        split_ratio = sp.ratio

        with ctx.dialog("Delete note?", confirm_delete, description="This action cannot be undone.") as dlg:
            if dlg:
                with ctx.dialog_footer():
                    if ctx.button("Cancel", variant=ui.ButtonVariant.GHOST):
                        dlg.open = False
                    if ctx.button("Delete", variant=ui.ButtonVariant.DANGER, icon=ui.Icon.TRASH):
                        delete_current()
                        dlg.open = False
        confirm_delete = dlg.open

        palette_open, cmd_idx = ctx.command_palette(palette_open, commands)
        if cmd_idx == 0:
            add_note()
        elif cmd_idx == 1 and 0 <= selected < len(notes):
            notes[selected].pinned = not notes[selected].pinned
        elif cmd_idx == 2 and 0 <= selected < len(notes):
            confirm_delete = True
        elif cmd_idx == 3:
            ctx.theme_mode = ui.ThemeMode.LIGHT if ctx.theme_mode == ui.ThemeMode.DARK else ui.ThemeMode.DARK

    with ui.App("Notes — yapps", width=1020, height=680) as app:
        app.run(draw)


if __name__ == "__main__":
    main()
