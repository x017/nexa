"""Live Theme token customization and perceptual OKLab/OKLCH color helpers."""

from __future__ import annotations

from typing import Tuple

from ._cdefs import CuiColor, CuiShadow, CuiTheme, to_packed_color
from ._lib import get_cdll
from .types import Accent, Color, ColorLike, Shadow, Token


def oklch(l: float, c: float, h_degrees: float, alpha: float = 1.0) -> Color:
    """Construct a ``Color`` from perceptual OKLCH coordinates."""
    u = int(get_cdll().nexa_oklch(float(l), float(c), float(h_degrees), float(alpha)))
    return Color._from_packed(u)


def mix_colors(a: ColorLike, b: ColorLike, t: float) -> Color:
    """Mix two colors in perceptual OKLab space (like CSS ``color-mix(in oklab, ...)``)."""
    u = int(get_cdll().nexa_mix(to_packed_color(a), to_packed_color(b), float(t)))
    return Color._from_packed(u)


def with_alpha(c: ColorLike, alpha_multiplier: float) -> Color:
    """Multiply a color's alpha channel by ``alpha_multiplier``."""
    u = int(get_cdll().nexa_alpha(to_packed_color(c), float(alpha_multiplier)))
    return Color._from_packed(u)


def accent_name(accent: Accent) -> str:
    raw = get_cdll().cui_accent_name(int(accent))
    return raw.decode("utf-8") if raw else accent.name.lower()


def _c2py_color(cc: CuiColor) -> Color:
    return Color(cc.r, cc.g, cc.b, cc.a)


def _assign_c_color(dst: CuiColor, src: ColorLike) -> None:
    u = to_packed_color(src)
    dst.r = u & 0xFF
    dst.g = (u >> 8) & 0xFF
    dst.b = (u >> 16) & 0xFF
    dst.a = (u >> 24) & 0xFF


def _c2py_shadow_pair(arr) -> Tuple[Shadow, Shadow]:
    return (
        Shadow(arr[0].y, arr[0].blur, arr[0].spread, arr[0].alpha),
        Shadow(arr[1].y, arr[1].blur, arr[1].spread, arr[1].alpha),
    )


def _assign_shadow_pair(arr, pair: Tuple[Shadow, Shadow]) -> None:
    for i in (0, 1):
        s = pair[i]
        arr[i] = CuiShadow(float(s.y), float(s.blur), float(s.spread), float(s.alpha))


class ThemeProxy:
    """Direct read/write view over ``cui_theme`` of a ``UI`` context.

    Edits apply immediately on the next frame while ``ui.set_theme`` and
    ``ui.set_accent`` smoothly spring-animate between palettes.
    """

    __slots__ = ("_ptr",)

    def __init__(self, ptr) -> None:
        self._ptr = ptr

    def _t(self) -> CuiTheme:
        return self._ptr.contents

    def __getitem__(self, token: Token) -> Color:
        idx = int(token)
        if idx < 0 or idx >= int(Token.COUNT):
            raise IndexError(token)
        return _c2py_color(self._t().colors[idx])

    def __setitem__(self, token: Token, color: ColorLike) -> None:
        idx = int(token)
        if idx < 0 or idx >= int(Token.COUNT):
            raise IndexError(token)
        _assign_c_color(self._t().colors[idx], color)

    @property
    def radius_control(self) -> float:
        return float(self._t().radius_control)

    @radius_control.setter
    def radius_control(self, v: float) -> None:
        self._t().radius_control = float(v)

    @property
    def radius_panel(self) -> float:
        return float(self._t().radius_panel)

    @radius_panel.setter
    def radius_panel(self, v: float) -> None:
        self._t().radius_panel = float(v)

    @property
    def radius_surface(self) -> float:
        return float(self._t().radius_surface)

    @radius_surface.setter
    def radius_surface(self, v: float) -> None:
        self._t().radius_surface = float(v)

    @property
    def control_sm(self) -> float:
        return float(self._t().control_sm)

    @control_sm.setter
    def control_sm(self, v: float) -> None:
        self._t().control_sm = float(v)

    @property
    def control_md(self) -> float:
        return float(self._t().control_md)

    @control_md.setter
    def control_md(self, v: float) -> None:
        self._t().control_md = float(v)

    @property
    def control_lg(self) -> float:
        return float(self._t().control_lg)

    @control_lg.setter
    def control_lg(self, v: float) -> None:
        self._t().control_lg = float(v)

    @property
    def text_xs(self) -> float:
        return float(self._t().text_xs)

    @text_xs.setter
    def text_xs(self, v: float) -> None:
        self._t().text_xs = float(v)

    @property
    def text_sm(self) -> float:
        return float(self._t().text_sm)

    @text_sm.setter
    def text_sm(self, v: float) -> None:
        self._t().text_sm = float(v)

    @property
    def text_body(self) -> float:
        return float(self._t().text_body)

    @text_body.setter
    def text_body(self, v: float) -> None:
        self._t().text_body = float(v)

    @property
    def text_lg(self) -> float:
        return float(self._t().text_lg)

    @text_lg.setter
    def text_lg(self, v: float) -> None:
        self._t().text_lg = float(v)

    @property
    def headings(self) -> Tuple[float, float, float, float]:
        h = self._t().heading
        return (float(h[0]), float(h[1]), float(h[2]), float(h[3]))

    @headings.setter
    def headings(self, values: Tuple[float, float, float, float]) -> None:
        h = self._t().heading
        for i in range(4):
            h[i] = float(values[i])

    @property
    def shadow_resting(self) -> Tuple[Shadow, Shadow]:
        return _c2py_shadow_pair(self._t().shadow_resting)

    @shadow_resting.setter
    def shadow_resting(self, pair: Tuple[Shadow, Shadow]) -> None:
        _assign_shadow_pair(self._t().shadow_resting, pair)

    @property
    def shadow_raised(self) -> Tuple[Shadow, Shadow]:
        return _c2py_shadow_pair(self._t().shadow_raised)

    @shadow_raised.setter
    def shadow_raised(self, pair: Tuple[Shadow, Shadow]) -> None:
        _assign_shadow_pair(self._t().shadow_raised, pair)

    @property
    def shadow_floating(self) -> Tuple[Shadow, Shadow]:
        return _c2py_shadow_pair(self._t().shadow_floating)

    @shadow_floating.setter
    def shadow_floating(self, pair: Tuple[Shadow, Shadow]) -> None:
        _assign_shadow_pair(self._t().shadow_floating, pair)

    @property
    def motion(self) -> float:
        return float(self._t().motion)

    @motion.setter
    def motion(self, v: float) -> None:
        self._t().motion = float(v)

    @property
    def font_scale(self) -> float:
        return float(self._t().font_scale)

    @font_scale.setter
    def font_scale(self, v: float) -> None:
        self._t().font_scale = float(v)
