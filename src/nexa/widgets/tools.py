"""Developer & editor tools: property inspector, typed property editors, and ring-buffer log console."""

from __future__ import annotations

import ctypes
import threading
import time
from ctypes import c_bool, c_char_p, c_double, c_float, c_int, c_uint32
from typing import Optional, Sequence, Tuple

from .._cdefs import (
    CuiInspectorOpts,
    CuiLogViewOpts,
    CuiPropOpts,
    encode_opt,
    encode_str,
    encode_str_array,
    make_text_buffer,
    to_c_size,
    to_packed_color,
)
from .._lib import get_cdll
from ..scopes import ConditionalScope
from ..types import Color, ColorLike, LogLevel, Size, SizeKind, SizeLike


class LogBuffer:
    """Zero-allocation C-backed ring buffer for ``ui.log_view(...)``.

    Thread-safe: ``append`` / ``info`` / ``warn`` / ``error`` can be called from
    any background thread or ``asyncio`` task!
    """

    __slots__ = ("_lib", "_handle", "_t0", "_lock")

    def __init__(self, max_lines: int = 4096, text_bytes: int = 256 * 1024) -> None:
        self._lib = get_cdll()
        self._handle = self._lib.nexa_log_create(max(16, int(max_lines)), max(1024, int(text_bytes)))
        if not self._handle:
            raise MemoryError("nexa_log_create failed")
        self._t0 = time.monotonic()
        self._lock = threading.Lock()

    def close(self) -> None:
        if self._handle:
            self._lib.nexa_log_destroy(self._handle)
            self._handle = None

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def append(self, level: LogLevel, message: str, timestamp: Optional[float] = None) -> None:
        raw = message.encode("utf-8", errors="replace")
        ts = float(timestamp) if timestamp is not None else (time.monotonic() - self._t0)
        with self._lock:
            if self._handle:
                self._lib.cui_log_append_text(self._handle, int(level), ts, raw, len(raw))

    def trace(self, message: str) -> None:
        self.append(LogLevel.TRACE, message)

    def debug(self, message: str) -> None:
        self.append(LogLevel.DEBUG, message)

    def info(self, message: str) -> None:
        self.append(LogLevel.INFO, message)

    def warn(self, message: str) -> None:
        self.append(LogLevel.WARN, message)

    def error(self, message: str) -> None:
        self.append(LogLevel.ERROR, message)

    def clear(self) -> None:
        with self._lock:
            if self._handle:
                self._lib.cui_log_clear(self._handle)

    def __len__(self) -> int:
        with self._lock:
            return int(self._lib.nexa_log_count(self._handle)) if self._handle else 0

    @property
    def total_appended(self) -> int:
        with self._lock:
            return int(self._lib.nexa_log_total(self._handle)) if self._handle else 0

    def get_line(self, index: int) -> Optional[Tuple[LogLevel, float, str]]:
        with self._lock:
            if not self._handle:
                return None
            t_out = c_double(0.0)
            lvl_out = c_int(0)
            txt_out = c_char_p()
            len_out = c_int(0)
            ok = bool(self._lib.nexa_log_line_at(
                self._handle, int(index), ctypes.byref(t_out),
                ctypes.byref(lvl_out), ctypes.byref(txt_out), ctypes.byref(len_out)
            ))
            if not ok:
                return None
            text = ctypes.string_at(txt_out, int(len_out.value)).decode("utf-8", errors="replace") if txt_out.value else ""
            return LogLevel(int(lvl_out.value)), float(t_out.value), text


def _build_prop_opts(
    keep: list,
    *,
    min: float = 0.0,
    max: float = 0.0,
    step: float = 0.0,
    format: Optional[str] = None,
    suffix: Optional[str] = None,
    placeholder: Optional[str] = None,
    tooltip: Optional[str] = None,
    disabled: bool = False,
    checkbox: bool = False,
) -> CuiPropOpts:
    opts = CuiPropOpts()
    opts.min = float(min)
    opts.max = float(max)
    opts.step = float(step)
    opts.format = encode_opt(format, keep)
    opts.suffix = encode_opt(suffix, keep)
    opts.placeholder = encode_opt(placeholder, keep)
    opts.tooltip = encode_opt(tooltip, keep)
    opts.disabled = bool(disabled)
    opts.checkbox = bool(checkbox)
    keep.append(opts)
    return opts


