"""Value-returning text, numeric, scrub, money, OTP, tag, shortcut, signature & dropzone inputs."""

from __future__ import annotations

import ctypes
from ctypes import POINTER, c_double, c_float, c_int
from typing import List, Optional, Sequence, Tuple, Union, overload

from .._cdefs import (
    CuiDropzoneOpts,
    CuiInlineEditOpts,
    CuiInputOpts,
    CuiKeyCombo,
    CuiMoneyOpts,
    CuiNumberOpts,
    CuiScrubOpts,
    CuiShortcutRecorderOpts,
    CuiSignatureOpts,
    CuiTagOpts,
    CuiVec2,
    encode_opt,
    encode_str,
    make_text_buffer,
    to_c_color,
    to_c_size,
)
from ..types import (
    ColorLike,
    ControlSize,
    FontRole,
    InputFlags,
    Key,
    KeyCombo,
    Mod,
    Size,
    SizeKind,
    SizeLike,
    Vec2,
)


def _build_input_opts(
    keep: list,
    *,
    label: Optional[str] = None,
    placeholder: Optional[str] = None,
    icon: Optional[str] = None,
    hint: Optional[str] = None,
    error: Optional[str] = None,
    password: bool = False,
    disabled: bool = False,
    clearable: bool = False,
    autofocus: bool = False,
    read_only: bool = False,
    size: ControlSize = ControlSize.MD,
    width: SizeLike = None,
    height: float = 0.0,
    prefix: Optional[str] = None,
    suffix: Optional[str] = None,
    bg: ColorLike = None,
    color: ColorLike = None,
    text_color: ColorLike = None,
    placeholder_color: ColorLike = None,
    border_color: ColorLike = None,
    focus_color: ColorLike = None,
) -> CuiInputOpts:
    opts = CuiInputOpts()
    opts.label = encode_opt(label, keep)
    opts.placeholder = encode_opt(placeholder, keep)
    opts.icon = encode_opt(icon, keep)
    opts.hint = encode_opt(hint, keep)
    opts.error = encode_opt(error, keep)
    opts.password = bool(password)
    opts.disabled = bool(disabled)
    opts.clearable = bool(clearable)
    opts.autofocus = bool(autofocus)
    opts.read_only = bool(read_only)
    opts.size = int(size)
    opts.width = to_c_size(width)
    if isinstance(height, Size):
        opts.height = -1.0 if height.kind in (SizeKind.GROW, SizeKind.PERCENT) else float(height.value)
    else:
        opts.height = float(height)
    opts.prefix = encode_opt(prefix, keep)
    opts.suffix = encode_opt(suffix, keep)
    # convert lazily: the default path must not pay for ctypes field writes
    if bg is not None:
        opts.bg = to_c_color(bg)
    if text_color is not None or color is not None:
        opts.text_color = to_c_color(text_color if text_color is not None else color)
    if placeholder_color is not None:
        opts.placeholder_color = to_c_color(placeholder_color)
    if border_color is not None:
        opts.border_color = to_c_color(border_color)
    if focus_color is not None:
        opts.focus_color = to_c_color(focus_color)
    keep.append(opts)
    return opts


