"""Conversation, threaded comments, typing indicators, and collaborative presence."""

from __future__ import annotations

import ctypes
from ctypes import c_bool, c_int
from typing import Optional, Sequence, Tuple

from .._cdefs import (
    CuiChatOpts,
    CuiCommentOpts,
    CuiMarkdownResult,
    CuiPresenceUser,
    encode_opt,
    encode_str,
    to_c_color,
)
from ..types import CommentFlags, MarkdownResult, PresenceUser


class SocialMixin:
    __slots__ = ()

    def chat_message(
        self,
        text: str,
        *,
        mine: bool = False,
        author: Optional[str] = None,
        time: Optional[str] = None,
        status: Optional[str] = None,
        grouped: bool = False,
        last_in_group: bool = True,
        avatar: int = 0,
        markdown: bool = False,
    ) -> Optional[MarkdownResult]:
        keep = self._frame_keepalive
        opts = CuiChatOpts()
        opts.mine = bool(mine)
        opts.author = encode_opt(author, keep)
        opts.time = encode_opt(time, keep)
        opts.status = encode_opt(status, keep)
        opts.grouped = bool(grouped)
        opts.last_in_group = bool(last_in_group)
        opts.avatar = int(avatar)
        opts.markdown = bool(markdown)
        c_md = None
        if markdown:
            c_md = CuiMarkdownResult()
            opts.markdown_result = ctypes.pointer(c_md)
            keep.append(c_md)
        keep.append(opts)
        self._lib.cui_chat_message_ex(self._ctx, encode_str(text, keep), ctypes.byref(opts))
        if c_md is not None:
            res = MarkdownResult(
                link=c_md.link.decode("utf-8", errors="replace") if c_md.link else None,
                hovered_link=c_md.hovered_link.decode("utf-8", errors="replace") if c_md.hovered_link else None,
                task_offset=int(c_md.task_offset),
                task_line=int(c_md.task_line),
                task_checked=bool(c_md.task_checked),
                height=float(c_md.height),
            )
            self._record_change(bool(res))
            return res
        return None

    def chat_divider(self, label: str) -> None:
        self._lib.cui_chat_divider(self._ctx, encode_str(label, self._frame_keepalive))

    def typing_indicator(self, name: str = "") -> None:
        self._lib.cui_typing_indicator(self._ctx, encode_str(name, self._frame_keepalive))

    def comment(
        self,
        id: str,
        author: str,
        text: str,
        *,
        time: Optional[str] = None,
        depth: int = 0,
        likes: int = 0,
        liked: bool = False,
        edited: bool = False,
        badge: Optional[str] = None,
    ) -> Tuple[CommentFlags, int, bool]:
        """Threaded comment; returns ``(flags, updated_likes, updated_liked)``."""
        keep = self._frame_keepalive
        c_likes = c_int(int(likes))
        c_liked = c_bool(bool(liked))
        opts = CuiCommentOpts()
        opts.time = encode_opt(time, keep)
        opts.depth = int(depth)
        opts.likes = ctypes.pointer(c_likes)
        opts.liked = ctypes.pointer(c_liked)
        opts.edited = bool(edited)
        opts.badge = encode_opt(badge, keep)
        keep.extend((c_likes, c_liked, opts))
        flags = CommentFlags(int(self._lib.cui_comment_ex(
            self._ctx, encode_str(id, keep), encode_str(author, keep), encode_str(text, keep),
            ctypes.byref(opts)
        )))
        self._record_change(bool(flags))
        return flags, int(c_likes.value), bool(c_liked.value)

    def presence(
        self,
        id: str,
        users: Sequence[PresenceUser],
        *,
        max_visible: int = 4,
        size: float = 30.0,
    ) -> None:
        keep = self._frame_keepalive
        n = len(users)
        arr = (CuiPresenceUser * n)()
        for i, u in enumerate(users):
            arr[i].name = encode_str(u.name, keep)
            arr[i].color = to_c_color(u.color)
            arr[i].avatar = int(u.avatar)
            arr[i].idle = bool(u.idle)
        keep.append(arr)
        self._lib.cui_presence(
            self._ctx, encode_str(id, keep), arr, n, int(max_visible), float(size)
        )
