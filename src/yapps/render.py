"""Renderers (Software, OpenGL, Custom) and zero-copy DrawData inspection."""

from __future__ import annotations

import ctypes
from pathlib import Path
from typing import Callable, Optional, Sequence, Tuple, Union

from ._cdefs import (
    CuiDrawCmd,
    CuiDrawData,
    CuiVertex,
    GlLoaderFn,
    TexCreateFn,
    TexDestroyFn,
    TexUpdateFn,
)
from ._lib import get_cdll
from .types import BuildFeatures, Color, PixelFormat, Rect, ShadeMode, TextureFormat


def build_features() -> BuildFeatures:
    """Return bitmask of features compiled into ``libyapps_cui``."""
    return BuildFeatures(int(get_cdll().yapps_features()))


def native_version() -> str:
    v = get_cdll().yapps_version()
    return v.decode("utf-8") if v else "1.0.0"


def write_png(path: Union[str, Path], rgba: Union[bytes, bytearray, memoryview],
              width: int, height: int, stride: int = 0) -> bool:
    """Write an RGBA8 pixel buffer to a PNG file using CUI's built-in encoder."""
    if stride <= 0:
        stride = width * 4
    expected = stride * height
    mv = memoryview(rgba)
    if mv.nbytes < expected:
        raise ValueError(f"Buffer too small: got {mv.nbytes} bytes, need at least {expected}")
    p_bytes = str(path).encode("utf-8")
    if mv.readonly:
        buf = (ctypes.c_uint8 * mv.nbytes).from_buffer_copy(mv)
    else:
        buf = (ctypes.c_uint8 * mv.nbytes).from_buffer(mv)
    return bool(get_cdll().cui_write_png(p_bytes, buf, int(width), int(height), int(stride)))


# ---------------------------------------------------------------------------
# Zero-Copy DrawData Views (for custom Vulkan / Metal / WebGPU / DX12 engines)
# ---------------------------------------------------------------------------

class DrawCmdInfo:
    __slots__ = ("clip", "texture", "index_offset", "index_count")

    def __init__(self, clip: Rect, texture: int, index_offset: int, index_count: int) -> None:
        self.clip = clip
        self.texture = texture
        self.index_offset = index_offset
        self.index_count = index_count

    def __repr__(self) -> str:
        return (f"DrawCmdInfo(clip={self.clip!r}, texture={self.texture}, "
                f"index_offset={self.index_offset}, index_count={self.index_count})")


class VertexInfo:
    __slots__ = ("x", "y", "u", "v", "lx", "ly", "hw", "hh",
                 "r_tl", "r_tr", "r_br", "r_bl", "border", "mode", "color", "border_color")

    def __init__(self, cv: CuiVertex) -> None:
        self.x = cv.x
        self.y = cv.y
        self.u = cv.u
        self.v = cv.v
        self.lx = cv.lx
        self.ly = cv.ly
        self.hw = cv.hw
        self.hh = cv.hh
        self.r_tl = cv.r_tl
        self.r_tr = cv.r_tr
        self.r_br = cv.r_br
        self.r_bl = cv.r_bl
        self.border = cv.border
        self.mode = ShadeMode(int(round(cv.mode)))
        self.color = Color(cv.color.r, cv.color.g, cv.color.b, cv.color.a)
        self.border_color = Color(cv.border_color.r, cv.border_color.g, cv.border_color.b, cv.border_color.a)


