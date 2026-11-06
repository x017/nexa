"""Mail Client: swipeable inbox, filter chips, threaded comments, dropzone & compose sheet (port of mail.c)."""

from __future__ import annotations

import yapps as ui


def main() -> None:
    messages = [
        {
            "id": 1,
            "sender": "Claire Dubois",
            "subject": "Design review for v1.0 tokens",
            "time": "10:42",
            "unread": True,
            "starred": True,
            "body": "Attached the updated OKLCH contrast table for dark surfaces. Every token clears WCAG AA.",
        },
        {
            "id": 2,
            "sender": "Henrik Lind",
            "subject": "Linux wheel size report",
            "time": "09:15",
            "unread": False,
            "starred": False,
            "body": "With -ffunction-sections and --gc-sections, libyapps_cui.so came in at 652 KB including fonts!",
        },
        {
            "id": 3,
            "sender": "Amina Patel",
            "subject": "Customer telemetry pipeline",
            "time": "Yesterday",
            "unread": True,
            "starred": False,
            "body": "Can we expose a non-blocking Channel for background WebSocket ingestion? Looks super clean.",
        },
    ]
    selected_id = 1
    unread_only = False
    starred_only = False
    compose_open = False
    to_addr = ""
    subj = ""
    draft = ""
    attached: list[str] = []
    likes = 3
    liked = False

    def draw(ctx: ui.UI) -> None:
        nonlocal selected_id, unread_only, starred_only, compose_open, to_addr, subj, draft, likes, liked

        with ctx.row(width=ui.FILL, height=ui.FILL, bg=ui.Color.BACKGROUND):
            # Inbox column
            with ctx.column(width=340, height=ui.FILL, bg=ui.Color.SURFACE_MUTED, pad=12, gap=10):
                with ctx.row(align=ui.Align.CENTER, gap=8):
                    ctx.heading("Inbox", level=3)
                    ctx.spacer()
                    ctx.theme_toggle()
                    if ctx.button("Compose", icon=ui.Icon.SQUARE_PEN, size=ui.ControlSize.SM, variant=ui.ButtonVariant.PRIMARY):
                        compose_open = True

                with ctx.row(gap=8):
                    unread_only = ctx.chip("Unread", unread_only, icon=ui.Icon.MAIL)
                    starred_only = ctx.chip("Starred", starred_only, icon=ui.Icon.STAR)

                with ctx.scroll("mail_list", width=ui.FILL, height=ui.FILL, gap=4):
                    for msg in list(messages):
                        if unread_only and not msg["unread"]:
                            continue
                        if starred_only and not msg["starred"]:
                            continue
                        mid = msg["id"]
                        with ctx.swipe_item(
                            f"msg_{mid}",
                            left=[ui.SwipeAction("Star", icon=ui.Icon.STAR, tone=ui.Tone.WARNING)],
                            right=[ui.SwipeAction("Archive", icon=ui.Icon.ARCHIVE, tone=ui.Tone.DANGER)],
                        ) as sw:
                            if ctx.list_item(
                                msg["sender"],
                                subtitle=msg["subject"],
                                trailing=msg["time"],
                                avatar=msg["sender"],
                                selected=(mid == selected_id),
                            ):
                                selected_id = mid
                                msg["unread"] = False
                        if sw.action == 0:
                            msg["starred"] = not msg["starred"]
                        elif sw.action >= 100:
                            messages.remove(msg)

            # Reading pane
            with ctx.scroll("mail_reader", width=ui.FILL, height=ui.FILL, pad=28, gap=18):
                cur = next((m for m in messages if m["id"] == selected_id), None)
                if cur is None:
                    ctx.empty_state("Select a conversation", icon=ui.Icon.INBOX)
                else:
                    ctx.heading(cur["subject"], level=2)
                    _, likes, liked = ctx.comment(
                        f"c_{cur['id']}", cur["sender"], cur["body"],
                        time=cur["time"], likes=likes, liked=liked, badge="Core Team",
                    )
                    ctx.separator()
                    dropped, browse = ctx.dropzone(
                        "reply_files",
                        title="Drop attachments to reply",
                        accept="png;jpg;pdf;md",
                        compact=True,
                    )
                    if dropped:
                        attached.extend(dropped)
                    if browse:
                        ctx.toast("Drop files onto the window to attach", tone=ui.Tone.INFO)
                    for path in attached:
                        ctx.badge(path, icon=ui.Icon.PAPERCLIP, tone=ui.Tone.ACCENT)

        with ctx.sheet("New Message", compose_open, side=ui.Side.RIGHT, size=420) as sh:
            if sh:
                with ctx.column(gap=14, width=ui.FILL):
                    to_addr = ctx.input("to", to_addr, label="To", placeholder="colleague@company.com")
                    subj = ctx.input("subj", subj, label="Subject")
                    draft = ctx.textarea("body", draft, label="Message", height=180)
                    if ctx.button("Send message", icon=ui.Icon.SEND, variant=ui.ButtonVariant.PRIMARY, full_width=True):
                        ctx.toast("Message sent", description=f"Delivered to {to_addr or 'recipient'}.", tone=ui.Tone.SUCCESS)
                        sh.open = False
        compose_open = sh.open

    with ui.App("Mail — yapps", width=1060, height=680) as app:
        app.run(draw)


if __name__ == "__main__":
    main()
