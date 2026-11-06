"""Cross-platform application window & headless fallback loop with thread-safe dispatch."""

from __future__ import annotations

import collections
import ctypes
import os
import threading
import time
from ctypes import c_float
from pathlib import Path
from typing import Any, Callable, Deque, Optional, Tuple, Union

from ._cdefs import AppFrameFn, CuiAppDesc, CuiFileDialogOpts, encode_opt
from ._context_var import pop_current_ui, push_current_ui
from ._lib import get_cdll
from .render import SoftwareRenderer, write_png
from .types import Accent, FileDialogKind, RendererKind, ThemeMode, Vec2
from .ui import UI


def open_url(url: str) -> bool:
    """Open a URL or local path in the OS default browser/handler."""
    return bool(get_cdll().cui_app_open_url(url.encode("utf-8")))


class App:
    """Windowed or headless application host for ``yapps``.

    Supports:
    - Loop style: ``while app.frame(): ...``
    - Callback style: ``app.run(draw_fn)`` (smooth live resize on Win32/macOS)
    - Cooperative ``asyncio`` style: ``await app.run_async(draw_fn)``
    - Thread-safe UI dispatch: ``app.call_soon_threadsafe(fn, *args)`` and ``app.wake()``
    - Automatic headless offscreen fallback when ``headless=True`` or ``YAPPS_HEADLESS=1``.
    """

    def __init__(
        self,
        title: str = "yapps",
        width: int = 1080,
        height: int = 720,
        *,
        min_width: int = 360,
        min_height: int = 280,
        fixed_size: bool = False,
        continuous: bool = False,
        no_vsync: bool = False,
        hidden: bool = False,
        renderer: RendererKind = RendererKind.AUTO,
        theme: ThemeMode = ThemeMode.LIGHT,
        accent: Accent = Accent.BLUE,
        follow_system_theme: bool = False,
        headless: Union[bool, str] = "auto",
    ) -> None:
        self._lib = get_cdll()
        self._dispatch: Deque[Callable[[], Any]] = collections.deque()
        self._wake_callbacks: list[Callable[[], None]] = []
        self._ctx_token = None
        self._title = title
        self._continuous = bool(continuous)

        env_headless = (
            os.environ.get("YAPPS_HEADLESS", "").strip().lower() in ("1", "true", "yes")
            or os.environ.get("CUI_HEADLESS", "").strip().lower() in ("1", "true", "yes")
        )
        force_headless = (headless is True) or env_headless
        max_f_env = os.environ.get("YAPPS_MAX_FRAMES") or os.environ.get("CUI_MAX_FRAMES")
        self._env_max_frames: Optional[int] = int(max_f_env) if max_f_env else None

        self._app: Optional[int] = None
        self._headless_sw: Optional[SoftwareRenderer] = None
        self._headless_running: bool = False
        self._headless_in_frame: bool = False
        self._headless_wake_ev = threading.Event()
        self._headless_size = [max(1, int(width)), max(1, int(height))]
        self._headless_last_t = time.monotonic()
        self._screenshot_path = os.environ.get("CUI_SCREENSHOT") or None
        self._screenshot_frames = int(os.environ.get("CUI_SCREENSHOT_FRAMES") or "90")
        self._frame_counter = 0

        if not force_headless:
            keep: list[Any] = []
            desc = CuiAppDesc()
            desc.title = encode_opt(title, keep)
            desc.width = int(width)
            desc.height = int(height)
            desc.min_width = int(min_width)
            desc.min_height = int(min_height)
            desc.fixed_size = bool(fixed_size)
            desc.continuous = bool(continuous)
            desc.no_vsync = bool(no_vsync)
            desc.hidden = bool(hidden)
            desc.renderer = int(renderer)
            desc.theme = int(theme)
            desc.accent = int(accent)
            desc.follow_system_theme = bool(follow_system_theme)

            handle = self._lib.cui_app_create(ctypes.byref(desc))
            if handle:
                self._app = int(handle)
                ctx_ptr = int(self._lib.cui_app_ui(self._app))
                self.ui = UI(_adopt_handle=ctx_ptr, _owns_ctx=False)
                return
            if headless is False:
                raise RuntimeError("Could not create native OS window (set headless=True or headless='auto' for offscreen mode)")

        # Headless offscreen mode (works in CI, Docker, SSH, tests, screenshots)
        env_theme = os.environ.get("CUI_THEME", "").strip().lower()
        if env_theme == "dark":
            theme = ThemeMode.DARK
        elif env_theme == "light":
            theme = ThemeMode.LIGHT

        self._headless_sw = SoftwareRenderer()
        self.ui = UI(
            width=float(self._headless_size[0]),
            height=float(self._headless_size[1]),
            scale=1.0,
            theme=theme,
            accent=accent,
            renderer=self._headless_sw,
        )
        self._headless_running = True
        if self._screenshot_path or self._env_max_frames is not None:
            self._continuous = True

    @property
    def is_headless(self) -> bool:
        return self._app is None

    @property
    def is_software(self) -> bool:
        if self._app is not None:
            return bool(self._lib.cui_app_is_software(self._app))
        return True

    @property
    def backend(self) -> str:
        if self._app is not None:
            b = self._lib.cui_app_backend(self._app)
            return b.decode("utf-8") if b else "unknown"
        return "headless"

    @property
    def native_window(self) -> int:
        if self._app is not None:
            return int(self._lib.cui_app_native_window(self._app) or 0)
        return 0

    @property
    def size(self) -> Vec2:
        if self._app is not None:
            w, h = c_float(0.0), c_float(0.0)
            self._lib.yapps_app_size(self._app, ctypes.byref(w), ctypes.byref(h))
            return Vec2(float(w.value), float(h.value))
        return Vec2(float(self._headless_size[0]), float(self._headless_size[1]))

    def set_size(self, width: int, height: int) -> None:
        if self._app is not None:
            self._lib.cui_app_set_size(self._app, int(width), int(height))
        else:
            self._headless_size = [max(1, int(width)), max(1, int(height))]
            self.ui.set_viewport(float(self._headless_size[0]), float(self._headless_size[1]), 1.0)
            self.wake()

    def set_title(self, title: str) -> None:
        self._title = title
        if self._app is not None:
            self._lib.cui_app_set_title(self._app, title.encode("utf-8"))

    # ---- Cross-thread wakeup & UI-thread callback dispatch ----

    def wake(self) -> None:
        """Thread-safe: wake an idle event-driven frame loop from any thread or asyncio task."""
        if self._app is not None:
            self._lib.cui_app_wake(self._app)
        else:
            self._headless_wake_ev.set()
        for cb in list(self._wake_callbacks):
            try:
                cb()
            except Exception:
                pass

    def call_soon_threadsafe(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Schedule ``fn(*args, **kwargs)`` to run on the UI thread before the next frame."""
        if args or kwargs:
            self._dispatch.append(lambda: fn(*args, **kwargs))
        else:
            self._dispatch.append(fn)
        self.wake()

    def _drain_dispatch(self) -> None:
        # Bounded drain per frame so a producer loop cannot starve rendering
        count = len(self._dispatch)
        for _ in range(count):
            try:
                cb = self._dispatch.popleft()
            except IndexError:
                break
            cb()

    def quit(self) -> None:
        """Request clean loop termination (thread-safe)."""
        if self._app is not None:
            self._lib.cui_app_quit(self._app)
        else:
            self._headless_running = False
            self._headless_wake_ev.set()
        self.wake()

    # ---- Frame Stepping & Main Loop ----

    def frame(self, *, wait: bool = True) -> bool:
        """Present previous frame, wait for events/animations (if ``wait=True``), and begin new frame.

        Activates ``self.ui`` as the current functional context for the loop body.
        """
        if self._ctx_token is not None:
            pop_current_ui(self._ctx_token)
            self._ctx_token = None

        if self._app is not None:
            if self._dispatch:
                self.ui.request_redraw()
            alive = bool(self._lib.cui_app_frame(self._app))
            # Previous frame's cui_end_frame has now completed inside cui_app_frame!
            self.ui._frame_keepalive.clear()
            self.ui._frame_canvas_cbs.clear()
            if not alive:
                return False
            self._drain_dispatch()
            self._ctx_token = push_current_ui(self.ui)
            return True

        # Headless software loop
        if self._headless_in_frame:
            dd = self.ui.end_frame()
            self._headless_in_frame = False
            self._frame_counter += 1
            if self._headless_sw is not None and dd.width_px > 0 and dd.height_px > 0:
                px = self._headless_sw.render(dd)
                if self._screenshot_path and self._frame_counter >= self._screenshot_frames:
                    write_png(self._screenshot_path, px, dd.width_px, dd.height_px)
                    self._headless_running = False
            if self._env_max_frames is not None and self._frame_counter >= self._env_max_frames:
                self._headless_running = False

        if not self._headless_running:
            return False

        if wait and not self._continuous and not self.ui.needs_redraw and not self._dispatch and self._frame_counter > 0:
            wakeup = self.ui.next_wakeup
            timeout = min(wakeup, 60.0) if wakeup > 0 else 0.05
            self._headless_wake_ev.wait(timeout=max(0.0, timeout))
        self._headless_wake_ev.clear()

        if not self._headless_running:
            return False

        self._drain_dispatch()
        now = time.monotonic()
        dt = max(1.0 / 240.0, now - self._headless_last_t)
        self._headless_last_t = now
        self.ui.set_viewport(float(self._headless_size[0]), float(self._headless_size[1]), 1.0)
        self.ui.begin_frame(dt)
        self._headless_in_frame = True
        self._ctx_token = push_current_ui(self.ui)
        return True

    def run(self, draw_fn: Callable[..., Any], *, max_frames: Optional[int] = None) -> int:
        """Run ``draw_fn(ui)`` (or zero-arg ``draw_fn()``) until window close or ``max_frames``."""
        import inspect
        try:
            sig = inspect.signature(draw_fn)
            takes_ui = len(sig.parameters) >= 1
        except (ValueError, TypeError):
            takes_ui = True

        frames = 0
        try:
            while self.frame():
                if takes_ui:
                    draw_fn(self.ui)
                else:
                    draw_fn()
                frames += 1
                if max_frames is not None and frames >= max_frames:
                    self.quit()
        finally:
            if self._ctx_token is not None:
                pop_current_ui(self._ctx_token)
                self._ctx_token = None
        return 0

    async def run_async(
        self, draw_fn: Callable[..., Any], *, max_frames: Optional[int] = None
    ) -> int:
        """Run this ``App`` cooperatively inside the active ``asyncio`` event loop."""
        from .aio import run_app_async
        return await run_app_async(self, draw_fn, max_frames=max_frames)

    # ---- Screenshots & Native File Dialogs ----

    def screenshot_rgba(self) -> Tuple[bytes, int, int]:
        """Capture current UI into ``(rgba_bytes, width_px, height_px)``."""
        if self._app is not None:
            if self._headless_in_frame:
                pass
            dd = self.ui.draw_data()
            w, h = dd.size_px
            if w <= 0 or h <= 0:
                v = self.size
                w, h = max(1, int(v.x)), max(1, int(v.y))
            buf = ctypes.create_string_buffer(w * h * 4)
            ok = bool(self._lib.cui_app_screenshot(self._app, buf, w, h))
            if not ok:
                raise RuntimeError("cui_app_screenshot failed")
            return buf.raw, w, h

        # Headless mode: finish open frame if needed
        if self._headless_in_frame:
            dd = self.ui.end_frame()
            self._headless_in_frame = False
        else:
            dd = self.ui.draw_data()
        assert self._headless_sw is not None
        px = self._headless_sw.render(dd)
        return px, dd.width_px, dd.height_px

    def save_screenshot(self, path: Union[str, Path]) -> bool:
        rgba, w, h = self.screenshot_rgba()
        return write_png(path, rgba, w, h)

    def file_dialog(
        self,
        kind: FileDialogKind = FileDialogKind.OPEN,
        *,
        title: Optional[str] = None,
        filter_name: Optional[str] = None,
        filter_ext: Optional[str] = None,
        default_name: Optional[str] = None,
    ) -> Optional[str]:
        """Open a native OS file/save/folder picker dialog; returns UTF-8 path or ``None``."""
        if self._app is None:
            return None
        keep: list[Any] = []
        opts = CuiFileDialogOpts()
        opts.kind = int(kind)
        opts.title = encode_opt(title, keep)
        opts.filter_name = encode_opt(filter_name, keep)
        opts.filter = encode_opt(filter_ext, keep)
        opts.default_name = encode_opt(default_name, keep)
        out = ctypes.create_string_buffer(4096)
        ok = bool(self._lib.cui_app_file_dialog(self._app, ctypes.byref(opts), out, len(out)))
        return out.value.decode("utf-8", errors="replace") if ok else None

    def open_file_dialog(
        self, *, title: str = "Open File", filter_name: Optional[str] = None, filter_ext: Optional[str] = None
    ) -> Optional[str]:
        return self.file_dialog(FileDialogKind.OPEN, title=title, filter_name=filter_name, filter_ext=filter_ext)

    def save_file_dialog(
        self, *, title: str = "Save File", default_name: Optional[str] = None,
        filter_name: Optional[str] = None, filter_ext: Optional[str] = None
    ) -> Optional[str]:
        return self.file_dialog(
            FileDialogKind.SAVE, title=title, default_name=default_name,
            filter_name=filter_name, filter_ext=filter_ext
        )

    def select_folder_dialog(self, *, title: str = "Select Folder") -> Optional[str]:
        return self.file_dialog(FileDialogKind.FOLDER, title=title)

    # ---- Cleanup ----

    def close(self) -> None:
        if self._ctx_token is not None:
            try:
                pop_current_ui(self._ctx_token)
            except ValueError:
                pass
            self._ctx_token = None
        if self._app is not None:
            self._lib.cui_app_destroy(self._app)
            self._app = None
            self.ui._ctx = 0
            self.ui._frame_keepalive.clear()
            self.ui._frame_canvas_cbs.clear()
        elif self._headless_sw is not None:
            if self._headless_in_frame:
                try:
                    self.ui.end_frame()
                except Exception:
                    pass
                self._headless_in_frame = False
            self.ui.close()
            self._headless_sw.close()
            self._headless_sw = None
            self._headless_running = False

    def __enter__(self) -> App:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
