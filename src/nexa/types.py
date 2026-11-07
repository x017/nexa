"""Pythonic value types, enums, flags, and data records for nexa.

All classes use ``__slots__`` and avoid heavy stdlib imports so startup stays
sub-millisecond and frozen binaries stay tiny.
"""

from __future__ import annotations

import sys
from enum import IntEnum, IntFlag
from typing import Iterable, Iterator, Optional, Sequence, Tuple, Union


# ---------------------------------------------------------------------------
# Enums & Flags (1:1 values with cui.h / cui_app.h / cui_render.h)
# ---------------------------------------------------------------------------

class Token(IntEnum):
    NONE = 0
    BACKGROUND = 1
    SURFACE = 2
    SURFACE_RAISED = 3
    SURFACE_MUTED = 4
    FOREGROUND = 5
    TEXT_SECONDARY = 6
    TEXT_MUTED = 7
    BORDER = 8
    BORDER_SUBTLE = 9
    BORDER_STRONG = 10
    ACCENT = 11
    ACCENT_STRONG = 12
    ACCENT_SUBTLE = 13
    ACCENT_FOREGROUND = 14
    SUCCESS = 15
    WARNING = 16
    DANGER = 17
    INFO = 18
    CONTROL_ON = 19
    CONTROL_GLYPH = 20
    CONTROL_TRACK = 21
    CONTROL_TRACK_HOVER = 22
    CONTROL_THUMB = 23
    CONTROL_THUMB_ON = 24
    HOVER = 25
    ACTIVE = 26
    SCRIM = 27
    FOCUS_RING = 28
    SERIES_1 = 29
    SERIES_2 = 30
    SERIES_3 = 31
    SERIES_4 = 32
    SERIES_5 = 33
    SERIES_6 = 34
    COUNT = 35


class ThemeMode(IntEnum):
    LIGHT = 0
    DARK = 1


class Accent(IntEnum):
    """Built-in perceptual OKLCH theme accent palettes."""

    NEUTRAL = 0
    VIOLET = 1
    BLUE = 2
    GREEN = 3
    AMBER = 4
    ORANGE = 5
    CORAL = 6
    ROSE = 7


# Expose CUI_ACCENT_COUNT parity without adding a 9th member when iterating `for a in ui.Accent`
type.__setattr__(Accent, "COUNT", 8)


class RendererKind(IntEnum):
    AUTO = 0
    OPENGL = 1
    SOFTWARE = 2


class PixelFormat(IntEnum):
    RGBA = 0
    BGRA = 1


class TextureFormat(IntEnum):
    R8 = 1
    RGBA8 = 4


class FontRole(IntEnum):
    BODY = 0
    MEDIUM = 1
    DISPLAY = 2
    MONO = 3
    ICONS = 4


class SizeKind(IntEnum):
    FIT = 0
    GROW = 1
    FIXED = 2
    PERCENT = 3


class Direction(IntEnum):
    COLUMN = 0
    ROW = 1
    STACK = 2
    GRID = 3


class Align(IntEnum):
    DEFAULT = 0
    START = 1
    CENTER = 2
    END = 3
    STRETCH = 4


class Justify(IntEnum):
    START = 0
    CENTER = 1
    END = 2
    BETWEEN = 3
    AROUND = 4


class Elevation(IntEnum):
    NONE = 0
    RESTING = 1
    RAISED = 2
    FLOATING = 3


class TextAlign(IntEnum):
    LEFT = 0
    CENTER = 1
    RIGHT = 2


class ButtonVariant(IntEnum):
    DEFAULT = 0
    SECONDARY = 1
    PRIMARY = 2
    OUTLINE = 3
    GHOST = 4
    DANGER = 5
    LINK = 6


class ControlSize(IntEnum):
    MD = 0
    SM = 1
    LG = 2


class TabsVariant(IntEnum):
    UNDERLINE = 0
    PILL = 1


class Placement(IntEnum):
    BOTTOM_START = 0
    BOTTOM = 1
    BOTTOM_END = 2
    TOP_START = 3
    TOP = 4
    TOP_END = 5
    RIGHT_START = 6
    LEFT_START = 7
    RIGHT = 8
    LEFT = 9


class Side(IntEnum):
    RIGHT = 0
    LEFT = 1
    BOTTOM = 2
    TOP = 3


class Tone(IntEnum):
    NEUTRAL = 0
    INFO = 1
    SUCCESS = 2
    WARNING = 3
    DANGER = 4
    VIOLET = 5
    TEAL = 6
    ROSE = 7
    ACCENT = 8


class Status(IntEnum):
    IDLE = 0
    BUSY = 1
    SUCCESS = 2
    ERROR = 3


class LoaderStyle(IntEnum):
    DOTS = 0
    BARS = 1
    PULSE = 2
    ORBIT = 3
    GRID = 4


class TaskStatus(IntEnum):
    PENDING = 0
    RUNNING = 1
    DONE = 2
    FAILED = 3
    SKIPPED = 4


class VoiceState(IntEnum):
    IDLE = 0
    LISTENING = 1
    THINKING = 2
    SPEAKING = 3


class LogLevel(IntEnum):
    TRACE = 0
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4


class ShadeMode(IntEnum):
    TEXT = 0
    RRECT = 1
    SHADOW = 2
    IMAGE = 3
    SOLID = 4


class FileDialogKind(IntEnum):
    OPEN = 0
    SAVE = 1
    FOLDER = 2


class MouseButton(IntEnum):
    LEFT = 0
    RIGHT = 1
    MIDDLE = 2


class Cursor(IntEnum):
    ARROW = 0
    HAND = 1
    TEXT = 2
    RESIZE_EW = 3
    RESIZE_NS = 4
    MOVE = 5
    NOT_ALLOWED = 6


class Key(IntEnum):
    NONE = 0
    TAB = 1
    ENTER = 2
    ESCAPE = 3
    BACKSPACE = 4
    DELETE = 5
    SPACE = 6
    LEFT = 7
    RIGHT = 8
    UP = 9
    DOWN = 10
    HOME = 11
    END = 12
    PAGE_UP = 13
    PAGE_DOWN = 14
    A = 15; B = 16; C = 17; D = 18; E = 19; F = 20; G = 21; H = 22; I = 23
    J = 24; K = 25; L = 26; M = 27; N = 28; O = 29; P = 30; Q = 31; R = 32
    S = 33; T = 34; U = 35; V = 36; W = 37; X = 38; Y = 39; Z = 40
    NUM_0 = 41; NUM_1 = 42; NUM_2 = 43; NUM_3 = 44; NUM_4 = 45
    NUM_5 = 46; NUM_6 = 47; NUM_7 = 48; NUM_8 = 49; NUM_9 = 50
    MINUS = 51
    EQUAL = 52
    COMMA = 53
    PERIOD = 54
    SLASH = 55
    F1 = 56; F2 = 57; F3 = 58; F4 = 59; F5 = 60; F6 = 61
    F7 = 62; F8 = 63; F9 = 64; F10 = 65; F11 = 66; F12 = 67


