"""Scalable Object-Oriented UI architecture: Component, View, Router, Store, and Application."""

from __future__ import annotations

from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, TypeVar, Union

from ._context_var import resolve_ui
from .app import App
from .concurrent import BackgroundRunner
from .types import Accent, RendererKind, ThemeMode
from .ui import UI

S = TypeVar("S")


class Store(Generic[S]):
    """Observable application state container for scalable OOP / MVVM / Flux architectures.

    Calling ``store.update(...)`` or ``store.value = ...`` notifies subscribers and
    wakes any bound ``App`` automatically (even from background threads when used with
    ``app.call_soon_threadsafe``).
    """

    __slots__ = ("_state", "_listeners", "_wake")

    def __init__(self, initial: S, *, wake: Optional[Callable[[], None]] = None) -> None:
        self._state: S = initial
        self._listeners: List[Callable[[S], Any]] = []
        self._wake = wake

    @property
    def value(self) -> S:
        return self._state

    @value.setter
    def value(self, new_state: S) -> None:
        self._state = new_state
        self.notify()

    def update(self, mutator: Callable[[S], Optional[S]]) -> S:
        res = mutator(self._state)
        if res is not None:
            self._state = res
        self.notify()
        return self._state

    def subscribe(self, listener: Callable[[S], Any]) -> Callable[[], None]:
        self._listeners.append(listener)

        def _unsub() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return _unsub

    def bind_wake(self, wake: Callable[[], None]) -> None:
        self._wake = wake

    def notify(self) -> None:
        for fn in list(self._listeners):
            fn(self._state)
        if self._wake is not None:
            self._wake()


class Component:
    """Reusable, automatically ID-scoped immediate-mode UI component.

    Subclass and implement ``build(self, ui: UI) -> Any``. Calling ``comp(ui)`` (or
    ``comp()`` inside an active functional frame) pushes ``self.key`` onto CUI's ID
    stack so multiple instances never collide on widget IDs!
    """

    _next_uid: int = 1

    def __init__(self, key: Optional[str] = None) -> None:
        if key is None:
            uid = Component._next_uid
            Component._next_uid += 1
            key = f"{self.__class__.__name__}#{uid}"
        self.key: str = key
        self._mounted: bool = False

    def on_mount(self, ui: UI) -> None:
        """Called once before the component's first ``build(ui)``."""

    def on_unmount(self) -> None:
        """Optional cleanup hook when removed from a parent or ``Router``."""

    def build(self, ui: UI) -> Any:
        raise NotImplementedError

    def render(self, ui: Optional[UI] = None) -> Any:
        ctx = resolve_ui(ui)
        if not self._mounted:
            self._mounted = True
            self.on_mount(ctx)
        with ctx.id_scope(self.key):
            return self.build(ctx)

    def __call__(self, ui: Optional[UI] = None) -> Any:
        return self.render(ui)


class View(Component):
    """Named screen/route inside a ``Router`` with navigation lifecycle hooks."""

    title: str = ""
    icon: Optional[str] = None

    def on_enter(self, params: Dict[str, Any]) -> None:
        """Called when navigated to via ``Router.push`` or ``Router.replace``."""

    def on_leave(self) -> None:
        """Called when navigated away from."""


