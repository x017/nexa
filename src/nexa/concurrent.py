"""Thread-safe channels, background worker pools, and non-blocking HTTP helpers for nexa UIs."""

from __future__ import annotations

import collections
import json
import threading
import time
import urllib.request
from typing import Any, Callable, Deque, Generic, Iterable, List, Optional, Tuple, TypeVar

from .types import Status, TaskStatus

T = TypeVar("T")


class Channel(Generic[T]):
    """Lock-light MPSC channel bridging background threads/sockets to the 60fps UI loop.

    Calling ``send(item)`` from any thread enqueues ``item`` and invokes ``wake()``
    so a sleeping event-driven ``App`` wakes up immediately with zero polling CPU.
    Inside your UI frame, call ``for msg in channel.drain(): ...`` without ever blocking!
    """

    __slots__ = ("_q", "_max", "_lock", "_wake", "_closed")

    def __init__(
        self,
        *,
        maxsize: int = 0,
        wake: Optional[Callable[[], None]] = None,
    ) -> None:
        self._q: Deque[T] = collections.deque()
        self._max = int(maxsize)
        self._lock = threading.Lock()
        self._wake = wake
        self._closed = False

    def send(self, item: T) -> bool:
        """Thread-safe: push ``item`` and wake the UI loop. Drops oldest if ``maxsize`` exceeded."""
        with self._lock:
            if self._closed:
                return False
            if self._max > 0 and len(self._q) >= self._max:
                self._q.popleft()
            self._q.append(item)
        if self._wake is not None:
            self._wake()
        return True

    def try_recv(self) -> Tuple[Optional[T], bool]:
        """Non-blocking pop returning ``(item, True)`` or ``(None, False)``."""
        with self._lock:
            if not self._q:
                return None, False
            return self._q.popleft(), True

    def drain(self, limit: int = 0) -> List[T]:
        """Non-blocking drain of all queued items for processing at the start of a UI frame."""
        with self._lock:
            if not self._q:
                return []
            if limit <= 0 or limit >= len(self._q):
                items = list(self._q)
                self._q.clear()
                return items
            return [self._q.popleft() for _ in range(limit)]

    def close(self) -> None:
        with self._lock:
            self._closed = True
        if self._wake is not None:
            self._wake()

    @property
    def closed(self) -> bool:
        return self._closed

    def __len__(self) -> int:
        with self._lock:
            return len(self._q)


class TaskHandle(Generic[T]):
    """Observable state of a background task or network request.

    Maps directly onto ``ui.status_button(label, task.button_status)``,
    ``ui.progress(task.progress)``, ``ui.tool_call(..., status=task.status)``, and
    ``ui.agent_status(..., status=task.status, seconds=task.elapsed)``!
    """

    __slots__ = (
        "_status", "_result", "_error", "_progress", "_message",
        "_t_start", "_t_end", "_cancel_ev", "_wake", "_on_cancel",
    )

    def __init__(self, wake: Optional[Callable[[], None]] = None) -> None:
        self._status = TaskStatus.PENDING
        self._result: Optional[T] = None
        self._error: Optional[BaseException] = None
        self._progress: float = 0.0
        self._message: str = ""
        self._t_start: float = 0.0
        self._t_end: float = 0.0
        self._cancel_ev = threading.Event()
        self._wake = wake
        self._on_cancel: Optional[Callable[[], Any]] = None

    @property
    def status(self) -> TaskStatus:
        return self._status

    @property
    def button_status(self) -> Status:
        """Convert to ``nexa.Status`` for ``ui.status_button(...)``."""
        s = self._status
        if s == TaskStatus.RUNNING:
            return Status.BUSY
        if s == TaskStatus.DONE:
            return Status.SUCCESS
        if s == TaskStatus.FAILED:
            return Status.ERROR
        return Status.IDLE

    @property
    def running(self) -> bool:
        return self._status == TaskStatus.RUNNING

    @property
    def done(self) -> bool:
        return self._status in (TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.SKIPPED)

    @property
    def cancelled(self) -> bool:
        return self._cancel_ev.is_set()

    @property
    def result(self) -> Optional[T]:
        return self._result

    @property
    def error(self) -> Optional[BaseException]:
        return self._error

    @property
    def progress(self) -> float:
        return self._progress

    @property
    def message(self) -> str:
        return self._message

    @property
    def elapsed(self) -> float:
        if self._t_start == 0.0:
            return 0.0
        end = self._t_end if self._t_end > 0.0 else time.monotonic()
        return max(0.0, end - self._t_start)

    def set_progress(self, value: float, message: Optional[str] = None) -> None:
        """Callable from inside the worker function to update UI progress & wake window."""
        self._progress = max(0.0, min(1.0, float(value)))
        if message is not None:
            self._message = message
        if self._wake is not None:
            self._wake()

    def cancel(self) -> None:
        self._cancel_ev.set()
        if self._status == TaskStatus.PENDING:
            self._status = TaskStatus.SKIPPED
        if self._on_cancel is not None:
            self._on_cancel()
        if self._wake is not None:
            self._wake()