class Mod(IntFlag):
    NONE = 0
    SHIFT = 1 << 0
    CTRL = 1 << 1
    ALT = 1 << 2
    SUPER = 1 << 3
    PRIMARY = (1 << 3) if sys.platform == "darwin" else (1 << 1)


class InputFlags(IntFlag):
    NONE = 0
    CHANGED = 1
    SUBMITTED = 2
    FOCUSED = 4
    BLURRED = 8


class CommentFlags(IntFlag):
    NONE = 0
    LIKE = 1
    REPLY = 2


class PlayerFlags(IntFlag):
    NONE = 0
    TOGGLE = 1
    PREV = 2
    NEXT = 4
    SEEK = 8


class ResponseFlags(IntFlag):
    NONE = 0
    COPY = 1
    REGENERATE = 2
    UP = 4
    DOWN = 8
    SHARE = 16


ResponseActionFlags = ResponseFlags


class ComposerFlags(IntFlag):
    NONE = 0
    SEND = 1
    STOP = 2
    ATTACH = 4
    REMOVE = 8
    MODEL = 16


class BuildFeatures(IntFlag):
    NONE = 0
    SW = 1 << 0
    GL = 1 << 1
    APP = 1 << 2
    DEFAULT_FONTS = 1 << 3
    STB_IMAGE = 1 << 4
    IMAGE_ALL = 1 << 5
    TEXT_SHAPING = 1 << 6


class TreeFlags(IntFlag):
    NONE = 0
    HAS_CHILDREN = 1 << 0
    OPEN = 1 << 1
    SELECTED = 1 << 2
    LOADING = 1 << 3


class DiffMode(IntEnum):
    SPLIT = 0
    INLINE = 1


class DiffRowKind(IntEnum):
    CONTEXT = 0
    ADD = 1
    DELETE = 2
    CHANGE = 3
    FOLD = 4


class DiffFlags(IntFlag):
    NONE = 0
    IGNORE_EOL = 1 << 0


class CurveMode(IntEnum):
    SMOOTH = 0
    FREE = 1
    LINEAR = 2
    STEP = 3


class TimelineRuler(IntEnum):
    FRAMES = 0
    SECONDS = 1
    TIMECODE = 2


# ---------------------------------------------------------------------------
# Geometry, Sizing & Colors
# ---------------------------------------------------------------------------

class Vec2:
    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        self.x = float(x)
        self.y = float(y)

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Vec2):
            return self.x == other.x and self.y == other.y
        if isinstance(other, tuple) and len(other) == 2:
            return self.x == other[0] and self.y == other[1]
        return False

    def __repr__(self) -> str:
        return f"Vec2({self.x:g}, {self.y:g})"


Vec2Like = Union[Vec2, Tuple[float, float]]


class Rect:
    __slots__ = ("x", "y", "w", "h")

    def __init__(self, x: float = 0.0, y: float = 0.0, w: float = 0.0, h: float = 0.0) -> None:
        self.x = float(x)
        self.y = float(y)
        self.w = float(w)
        self.h = float(h)

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    @property
    def center(self) -> Vec2:
        return Vec2(self.x + self.w * 0.5, self.y + self.h * 0.5)

    def contains(self, x: float, y: float) -> bool:
        return self.x <= x < self.x + self.w and self.y <= y < self.y + self.h

    def inset(self, d: float) -> Rect:
        return Rect(self.x + d, self.y + d, max(0.0, self.w - 2.0 * d), max(0.0, self.h - 2.0 * d))

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y
        yield self.w
        yield self.h

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Rect):
            return (self.x, self.y, self.w, self.h) == (other.x, other.y, other.w, other.h)
        return False

    def __repr__(self) -> str:
        return f"Rect(x={self.x:g}, y={self.y:g}, w={self.w:g}, h={self.h:g})"


RectLike = Union[Rect, Tuple[float, float, float, float]]


class Corners:
    __slots__ = ("tl", "tr", "br", "bl")

    def __init__(self, tl: float = 0.0, tr: Optional[float] = None,
                 br: Optional[float] = None, bl: Optional[float] = None) -> None:
        if tr is None and br is None and bl is None:
            v = float(tl)
            self.tl = self.tr = self.br = self.bl = v
        else:
            self.tl = float(tl)
            self.tr = float(tl if tr is None else tr)
            self.br = float(tl if br is None else br)
            self.bl = float(self.tr if bl is None else bl)

    def __iter__(self) -> Iterator[float]:
        yield self.tl
        yield self.tr
        yield self.br
        yield self.bl

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Corners):
            return (self.tl, self.tr, self.br, self.bl) == (other.tl, other.tr, other.br, other.bl)
        return False

    def __repr__(self) -> str:
        return f"Corners({self.tl:g}, {self.tr:g}, {self.br:g}, {self.bl:g})"


CornersLike = Union[Corners, float, int, Tuple[float, float, float, float]]


class Size:
    """Layout dimension specification (fit, grow, fixed points, or percentage)."""

    __slots__ = ("kind", "value")

    def __init__(self, kind: SizeKind = SizeKind.FIT, value: float = 0.0) -> None:
        self.kind = SizeKind(kind)
        self.value = float(value)

    @classmethod
    def fit(cls) -> Size:
        return FIT

    @classmethod
    def fill(cls) -> Size:
        return FILL

    @classmethod
    def grow(cls, weight: float = 1.0) -> Size:
        return cls(SizeKind.GROW, weight)

    @classmethod
    def px(cls, points: float) -> Size:
        return cls(SizeKind.FIXED, points)

    @classmethod
    def pct(cls, percent: float) -> Size:
        return cls(SizeKind.PERCENT, percent)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Size) and self.kind == other.kind and self.value == other.value

    def __repr__(self) -> str:
        return f"Size({self.kind.name}, {self.value:g})"


FIT = Size(SizeKind.FIT, 0.0)
FILL = Size(SizeKind.GROW, 1.0)


def GROW(weight: float = 1.0) -> Size:
    return Size(SizeKind.GROW, weight)


def PX(points: float) -> Size:
    return Size(SizeKind.FIXED, points)


def PCT(percent: float) -> Size:
    return Size(SizeKind.PERCENT, percent)


SizeLike = Union[Size, float, int, None]