class DrawData:
    """View over ``cui_draw_data`` valid from ``end_frame()`` until next ``begin_frame()``."""

    __slots__ = ("_ptr",)

    def __init__(self, ptr: ctypes.POINTER(CuiDrawData)) -> None:
        if not ptr:
            raise RuntimeError("Null cui_draw_data pointer")
        self._ptr = ptr

    @property
    def raw_ptr(self):
        return self._ptr

    @property
    def width_px(self) -> int:
        return int(self._ptr.contents.width_px)

    @property
    def height_px(self) -> int:
        return int(self._ptr.contents.height_px)

    @property
    def size_px(self) -> Tuple[int, int]:
        d = self._ptr.contents
        return int(d.width_px), int(d.height_px)

    @property
    def vertex_count(self) -> int:
        return int(self._ptr.contents.vertex_count)

    @property
    def index_count(self) -> int:
        return int(self._ptr.contents.index_count)

    @property
    def command_count(self) -> int:
        return int(self._ptr.contents.command_count)

    @property
    def clear_color(self) -> Color:
        c = self._ptr.contents.clear_color
        return Color(c.r, c.g, c.b, c.a)

    @property
    def font_atlas(self) -> int:
        return int(self._ptr.contents.font_atlas)

    def vertices_bytes(self) -> bytes:
        """Copy packed vertex buffer (64 bytes per vertex) for GPU upload."""
        d = self._ptr.contents
        if d.vertex_count <= 0 or not d.vertices:
            return b""
        return ctypes.string_at(d.vertices, d.vertex_count * ctypes.sizeof(CuiVertex))

    def indices_bytes(self) -> bytes:
        """Copy packed uint32 index buffer for GPU upload."""
        d = self._ptr.contents
        if d.index_count <= 0 or not d.indices:
            return b""
        return ctypes.string_at(d.indices, d.index_count * ctypes.sizeof(ctypes.c_uint32))

    def commands(self) -> Tuple[DrawCmdInfo, ...]:
        d = self._ptr.contents
        out = []
        for i in range(d.command_count):
            cmd: CuiDrawCmd = d.commands[i]
            out.append(DrawCmdInfo(
                Rect(cmd.clip.x, cmd.clip.y, cmd.clip.w, cmd.clip.h),
                int(cmd.texture),
                int(cmd.index_offset),
                int(cmd.index_count),
            ))
        return tuple(out)

    def vertex_at(self, index: int) -> VertexInfo:
        d = self._ptr.contents
        if index < 0 or index >= d.vertex_count:
            raise IndexError(index)
        return VertexInfo(d.vertices[index])


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------