class InputsMixin:
    __slots__ = ()

    def input(self, id: str, value: str, *, max_bytes: int = 512, **kwargs) -> str:
        """Single-line text input returning the updated string.

        Inspect ``ui.changed``, ``ui.submitted`` (Enter), ``ui.focused``, or ``ui.blurred``
        after calling if you need transition flags.
        """
        keep = self._frame_keepalive
        buf, cap = make_text_buffer(value, max_bytes)
        opts = _build_input_opts(keep, **kwargs)
        flags = int(self._lib.cui_input_ex(self._ctx, encode_str(id, keep), buf, cap, ctypes.byref(opts)))
        self._record_input_flags(flags)
        if flags & InputFlags.CHANGED:
            return buf.value.decode("utf-8", errors="replace")
        return value

    def textarea(self, id: str, value: str, *, max_bytes: int = 4096, **kwargs) -> str:
        """Multi-line word-wrapping text editor returning the updated string."""
        keep = self._frame_keepalive
        buf, cap = make_text_buffer(value, max_bytes)
        opts = _build_input_opts(keep, **kwargs)
        flags = int(self._lib.cui_textarea_ex(self._ctx, encode_str(id, keep), buf, cap, ctypes.byref(opts)))
        self._record_input_flags(flags)
        if flags & InputFlags.CHANGED:
            return buf.value.decode("utf-8", errors="replace")
        return value

    def search(self, id: str, value: str, *, max_bytes: int = 256, **kwargs) -> str:
        """Search box with leading lens icon & clear button, returning updated query."""
        keep = self._frame_keepalive
        buf, cap = make_text_buffer(value, max_bytes)
        opts = _build_input_opts(keep, **kwargs)
        flags = int(self._lib.cui_search_ex(self._ctx, encode_str(id, keep), buf, cap, ctypes.byref(opts)))
        self._record_input_flags(flags)
        if flags & InputFlags.CHANGED:
            return buf.value.decode("utf-8", errors="replace")
        return value

    def number(
        self,
        id: str,
        value: float,
        min_value: float = -1e12,
        max_value: float = 1e12,
        *,
        label: Optional[str] = None,
        step: float = 1.0,
        decimals: int = 0,
        disabled: bool = False,
        width: SizeLike = None,
        suffix: Optional[str] = None,
    ) -> float:
        keep = self._frame_keepalive
        c_val = c_double(float(value))
        opts = CuiNumberOpts()
        opts.label = encode_opt(label, keep)
        opts.step = float(step)
        opts.decimals = int(decimals)
        opts.disabled = bool(disabled)
        opts.width = to_c_size(width)
        opts.suffix = encode_opt(suffix, keep)
        keep.append(opts)
        changed = bool(self._lib.cui_number_ex(
            self._ctx, encode_str(id, keep), ctypes.byref(c_val),
            float(min_value), float(max_value), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return float(c_val.value)

    def scrub(
        self,
        label: str,
        value: float,
        min_value: float,
        max_value: float,
        *,
        step: float = 0.0,
        format: Optional[str] = None,
        suffix: Optional[str] = None,
        icon: Optional[str] = None,
        width: SizeLike = None,
    ) -> float:
        keep = self._frame_keepalive
        c_val = c_float(float(value))
        opts = CuiScrubOpts()
        opts.step = float(step)
        opts.format = encode_opt(format, keep)
        opts.suffix = encode_opt(suffix, keep)
        opts.icon = encode_opt(icon, keep)
        opts.width = to_c_size(width)
        keep.append(opts)
        changed = bool(self._lib.cui_scrub_ex(
            self._ctx, encode_str(label, keep), ctypes.byref(c_val),
            float(min_value), float(max_value), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return float(c_val.value)

    def money_input(
        self,
        id: str,
        value: float,
        *,
        label: Optional[str] = None,
        symbol: Optional[str] = "$",
        code: Optional[str] = None,
        decimals: int = 2,
        width: SizeLike = None,
        hint: Optional[str] = None,
    ) -> float:
        keep = self._frame_keepalive
        c_val = c_double(float(value))
        opts = CuiMoneyOpts()
        opts.label = encode_opt(label, keep)
        opts.symbol = encode_opt(symbol, keep)
        opts.code = encode_opt(code, keep)
        opts.decimals = int(decimals)
        opts.width = to_c_size(width)
        opts.hint = encode_opt(hint, keep)
        keep.append(opts)
        changed = bool(self._lib.cui_money_input_ex(
            self._ctx, encode_str(id, keep), ctypes.byref(c_val), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return float(c_val.value)

    def inline_edit(
        self,
        id: str,
        value: str,
        *,
        max_bytes: int = 256,
        font: Union[FontRole, int] = FontRole.BODY,
        size: float = 0.0,
        placeholder: Optional[str] = None,
        width: SizeLike = None,
    ) -> str:
        keep = self._frame_keepalive
        buf, cap = make_text_buffer(value, max_bytes)
        opts = CuiInlineEditOpts()
        opts.font = int(font)
        opts.size = float(size)
        opts.placeholder = encode_opt(placeholder, keep)
        opts.width = to_c_size(width)
        keep.append(opts)
        flags = int(self._lib.cui_inline_edit_ex(self._ctx, encode_str(id, keep), buf, cap, ctypes.byref(opts)))
        self._record_input_flags(flags)
        if flags & InputFlags.CHANGED:
            return buf.value.decode("utf-8", errors="replace")
        return value

    @overload
    def tag_input(self, id: str, tags: str, **kwargs) -> str: ...
    @overload
    def tag_input(self, id: str, tags: Sequence[str], **kwargs) -> List[str]: ...

    def tag_input(
        self,
        id: str,
        tags: Union[str, Sequence[str]],
        *,
        label: Optional[str] = None,
        placeholder: Optional[str] = None,
        max_tags: int = 0,
        width: SizeLike = None,
        max_bytes: int = 1024,
    ) -> Union[str, List[str]]:
        """Tag chip input. Accepts either a comma-separated ``str`` or ``Sequence[str]`` and returns the same type."""
        keep = self._frame_keepalive
        is_str = isinstance(tags, str)
        csv = tags if is_str else ", ".join(tags)
        buf, cap = make_text_buffer(csv, max_bytes)
        opts = CuiTagOpts()
        opts.label = encode_opt(label, keep)
        opts.placeholder = encode_opt(placeholder, keep)
        opts.max_tags = int(max_tags)
        opts.width = to_c_size(width)
        keep.append(opts)
        changed = bool(self._lib.cui_tag_input_ex(self._ctx, encode_str(id, keep), buf, cap, ctypes.byref(opts)))
        self._record_change(changed)
        new_csv = buf.value.decode("utf-8", errors="replace") if changed else csv
        if is_str:
            return new_csv
        return [p.strip() for p in new_csv.split(",") if p.strip()]

    def otp_input(self, id: str, code: str, length: int = 6) -> Tuple[str, bool]:
        """One-time passcode box input; returns ``(code, just_completed)``."""
        keep = self._frame_keepalive
        if length < 1 or length > 12:
            raise ValueError("otp_input length must be in 1..12")
        raw = code.encode("ascii", errors="ignore")[:length]
        buf = ctypes.create_string_buffer(raw, length + 2)
        completed = bool(self._lib.cui_otp_input(self._ctx, encode_str(id, keep), buf, int(length)))
        new_code = buf.value.decode("ascii", errors="ignore")
        self._record_input_flags(
            (InputFlags.CHANGED if new_code != code else 0) | (InputFlags.SUBMITTED if completed else 0)
        )
        return new_code, completed

    def password_strength(self, password: str) -> int:
        return int(self._lib.cui_password_strength(self._ctx, encode_str(password, self._frame_keepalive)))

    def shortcut_recorder(
        self,
        id: str,
        combo: KeyCombo,
        *,
        placeholder: Optional[str] = None,
        width: SizeLike = None,
    ) -> KeyCombo:
        keep = self._frame_keepalive
        c_combo = CuiKeyCombo(int(combo.mods), int(combo.key))
        opts = CuiShortcutRecorderOpts()
        opts.placeholder = encode_opt(placeholder, keep)
        opts.width = to_c_size(width)
        keep.append(opts)
        changed = bool(self._lib.cui_shortcut_recorder_ex(
            self._ctx, encode_str(id, keep), ctypes.byref(c_combo), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return KeyCombo(Mod(c_combo.mods), Key(c_combo.key))

    def shortcut_label(self, combo: KeyCombo) -> str:
        raw = self._lib.nexa_shortcut_label(self._ctx, int(combo.mods), int(combo.key))
        return raw.decode("utf-8") if raw else ""

    def key_name(self, key: Key) -> str:
        raw = self._lib.cui_key_name(int(key))
        return raw.decode("utf-8") if raw else ""

    def signature_pad(
        self,
        id: str,
        *,
        width: SizeLike = None,
        height: float = 0.0,
        placeholder: Optional[str] = None,
        ink: ColorLike = None,
    ) -> bool:
        keep = self._frame_keepalive
        opts = CuiSignatureOpts()
        opts.width = to_c_size(width)
        opts.height = float(height)
        opts.placeholder = encode_opt(placeholder, keep)
        opts.ink = to_c_color(ink)
        keep.append(opts)
        changed = bool(self._lib.cui_signature_pad_ex(self._ctx, encode_str(id, keep), ctypes.byref(opts)))
        self._record_change(changed)
        return changed

    def signature_strokes(self, id: str) -> List[List[Vec2]]:
        """Read captured strokes from ``signature_pad`` as ``list[list[Vec2]]``."""
        pts_p = POINTER(CuiVec2)()
        ends_p = POINTER(c_int)()
        sc = c_int(0)
        total = int(self._lib.cui_signature_points(
            self._ctx, encode_str(id, self._frame_keepalive),
            ctypes.byref(pts_p), ctypes.byref(ends_p), ctypes.byref(sc)
        ))
        if total <= 0 or sc.value <= 0:
            return []
        strokes: List[List[Vec2]] = []
        start = 0
        for s in range(sc.value):
            end = int(ends_p[s])
            strokes.append([Vec2(float(pts_p[i].x), float(pts_p[i].y)) for i in range(start, end)])
            start = end
        return strokes

    def signature_clear(self, id: str) -> None:
        self._lib.cui_signature_clear(self._ctx, encode_str(id, self._frame_keepalive))

    def dropzone(
        self,
        id: str,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        accept: Optional[str] = None,
        height: float = 0.0,
        width: SizeLike = None,
        compact: bool = False,
    ) -> Tuple[List[str], bool]:
        """Dropzone for OS file drops; returns ``(dropped_paths, browse_clicked)``."""
        keep = self._frame_keepalive
        opts = CuiDropzoneOpts()
        opts.title = encode_opt(title, keep)
        opts.description = encode_opt(description, keep)
        opts.icon = encode_opt(icon, keep)
        opts.accept = encode_opt(accept, keep)
        opts.height = float(height)
        opts.width = to_c_size(width)
        opts.compact = bool(compact)
        keep.append(opts)
        rc = int(self._lib.cui_dropzone_ex(self._ctx, encode_str(id, keep), ctypes.byref(opts)))
        if rc == -1:
            self._record_change(True)
            return [], True
        if rc > 0:
            files: List[str] = []
            for i in range(rc):
                p = self._lib.cui_dropped_file(self._ctx, i)
                if p:
                    files.append(p.decode("utf-8", errors="replace"))
            self._record_change(True)
            return files, False
        self._record_change(False)
        return [], False

    @staticmethod
    def path_has_extension(path: str, accept: str) -> bool:
        from .._lib import get_cdll
        return bool(get_cdll().cui_path_has_extension(path.encode("utf-8"), accept.encode("utf-8")))