class Color:
    """RGBA color or semantic theme token color."""

    __slots__ = ("r", "g", "b", "a")

    BACKGROUND: Color
    SURFACE: Color
    SURFACE_RAISED: Color
    SURFACE_MUTED: Color
    FOREGROUND: Color
    TEXT_SECONDARY: Color
    TEXT_MUTED: Color
    BORDER: Color
    BORDER_SUBTLE: Color
    BORDER_STRONG: Color
    ACCENT: Color
    ACCENT_STRONG: Color
    ACCENT_SUBTLE: Color
    ACCENT_FOREGROUND: Color
    SUCCESS: Color
    WARNING: Color
    DANGER: Color
    INFO: Color
    HOVER: Color
    SCRIM: Color
    TRANSPARENT: Color

    def __init__(self, r: int = 0, g: int = 0, b: int = 0, a: int = 255) -> None:
        self.r = int(r) & 0xFF
        self.g = int(g) & 0xFF
        self.b = int(b) & 0xFF
        self.a = int(a) & 0xFF

    @classmethod
    def rgb(cls, hex_rgb: int) -> Color:
        return cls((hex_rgb >> 16) & 0xFF, (hex_rgb >> 8) & 0xFF, hex_rgb & 0xFF, 255)

    @classmethod
    def rgba(cls, hex_rgba: int) -> Color:
        return cls((hex_rgba >> 24) & 0xFF, (hex_rgba >> 16) & 0xFF, (hex_rgba >> 8) & 0xFF, hex_rgba & 0xFF)

    @classmethod
    def hex(cls, value: str) -> Color:
        s = value.strip().lstrip("#")
        if len(s) == 3:
            s = "".join(ch * 2 for ch in s)
        if len(s) == 6:
            return cls.rgb(int(s, 16))
        if len(s) == 8:
            return cls.rgba(int(s, 16))
        raise ValueError(f"Invalid hex color: {value!r}")

    @classmethod
    def token(cls, tok: Token) -> Color:
        return cls(int(tok), 0xC5, 0x1D, 0)

    @classmethod
    def series(cls, index: int) -> Color:
        return cls.token(Token(int(Token.SERIES_1) + (index % 6)))

    @classmethod
    def _from_packed(cls, u: int) -> Color:
        return cls(u & 0xFF, (u >> 8) & 0xFF, (u >> 16) & 0xFF, (u >> 24) & 0xFF)

    def _packed(self) -> int:
        return self.r | (self.g << 8) | (self.b << 16) | (self.a << 24)

    def with_alpha(self, alpha: Union[float, int]) -> Color:
        """Return an RGBA copy with updated alpha (`0.0..1.0` float or `0..255` int)."""
        if isinstance(alpha, float):
            a_u8 = max(0, min(255, int(round(alpha * 255.0))))
        else:
            a_u8 = max(0, min(255, int(alpha)))
        return Color(self.r, self.g, self.b, a_u8)

    @property
    def is_token(self) -> bool:
        return self.a == 0 and self.g == 0xC5 and self.b == 0x1D and self.r != 0

    def to_hex(self, include_alpha: bool = False) -> str:
        if include_alpha:
            return f"#{self.r:02x}{self.g:02x}{self.b:02x}{self.a:02x}"
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def __iter__(self) -> Iterator[int]:
        yield self.r
        yield self.g
        yield self.b
        yield self.a

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Color) and (self.r, self.g, self.b, self.a) == (other.r, other.g, other.b, other.a)

    def __repr__(self) -> str:
        if self.is_token:
            try:
                return f"Color.token(Token.{Token(self.r).name})"
            except ValueError:
                pass
        return f"Color({self.r}, {self.g}, {self.b}, {self.a})"


Color.TRANSPARENT = Color(0, 0, 0, 0)
Color.BACKGROUND = Color.token(Token.BACKGROUND)
Color.SURFACE = Color.token(Token.SURFACE)
Color.SURFACE_RAISED = Color.token(Token.SURFACE_RAISED)
Color.SURFACE_MUTED = Color.token(Token.SURFACE_MUTED)
Color.FOREGROUND = Color.token(Token.FOREGROUND)
Color.TEXT_SECONDARY = Color.token(Token.TEXT_SECONDARY)
Color.TEXT_MUTED = Color.token(Token.TEXT_MUTED)
Color.BORDER = Color.token(Token.BORDER)
Color.BORDER_SUBTLE = Color.token(Token.BORDER_SUBTLE)
Color.BORDER_STRONG = Color.token(Token.BORDER_STRONG)
Color.ACCENT = Color.token(Token.ACCENT)
Color.ACCENT_STRONG = Color.token(Token.ACCENT_STRONG)
Color.ACCENT_SUBTLE = Color.token(Token.ACCENT_SUBTLE)
Color.ACCENT_FOREGROUND = Color.token(Token.ACCENT_FOREGROUND)
Color.SUCCESS = Color.token(Token.SUCCESS)
Color.WARNING = Color.token(Token.WARNING)
Color.DANGER = Color.token(Token.DANGER)
Color.INFO = Color.token(Token.INFO)
Color.HOVER = Color.token(Token.HOVER)
Color.SCRIM = Color.token(Token.SCRIM)

ColorLike = Union[Color, Token, int, str, Tuple[int, int, int], Tuple[int, int, int, int], None]


# ---------------------------------------------------------------------------
# Dates, Shortcuts, Metrics & Shadow
# ---------------------------------------------------------------------------

class Date:
    __slots__ = ("year", "month", "day")

    def __init__(self, year: int = 0, month: int = 0, day: int = 0) -> None:
        self.year = int(year)
        self.month = int(month)
        self.day = int(day)

    @classmethod
    def today(cls) -> Date:
        import ctypes
        from ._lib import get_cdll
        out = (ctypes.c_int * 3)()
        get_cdll().nexa_date_today(out)
        return cls(out[0], out[1], out[2])

    @classmethod
    def from_days(cls, days_since_epoch: int) -> Date:
        import ctypes
        from ._lib import get_cdll
        out = (ctypes.c_int * 3)()
        get_cdll().nexa_date_from_days(int(days_since_epoch), out)
        return cls(out[0], out[1], out[2])

    def to_days(self) -> int:
        from ._lib import get_cdll
        return int(get_cdll().nexa_date_to_days(self.year, self.month, self.day))

    @property
    def is_empty(self) -> bool:
        return self.year == 0

    def isoformat(self) -> str:
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"

    def __iter__(self) -> Iterator[int]:
        yield self.year
        yield self.month
        yield self.day

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Date) and (self.year, self.month, self.day) == (other.year, other.month, other.day)

    def __repr__(self) -> str:
        return f"Date({self.year}, {self.month}, {self.day})"


class DateRange:
    __slots__ = ("start", "end")

    def __init__(self, start: Optional[Date] = None, end: Optional[Date] = None) -> None:
        self.start = start if start is not None else Date()
        self.end = end if end is not None else Date()

    def __iter__(self) -> Iterator[Date]:
        yield self.start
        yield self.end

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DateRange) and self.start == other.start and self.end == other.end

    def __repr__(self) -> str:
        return f"DateRange({self.start!r}, {self.end!r})"


class KeyCombo:
    __slots__ = ("mods", "key")

    def __init__(self, mods: Union[Mod, int] = Mod.NONE, key: Key = Key.NONE) -> None:
        self.mods = Mod(int(mods))
        self.key = Key(int(key))

    def __iter__(self) -> Iterator[int]:
        yield int(self.mods)
        yield int(self.key)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, KeyCombo) and self.mods == other.mods and self.key == other.key

    def __repr__(self) -> str:
        return f"KeyCombo(mods={self.mods!r}, key={self.key!r})"


class TextMetrics:
    __slots__ = ("width", "height", "ascent", "descent", "line_height")

    def __init__(self, width: float, height: float, ascent: float, descent: float, line_height: float) -> None:
        self.width = width
        self.height = height
        self.ascent = ascent
        self.descent = descent
        self.line_height = line_height

    def __repr__(self) -> str:
        return f"TextMetrics(width={self.width:g}, height={self.height:g}, line_height={self.line_height:g})"


