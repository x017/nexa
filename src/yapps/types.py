"""Pythonic value types, enums, flags, and data records for yapps.

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
    NEUTRAL = 0
    VIOLET = 1
    BLUE = 2
    GREEN = 3
    AMBER = 4
    ORANGE = 5
    CORAL = 6
    ROSE = 7


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
        get_cdll().yapps_date_today(out)
        return cls(out[0], out[1], out[2])

    @classmethod
    def from_days(cls, days_since_epoch: int) -> Date:
        import ctypes
        from ._lib import get_cdll
        out = (ctypes.c_int * 3)()
        get_cdll().yapps_date_from_days(int(days_since_epoch), out)
        return cls(out[0], out[1], out[2])

    def to_days(self) -> int:
        from ._lib import get_cdll
        return int(get_cdll().yapps_date_to_days(self.year, self.month, self.day))

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
    __slots__ = ("title", "width", "align", "sortable", "fixed")

    def __init__(self, title: str, width: float = 150.0, align: TextAlign = TextAlign.LEFT,
                 sortable: bool = False, fixed: bool = False) -> None:
        self.title = title
        self.width = float(width)
        self.align = align
        self.sortable = sortable
        self.fixed = fixed


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