class BackgroundRunner:
    """Lightweight daemon worker pool that dispatches completion/streaming callbacks onto the UI thread."""

    __slots__ = ("_dispatch", "_wake", "_sem", "_closed")

    def __init__(
        self,
        *,
        dispatch: Optional[Callable[[Callable[[], Any]], None]] = None,
        wake: Optional[Callable[[], None]] = None,
        max_workers: int = 4,
    ) -> None:
        self._wake = wake
        self._dispatch = dispatch
        self._sem = threading.BoundedSemaphore(max(1, int(max_workers)))
        self._closed = False

    @classmethod
    def for_app(cls, app: Any, *, max_workers: int = 4) -> BackgroundRunner:
        return cls(dispatch=app.call_soon_threadsafe, wake=app.wake, max_workers=max_workers)

    def _post_ui(self, fn: Callable[[], Any]) -> None:
        if self._dispatch is not None:
            self._dispatch(fn)
        else:
            fn()
            if self._wake is not None:
                self._wake()

    def submit(
        self,
        fn: Callable[..., T],
        *args: Any,
        on_done: Optional[Callable[[T], Any]] = None,
        on_error: Optional[Callable[[BaseException], Any]] = None,
        **kwargs: Any,
    ) -> TaskHandle[T]:
        """Run ``fn(*args, **kwargs)`` on a daemon worker thread and marshal callbacks to the UI thread."""
        handle: TaskHandle[T] = TaskHandle(wake=self._wake)

        def _worker() -> None:
            with self._sem:
                if handle.cancelled or self._closed:
                    handle._status = TaskStatus.SKIPPED
                    if self._wake:
                        self._wake()
                    return
                handle._status = TaskStatus.RUNNING
                handle._t_start = time.monotonic()
                if self._wake:
                    self._wake()
                try:
                    val = fn(*args, **kwargs)
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

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return handle

    def stream(
        self,
        gen_fn: Callable[..., Iterable[T]],
        *args: Any,
        on_item: Callable[[T], Any],
        on_done: Optional[Callable[[], Any]] = None,
        on_error: Optional[Callable[[BaseException], Any]] = None,
        **kwargs: Any,
    ) -> TaskHandle[None]:
        """Run an iterator/generator (e.g. SSE / LLM stream / socket reader) on a worker thread."""
        handle: TaskHandle[None] = TaskHandle(wake=self._wake)

        def _worker() -> None:
            with self._sem:
                if handle.cancelled or self._closed:
                    handle._status = TaskStatus.SKIPPED
                    return
                handle._status = TaskStatus.RUNNING
                handle._t_start = time.monotonic()
                if self._wake:
                    self._wake()
                try:
                    for item in gen_fn(*args, **kwargs):
                        if handle.cancelled or self._closed:
                            handle._status = TaskStatus.SKIPPED
                            handle._t_end = time.monotonic()
                            if self._wake:
                                self._wake()
                            return
                        self._post_ui(lambda x=item: on_item(x))
                except BaseException as exc:
                    handle._error = exc
                    handle._t_end = time.monotonic()
                    handle._status = TaskStatus.FAILED
                    if on_error is not None:
                        self._post_ui(lambda e=exc: on_error(e))
                    elif self._wake:
                        self._wake()
                    return
                handle._progress = 1.0
                handle._t_end = time.monotonic()
                handle._status = TaskStatus.DONE
                if on_done is not None:
                    self._post_ui(on_done)
                elif self._wake:
                    self._wake()

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return handle

    def fetch_bytes(
        self,
        url: str,
        *,
        method: str = "GET",
        headers: Optional[dict[str, str]] = None,
        body: Optional[bytes] = None,
        timeout: float = 15.0,
        on_done: Optional[Callable[[bytes], Any]] = None,
        on_error: Optional[Callable[[BaseException], Any]] = None,
    ) -> TaskHandle[bytes]:
        """Zero-dependency non-blocking HTTP request delivering ``bytes`` to the UI thread."""
        def _do_req() -> bytes:
            req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()

        return self.submit(_do_req, on_done=on_done, on_error=on_error)

    def fetch_json(
        self,
        url: str,
        *,
        method: str = "GET",
        headers: Optional[dict[str, str]] = None,
        payload: Any = None,
        timeout: float = 15.0,
        on_done: Optional[Callable[[Any], Any]] = None,
        on_error: Optional[Callable[[BaseException], Any]] = None,
    ) -> TaskHandle[Any]:
        """Zero-dependency non-blocking JSON HTTP request delivering parsed data to the UI thread."""
        hdrs = dict(headers or {})
        hdrs.setdefault("Accept", "application/json")
        raw_body: Optional[bytes] = None
        if payload is not None:
            raw_body = json.dumps(payload).encode("utf-8")
            hdrs.setdefault("Content-Type", "application/json")

        def _do_json() -> Any:
            req = urllib.request.Request(url, data=raw_body, headers=hdrs, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))

        return self.submit(_do_json, on_done=on_done, on_error=on_error)

    def close(self) -> None:
        self._closed = True