class Shadow:
    __slots__ = ("y", "blur", "spread", "alpha")

    def __init__(self, y: float = 0.0, blur: float = 0.0, spread: float = 0.0, alpha: float = 0.0) -> None:
        self.y = float(y)
        self.blur = float(blur)
        self.spread = float(spread)
        self.alpha = float(alpha)

    def __repr__(self) -> str:
        return f"Shadow(y={self.y:g}, blur={self.blur:g}, spread={self.spread:g}, alpha={self.alpha:g})"


# ---------------------------------------------------------------------------
# Component Descriptor & Result Value Types
# ---------------------------------------------------------------------------

class InputResult:
    """Returned by ``*_event`` input widgets; unpacks as ``(value, flags)``."""

    __slots__ = ("value", "flags")

    def __init__(self, value: str, flags: Union[InputFlags, int]) -> None:
        self.value = value
        self.flags = InputFlags(int(flags))

    @property
    def changed(self) -> bool:
        return bool(self.flags & InputFlags.CHANGED)

    @property
    def submitted(self) -> bool:
        return bool(self.flags & InputFlags.SUBMITTED)

    @property
    def focused(self) -> bool:
        return bool(self.flags & InputFlags.FOCUSED)

    @property
    def blurred(self) -> bool:
        return bool(self.flags & InputFlags.BLURRED)

    def __iter__(self):
        yield self.value
        yield self.flags

    def __repr__(self) -> str:
        return f"InputResult(value={self.value!r}, flags={self.flags!r})"


class TableColumn:
    __slots__ = ("title", "width", "align", "sortable")

    def __init__(self, title: str, width: SizeLike = None,
                 align: TextAlign = TextAlign.LEFT, sortable: bool = False) -> None:
        self.title = title
        self.width = width
        self.align = align
        self.sortable = sortable


class TableSort:
    __slots__ = ("column", "descending")

    def __init__(self, column: int = 0, descending: bool = False) -> None:
        self.column = int(column)
        self.descending = bool(descending)

    def __iter__(self):
        yield self.column
        yield self.descending

    def __eq__(self, other: object) -> bool:
        return isinstance(other, TableSort) and (self.column, self.descending) == (other.column, other.descending)

    def __repr__(self) -> str:
        return f"TableSort(column={self.column}, descending={self.descending})"


class GridColumn:
    __slots__ = ("title", "width", "align", "sortable", "fixed", "priority")

    def __init__(self, title: str, width: float = 150.0, align: TextAlign = TextAlign.LEFT,
                 sortable: bool = False, fixed: bool = False, priority: int = 0) -> None:
        self.title = title
        self.width = float(width)
        self.align = align
        self.sortable = sortable
        self.fixed = fixed
        self.priority = int(priority)


class Series:
    __slots__ = ("name", "values", "color")

    def __init__(self, name: str, values: Sequence[float], color: ColorLike = None) -> None:
        self.name = name
        self.values = tuple(float(v) for v in values)
        self.color = color


class ScatterSeries:
    __slots__ = ("name", "points", "sizes", "color")

    def __init__(self, name: str, points: Sequence[Vec2Like],
                 sizes: Optional[Sequence[float]] = None, color: ColorLike = None) -> None:
        self.name = name
        self.points = tuple((float(p.x), float(p.y)) if isinstance(p, Vec2) else (float(p[0]), float(p[1])) for p in points)
        self.sizes = tuple(float(s) for s in sizes) if sizes is not None else None
        self.color = color


class VizItem:
    __slots__ = ("label", "value", "color")

    def __init__(self, label: str, value: float, color: ColorLike = None) -> None:
        self.label = label
        self.value = float(value)
        self.color = color


class SankeyLink:
    __slots__ = ("source", "target", "value")

    def __init__(self, source: int, target: int, value: float) -> None:
        self.source = int(source)
        self.target = int(target)
        self.value = float(value)

    @property
    def from_node(self) -> int:
        return self.source

    @property
    def to_node(self) -> int:
        return self.target


class Choice:
    __slots__ = ("title", "description", "icon", "badge")

    def __init__(self, title: str, description: Optional[str] = None,
                 icon: Optional[str] = None, badge: Optional[str] = None) -> None:
        self.title = title
        self.description = description
        self.icon = icon
        self.badge = badge


class Command:
    __slots__ = ("title", "icon", "group", "shortcut")

    def __init__(self, title: str, icon: Optional[str] = None,
                 group: Optional[str] = None, shortcut: Optional[str] = None) -> None:
        self.title = title
        self.icon = icon
        self.group = group
        self.shortcut = shortcut


class Reaction:
    __slots__ = ("icon", "count", "active")

    def __init__(self, icon: str, count: int = 0, active: bool = False) -> None:
        self.icon = icon
        self.count = int(count)
        self.active = bool(active)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Reaction) and (self.icon, self.count, self.active) == (other.icon, other.count, other.active)

    def __repr__(self) -> str:
        return f"Reaction(icon={self.icon!r}, count={self.count}, active={self.active})"


class SpeedAction:
    __slots__ = ("icon", "label")

    def __init__(self, icon: str, label: str) -> None:
        self.icon = icon
        self.label = label


class SwipeAction:
    __slots__ = ("icon", "label", "tone")

    def __init__(self, label: str, icon: Optional[str] = None, tone: Tone = Tone.NEUTRAL) -> None:
        self.icon = icon
        self.label = label
        self.tone = tone


class FilterField:
    __slots__ = ("name", "options", "icon")

    def __init__(self, name: str, options: Sequence[str], icon: Optional[str] = None) -> None:
        self.name = name
        self.options = tuple(options)
        self.icon = icon


class PresenceUser:
    __slots__ = ("name", "color", "avatar", "idle")

    def __init__(self, name: str, color: ColorLike = None, avatar: int = 0, idle: bool = False) -> None:
        self.name = name
        self.color = color
        self.avatar = int(avatar)
        self.idle = bool(idle)


class TickerItem:
    __slots__ = ("label", "value", "delta", "lower_is_better")

    def __init__(self, label: str, value: str, delta: float = 0.0, lower_is_better: bool = False) -> None:
        self.label = label
        self.value = value
        self.delta = float(delta)
        self.lower_is_better = bool(lower_is_better)


class TabBarItem:
    __slots__ = ("icon", "label", "badge")

    def __init__(self, icon: str, label: str, badge: int = 0) -> None:
        self.icon = icon
        self.label = label
        self.badge = int(badge)


class NowPlaying:
    __slots__ = ("title", "artist", "art", "art_color", "position", "duration", "playing")

    def __init__(self, title: str = "", artist: str = "", art: int = 0,
                 art_color: ColorLike = None, position: float = 0.0,
                 duration: float = 1.0, playing: bool = False) -> None:
        self.title = title
        self.artist = artist
        self.art = int(art)
        self.art_color = art_color
        self.position = float(position)
        self.duration = float(duration)
        self.playing = bool(playing)


class PlanStep:
    __slots__ = ("title", "detail", "status")

    def __init__(self, title: str, status: TaskStatus = TaskStatus.PENDING,
                 detail: Optional[str] = None) -> None:
        self.title = title
        self.detail = detail
        self.status = status


