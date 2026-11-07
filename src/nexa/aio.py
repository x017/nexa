"""Asyncio integration: cooperative single-thread ``run_async`` & threaded ``AsyncBridge``."""

from __future__ import annotations

import asyncio
import inspect
import threading
import time
from typing import Any, AsyncIterable, Callable, Coroutine, Optional, TypeVar

from ._context_var import pop_current_ui, push_current_ui
from .concurrent import TaskHandle
from .types import TaskStatus

T = TypeVar("T")


async def run_app_async(
    app: Any,
    draw_fn: Callable[..., Any],
    *,
    max_frames: Optional[int] = None,
) -> int:
    """Cooperatively drive an ``App`` inside the current ``asyncio`` event loop.

    All ``asyncio`` tasks (``httpx.AsyncClient``, ``aiohttp``, WebSockets, ``asyncio.StreamReader``)
    run on the exact same thread as ``ui``, so coroutines can mutate Python state directly
    and call ``app.wake()`` without locks!
    """
    try:
        sig = inspect.signature(draw_fn)
        takes_ui = len(sig.parameters) >= 1
    except (ValueError, TypeError):
        takes_ui = True

    wake_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _on_wake() -> None:
        loop.call_soon_threadsafe(wake_event.set)

    app._wake_callbacks.append(_on_wake)
    frames = 0
    try:
        while True:
            wake_event.clear()
            if not app.frame(wait=False):
                break

            try:
                if takes_ui:
                    res = draw_fn(app.ui)
                else:
                    res = draw_fn()
                if inspect.isawaitable(res):
                    await res
            finally:
                if app._ctx_token is not None:
                    pop_current_ui(app._ctx_token)
                    app._ctx_token = None

            frames += 1
            if max_frames is not None and frames >= max_frames:
                app.quit()
                # Flush final frame if headless screenshot requested
                app.frame(wait=False)
                break

            # Yield cooperatively to pending coroutines / network sockets
            if app._continuous or app.ui.needs_redraw or app._dispatch:
                await asyncio.sleep(0)
            else:
                wakeup = app.ui.next_wakeup
                delay = min(wakeup, 0.05) if wakeup > 0 else 0.016
                try:
                    await asyncio.wait_for(wake_event.wait(), timeout=max(0.001, delay))
                except asyncio.TimeoutError:
                    pass
    finally:
        if _on_wake in app._wake_callbacks:
            app._wake_callbacks.remove(_on_wake)
    return 0


class AsyncBridge:
    """Dedicated background ``asyncio`` event-loop thread paired with a synchronous native ``App``.

    Ideal when running blocking OS window loops (Win32/Cocoa/X11) while executing
    ``async def`` coroutines, WebSockets, or async HTTP streams concurrently.
    """

    __slots__ = ("_dispatch", "_wake", "_loop", "_thread", "_ready")

    def __init__(
        self,
        *,
        dispatch: Optional[Callable[[Callable[[], Any]], None]] = None,
        wake: Optional[Callable[[], None]] = None,
    ) -> None:
        self._dispatch = dispatch
        self._wake = wake
        self._ready = threading.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._ready.wait()

    @classmethod
    def for_app(cls, app: Any) -> AsyncBridge:
        return cls(dispatch=app.call_soon_threadsafe, wake=app.wake)

    def _run_loop(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        self._ready.set()
        loop.run_forever()
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.close()

    def _post_ui(self, fn: Callable[[], Any]) -> None:
        if self._dispatch is not None:
            self._dispatch(fn)
        else:
            fn()
            if self._wake is not None:
                self._wake()

    def spawn(
        self,
        coro: Coroutine[Any, Any, T],
        *,
        on_done: Optional[Callable[[T], Any]] = None,
        on_error: Optional[Callable[[BaseException], Any]] = None,
    ) -> TaskHandle[T]:
        """Schedule ``coro`` on the background ``asyncio`` loop and deliver results on the UI thread."""
        assert self._loop is not None
        handle: TaskHandle[T] = TaskHandle(wake=self._wake)
        handle._status = TaskStatus.RUNNING
        handle._t_start = time.monotonic()

        async def _runner() -> None:
            try:
                val = await coro
            except asyncio.CancelledError:
                handle._status = TaskStatus.SKIPPED
                handle._t_end = time.monotonic()
                if self._wake:
                    self._wake()
                return
            except BaseException as exc:
                handle._error = exc
                handle._t_end = time.monotonic()
                if on_error is not None:
                    def _finish_err(e: BaseException = exc) -> None:
                        try:
                            on_error(e)
                        finally:
                            handle._status = TaskStatus.FAILED
                    self._post_ui(_finish_err)
                else:
                    handle._status = TaskStatus.FAILED
                    if self._wake:
                        self._wake()
                return
            handle._result = val
            handle._progress = 1.0
            handle._t_end = time.monotonic()
            if on_done is not None:
                def _finish_ok(v: T = val) -> None:
                    try:
                        on_done(v)
                    finally:
                        handle._status = TaskStatus.DONE
                self._post_ui(_finish_ok)
            else:
                def _mark_done() -> None:
                    handle._status = TaskStatus.DONE
                self._post_ui(_mark_done)

        fut = asyncio.run_coroutine_threadsafe(_runner(), self._loop)
        handle._on_cancel = fut.cancel
        return handle

    def stream(
        self,
        agen: AsyncIterable[T],
        *,
        on_item: Callable[[T], Any],
        on_done: Optional[Callable[[], Any]] = None,
        on_error: Optional[Callable[[BaseException], Any]] = None,
    ) -> TaskHandle[None]:
        """Consume an async iterator (e.g. streaming LLM / WebSocket) and push items to the UI thread."""
        async def _consume() -> None:
            async for item in agen:
                self._post_ui(lambda x=item: on_item(x))

        return self.spawn(
            _consume(),
            on_done=(lambda _: on_done()) if on_done is not None else None,
            on_error=on_error,
        )

    def close(self) -> None:
        if self._loop is not None and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=2.0)