class ToolsMixin:
    __slots__ = ()

    def inspector(
        self,
        id: str,
        *,
        width: SizeLike = None,
        label_width: float = 0.0,
    ) -> ConditionalScope:
        keep = self._frame_keepalive
        opts = CuiInspectorOpts()
        opts.width = to_c_size(width)
        opts.label_width = float(label_width)
        keep.append(opts)
        vis = bool(self._lib.cui_inspector_begin_ex(self._ctx, encode_str(id, keep), ctypes.byref(opts)))
        return ConditionalScope(self._ctx, self._lib.cui_inspector_end, vis)

    def inspector_group(self, title: str, is_open: Optional[bool] = None) -> Tuple[bool, bool]:
        """Inspector section header; returns ``(visible, is_open)``."""
        keep = self._frame_keepalive
        if is_open is None:
            vis = bool(self._lib.cui_inspector_group(self._ctx, encode_str(title, keep), None))
            return vis, True
        c_open = c_bool(bool(is_open))
        vis = bool(self._lib.cui_inspector_group(self._ctx, encode_str(title, keep), ctypes.byref(c_open)))
        new_open = bool(c_open.value)
        self._record_change(new_open != is_open)
        return vis, new_open

    def prop_float(self, label: str, value: float, **kwargs) -> float:
        keep = self._frame_keepalive
        c_val = c_float(float(value))
        opts = _build_prop_opts(keep, **kwargs)
        changed = bool(self._lib.cui_prop_float_ex(
            self._ctx, encode_str(label, keep), ctypes.byref(c_val), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return float(c_val.value)

    def prop_int(self, label: str, value: int, **kwargs) -> int:
        keep = self._frame_keepalive
        c_val = c_int(int(value))
        opts = _build_prop_opts(keep, **kwargs)
        changed = bool(self._lib.cui_prop_int_ex(
            self._ctx, encode_str(label, keep), ctypes.byref(c_val), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return int(c_val.value)

    def prop_text(self, label: str, value: str, *, max_bytes: int = 256, **kwargs) -> str:
        keep = self._frame_keepalive
        buf, cap = make_text_buffer(value, max_bytes)
        opts = _build_prop_opts(keep, **kwargs)
        changed = bool(self._lib.cui_prop_text_ex(
            self._ctx, encode_str(label, keep), buf, cap, ctypes.byref(opts)
        ))
        self._record_change(changed)
        return buf.value.decode("utf-8", errors="replace") if changed else value

    def prop_bool(self, label: str, value: bool, **kwargs) -> bool:
        keep = self._frame_keepalive
        c_val = c_bool(bool(value))
        opts = _build_prop_opts(keep, **kwargs)
        changed = bool(self._lib.cui_prop_bool_ex(
            self._ctx, encode_str(label, keep), ctypes.byref(c_val), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return bool(c_val.value)

    def prop_enum(self, label: str, items: Sequence[str], index: int, **kwargs) -> int:
        keep = self._frame_keepalive
        arr, n = encode_str_array(items, keep)
        c_idx = c_int(int(index))
        opts = _build_prop_opts(keep, **kwargs)
        changed = bool(self._lib.cui_prop_enum_ex(
            self._ctx, encode_str(label, keep), arr, n, ctypes.byref(c_idx), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return int(c_idx.value)

    def prop_color(self, label: str, value: ColorLike, **kwargs) -> Color:
        keep = self._frame_keepalive
        c_col = c_uint32(to_packed_color(value))
        opts = _build_prop_opts(keep, **kwargs)
        changed = bool(self._lib.nexa_prop_color(
            self._ctx, encode_str(label, keep), ctypes.byref(c_col), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return Color._from_packed(int(c_col.value))

    def prop_vec(self, label: str, values: Sequence[float], **kwargs) -> Tuple[float, ...]:
        keep = self._frame_keepalive
        n = len(values)
        if n not in (2, 3, 4):
            raise ValueError(f"prop_vec requires 2, 3, or 4 components, got {n}")
        c_vec = (c_float * n)(*(float(v) for v in values))
        opts = _build_prop_opts(keep, **kwargs)
        changed = bool(self._lib.cui_prop_vec_ex(
            self._ctx, encode_str(label, keep), c_vec, n, ctypes.byref(opts)
        ))
        self._record_change(changed)
        return tuple(float(c_vec[i]) for i in range(n))

    def prop_vec2(self, label: str, xy: Tuple[float, float], **kwargs) -> Tuple[float, float]:
        r = self.prop_vec(label, xy, **kwargs)
        return (r[0], r[1])

    def prop_vec3(self, label: str, xyz: Tuple[float, float, float], **kwargs) -> Tuple[float, float, float]:
        r = self.prop_vec(label, xyz, **kwargs)
        return (r[0], r[1], r[2])

    def prop_vec4(
        self, label: str, xyzw: Tuple[float, float, float, float], **kwargs
    ) -> Tuple[float, float, float, float]:
        r = self.prop_vec(label, xyzw, **kwargs)
        return (r[0], r[1], r[2], r[3])

    def log_view(
        self,
        id: str,
        buffer: LogBuffer,
        *,
        width: SizeLike = None,
        height: SizeLike = 320.0,
        timestamps: bool = False,
        no_toolbar: bool = False,
        size: float = 0.0,
    ) -> None:
        keep = self._frame_keepalive
        opts = CuiLogViewOpts()
        opts.width = to_c_size(width)
        if height is None:
            opts.height = 320.0
        elif isinstance(height, Size):
            opts.height = -1.0 if height.kind in (SizeKind.GROW, SizeKind.PERCENT) else float(height.value)
        else:
            opts.height = float(height)
        opts.timestamps = bool(timestamps)
        opts.no_toolbar = bool(no_toolbar)
        opts.size = float(size)
        keep.extend((buffer, opts))
        with buffer._lock:
            if buffer._handle:
                self._lib.cui_log_view_ex(
                    self._ctx, encode_str(id, keep), buffer._handle, ctypes.byref(opts)
                )