class Source:
    __slots__ = ("title", "url", "snippet")

    def __init__(self, title: str, url: str = "", snippet: Optional[str] = None) -> None:
        self.title = title
        self.url = url
        self.snippet = snippet


class PromptSuggestion:
    __slots__ = ("title", "detail", "icon")

    def __init__(self, title: str, detail: Optional[str] = None, icon: Optional[str] = None) -> None:
        self.title = title
        self.detail = detail
        self.icon = icon


class Model:
    __slots__ = ("name", "detail", "badge", "icon")

    def __init__(self, name: str, detail: Optional[str] = None,
                 badge: Optional[str] = None, icon: Optional[str] = None) -> None:
        self.name = name
        self.detail = detail
        self.badge = badge
        self.icon = icon


ModelInfo = Model


class ComposerResult:
    """Returned by ``chat_composer``; unpacks as ``(text, flags, model, removed)``."""

    __slots__ = ("text", "flags", "model", "removed")

    def __init__(self, text: str, flags: Union[ComposerFlags, int], model: int = 0, removed: int = -1) -> None:
        self.text = text
        self.flags = ComposerFlags(int(flags))
        self.model = int(model)
        self.removed = int(removed)

    @property
    def sent(self) -> bool:
        return bool(self.flags & ComposerFlags.SEND)

    @property
    def stopped(self) -> bool:
        return bool(self.flags & ComposerFlags.STOP)

    @property
    def attach_clicked(self) -> bool:
        return bool(self.flags & ComposerFlags.ATTACH)

    def __iter__(self):
        yield self.text
        yield self.flags
        yield self.model
        yield self.removed

    def __repr__(self) -> str:
        return f"ComposerResult(text={self.text!r}, flags={self.flags!r}, model={self.model}, removed={self.removed})"


class KanbanMove:
    __slots__ = ("card", "from_column", "to_column", "to_index")

    def __init__(self, card: int, from_column: int, to_column: int, to_index: int) -> None:
        self.card = int(card)
        self.from_column = int(from_column)
        self.to_column = int(to_column)
        self.to_index = int(to_index)

    def __iter__(self):
        yield self.card
        yield self.from_column
        yield self.to_column
        yield self.to_index

    def __repr__(self) -> str:
        return f"KanbanMove(card={self.card}, from_column={self.from_column}, to_column={self.to_column}, to_index={self.to_index})"


class CalEvent:
    __slots__ = ("title", "detail", "day", "start", "end", "tone")

    def __init__(self, title: str, day: int, start: float, end: float,
                 detail: Optional[str] = None, tone: Tone = Tone.ACCENT) -> None:
        self.title = title
        self.detail = detail
        self.day = int(day)
        self.start = float(start)
        self.end = float(end)
        self.tone = tone

    def __repr__(self) -> str:
        return f"CalEvent(title={self.title!r}, day={self.day}, start={self.start:g}, end={self.end:g})"


class GanttTask:
    __slots__ = ("name", "owner", "start", "end", "progress", "tone", "depends_on", "milestone")

    def __init__(self, name: str, start: int, end: int, progress: float = 0.0,
                 owner: Optional[str] = None, tone: Tone = Tone.ACCENT,
                 depends_on: int = -1, milestone: bool = False) -> None:
        self.name = name
        self.owner = owner
        self.start = int(start)
        self.end = int(end)
        self.progress = float(progress)
        self.tone = tone
        self.depends_on = int(depends_on)
        self.milestone = bool(milestone)

    def __repr__(self) -> str:
        return f"GanttTask(name={self.name!r}, start={self.start}, end={self.end}, progress={self.progress:g})"


class TocItem:
    __slots__ = ("title", "anchor", "level")

    def __init__(self, title: str, anchor: str, level: int = 1) -> None:
        self.title = title
        self.anchor = anchor
        self.level = int(level)


class CheckStep:
    __slots__ = ("title", "description", "action", "done")

    def __init__(self, title: str, description: Optional[str] = None,
                 action: Optional[str] = None, done: bool = False) -> None:
        self.title = title
        self.description = description
        self.action = action
        self.done = bool(done)


class DocTab:
    __slots__ = ("title", "icon", "tooltip", "dirty")

    def __init__(self, title: str, icon: Optional[str] = None,
                 tooltip: Optional[str] = None, dirty: bool = False) -> None:
        self.title = title
        self.icon = icon
        self.tooltip = tooltip
        self.dirty = bool(dirty)


class DocTabsResult:
    """Returned by ``doc_tabs``; unpacks as ``(selected, close, move_from, move_to)``."""

    __slots__ = ("selected", "changed", "close", "move_from", "move_to")

    def __init__(self, selected: int, changed: bool, close: int, move_from: int, move_to: int) -> None:
        self.selected = int(selected)
        self.changed = bool(changed)
        self.close = int(close)
        self.move_from = int(move_from)
        self.move_to = int(move_to)

    @property
    def moved(self) -> bool:
        return self.move_from >= 0 and self.move_to >= 0

    def apply_to(self, items: list) -> int:
        """Apply any reorder or close event in-place to ``items`` and return new ``selected``."""
        sel = self.selected
        if self.moved and 0 <= self.move_from < len(items) and 0 <= self.move_to < len(items):
            item = items.pop(self.move_from)
            items.insert(self.move_to, item)
        if 0 <= self.close < len(items):
            items.pop(self.close)
            if sel >= len(items):
                sel = max(0, len(items) - 1)
        return sel

    def __iter__(self):
        yield self.selected
        yield self.close
        yield self.move_from
        yield self.move_to

    def __repr__(self) -> str:
        return (f"DocTabsResult(selected={self.selected}, changed={self.changed}, "
                f"close={self.close}, move_from={self.move_from}, move_to={self.move_to})")


class NodeView:
    __slots__ = ("x", "y", "zoom")

    def __init__(self, x: float = 0.0, y: float = 0.0, zoom: float = 1.0) -> None:
        self.x = float(x)
        self.y = float(y)
        self.zoom = float(zoom)

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.zoom

    def __repr__(self) -> str:
        return f"NodeView(x={self.x:g}, y={self.y:g}, zoom={self.zoom:g})"


class CanvasResult:
    __slots__ = ("rect", "hovered", "pressed", "clicked", "mouse")

    def __init__(self, rect: Rect, hovered: bool, pressed: bool, clicked: bool, mouse: Vec2) -> None:
        self.rect = rect
        self.hovered = hovered
        self.pressed = pressed
        self.clicked = clicked
        self.mouse = mouse

    def __repr__(self) -> str:
        return f"CanvasResult(rect={self.rect!r}, hovered={self.hovered}, pressed={self.pressed}, clicked={self.clicked})"


class DropResult:
    """Returned by ``dropzone``: exposes ``.clicked`` and ``.files`` (tuple of dropped paths)."""

    __slots__ = ("code", "files")

    def __init__(self, code: int, files: Tuple[str, ...] = ()) -> None:
        self.code = int(code)
        self.files = files

    @property
    def clicked(self) -> bool:
        return self.code == -1

    @property
    def dropped(self) -> bool:
        return self.code > 0

    def __bool__(self) -> bool:
        return self.code != 0

    def __int__(self) -> int:
        return self.code

    def __repr__(self) -> str:
        return f"DropResult(code={self.code}, files={self.files!r})"


