"""Core ``UI`` (``Context``) class combining full manual control with all ~150 components."""

from __future__ import annotations

import ctypes
from ctypes import c_char_p, c_float, c_void_p
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence, Tuple, Union

from ._cdefs import (
    CanvasTrampFn,
    PlatGetClipFn,
    PlatSetClipFn,
    PlatSetCursorFn,
    PlatSetImeFn,
    encode_str_array,
)
from ._context_var import pop_current_ui, push_current_ui
from ._lib import get_cdll
from .render import CustomRenderer, DrawData, GLRenderer, SoftwareRenderer
from .theme import ThemeProxy
from .types import (
    Accent,
    Cursor,
    InputFlags,
    Key,
    Mod,
    MouseButton,
    PixelFormat,
    Rect,
    ThemeMode,
    Vec2,
)
from .widgets.actions import ActionsMixin
from .widgets.ai import AIMixin
from .widgets.charts import ChartsMixin
from .widgets.chrome import ChromeMixin
from .widgets.data import DataMixin
from .widgets.feedback import FeedbackMixin
from .widgets.inputs import InputsMixin
from .widgets.layout import LayoutMixin
from .widgets.media import MediaMixin
from .widgets.motion import MotionMixin
from .widgets.navigation import NavigationMixin
from .widgets.nodes_canvas import NodesCanvasMixin
from .widgets.overlays import OverlaysMixin
from .widgets.pickers import PickersMixin
from .widgets.planning import PlanningMixin
from .widgets.selection import SelectionMixin
from .widgets.social import SocialMixin
from .widgets.text import TextMixin
from .widgets.tools import ToolsMixin


class _FrameScope:
    __slots__ = ("_ui", "_dt", "_token")

    def __init__(self, ui: UI, dt: float) -> None:
        self._ui = ui
        self._dt = dt
        self._token = None

    def __enter__(self) -> UI:
        self._ui.begin_frame(self._dt)
        self._token = push_current_ui(self._ui)
        return self._ui

    def __exit__(self, exc_type, *exc) -> None:
        if self._token is not None:
            pop_current_ui(self._token)
            self._token = None
        if exc_type is None:
            self._ui.end_frame()