class SoftwareRenderer:
    """Multi-threaded CPU rasterizer matching GPU output without needing OpenGL."""

    __slots__ = ("_lib", "_handle")

    def __init__(self, threads: int = 0) -> None:
        self._lib = get_cdll()
        self._handle = self._lib.cui_sw_create()
        if not self._handle:
            raise RuntimeError("SoftwareRenderer unavailable (compiled with YAPPS_WITH_SW=0?)")
        if threads > 0:
            self._lib.cui_sw_set_threads(self._handle, int(threads))

    @property
    def handle(self) -> int:
        return int(self._handle or 0)

    def set_threads(self, threads: int) -> None:
        if self._handle:
            self._lib.cui_sw_set_threads(self._handle, int(threads))

    def render(
        self,
        draw_data: DrawData,
        *,
        buffer: Optional[Union[bytearray, memoryview]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        stride: int = 0,
        pixel_format: PixelFormat = PixelFormat.RGBA,
    ) -> bytes:
        """Rasterize ``draw_data`` into ``buffer`` (or allocate a fresh ``bytes`` buffer)."""
        if not self._handle:
            raise RuntimeError("SoftwareRenderer is closed")
        w = int(width if width is not None else draw_data.width_px)
        h = int(height if height is not None else draw_data.height_px)
        if w <= 0 or h <= 0:
            return b""
        row_stride = int(stride if stride > 0 else w * 4)
        total = row_stride * h

        if buffer is not None:
            mv = memoryview(buffer)
            if mv.readonly:
                raise TypeError("Target pixel buffer must be writable (e.g. bytearray or writable memoryview)")
            if mv.nbytes < total:
                raise ValueError(f"Buffer too small ({mv.nbytes} < {total})")
            c_buf = (ctypes.c_uint8 * mv.nbytes).from_buffer(mv)
            self._lib.cui_sw_render(self._handle, draw_data.raw_ptr, c_buf, w, h, row_stride, int(pixel_format))
            return bytes(mv[:total])

        raw = ctypes.create_string_buffer(total)
        self._lib.cui_sw_render(self._handle, draw_data.raw_ptr, raw, w, h, row_stride, int(pixel_format))
        return raw.raw

    def render_to_png(self, draw_data: DrawData, path: Union[str, Path]) -> bool:
        w, h = draw_data.size_px
        if w <= 0 or h <= 0:
            return False
        pixels = self.render(draw_data, width=w, height=h, pixel_format=PixelFormat.RGBA)
        return write_png(path, pixels, w, h, w * 4)

    def close(self) -> None:
        if self._handle:
            self._lib.cui_sw_destroy(self._handle)
            self._handle = None

    def __enter__(self) -> SoftwareRenderer:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass


class GLRenderer:
    """OpenGL 3.3 Core / OpenGL ES 3.0 renderer for custom window loops."""

    __slots__ = ("_lib", "_handle", "_c_loader")

    def __init__(self, loader: Callable[[str], Optional[int]]) -> None:
        self._lib = get_cdll()

        def _tramp(name_bytes: bytes) -> int:
            name = name_bytes.decode("ascii", errors="ignore")
            addr = loader(name)
            if addr is None:
                return 0
            if isinstance(addr, ctypes.c_void_p):
                return int(addr.value or 0)
            return int(addr)

        self._c_loader = GlLoaderFn(_tramp)
        self._handle = self._lib.cui_gl_create(self._c_loader)
        if not self._handle:
            raise RuntimeError("Could not initialize GLRenderer (requires active GL 3.3+ or GLES 3.0+ context)")

    @property
    def handle(self) -> int:
        return int(self._handle or 0)

    def render(self, draw_data: DrawData, *, clear: bool = True) -> None:
        if not self._handle:
            raise RuntimeError("GLRenderer is closed")
        self._lib.cui_gl_render(self._handle, draw_data.raw_ptr, bool(clear))

    def read_pixels(self, width: int, height: int) -> bytes:
        if not self._handle:
            raise RuntimeError("GLRenderer is closed")
        buf = ctypes.create_string_buffer(int(width) * int(height) * 4)
        self._lib.cui_gl_read_pixels(self._handle, int(width), int(height), buf)
        return buf.raw

    def close(self) -> None:
        if self._handle:
            self._lib.cui_gl_destroy(self._handle)
            self._handle = None

    def __enter__(self) -> GLRenderer:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass


class CustomRenderer:
    """Bridge for user-defined GPU backends (Vulkan, Metal, Direct3D, WebGPU)."""

    __slots__ = ("_create_cb", "_update_cb", "_destroy_cb", "_c_create", "_c_update", "_c_destroy")

    def __init__(
        self,
        *,
        on_create: Callable[[int, int, TextureFormat, bytes], int],
        on_update: Callable[[int, int, int, int, int, bytes, int], None],
        on_destroy: Callable[[int], None],
    ) -> None:
        self._create_cb = on_create
        self._update_cb = on_update
        self._destroy_cb = on_destroy

        def _create(_u, w: int, h: int, fmt: int, pixels_ptr: int) -> int:
            tf = TextureFormat(fmt)
            bpp = 1 if tf == TextureFormat.R8 else 4
            data = ctypes.string_at(pixels_ptr, w * h * bpp) if pixels_ptr else b""
            return int(self._create_cb(w, h, tf, data))

        def _update(_u, tex: int, x: int, y: int, w: int, h: int, pixels_ptr: int, stride: int) -> None:
            data = ctypes.string_at(pixels_ptr, stride * h) if (pixels_ptr and h > 0) else b""
            self._update_cb(int(tex), x, y, w, h, data, stride)

        def _destroy(_u, tex: int) -> None:
            self._destroy_cb(int(tex))

        self._c_create = TexCreateFn(_create)
        self._c_update = TexUpdateFn(_update)
        self._c_destroy = TexDestroyFn(_destroy)
