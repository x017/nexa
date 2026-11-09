"""Functional top-level widget & context wrappers resolving the active ``UI`` via ``ContextVar``."""

from __future__ import annotations

import functools
from typing import Any, Callable, Dict, Optional

from ._context_var import get_current_ui, try_get_current_ui
from .app import App
from .ui import UI
from .widgets.data import diff_compute, diff_words, markdown_apply_task, tree_sort
from .widgets.tools import curve_eval, flame_sort, gradient_eval

_EXCLUDED = frozenset({
    "close",
    "begin_frame",
    "end_frame",
    "frame",
    "set_viewport",
    "set_renderer",
    "set_platform",
    "render_rgba",
    "render_to_png",
    "draw_data",
    "raw_handle",
    "diff_compute",
    "diff_words",
    "markdown_apply_task",
    "tree_sort",
    "flame_sort",
    "curve_eval",
    "gradient_eval",
})


def current_ui() -> UI:
    """Return the currently active ``UI`` context in this thread / asyncio task."""
    return get_current_ui()


def changed() -> bool:
    """True if the most recently called widget in the current frame modified its value."""
    return get_current_ui().changed


def submitted() -> bool:
    """True if the most recently called input/OTP/composer widget was submitted (Enter)."""
    return get_current_ui().submitted


def focused() -> bool:
    return get_current_ui().focused


def blurred() -> bool:
    return get_current_ui().blurred


def run(
    draw_fn: Callable[..., Any],
    *,
    title: str = "nexa",
    width: int = 1080,
    height: int = 720,
    max_frames: Optional[int] = None,
    **app_kwargs: Any,
) -> int:
    """One-line functional entry point: creates an ``App``, runs ``draw_fn``, and cleans up."""
    with App(title=title, width=width, height=height, **app_kwargs) as app:
        return app.run(draw_fn, max_frames=max_frames)


def _make_proxy(name: str, method: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(method)
    def _proxy(*args: Any, **kwargs: Any) -> Any:
        return method(get_current_ui(), *args, **kwargs)

    _proxy.__qualname__ = name
    return _proxy


FUNCTIONAL_EXPORTS: Dict[str, Callable[..., Any]] = {
    "current_ui": current_ui,
    "changed": changed,
    "submitted": submitted,
    "focused": focused,
    "blurred": blurred,
    "run": run,
    "diff_compute": diff_compute,
    "diff_words": diff_words,
    "markdown_apply_task": markdown_apply_task,
    "tree_sort": tree_sort,
    "flame_sort": flame_sort,
    "curve_eval": curve_eval,
    "gradient_eval": gradient_eval,
}

for _attr_name in dir(UI):
    if _attr_name.startswith("_") or _attr_name in _EXCLUDED:
        continue
    _attr = getattr(UI, _attr_name)
    if callable(_attr) and not isinstance(_attr, type):
        _fn = _make_proxy(_attr_name, _attr)
        globals()[_attr_name] = _fn
        FUNCTIONAL_EXPORTS[_attr_name] = _fn

__all__ = list(FUNCTIONAL_EXPORTS.keys())