class UI(
    LayoutMixin,
    TextMixin,
    ActionsMixin,
    SelectionMixin,
    InputsMixin,
    PickersMixin,
    NavigationMixin,
    OverlaysMixin,
    FeedbackMixin,
    DataMixin,
    ChartsMixin,
    PlanningMixin,
    AIMixin,
    SocialMixin,
    MediaMixin,
    MotionMixin,
    ChromeMixin,
    ToolsMixin,
    NodesCanvasMixin,
):
    """Immediate-mode UI context wrapping ``cui_ctx``.

    Can be created standalone (headless rendering, custom GLFW/SDL/Pygame/Vulkan loops)
    or obtained automatically from ``App.ui``.
    """

    def __init__(
        self,
        *,
        width: float = 800.0,
        height: float = 600.0,
        scale: float = 1.0,
        theme: ThemeMode = ThemeMode.LIGHT,
        accent: Accent = Accent.BLUE,
        reduced_motion: bool = False,
        no_default_fonts: bool = False,
        font_scale: float = 1.0,
        renderer: Optional[Union[SoftwareRenderer, GLRenderer, CustomRenderer]] = None,
        _adopt_handle: Optional[int] = None,
        _owns_ctx: bool = True,
    ) -> None:
        self._lib = get_cdll()
        self._owns_ctx = bool(_owns_ctx)
        self._renderer_ref: Any = None
        self._plat_holder: Optional[int] = None
        self._plat_cbs: Tuple[Any, ...] = ()
        self._clip_buf: Optional[bytes] = None

        self._frame_keepalive: List[Any] = []
        self._frame_canvas_cbs: List[Callable[[UI, Rect], None]] = []
        self._canvas_error: Optional[BaseException] = None

        # Per-call transition flags updated by widgets
        self._last_changed: bool = False
        self._last_submitted: bool = False
        self._last_focused: bool = False
        self._last_blurred: bool = False

        def _canvas_tramp(_ui_ptr: int, x: float, y: float, w: float, h: float, slot: int) -> None:
            if self._canvas_error is None and 0 <= slot < len(self._frame_canvas_cbs):
                try:
                    self._frame_canvas_cbs[slot](self, Rect(x, y, w, h))
                except BaseException as exc:
                    self._canvas_error = exc

        self._canvas_trampoline = CanvasTrampFn(_canvas_tramp)

        if _adopt_handle is not None:
            self._ctx = int(_adopt_handle)
        else:
            sw_h = renderer.handle if isinstance(renderer, SoftwareRenderer) else None
            gl_h = renderer.handle if isinstance(renderer, GLRenderer) else None
            self._ctx = int(self._lib.nexa_ctx_create(
                int(theme), int(accent), bool(no_default_fonts), sw_h, gl_h
            ))
            if not self._ctx:
                raise MemoryError("cui_create failed")
            if reduced_motion:
                self._lib.cui_set_reduced_motion(self._ctx, True)
            if isinstance(renderer, CustomRenderer):
                self.set_renderer(renderer)
            else:
                self._renderer_ref = renderer
            if font_scale != 1.0:
                self.theme.font_scale = float(font_scale)
            if width > 0 and height > 0:
                self.set_viewport(width, height, scale)

    # ---- Transition flag inspection ----

    def _record_change(self, changed: bool) -> None:
        self._last_changed = bool(changed)
        self._last_submitted = False
        self._last_focused = False
        self._last_blurred = False

    def _record_input_flags(self, flags: int) -> None:
        self._last_changed = bool(flags & InputFlags.CHANGED)
        self._last_submitted = bool(flags & InputFlags.SUBMITTED)
        self._last_focused = bool(flags & InputFlags.FOCUSED)
        self._last_blurred = bool(flags & InputFlags.BLURRED)

    @property
    def changed(self) -> bool:
        """True if the most recently called value-returning widget modified its value."""
        return self._last_changed

    @property
    def submitted(self) -> bool:
        """True if the most recently called input/OTP/composer widget was submitted (e.g. Enter)."""
        return self._last_submitted

    @property
    def focused(self) -> bool:
        """True on the frame the most recently called input widget gained focus."""
        return self._last_focused

    @property
    def blurred(self) -> bool:
        """True on the frame the most recently called input widget lost focus."""
        return self._last_blurred

    # ---- Raw Handle & Lifecycle ----

    @property
    def raw_handle(self) -> int:
        return int(self._ctx or 0)

    def close(self) -> None:
        if self._ctx and self._owns_ctx:
            if self._plat_holder:
                self._lib.nexa_free_platform(self._ctx, self._plat_holder)
                self._plat_holder = None
            self._lib.cui_destroy(self._ctx)
        self._ctx = 0
        self._frame_keepalive.clear()
        self._frame_canvas_cbs.clear()

    def __enter__(self) -> UI:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    # ---- Renderer & Platform Wiring ----

    def set_renderer(
        self, renderer: Optional[Union[SoftwareRenderer, GLRenderer, CustomRenderer]]
    ) -> None:
        self._renderer_ref = renderer
        if renderer is None:
            self._lib.nexa_ctx_set_sw_renderer(self._ctx, None)
        elif isinstance(renderer, SoftwareRenderer):
            self._lib.nexa_ctx_set_sw_renderer(self._ctx, renderer.handle)
        elif isinstance(renderer, GLRenderer):
            self._lib.nexa_ctx_set_gl_renderer(self._ctx, renderer.handle)
        elif isinstance(renderer, CustomRenderer):
            self._lib.nexa_ctx_set_custom_renderer(
                self._ctx, None, renderer._c_create, renderer._c_update, renderer._c_destroy
            )
        else:
            raise TypeError(f"Unsupported renderer: {type(renderer)!r}")

    def set_platform(
        self,
        *,
        set_clipboard: Optional[Callable[[str], None]] = None,
        get_clipboard: Optional[Callable[[], str]] = None,
        set_cursor: Optional[Callable[[Cursor], None]] = None,
        set_ime_rect: Optional[Callable[[Rect], None]] = None,
    ) -> None:
        """Attach custom OS clipboard, mouse cursor, and IME callbacks."""
        if self._plat_holder:
            self._lib.nexa_free_platform(self._ctx, self._plat_holder)
            self._plat_holder = None

        c_set_clip = ctypes.cast(None, PlatSetClipFn)
        c_get_clip = ctypes.cast(None, PlatGetClipFn)
        c_set_cur = ctypes.cast(None, PlatSetCursorFn)
        c_set_ime = ctypes.cast(None, PlatSetImeFn)

        if set_clipboard is not None:
            def _sc(_u, s: bytes) -> None:
                set_clipboard(s.decode("utf-8", errors="replace") if s else "")
            c_set_clip = PlatSetClipFn(_sc)

        if get_clipboard is not None:
            def _gc(_u) -> Optional[bytes]:
                txt = get_clipboard() or ""
                self._clip_buf = txt.encode("utf-8")
                return self._clip_buf
            c_get_clip = PlatGetClipFn(_gc)

        if set_cursor is not None:
            def _cur(_u, cur: int) -> None:
                set_cursor(Cursor(cur))
            c_set_cur = PlatSetCursorFn(_cur)

        if set_ime_rect is not None:
            def _ime(_u, x: float, y: float, w: float, h: float) -> None:
                set_ime_rect(Rect(x, y, w, h))
            c_set_ime = PlatSetImeFn(_ime)

        self._plat_cbs = (c_set_clip, c_get_clip, c_set_cur, c_set_ime)
        self._plat_holder = self._lib.nexa_set_platform(
            self._ctx, None, c_set_clip, c_get_clip, c_set_cur, c_set_ime
        )

    # ---- Frame Lifecycle & Viewport ----

    def set_viewport(self, width: float, height: float, scale: float = 1.0) -> None:
        self._lib.cui_set_viewport(self._ctx, float(width), float(height), float(scale))

    def begin_frame(self, dt: float = 1.0 / 60.0) -> None:
        self._frame_keepalive.clear()
        self._frame_canvas_cbs.clear()
        self._lib.cui_begin_frame(self._ctx, float(dt))

    def end_frame(self) -> DrawData:
        self._canvas_error = None
        self._lib.cui_end_frame(self._ctx)
        # Layout & deferred paint callbacks have now run; safe to release temporary frame buffers!
        self._frame_keepalive.clear()
        self._frame_canvas_cbs.clear()
        err = self._canvas_error
        self._canvas_error = None
        if err is not None:
            raise err
        return self.draw_data()

    def frame(self, dt: float = 1.0 / 60.0) -> _FrameScope:
        """Context manager running ``begin_frame(dt)``, activating functional API, and calling ``end_frame()``."""
        return _FrameScope(self, dt)

    def draw_data(self) -> DrawData:
        ptr = self._lib.cui_get_draw_data(self._ctx)
        return DrawData(ptr)

    def render_rgba(
        self,
        renderer: Optional[SoftwareRenderer] = None,
        *,
        pixel_format: PixelFormat = PixelFormat.RGBA,
    ) -> bytes:
        """Rasterize the latest ``end_frame()`` draw list to RGBA/BGRA bytes."""
        sw = renderer if renderer is not None else (
            self._renderer_ref if isinstance(self._renderer_ref, SoftwareRenderer) else None
        )
        if sw is None:
            raise RuntimeError("Pass a SoftwareRenderer or initialize UI(renderer=SoftwareRenderer())")
        return sw.render(self.draw_data(), pixel_format=pixel_format)

    def render_to_png(
        self, path: Union[str, Path], renderer: Optional[SoftwareRenderer] = None
    ) -> bool:
        sw = renderer if renderer is not None else (
            self._renderer_ref if isinstance(self._renderer_ref, SoftwareRenderer) else None
        )
        if sw is None:
            raise RuntimeError("Pass a SoftwareRenderer or initialize UI(renderer=SoftwareRenderer())")
        return sw.render_to_png(self.draw_data(), path)

    @property
    def needs_redraw(self) -> bool:
        return bool(self._lib.cui_needs_redraw(self._ctx))

    @property
    def next_wakeup(self) -> float:
        return float(self._lib.cui_next_wakeup(self._ctx))

    def request_redraw(self) -> None:
        self._lib.cui_request_redraw(self._ctx)

    @property
    def viewport_size(self) -> Vec2:
        w, h = c_float(0.0), c_float(0.0)
        self._lib.nexa_viewport_size(self._ctx, ctypes.byref(w), ctypes.byref(h))
        return Vec2(float(w.value), float(h.value))

    @property
    def scale(self) -> float:
        return float(self._lib.cui_dpi_scale(self._ctx))

    @property
    def dt(self) -> float:
        return float(self._lib.cui_delta_time(self._ctx))

    @property
    def time(self) -> float:
        return float(self._lib.cui_time(self._ctx))

    @property
    def frame_count(self) -> int:
        return int(self._lib.cui_frame_count(self._ctx))

    # ---- Theme & Appearance ----

    @property
    def theme(self) -> ThemeProxy:
        return ThemeProxy(self._lib.cui_theme_get(self._ctx))

    @property
    def theme_mode(self) -> ThemeMode:
        return ThemeMode(int(self._lib.cui_get_theme_mode(self._ctx)))

    @theme_mode.setter
    def theme_mode(self, mode: ThemeMode) -> None:
        self.set_theme(mode)

    def set_theme(self, mode: ThemeMode) -> None:
        self._lib.cui_set_theme(self._ctx, int(mode))

    @property
    def accent(self) -> Accent:
        return Accent(int(self._lib.cui_get_accent(self._ctx)))

    @accent.setter
    def accent(self, accent: Accent) -> None:
        self.set_accent(accent)

    def set_accent(self, accent: Accent) -> None:
        self._lib.cui_set_accent(self._ctx, int(accent))

    def set_reduced_motion(self, reduced: bool) -> None:
        self._lib.cui_set_reduced_motion(self._ctx, bool(reduced))

    @property
    def font_scale(self) -> float:
        return self.theme.font_scale

    @font_scale.setter
    def font_scale(self, scale: float) -> None:
        self.theme.font_scale = float(scale)

    def set_font_scale(self, scale: float) -> None:
        self.theme.font_scale = float(scale)

    # ---- Manual Event Injection (Full Control) ----

    def input_mouse_move(self, x: float, y: float) -> None:
        self._lib.cui_input_mouse_move(self._ctx, float(x), float(y))

    def input_mouse_leave(self) -> None:
        self._lib.cui_input_mouse_leave(self._ctx)

    def input_mouse_button(self, button: MouseButton, down: bool) -> None:
        self._lib.cui_input_mouse_button(self._ctx, int(button), bool(down))

    def input_click(self, x: float, y: float, button: MouseButton = MouseButton.LEFT) -> None:
        """Convenience helper for tests/automation: move + press on next frame."""
        self.input_mouse_move(x, y)
        self.input_mouse_button(button, True)

    def input_scroll(self, dx: float, dy: float) -> None:
        self._lib.cui_input_scroll(self._ctx, float(dx), float(dy))

    def input_key(self, key: Key, down: bool, mods: Union[Mod, int] = Mod.NONE) -> None:
        self._lib.cui_input_key(self._ctx, int(key), bool(down), int(mods))

    def input_text(self, text: str) -> None:
        self._lib.cui_input_text(self._ctx, text.encode("utf-8"))

    def input_char(self, codepoint: Union[int, str]) -> None:
        s = codepoint if isinstance(codepoint, str) else chr(int(codepoint))
        self.input_text(s)

    def input_focus(self, window_focused: bool) -> None:
        self._lib.cui_input_focus(self._ctx, bool(window_focused))

    def input_file_hover(self, hovering: bool, x: float, y: float) -> None:
        self._lib.cui_input_file_hover(self._ctx, bool(hovering), float(x), float(y))

    def input_file_drop(self, paths: Sequence[str], x: float, y: float) -> None:
        keep: List[Any] = []
        arr, n = encode_str_array(paths, keep)
        self._lib.cui_input_file_drop(self._ctx, arr, n, float(x), float(y))

    # ---- Input & File Drop Queries ----

    @property
    def cursor(self) -> Cursor:
        return Cursor(int(self._lib.cui_get_cursor(self._ctx)))

    @property
    def dropped_files(self) -> List[str]:
        n = int(self._lib.cui_dropped_file_count(self._ctx))
        out: List[str] = []
        for i in range(n):
            p = self._lib.cui_dropped_file(self._ctx, i)
            if p:
                out.append(p.decode("utf-8", errors="replace"))
        return out

    @property
    def file_drag_active(self) -> bool:
        return bool(self._lib.cui_file_drag_active(self._ctx))

    @property
    def mouse_pos(self) -> Vec2:
        x, y = c_float(0.0), c_float(0.0)
        self._lib.nexa_mouse_pos(self._ctx, ctypes.byref(x), ctypes.byref(y))
        return Vec2(float(x.value), float(y.value))

    def mouse_down(self, button: MouseButton = MouseButton.LEFT) -> bool:
        return bool(self._lib.cui_mouse_down(self._ctx, int(button)))

    def mouse_clicked(self, button: MouseButton = MouseButton.LEFT) -> bool:
        return bool(self._lib.cui_mouse_clicked(self._ctx, int(button)))

    mouse_pressed = mouse_clicked

    def key_down(self, key: Key) -> bool:
        return bool(self._lib.cui_key_down(self._ctx, int(key)))

    def key_pressed(self, key: Key) -> bool:
        return bool(self._lib.cui_key_pressed(self._ctx, int(key)))

    @property
    def modifiers(self) -> Mod:
        return Mod(int(self._lib.cui_key_mods(self._ctx)))

    def shortcut(self, mods: Union[Mod, int], key: Key) -> bool:
        return bool(self._lib.cui_shortcut(self._ctx, int(mods), int(key)))

    @property
    def wants_keyboard(self) -> bool:
        return bool(self._lib.cui_wants_keyboard(self._ctx))

    @property
    def wants_mouse(self) -> bool:
        return bool(self._lib.cui_wants_mouse(self._ctx))


Context = UI