class Router:
    """Declarative multi-view router with back/forward history stack."""

    __slots__ = ("_routes", "_stack", "_index", "_wake")

    def __init__(
        self,
        routes: Optional[Dict[str, Union[View, Callable[[], View]]]] = None,
        *,
        initial: Optional[str] = None,
        wake: Optional[Callable[[], None]] = None,
    ) -> None:
        self._routes: Dict[str, View] = {}
        self._stack: List[Tuple[str, Dict[str, Any]]] = []
        self._index: int = -1
        self._wake = wake
        if routes:
            for name, v in routes.items():
                self.register(name, v)
        if initial is not None:
            self.replace(initial)
        elif self._routes:
            first = next(iter(self._routes))
            self.replace(first)

    def register(self, name: str, view: Union[View, Callable[[], View]]) -> None:
        inst = view() if callable(view) and not isinstance(view, View) else view
        self._routes[name] = inst
        if self._index < 0:
            self.replace(name)

    @property
    def current_name(self) -> str:
        return self._stack[self._index][0] if 0 <= self._index < len(self._stack) else ""

    @property
    def current(self) -> str:
        """Alias for ``current_name``."""
        return self.current_name

    @property
    def current_params(self) -> Dict[str, Any]:
        return self._stack[self._index][1] if 0 <= self._index < len(self._stack) else {}

    @property
    def current_view(self) -> Optional[View]:
        return self._routes.get(self.current_name)

    @property
    def can_go_back(self) -> bool:
        return self._index > 0

    @property
    def can_go_forward(self) -> bool:
        return 0 <= self._index < len(self._stack) - 1

    def push(self, name: str, **params: Any) -> None:
        if name not in self._routes:
            raise KeyError(f"Unknown route: {name!r}")
        cur = self.current_view
        if cur is not None:
            cur.on_leave()
        if self._index < len(self._stack) - 1:
            del self._stack[self._index + 1:]
        self._stack.append((name, dict(params)))
        self._index = len(self._stack) - 1
        self._routes[name].on_enter(self.current_params)
        if self._wake:
            self._wake()

    def replace(self, name: str, **params: Any) -> None:
        if name not in self._routes:
            raise KeyError(f"Unknown route: {name!r}")
        cur = self.current_view
        if cur is not None:
            cur.on_leave()
        if self._index < 0:
            self._stack.append((name, dict(params)))
            self._index = 0
        else:
            self._stack[self._index] = (name, dict(params))
        self._routes[name].on_enter(self.current_params)
        if self._wake:
            self._wake()

    def back(self) -> bool:
        if not self.can_go_back:
            return False
        cur = self.current_view
        if cur is not None:
            cur.on_leave()
        self._index -= 1
        nxt = self.current_view
        if nxt is not None:
            nxt.on_enter(self.current_params)
        if self._wake:
            self._wake()
        return True

    def forward(self) -> bool:
        if not self.can_go_forward:
            return False
        cur = self.current_view
        if cur is not None:
            cur.on_leave()
        self._index += 1
        nxt = self.current_view
        if nxt is not None:
            nxt.on_enter(self.current_params)
        if self._wake:
            self._wake()
        return True

    def render(self, ui: Optional[UI] = None) -> Any:
        view = self.current_view
        if view is not None:
            return view.render(ui)
        return None

    def __call__(self, ui: Optional[UI] = None) -> Any:
        return self.render(ui)

    navigate = push


class Application:
    """High-level OOP base class bundling ``App``, ``BackgroundRunner``, and ``Router``.

    Example::

        class CounterApp(yapps.Application):
            def setup(self):
                self.count = 0

            def build(self, ui: yapps.UI):
                with ui.column(pad=24, gap=12):
                    ui.heading(f"Count: {self.count}")
                    if ui.button("Increment", variant=yapps.ButtonVariant.PRIMARY):
                        self.count += 1
    """

    title: str = "yapps"
    width: int = 1080
    height: int = 720
    theme: ThemeMode = ThemeMode.LIGHT
    accent: Accent = Accent.BLUE

    def __init__(
        self,
        title: Optional[str] = None,
        *,
        width: Optional[int] = None,
        height: Optional[int] = None,
        theme: Optional[ThemeMode] = None,
        accent: Optional[Accent] = None,
        renderer: RendererKind = RendererKind.AUTO,
        headless: Union[bool, str] = "auto",
        max_workers: int = 4,
        **app_kwargs: Any,
    ) -> None:
        self.app = App(
            title=title if title is not None else self.title,
            width=width if width is not None else self.width,
            height=height if height is not None else self.height,
            theme=theme if theme is not None else self.theme,
            accent=accent if accent is not None else self.accent,
            renderer=renderer,
            headless=headless,
            **app_kwargs,
        )
        self.ui: UI = self.app.ui
        self.runner = BackgroundRunner.for_app(self.app, max_workers=max_workers)
        self.router = Router(wake=self.app.wake)
        self._async_bridge: Any = None
        self.setup()

    @property
    def async_bridge(self):
        """Lazily start a background ``AsyncBridge`` thread on first access."""
        if self._async_bridge is None:
            from .aio import AsyncBridge
            self._async_bridge = AsyncBridge.for_app(self.app)
        return self._async_bridge

    def setup(self) -> None:
        """Override to initialize state, routes, fonts, or startup tasks."""

    def on_close(self) -> None:
        """Override for shutdown cleanup."""

    def build(self, ui: UI) -> None:
        """Override to build the application UI; defaults to rendering ``self.router``."""
        self.router.render(ui)

    def call_soon(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        self.app.call_soon_threadsafe(fn, *args, **kwargs)

    def wake(self) -> None:
        self.app.wake()

    def quit(self) -> None:
        self.app.quit()

    def run(self, *, max_frames: Optional[int] = None) -> int:
        try:
            return self.app.run(self.build, max_frames=max_frames)
        finally:
            self.close()

    async def run_async(self, *, max_frames: Optional[int] = None) -> int:
        try:
            return await self.app.run_async(self.build, max_frames=max_frames)
        finally:
            self.close()

    def close(self) -> None:
        try:
            self.on_close()
        finally:
            self.runner.close()
            if self._async_bridge is not None:
                self._async_bridge.close()
                self._async_bridge = None
            self.app.close()

    def __enter__(self) -> Application:
        return self

    def __exit__(self, *exc) -> None:
        self.close()
