"""Context-free C99 utilities added with CUI 1.2–1.4.

These need no open frame: regex search, cron scheduling, URL query strings and
HTTP helpers.  Widget-facing additions (``request_wakeup``, ``set_strings``,
``response_status``) live on :class:`nexa.UI`.
"""

from __future__ import annotations

import ctypes
from ctypes import c_char_p, c_int, c_int64, c_size_t
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from ._cdefs import CUI_REGEX_GROUPS, CuiKvPair, CuiRegexMatch, CuiStrings
from ._lib import get_cdll

REGEX_IGNORECASE = 1
REGEX_MULTILINE = 2
REGEX_DOTALL = 4


class RegexMatch:
    """One match of :func:`regex_search`, with its capture groups."""

    __slots__ = ("start", "end", "groups", "group_spans", "group_names", "text")

    def __init__(self, start: int, end: int, groups: int, group_spans: Sequence[Tuple[int, int]],
                 group_names: Sequence[str], text: str = "") -> None:
        self.start = int(start)
        self.end = int(end)
        self.groups = int(groups)
        self.group_spans = tuple(group_spans)
        self.group_names = tuple(group_names)
        self.text = text

    def group(self, index: int) -> Optional[str]:
        """The text of capture group ``index`` (1 based), or None when it took no part."""
        if index == 0:
            return self.text[self.start : self.end]
        if not (1 <= index <= len(self.group_spans)):
            return None
        s, e = self.group_spans[index - 1]
        if s < 0 or e < 0:
            return None
        return self.text[s:e]

    def named(self, name: str) -> Optional[str]:
        """The text of the group called ``name`` (``(?<name> ...)``), or None."""
        for i, group_name in enumerate(self.group_names):
            if group_name == name:
                return self.group(i + 1)
        return None

    def __iter__(self):
        yield self.start
        yield self.end

    def __repr__(self) -> str:
        return f"RegexMatch({self.start}..{self.end}, groups={self.groups})"


def regex_search(
    pattern: str,
    text: str,
    *,
    ignore_case: bool = False,
    multiline: bool = False,
    dotall: bool = False,
    start: int = 0,
    limit: int = 1000,
) -> List[RegexMatch]:
    """All matches of ``pattern`` in ``text``, using CUI's own RE2-style engine.

    Groups, named groups ``(?<name> ...)``, lazy quantifiers, classes and anchors
    are supported.  A pattern that backtracks too long stops on its step budget
    instead of freezing.  Raises :class:`ValueError` for an invalid pattern.
    """
    flags = 0
    if ignore_case:
        flags |= REGEX_IGNORECASE
    if multiline:
        flags |= REGEX_MULTILINE
    if dotall:
        flags |= REGEX_DOTALL
    lib = get_cdll()
    raw = text.encode("utf-8")
    hay = ctypes.create_string_buffer(raw, len(raw) + 1)
    matches: List[RegexMatch] = []
    pos = int(start)
    for _ in range(max(1, int(limit))):
        m = CuiRegexMatch()
        err = c_char_p()
        found = int(lib.cui_regex_search(
            pattern.encode("utf-8"), flags, ctypes.cast(hay, c_char_p), int(len(raw)), int(pos),
            ctypes.byref(m), ctypes.byref(err)
        ))
        if found <= 0:
            if found < 0 and err.value:
                raise ValueError(err.value.decode("utf-8", errors="replace"))
            break
        # CUI stores capture group i at slot i and names in the same slot (group 0 unused)
        slots = list(range(1, min(m.groups, CUI_REGEX_GROUPS - 1) + 1))
        spans = [(int(m.group_start[i]), int(m.group_end[i])) for i in slots]
        names = [bytes(m.group_name[i]).split(b"\0", 1)[0].decode("utf-8", errors="replace") for i in slots]
        decoded = raw.decode("utf-8", errors="replace")
        matches.append(RegexMatch(m.start, m.end, m.groups, spans, names, decoded))
        pos = m.end if m.end > m.start else m.end + 1
        if pos > len(raw):
            break
    return matches


def cron_next(expression: str, after: Optional[int] = None, *, utc_offset: int = 0) -> Optional[int]:
    """The next epoch second a 5-field cron ``expression`` fires, or None when it never does."""
    import time

    when = int(time.time()) if after is None else int(after)
    out = c_int64(0)
    ok = bool(get_cdll().cui_cron_next(expression.encode("utf-8"), c_int64(when), int(utc_offset), ctypes.byref(out)))
    return int(out.value) if ok else None


def cron_describe(expression: str, ui: Any = None) -> str:
    """A sentence for a cron ``expression``, e.g. "Every 15 minutes".

    CUI builds the sentence in the frame's own arena, so this needs an active
    frame: call it inside ``with ui.frame():`` (or pass the ``UI`` explicitly).
    """
    from ._context_var import try_get_current_ui

    handle_ui = ui if ui is not None else try_get_current_ui()
    handle = getattr(handle_ui, "_ctx", None)
    if not handle:
        raise RuntimeError("cron_describe needs an active nexa frame (call it inside `with ui.frame():`)")
    text = get_cdll().cui_cron_describe(handle, expression.encode("utf-8"))
    return text.decode("utf-8", errors="replace") if text else ""


def url_params(url: str) -> Dict[str, str]:
    """The query parameters of ``url`` as a dict (duplicates keep the last value)."""
    cap = 256
    pairs = (CuiKvPair * cap)()
    n = int(get_cdll().cui_url_params(url.encode("utf-8"), pairs, cap))
    out: Dict[str, str] = {}
    for i in range(max(0, n)):
        key = bytes(pairs[i].key).split(b"\0", 1)[0].decode("utf-8", errors="replace")
        value = bytes(pairs[i].value).split(b"\0", 1)[0].decode("utf-8", errors="replace")
        out[key] = value
    return out


def url_set_params(url: str, params: Dict[str, str], *, cap: int = 8192) -> str:
    """``url`` with its query replaced by ``params``; returns the new URL."""
    n = len(params)
    pairs = (CuiKvPair * max(1, n))()
    for i, (key, value) in enumerate(params.items()):
        pairs[i].key = key.encode("utf-8")[:63]
        pairs[i].value = str(value).encode("utf-8")[:255]
        pairs[i].enabled = True
    buf = ctypes.create_string_buffer(url.encode("utf-8"), cap)
    ok = bool(get_cdll().cui_url_set_params(ctypes.cast(buf, c_char_p), c_size_t(cap), pairs, n))
    if not ok:
        raise ValueError("the URL with its parameters did not fit in the buffer")
    return buf.value.decode("utf-8", errors="replace")


def http_reason(status: int) -> str:
    """The reason phrase for an HTTP status code ("" when unknown)."""
    text = get_cdll().cui_http_reason(int(status))
    return text.decode("utf-8", errors="replace") if text else ""


def http_method_name(method: Union[int, str]) -> str:
    """``"GET"``, ``"POST"``… for an HTTP method index (0 is GET), or the name when given one."""
    if isinstance(method, str):
        return method.upper()
    text = get_cdll().cui_http_method_name(int(method))
    return text.decode("utf-8", errors="replace") if text else ""


__all__ = [
    "RegexMatch",
    "REGEX_IGNORECASE",
    "REGEX_MULTILINE",
    "REGEX_DOTALL",
    "regex_search",
    "cron_next",
    "cron_describe",
    "url_params",
    "url_set_params",
    "http_reason",
    "http_method_name",
]
