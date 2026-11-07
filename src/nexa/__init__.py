"""nexa — Pythonic C99-backed immediate-mode UI library (port of CUI)."""

from __future__ import annotations

from typing import Any

from ._context_var import get_current_ui, try_get_current_ui
from ._lib import get_cdll, get_library_path, locate_library
from .app import App, open_url
from .concurrent import BackgroundRunner, Channel, TaskHandle
from .functional import FUNCTIONAL_EXPORTS
from .icons import Icon
from .oop import Application, Component, Router, Store, View
from .render import (
    CustomRenderer,
    DrawCmdInfo,
    DrawData,
    GLRenderer,
    SoftwareRenderer,
    VertexInfo,
    build_features,
    native_version,
    write_png,
)
from .theme import ThemeProxy, accent_name, mix_colors, oklch, with_alpha
from .types import (
    FILL,
    FIT,
    GROW,
    PCT,
    PX,
    Accent,
    Align,
    BuildFeatures,
    ButtonVariant,
    CalEvent,
    CanvasResult,
    CheckStep,
    Choice,
    Color,
    ColorLike,
    Command,
    CommentFlags,
    ComposerFlags,
    ComposerResult,
    ControlSize,
    Corners,
    CornersLike,
    Cursor,
    Date,
    DateRange,
    Direction,
    DocTab,
    DocTabsResult,
    Elevation,
    FileDialogKind,
    FilterField,
    FontRole,
    GanttTask,
    GridColumn,
    InputFlags,
    Justify,
    KanbanMove,
    Key,
    KeyCombo,
    LoaderStyle,
    LogLevel,
    Mod,
    Model,
    ModelInfo,
    MouseButton,
    NodeView,
    NowPlaying,
    PixelFormat,
    Placement,
    PlanStep,
    PlayerFlags,
    PresenceUser,
    PromptSuggestion,
    Reaction,
    Rect,
    RendererKind,
    ResponseActionFlags,
    ResponseFlags,
    SankeyLink,
    ScatterSeries,
    Series,
    Shadow,
    ShadeMode,
    Side,
    Size,
    SizeKind,
    SizeLike,
    Source,
    SpeedAction,
    Status,
    SwipeAction,
    TabBarItem,
    TableColumn,
    TableSort,
    TabsVariant,
    TaskStatus,
    TextAlign,
    TextMetrics,
    TextureFormat,
    ThemeMode,
    TickerItem,
    TocItem,
    Token,
    Tone,
    Vec2,
    VizItem,
    VoiceState,
)
from .ui import Context, UI
from .widgets.tools import LogBuffer

__version__ = "1.0.0"

# Populate functional top-level API (`nexa.row(...)`, `nexa.button(...)`, `nexa.run(...)`, etc.)
globals().update(FUNCTIONAL_EXPORTS)


def __getattr__(name: str) -> Any:
    # Lazy imports keep `import nexa` sub-millisecond and avoid pulling `asyncio` or compiler
    # tooling into minimal frozen binaries unless explicitly used.
    if name in ("AsyncBridge", "run_app_async"):
        from . import aio
        return getattr(aio, name)
    if name == "aio":
        import importlib
        return importlib.import_module(".aio", __name__)
    if name == "build":
        import importlib
        return importlib.import_module(".build", __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