# ---------------------------------------------------------------------------
# CUI 1.1.0 Models & Value-Returning Results
# ---------------------------------------------------------------------------

class TreeNode:
    """Topology node for ``tree_table`` (flat arena of parent / first_child / next_sibling indices)."""

    __slots__ = ("parent", "first_child", "next_sibling", "flags")

    def __init__(
        self,
        parent: int = -1,
        first_child: int = -1,
        next_sibling: int = -1,
        flags: Union[TreeFlags, int] = TreeFlags.NONE,
    ) -> None:
        self.parent = int(parent)
        self.first_child = int(first_child)
        self.next_sibling = int(next_sibling)
        self.flags = TreeFlags(int(flags))

    @property
    def has_children(self) -> bool:
        return bool(self.flags & TreeFlags.HAS_CHILDREN)

    @property
    def is_open(self) -> bool:
        return bool(self.flags & TreeFlags.OPEN)

    @property
    def is_selected(self) -> bool:
        return bool(self.flags & TreeFlags.SELECTED)

    @property
    def is_loading(self) -> bool:
        return bool(self.flags & TreeFlags.LOADING)

    def __repr__(self) -> str:
        return (
            f"TreeNode(parent={self.parent}, first_child={self.first_child}, "
            f"next_sibling={self.next_sibling}, flags={self.flags!r})"
        )


class TreeTableEvents:
    """Events populated on exit of ``tree_table``."""

    __slots__ = ("activated", "expanded", "collapsed", "load", "selection_changed", "sort_changed")

    def __init__(
        self,
        activated: int = -1,
        expanded: int = -1,
        collapsed: int = -1,
        load: Tuple[int, ...] = (),
        selection_changed: bool = False,
        sort_changed: bool = False,
    ) -> None:
        self.activated = int(activated)
        self.expanded = int(expanded)
        self.collapsed = int(collapsed)
        self.load = tuple(int(x) for x in load)
        self.selection_changed = bool(selection_changed)
        self.sort_changed = bool(sort_changed)

    def __bool__(self) -> bool:
        return (
            self.activated >= 0
            or self.expanded >= 0
            or self.collapsed >= 0
            or bool(self.load)
            or self.selection_changed
            or self.sort_changed
        )

    def __repr__(self) -> str:
        return (
            f"TreeTableEvents(activated={self.activated}, expanded={self.expanded}, "
            f"collapsed={self.collapsed}, load={self.load!r}, "
            f"selection_changed={self.selection_changed}, sort_changed={self.sort_changed})"
        )


class PathBarResult:
    """Returned by ``path_bar``; unpacks as ``(clicked, submitted)``."""

    __slots__ = ("clicked", "submitted", "editing")

    def __init__(self, clicked: int = -1, submitted: Optional[str] = None, editing: bool = False) -> None:
        self.clicked = int(clicked)
        self.submitted = submitted
        self.editing = bool(editing)

    def __bool__(self) -> bool:
        return self.clicked >= 0 or self.submitted is not None

    def __iter__(self):
        yield self.clicked
        yield self.submitted

    def __repr__(self) -> str:
        return f"PathBarResult(clicked={self.clicked}, submitted={self.submitted!r}, editing={self.editing})"


class MarkdownResult:
    """Returned by ``markdown`` (and ``chat_message(..., markdown=True)``)."""

    __slots__ = ("link", "hovered_link", "task_offset", "task_line", "task_checked", "height")

    def __init__(
        self,
        link: Optional[str] = None,
        hovered_link: Optional[str] = None,
        task_offset: int = -1,
        task_line: int = -1,
        task_checked: bool = False,
        height: float = 0.0,
    ) -> None:
        self.link = link
        self.hovered_link = hovered_link
        self.task_offset = int(task_offset)
        self.task_line = int(task_line)
        self.task_checked = bool(task_checked)
        self.height = float(height)

    @property
    def task_toggled(self) -> bool:
        return self.task_offset >= 0

    def apply_task(self, markdown_text: str) -> str:
        """If a GFM task checkbox was toggled this frame, return updated ``markdown_text``."""
        if self.task_offset < 0:
            return markdown_text
        raw = bytearray(markdown_text.encode("utf-8"))
        off = self.task_offset
        if 0 <= off < len(raw) and raw[off] in (ord(" "), ord("x"), ord("X")):
            raw[off] = ord("x") if self.task_checked else ord(" ")
            return raw.decode("utf-8", errors="replace")
        return markdown_text

    def __bool__(self) -> bool:
        return self.link is not None or self.task_offset >= 0

    def __repr__(self) -> str:
        return (
            f"MarkdownResult(link={self.link!r}, task_line={self.task_line}, "
            f"task_checked={self.task_checked}, height={self.height:g})"
        )


class CodeEditorResult:
    """Returned by ``code_editor``; unpacks as ``(text, changed)``."""

    __slots__ = (
        "text", "changed", "refused", "focused", "cursor", "anchor",
        "line", "column", "line_count", "length",
        "bracket", "bracket_match", "find_matches", "find_index",
    )

    def __init__(
        self,
        text: str,
        changed: bool = False,
        refused: bool = False,
        focused: bool = False,
        cursor: int = 0,
        anchor: int = 0,
        line: int = 1,
        column: int = 1,
        line_count: int = 1,
        length: int = 0,
        bracket: int = -1,
        bracket_match: int = -1,
        find_matches: int = 0,
        find_index: int = -1,
    ) -> None:
        self.text = text
        self.changed = bool(changed)
        self.refused = bool(refused)
        self.focused = bool(focused)
        self.cursor = int(cursor)
        self.anchor = int(anchor)
        self.line = int(line)
        self.column = int(column)
        self.line_count = int(line_count)
        self.length = int(length)
        self.bracket = int(bracket)
        self.bracket_match = int(bracket_match)
        self.find_matches = int(find_matches)
        self.find_index = int(find_index)

    def __iter__(self):
        yield self.text
        yield self.changed

    def __bool__(self) -> bool:
        return self.changed

    def __repr__(self) -> str:
        return (
            f"CodeEditorResult(changed={self.changed}, line={self.line}, column={self.column}, "
            f"line_count={self.line_count}, length={self.length})"
        )


class DiffResult:
    """Returned by ``diff_view``."""

    __slots__ = (
        "added", "removed", "changes", "current", "current_changed",
        "mode", "folds", "hidden", "recomputed", "approximate",
    )

    def __init__(
        self,
        added: int = 0,
        removed: int = 0,
        changes: int = 0,
        current: int = 0,
        current_changed: bool = False,
        mode: DiffMode = DiffMode.SPLIT,
        folds: int = 0,
        hidden: int = 0,
        recomputed: bool = False,
        approximate: bool = False,
    ) -> None:
        self.added = int(added)
        self.removed = int(removed)
        self.changes = int(changes)
        self.current = int(current)
        self.current_changed = bool(current_changed)
        self.mode = DiffMode(int(mode))
        self.folds = int(folds)
        self.hidden = int(hidden)
        self.recomputed = bool(recomputed)
        self.approximate = bool(approximate)

    def __repr__(self) -> str:
        return (
            f"DiffResult(added={self.added}, removed={self.removed}, changes={self.changes}, "
            f"current={self.current}, mode={self.mode.name})"
        )


