"""Thread-safe and asyncio-task-safe active UI context resolution."""

from __future__ import annotations

from contextvars import ContextVar, Token as CtxToken
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .ui import UI

_CURRENT_UI: ContextVar[Optional["UI"]] = ContextVar("nexa_current_ui", default=None)


def get_current_ui() -> "UI":
    ui = _CURRENT_UI.get()
    if ui is None:
        raise RuntimeError(
            "No active nexa UI frame context. Either pass `ui` explicitly or call inside `while app.frame() as ui:` / `with ui.frame():`."
        )
    return ui


def try_get_current_ui() -> Optional["UI"]:
    return _CURRENT_UI.get()


def push_current_ui(ui: "UI") -> CtxToken:
    return _CURRENT_UI.set(ui)


def pop_current_ui(token: CtxToken) -> None:
    _CURRENT_UI.reset(token)


def resolve_ui(ui: Optional["UI"] = None) -> "UI":
    return ui if ui is not None else get_current_ui()
