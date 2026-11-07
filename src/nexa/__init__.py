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
    CodeEditorResult,
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
    CurveKey,
    CurveMode,
    CurveResult,
    Date,
    DateRange,
    DiffFlags,
    DiffHunk,
    DiffMode,
    DiffRange,
    DiffResult,
    DiffRow,
    DiffRowKind,
    DiffStats,
    Direction,
    DocTab,
    DocTabsResult,
    Elevation,
    FileDialogKind,
    FilterField,
    FlameResult,
    FlameSpan,
    FlameView,
    FontRole,
    GanttTask,
    GradientResult,
    GradientStop,
    GridColumn,
    HexRange,
    HexResult,
    HexSelection,
    InputFlags,
    Justify,
    KanbanMove,
    Key,
    KeyCombo,
    LoaderStyle,
    LogLevel,
    MarkdownResult,
    Mod,
    Model,
    ModelInfo,
    MouseButton,
    NodeView,
    NowPlaying,
    PathBarResult,
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
    TimelineClip,
    TimelineEditorResult,
    TimelineRuler,
    TimelineTrack,
    TimelineView,
    TocItem,
    Token,
    Tone,
    TreeFlags,
    TreeNode,
    TreeTableEvents,
    Vec2,
    VizItem,
    VoiceState,
)
from .ui import Context, UI
from .widgets.data import diff_compute, diff_words, tree_sort
from .widgets.tools import LogBuffer, curve_eval, flame_sort, gradient_eval

__version__ = "1.1.0"

# Populate functional top-level API (`nexa.row(...)`, `nexa.button(...)`, `nexa.run(...)`, etc.)
globals().update(FUNCTIONAL_EXPORTS)

# Restore context-free C99 utilities so they work without an active UI frame too
globals().update(
    diff_compute=diff_compute,
    diff_words=diff_words,
    tree_sort=tree_sort,
    flame_sort=flame_sort,
    curve_eval=curve_eval,
    gradient_eval=gradient_eval,
)


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