class DiffRow:
    __slots__ = ("kind", "old_line", "new_line", "change", "hidden")

    def __init__(self, kind: DiffRowKind, old_line: int, new_line: int, change: int, hidden: int) -> None:
        self.kind = DiffRowKind(int(kind))
        self.old_line = int(old_line)
        self.new_line = int(new_line)
        self.change = int(change)
        self.hidden = int(hidden)

    def __repr__(self) -> str:
        return (
            f"DiffRow(kind={self.kind.name}, old_line={self.old_line}, "
            f"new_line={self.new_line}, change={self.change}, hidden={self.hidden})"
        )


class DiffHunk:
    __slots__ = ("old_start", "old_count", "new_start", "new_count")

    def __init__(self, old_start: int, old_count: int, new_start: int, new_count: int) -> None:
        self.old_start = int(old_start)
        self.old_count = int(old_count)
        self.new_start = int(new_start)
        self.new_count = int(new_count)

    def __repr__(self) -> str:
        return f"DiffHunk(-{self.old_start},{self.old_count} +{self.new_start},{self.new_count})"


class DiffStats:
    __slots__ = ("added", "removed", "hunks", "old_lines", "new_lines", "approximate")

    def __init__(
        self,
        added: int = 0,
        removed: int = 0,
        hunks: int = 0,
        old_lines: int = 0,
        new_lines: int = 0,
        approximate: bool = False,
    ) -> None:
        self.added = int(added)
        self.removed = int(removed)
        self.hunks = int(hunks)
        self.old_lines = int(old_lines)
        self.new_lines = int(new_lines)
        self.approximate = bool(approximate)

    def __repr__(self) -> str:
        return (
            f"DiffStats(added={self.added}, removed={self.removed}, hunks={self.hunks}, "
            f"old_lines={self.old_lines}, new_lines={self.new_lines}, approximate={self.approximate})"
        )


class DiffRange:
    __slots__ = ("start", "length")

    def __init__(self, start: int, length: int) -> None:
        self.start = int(start)
        self.length = int(length)

    def __iter__(self):
        yield self.start
        yield self.length

    def __repr__(self) -> str:
        return f"DiffRange(start={self.start}, length={self.length})"


class HexRange:
    """Colored annotation span in ``hex_view``."""

    __slots__ = ("offset", "length", "tone", "label")

    def __init__(
        self,
        offset: int,
        length: int,
        tone: Tone = Tone.NEUTRAL,
        label: Optional[str] = None,
    ) -> None:
        self.offset = int(offset)
        self.length = int(length)
        self.tone = tone
        self.label = label


class HexSelection:
    __slots__ = ("start", "length", "cursor")

    def __init__(self, start: int = 0, length: int = 0, cursor: int = 0) -> None:
        self.start = int(start)
        self.length = int(length)
        self.cursor = int(cursor)

    def __iter__(self):
        yield self.start
        yield self.length
        yield self.cursor

    def __repr__(self) -> str:
        return f"HexSelection(start={self.start}, length={self.length}, cursor={self.cursor})"


class HexResult:
    """Returned by ``hex_view``."""

    __slots__ = (
        "selection", "selection_changed", "edited",
        "edit_offset", "edit_length", "hovered", "copied",
    )

    def __init__(
        self,
        selection: HexSelection,
        selection_changed: bool = False,
        edited: bool = False,
        edit_offset: int = 0,
        edit_length: int = 0,
        hovered: int = -1,
        copied: bool = False,
    ) -> None:
        self.selection = selection
        self.selection_changed = bool(selection_changed)
        self.edited = bool(edited)
        self.edit_offset = int(edit_offset)
        self.edit_length = int(edit_length)
        self.hovered = int(hovered)
        self.copied = bool(copied)

    def __bool__(self) -> bool:
        return self.edited or self.selection_changed

    def __repr__(self) -> str:
        return (
            f"HexResult(selection={self.selection!r}, edited={self.edited}, "
            f"hovered={self.hovered}, copied={self.copied})"
        )


class FlameSpan:
    """Single profiling span in ``flame_graph``."""

    __slots__ = ("name", "start", "end", "depth", "color_key")

    def __init__(
        self,
        name: str,
        start: float,
        end: float,
        depth: int = 0,
        color_key: int = 0,
    ) -> None:
        self.name = name
        self.start = float(start)
        self.end = float(end)
        self.depth = int(depth)
        self.color_key = int(color_key) & 0xFFFFFFFF

    @property
    def duration(self) -> float:
        return self.end - self.start

    def __repr__(self) -> str:
        return f"FlameSpan({self.name!r}, start={self.start:g}, end={self.end:g}, depth={self.depth})"


class FlameView:
    __slots__ = ("start", "end", "scroll")

    def __init__(self, start: float = 0.0, end: float = 0.0, scroll: float = 0.0) -> None:
        self.start = float(start)
        self.end = float(end)
        self.scroll = float(scroll)

    def __iter__(self):
        yield self.start
        yield self.end
        yield self.scroll

    def __repr__(self) -> str:
        return f"FlameView(start={self.start:g}, end={self.end:g}, scroll={self.scroll:g})"


class FlameResult:
    """Returned by ``flame_graph``."""

    __slots__ = ("selected", "view", "selection_changed", "view_changed", "hovered", "zoomed")

    def __init__(
        self,
        selected: int = -1,
        view: Optional[FlameView] = None,
        selection_changed: bool = False,
        view_changed: bool = False,
        hovered: int = -1,
        zoomed: int = -1,
    ) -> None:
        self.selected = int(selected)
        self.view = view or FlameView()
        self.selection_changed = bool(selection_changed)
        self.view_changed = bool(view_changed)
        self.hovered = int(hovered)
        self.zoomed = int(zoomed)

    def __bool__(self) -> bool:
        return self.selection_changed or self.view_changed

    def __repr__(self) -> str:
        return (
            f"FlameResult(selected={self.selected}, hovered={self.hovered}, "
            f"zoomed={self.zoomed}, view={self.view!r})"
        )


class CurveKey:
    """Bezier/linear/step keyframe in ``curve_editor`` and ``timeline_editor``."""

    __slots__ = ("x", "y", "in_dx", "in_dy", "out_dx", "out_dy", "mode")

    def __init__(
        self,
        x: float,
        y: float,
        in_dx: float = 0.0,
        in_dy: float = 0.0,
        out_dx: float = 0.0,
        out_dy: float = 0.0,
        mode: CurveMode = CurveMode.SMOOTH,
    ) -> None:
        self.x = float(x)
        self.y = float(y)
        self.in_dx = float(in_dx)
        self.in_dy = float(in_dy)
        self.out_dx = float(out_dx)
        self.out_dy = float(out_dy)
        self.mode = CurveMode(int(mode))

    def __repr__(self) -> str:
        return f"CurveKey(x={self.x:g}, y={self.y:g}, mode={self.mode.name})"


class CurveResult:
    """Returned by ``curve_editor``; unpacks as ``(keys, changed)``."""

    __slots__ = ("keys", "changed", "added", "removed", "selected", "hovered", "hover_x", "hover_y")

    def __init__(
        self,
        keys: List[CurveKey],
        changed: bool = False,
        added: int = -1,
        removed: int = -1,
        selected: int = -1,
        hovered: bool = False,
        hover_x: float = 0.0,
        hover_y: float = 0.0,
    ) -> None:
        self.keys = keys
        self.changed = bool(changed)
        self.added = int(added)
        self.removed = int(removed)
        self.selected = int(selected)
        self.hovered = bool(hovered)
        self.hover_x = float(hover_x)
        self.hover_y = float(hover_y)

    def __iter__(self):
        yield self.keys
        yield self.changed

    def __bool__(self) -> bool:
        return self.changed

    def __repr__(self) -> str:
        return f"CurveResult(keys={len(self.keys)}, changed={self.changed}, selected={self.selected})"


class GradientStop:
    """Color stop in ``gradient_editor``."""

    __slots__ = ("pos", "color")

    def __init__(self, pos: float, color: ColorLike) -> None:
        self.pos = float(pos)
        if isinstance(color, Color):
            self.color = color
        elif isinstance(color, str):
            self.color = Color.hex(color)
        elif isinstance(color, int):
            self.color = Color.rgb(color)
        elif isinstance(color, tuple):
            self.color = Color(*color)
        elif isinstance(color, Token):
            self.color = Color.token(color)
        else:
            raise TypeError(f"Unsupported color for GradientStop: {color!r}")

    def __repr__(self) -> str:
        return f"GradientStop(pos={self.pos:g}, color={self.color!r})"


class GradientResult:
    """Returned by ``gradient_editor``; unpacks as ``(stops, changed)``."""

    __slots__ = ("stops", "changed", "added", "removed", "selected")

    def __init__(
        self,
        stops: List[GradientStop],
        changed: bool = False,
        added: int = -1,
        removed: int = -1,
        selected: int = -1,
    ) -> None:
        self.stops = stops
        self.changed = bool(changed)
        self.added = int(added)
        self.removed = int(removed)
        self.selected = int(selected)

    def __iter__(self):
        yield self.stops
        yield self.changed

    def __bool__(self) -> bool:
        return self.changed

    def __repr__(self) -> str:
        return f"GradientResult(stops={len(self.stops)}, changed={self.changed}, selected={self.selected})"


class TimelineClip:
    """Clip span on a ``TimelineTrack``."""

    __slots__ = ("start", "end", "offset", "name", "selected")

    def __init__(
        self,
        start: float,
        end: float,
        offset: float = 0.0,
        name: Optional[str] = None,
        selected: bool = False,
    ) -> None:
        self.start = float(start)
        self.end = float(end)
        self.offset = float(offset)
        self.name = name
        self.selected = bool(selected)

    def __repr__(self) -> str:
        return f"TimelineClip(name={self.name!r}, start={self.start:g}, end={self.end:g}, selected={self.selected})"


class TimelineTrack:
    """Keyframe or clip track in ``timeline_editor``."""

    __slots__ = (
        "name", "icon", "depth", "collapsed", "muted", "locked",
        "color", "keys", "key_selected", "clips",
    )

    def __init__(
        self,
        name: str,
        *,
        icon: Optional[str] = None,
        depth: int = 0,
        collapsed: bool = False,
        muted: bool = False,
        locked: bool = False,
        color: int = 0,
        keys: Optional[List[CurveKey]] = None,
        key_selected: Optional[List[bool]] = None,
        clips: Optional[List[TimelineClip]] = None,
    ) -> None:
        self.name = name
        self.icon = icon
        self.depth = int(depth)
        self.collapsed = bool(collapsed)
        self.muted = bool(muted)
        self.locked = bool(locked)
        self.color = int(color) & 0xFF
        self.keys: List[CurveKey] = list(keys) if keys is not None else []
        self.key_selected: Optional[List[bool]] = list(key_selected) if key_selected is not None else None
        self.clips: List[TimelineClip] = list(clips) if clips is not None else []

    def __repr__(self) -> str:
        return f"TimelineTrack({self.name!r}, keys={len(self.keys)}, clips={len(self.clips)})"


class TimelineView:
    __slots__ = ("start", "end", "scroll")

    def __init__(self, start: float = 0.0, end: float = 0.0, scroll: float = 0.0) -> None:
        self.start = float(start)
        self.end = float(end)
        self.scroll = float(scroll)

    def __repr__(self) -> str:
        return f"TimelineView(start={self.start:g}, end={self.end:g}, scroll={self.scroll:g})"


class TimelineEditorResult:
    """Returned by ``timeline_editor``; unpacks as ``(time, changed)``."""

    __slots__ = (
        "time", "changed", "time_changed", "scrubbing", "play_toggled",
        "selection_changed", "view_changed", "keys_moved",
        "added_track", "added_key", "removed_keys", "removed_clips",
        "clip_track", "clip", "toggled", "current_track", "current_key",
        "hovered_track", "hovered_key", "view", "in_point", "out_point",
    )

    def __init__(
        self,
        time: float,
        *,
        changed: bool = False,
        time_changed: bool = False,
        scrubbing: bool = False,
        play_toggled: bool = False,
        selection_changed: bool = False,
        view_changed: bool = False,
        keys_moved: bool = False,
        added_track: int = -1,
        added_key: int = -1,
        removed_keys: int = 0,
        removed_clips: int = 0,
        clip_track: int = -1,
        clip: int = -1,
        toggled: int = -1,
        current_track: int = -1,
        current_key: int = -1,
        hovered_track: int = -1,
        hovered_key: int = -1,
        view: Optional[TimelineView] = None,
        in_point: Optional[float] = None,
        out_point: Optional[float] = None,
    ) -> None:
        self.time = float(time)
        self.changed = bool(changed)
        self.time_changed = bool(time_changed)
        self.scrubbing = bool(scrubbing)
        self.play_toggled = bool(play_toggled)
        self.selection_changed = bool(selection_changed)
        self.view_changed = bool(view_changed)
        self.keys_moved = bool(keys_moved)
        self.added_track = int(added_track)
        self.added_key = int(added_key)
        self.removed_keys = int(removed_keys)
        self.removed_clips = int(removed_clips)
        self.clip_track = int(clip_track)
        self.clip = int(clip)
        self.toggled = int(toggled)
        self.current_track = int(current_track)
        self.current_key = int(current_key)
        self.hovered_track = int(hovered_track)
        self.hovered_key = int(hovered_key)
        self.view = view
        self.in_point = in_point
        self.out_point = out_point

    def __iter__(self):
        yield self.time
        yield self.changed

    def __bool__(self) -> bool:
        return self.changed or self.time_changed or self.play_toggled

    def __repr__(self) -> str:
        return (
            f"TimelineEditorResult(time={self.time:g}, changed={self.changed}, "
            f"play_toggled={self.play_toggled}, current_track={self.current_track})"
        )
