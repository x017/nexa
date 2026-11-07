"""Low-level ctypes Structure & prototype definitions for CUI + nexa_bridge."""

from __future__ import annotations

import ctypes
from ctypes import (
    CFUNCTYPE,
    POINTER,
    Structure,
    c_bool,
    c_char,
    c_char_p,
    c_double,
    c_float,
    c_int,
    c_size_t,
    c_uint8,
    c_uint32,
    c_uint64,
    c_void_p,
)
from typing import Any, List, Optional, Sequence, Tuple

from .types import Color, ColorLike, Corners, CornersLike, Size, SizeKind, SizeLike, Token

c_texture = c_size_t  # uintptr_t


# ---------------------------------------------------------------------------
# Fundamental CUI structs
# ---------------------------------------------------------------------------

class CuiVec2(Structure):
    _fields_ = [("x", c_float), ("y", c_float)]


class CuiRect(Structure):
    _fields_ = [("x", c_float), ("y", c_float), ("w", c_float), ("h", c_float)]


class CuiCorners(Structure):
    _fields_ = [("tl", c_float), ("tr", c_float), ("br", c_float), ("bl", c_float)]


class CuiColor(Structure):
    _fields_ = [("r", c_uint8), ("g", c_uint8), ("b", c_uint8), ("a", c_uint8)]


class CuiSize(Structure):
    _fields_ = [("kind", c_int), ("value", c_float)]


class CuiShadow(Structure):
    _fields_ = [("y", c_float), ("blur", c_float), ("spread", c_float), ("alpha", c_float)]


class CuiTheme(Structure):
    _fields_ = [
        ("colors", CuiColor * 35),
        ("tone_sky", CuiColor),
        ("tone_teal", CuiColor),
        ("tone_green", CuiColor),
        ("tone_amber", CuiColor),
        ("tone_rose", CuiColor),
        ("tone_orchid", CuiColor),
        ("tone_violet", CuiColor),
        ("radius_control", c_float),
        ("radius_panel", c_float),
        ("radius_surface", c_float),
        ("control_sm", c_float),
        ("control_md", c_float),
        ("control_lg", c_float),
        ("text_xs", c_float),
        ("text_sm", c_float),
        ("text_body", c_float),
        ("text_lg", c_float),
        ("heading", c_float * 4),
        ("shadow_resting", CuiShadow * 2),
        ("shadow_raised", CuiShadow * 2),
        ("shadow_floating", CuiShadow * 2),
        ("motion", c_float),
        ("font_scale", c_float),
    ]


class CuiAppDesc(Structure):
    _fields_ = [
        ("title", c_char_p),
        ("width", c_int),
        ("height", c_int),
        ("min_width", c_int),
        ("min_height", c_int),
        ("fixed_size", c_bool),
        ("continuous", c_bool),
        ("no_vsync", c_bool),
        ("hidden", c_bool),
        ("renderer", c_int),
        ("theme", c_int),
        ("accent", c_int),
        ("follow_system_theme", c_bool),
    ]


class CuiFileDialogOpts(Structure):
    _fields_ = [
        ("kind", c_int),
        ("title", c_char_p),
        ("filter_name", c_char_p),
        ("filter", c_char_p),
        ("default_name", c_char_p),
    ]


class CuiVertex(Structure):
    _fields_ = [
        ("x", c_float), ("y", c_float),
        ("u", c_float), ("v", c_float),
        ("lx", c_float), ("ly", c_float),
        ("hw", c_float), ("hh", c_float),
        ("r_tl", c_float), ("r_tr", c_float), ("r_br", c_float), ("r_bl", c_float),
        ("border", c_float),
        ("mode", c_float),
        ("color", CuiColor),
        ("border_color", CuiColor),
    ]


class CuiDrawCmd(Structure):
    _fields_ = [
        ("clip", CuiRect),
        ("texture", c_texture),
        ("index_offset", c_uint32),
        ("index_count", c_uint32),
    ]


class CuiDrawData(Structure):
    _fields_ = [
        ("vertices", POINTER(CuiVertex)),
        ("vertex_count", c_int),
        ("indices", POINTER(c_uint32)),
        ("index_count", c_int),
        ("commands", POINTER(CuiDrawCmd)),
        ("command_count", c_int),
        ("width_px", c_int),
        ("height_px", c_int),
        ("clear_color", CuiColor),
        ("font_atlas", c_texture),
    ]


# ---------------------------------------------------------------------------
# Layout & Widget Option / Item Structs
# ---------------------------------------------------------------------------

class CuiBox(Structure):
    _fields_ = [
        ("_", c_int),
        ("id", c_char_p),
        ("dir", c_int),
        ("width", CuiSize),
        ("height", CuiSize),
        ("min_width", c_float),
        ("max_width", c_float),
        ("min_height", c_float),
        ("max_height", c_float),
        ("pad", c_float),
        ("pad_x", c_float),
        ("pad_y", c_float),
        ("pad_top", c_float),
        ("pad_right", c_float),
        ("pad_bottom", c_float),
        ("pad_left", c_float),
        ("gap", c_float),
        ("columns", c_int),
        ("min_column_width", c_float),
        ("wrap", c_bool),
        ("align", c_int),
        ("justify", c_int),
        ("bg", CuiColor),
        ("border_color", CuiColor),
        ("border", c_float),
        ("radius", c_float),
        ("radius_tl", c_float),
        ("radius_tr", c_float),
        ("radius_br", c_float),
        ("radius_bl", c_float),
        ("elevation", c_int),
        ("scroll_x", c_bool),
        ("scroll_y", c_bool),
        ("clip", c_bool),
        ("opacity", c_float),
    ]


class CuiCardOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("id", c_char_p),
        ("width", CuiSize),
        ("height", CuiSize),
        ("min_width", c_float),
        ("max_width", c_float),
        ("pad", c_float),
        ("pad_x", c_float),
        ("pad_y", c_float),
        ("gap", c_float),
        ("dir", c_int),
        ("align", c_int),
        ("wrap", c_bool),
        ("hoverable", c_bool),
        ("muted", c_bool),
        ("selected", c_bool),
    ]


class CuiScrollOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("id", c_char_p),
        ("width", CuiSize),
        ("height", CuiSize),
        ("horizontal", c_bool),
        ("pad", c_float),
        ("gap", c_float),
        ("fade_edges", c_bool),
        ("fade_color", CuiColor),
    ]


class CuiSplitOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("vertical", c_bool),
        ("min_first", c_float),
        ("min_second", c_float),
        ("width", CuiSize),
        ("height", CuiSize),
    ]


class CuiTextOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("font", c_int),
        ("size", c_float),
        ("color", CuiColor),
        ("align", c_int),
        ("nowrap", c_bool),
        ("tabular", c_bool),
        ("selectable", c_bool),
        ("width", CuiSize),
        ("line_height", c_float),
    ]


class CuiButtonOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("variant", c_int),
        ("size", c_int),
        ("icon", c_char_p),
        ("icon_right", c_char_p),
        ("disabled", c_bool),
        ("loading", c_bool),
        ("full_width", c_bool),
        ("selected", c_bool),
        ("tooltip", c_char_p),
        ("shortcut", c_char_p),
        ("width", CuiSize),
        ("color", CuiColor),
    ]


class CuiSegmentedOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("size", c_int),
        ("full_width", c_bool),
        ("icons", POINTER(c_char_p)),
    ]


class CuiCheckOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("description", c_char_p),
        ("disabled", c_bool),
        ("indeterminate", c_bool),
    ]


class CuiSliderOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("step", c_float),
        ("show_value", c_bool),
        ("format", c_char_p),
        ("disabled", c_bool),
        ("width", CuiSize),
    ]


class CuiChipOpts(Structure):
    _fields_ = [("_", c_int), ("icon", c_char_p), ("disabled", c_bool)]


class CuiInputOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("label", c_char_p),
        ("placeholder", c_char_p),
        ("icon", c_char_p),
        ("hint", c_char_p),
        ("error", c_char_p),
        ("password", c_bool),
        ("disabled", c_bool),
        ("clearable", c_bool),
        ("autofocus", c_bool),
        ("read_only", c_bool),
        ("size", c_int),
        ("width", CuiSize),
        ("height", c_float),
        ("prefix", c_char_p),
        ("suffix", c_char_p),
    ]


class CuiNumberOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("label", c_char_p),
        ("step", c_double),
        ("decimals", c_int),
        ("disabled", c_bool),
        ("width", CuiSize),
        ("suffix", c_char_p),
    ]


class CuiSelectOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("label", c_char_p),
        ("placeholder", c_char_p),
        ("icons", POINTER(c_char_p)),
        ("searchable", c_bool),
        ("disabled", c_bool),
        ("width", CuiSize),
    ]


class CuiDate(Structure):
    _fields_ = [("year", c_int), ("month", c_int), ("day", c_int)]


class CuiDateOpts(Structure):
    _fields_ = [("_", c_int), ("label", c_char_p), ("placeholder", c_char_p), ("width", CuiSize)]


class CuiDateRange(Structure):
    _fields_ = [("start", CuiDate), ("end", CuiDate)]


class CuiDateRangeOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("label", c_char_p),
        ("placeholder", c_char_p),
        ("width", CuiSize),
        ("no_presets", c_bool),
    ]


class CuiTabsOpts(Structure):
    _fields_ = [("_", c_int), ("variant", c_int), ("icons", POINTER(c_char_p)), ("full_width", c_bool)]


class CuiNavOpts(Structure):
    _fields_ = [("_", c_int), ("icon", c_char_p), ("badge", c_char_p), ("selected", c_bool), ("group", c_char_p)]


class CuiPopoverOpts(Structure):
    _fields_ = [("_", c_int), ("placement", c_int), ("width", c_float), ("pad", c_float), ("gap", c_float)]


class CuiMenuOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("icon", c_char_p),
        ("variant", c_int),
        ("placement", c_int),
        ("width", c_float),
        ("icon_only", c_bool),
    ]


class CuiMenuItemOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("icon", c_char_p),
        ("shortcut", c_char_p),
        ("danger", c_bool),
        ("disabled", c_bool),
        ("checked", c_bool),
    ]


class CuiDialogOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("description", c_char_p),
        ("width", c_float),
        ("no_close_button", c_bool),
        ("persistent", c_bool),
    ]


class CuiSheetOpts(Structure):
    _fields_ = [("_", c_int), ("side", c_int), ("size", c_float), ("description", c_char_p)]


class CuiToastOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("description", c_char_p),
        ("tone", c_int),
        ("duration", c_float),
        ("action", c_char_p),
        ("show_timer", c_bool),
    ]


class CuiAlertOpts(Structure):
    _fields_ = [("_", c_int), ("description", c_char_p), ("tone", c_int), ("icon", c_char_p), ("dismissible", c_bool)]


class CuiProgressOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("indeterminate", c_bool),
        ("tone", c_int),
        ("height", c_float),
        ("label", c_char_p),
        ("show_value", c_bool),
        ("width", CuiSize),
    ]


class CuiBadgeOpts(Structure):
    _fields_ = [("_", c_int), ("tone", c_int), ("dot", c_bool), ("solid", c_bool), ("icon", c_char_p), ("size", c_int)]


class CuiAvatarOpts(Structure):
    _fields_ = [("_", c_int), ("size", c_float), ("image", c_texture), ("status", c_char_p), ("square", c_bool)]


class CuiEmptyOpts(Structure):
    _fields_ = [("_", c_int), ("icon", c_char_p), ("description", c_char_p), ("action", c_char_p)]


class CuiMetricOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("delta", c_float),
        ("delta_label", c_char_p),
        ("spark", POINTER(c_float)),
        ("spark_count", c_int),
        ("icon", c_char_p),
        ("width", CuiSize),
        ("lower_is_better", c_bool),
    ]


class CuiTreeOpts(Structure):
    _fields_ = [("_", c_int), ("icon", c_char_p), ("leaf", c_bool), ("selected", c_bool)]


class CuiListItemOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("icon", c_char_p),
        ("subtitle", c_char_p),
        ("trailing", c_char_p),
        ("selected", c_bool),
        ("avatar", c_char_p),
    ]


class CuiTableColumn(Structure):
    _fields_ = [("title", c_char_p), ("width", CuiSize), ("align", c_int), ("sortable", c_bool)]


class CuiTableSort(Structure):
    _fields_ = [("column", c_int), ("descending", c_bool)]


class CuiTableOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("sort", POINTER(CuiTableSort)),
        ("height", CuiSize),
        ("striped", c_bool),
        ("compact", c_bool),
        ("selectable", c_bool),
    ]


class CuiSeries(Structure):
    _fields_ = [("name", c_char_p), ("values", POINTER(c_float)), ("count", c_int), ("color", CuiColor)]


class CuiChartOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("width", CuiSize),
        ("height", c_float),
        ("labels", POINTER(c_char_p)),
        ("label_count", c_int),
        ("area", c_bool),
        ("no_grid", c_bool),
        ("no_legend", c_bool),
        ("stacked", c_bool),
        ("smooth", c_bool),
        ("format", c_char_p),
        ("min", c_float),
        ("max", c_float),
    ]


class CuiImageOpts(Structure):
    _fields_ = [("_", c_int), ("width", CuiSize), ("height", CuiSize), ("radius", c_float), ("tint", CuiColor)]


class CuiCommand(Structure):
    _fields_ = [("title", c_char_p), ("icon", c_char_p), ("group", c_char_p), ("shortcut", c_char_p)]


class CuiChoice(Structure):
    _fields_ = [("title", c_char_p), ("description", c_char_p), ("icon", c_char_p), ("badge", c_char_p)]


class CuiRadioCardsOpts(Structure):
    _fields_ = [("_", c_int), ("columns", c_int)]


class CuiTagOpts(Structure):
    _fields_ = [("_", c_int), ("label", c_char_p), ("placeholder", c_char_p), ("max_tags", c_int), ("width", CuiSize)]


class CuiHoldOpts(Structure):
    _fields_ = [("_", c_int), ("duration", c_float), ("icon", c_char_p), ("variant", c_int)]


class CuiTimelineOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("time", c_char_p),
        ("description", c_char_p),
        ("icon", c_char_p),
        ("tone", c_int),
        ("last", c_bool),
    ]


class CuiSplitButtonOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("variant", c_int),
        ("size", c_int),
        ("icon", c_char_p),
        ("item_icons", POINTER(c_char_p)),
        ("disabled", c_bool),
    ]


class CuiToggleGroupOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("icons", POINTER(c_char_p)),
        ("exclusive", c_bool),
        ("icon_only", c_bool),
        ("size", c_int),
    ]


class CuiConfirmOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("confirm_label", c_char_p),
        ("icon", c_char_p),
        ("variant", c_int),
        ("size", c_int),
        ("timeout", c_float),
    ]


class CuiStatusButtonOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("busy_label", c_char_p),
        ("success_label", c_char_p),
        ("error_label", c_char_p),
        ("icon", c_char_p),
        ("variant", c_int),
        ("size", c_int),
    ]


class CuiReaction(Structure):
    _fields_ = [("icon", c_char_p), ("count", c_int), ("active", c_bool)]


class CuiSpeedAction(Structure):
    _fields_ = [("icon", c_char_p), ("label", c_char_p)]


class CuiSpeedDialOpts(Structure):
    _fields_ = [("_", c_int), ("icon", c_char_p), ("placement", c_int), ("tooltip", c_char_p)]


class CuiUserMenuOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("detail", c_char_p),
        ("status", c_char_p),
        ("avatar", c_texture),
        ("compact", c_bool),
        ("placement", c_int),
        ("width", c_float),
    ]


class CuiSwipeAction(Structure):
    _fields_ = [("icon", c_char_p), ("label", c_char_p), ("tone", c_int)]


class CuiGridColumn(Structure):
    _fields_ = [("title", c_char_p), ("width", c_float), ("align", c_int), ("sortable", c_bool), ("fixed", c_bool)]


class CuiGridOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("width", CuiSize),
        ("height", CuiSize),
        ("row_height", c_float),
        ("selected", POINTER(c_bool)),
        ("sort", POINTER(CuiTableSort)),
        ("striped", c_bool),
        ("cursor", POINTER(c_int)),
    ]


class CuiFilterField(Structure):
    _fields_ = [("name", c_char_p), ("icon", c_char_p), ("options", POINTER(c_char_p)), ("option_count", c_int)]


class CuiCodeOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("lang", c_char_p),
        ("title", c_char_p),
        ("line_numbers", c_bool),
        ("highlight_from", c_int),
        ("highlight_to", c_int),
        ("max_height", c_float),
        ("size", c_float),
        ("no_header", c_bool),
    ]


class CuiJsonOpts(Structure):
    _fields_ = [("_", c_int), ("expand_depth", c_int), ("max_height", c_float)]


class CuiChatOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("mine", c_bool),
        ("author", c_char_p),
        ("time", c_char_p),
        ("status", c_char_p),
        ("grouped", c_bool),
        ("last_in_group", c_bool),
        ("avatar", c_texture),
    ]


class CuiCommentOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("time", c_char_p),
        ("depth", c_int),
        ("likes", POINTER(c_int)),
        ("liked", POINTER(c_bool)),
        ("edited", c_bool),
        ("badge", c_char_p),
    ]


class CuiPresenceUser(Structure):
    _fields_ = [("name", c_char_p), ("color", CuiColor), ("avatar", c_texture), ("idle", c_bool)]


class CuiCarouselOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("height", c_float),
        ("auto_advance", c_float),
        ("gap", c_float),
        ("no_arrows", c_bool),
        ("no_dots", c_bool),
        ("loop", c_bool),
    ]


class CuiCompareOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("width", CuiSize),
        ("height", c_float),
        ("before_label", c_char_p),
        ("after_label", c_char_p),
        ("aspect", c_float),
    ]


class CuiCardStackOpts(Structure):
    _fields_ = [("_", c_int), ("width", CuiSize), ("height", c_float), ("visible", c_int)]


class CuiCounterOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("format", c_char_p),
        ("size", c_float),
        ("font", c_int),
        ("color", CuiColor),
        ("group_thousands", c_bool),
    ]


class CuiTickerItem(Structure):
    _fields_ = [("label", c_char_p), ("value", c_char_p), ("delta", c_float), ("lower_is_better", c_bool)]


class CuiTickerOpts(Structure):
    _fields_ = [("_", c_int), ("speed", c_float), ("height", c_float)]


class CuiHeatmapOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("row_labels", POINTER(c_char_p)),
        ("col_labels", POINTER(c_char_p)),
        ("cell", c_float),
        ("min", c_float),
        ("max", c_float),
        ("color", CuiColor),
        ("format", c_char_p),
        ("width", CuiSize),
    ]


class CuiCalendarHeatmapOpts(Structure):
    _fields_ = [("_", c_int), ("cell", c_float), ("color", CuiColor), ("format", c_char_p), ("unit", c_char_p)]


class CuiVizItem(Structure):
    _fields_ = [("label", c_char_p), ("value", c_float), ("color", CuiColor)]


class CuiTreemapOpts(Structure):
    _fields_ = [("_", c_int), ("width", CuiSize), ("height", c_float), ("format", c_char_p)]


class CuiRadarOpts(Structure):
    _fields_ = [("_", c_int), ("size", c_float), ("max", c_float), ("format", c_char_p), ("no_legend", c_bool)]


class CuiFunnelOpts(Structure):
    _fields_ = [("_", c_int), ("width", CuiSize), ("height", c_float), ("format", c_char_p), ("color", CuiColor)]


class CuiSankeyLink(Structure):
    _fields_ = [("from_", c_int), ("to", c_int), ("value", c_float)]


class CuiSankeyOpts(Structure):
    _fields_ = [("_", c_int), ("width", CuiSize), ("height", c_float), ("format", c_char_p), ("node_width", c_float)]


class CuiWaffleOpts(Structure):
    _fields_ = [("_", c_int), ("cell", c_float), ("columns", c_int), ("rows", c_int), ("format", c_char_p)]


class CuiSplitBarOpts(Structure):
    _fields_ = [("_", c_int), ("width", CuiSize), ("height", c_float), ("format", c_char_p), ("no_legend", c_bool)]


class CuiBarListOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("width", CuiSize),
        ("format", c_char_p),
        ("max_rows", c_int),
        ("keep_order", c_bool),
        ("color", CuiColor),
    ]


class CuiRingsOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("size", c_float),
        ("thickness", c_float),
        ("center", c_char_p),
        ("caption", c_char_p),
        ("legend", c_bool),
    ]


class CuiScatterSeries(Structure):
    _fields_ = [
        ("name", c_char_p),
        ("points", POINTER(CuiVec2)),
        ("sizes", POINTER(c_float)),
        ("count", c_int),
        ("color", CuiColor),
    ]


class CuiScatterOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("width", CuiSize),
        ("height", c_float),
        ("x_label", c_char_p),
        ("y_label", c_char_p),
        ("x_format", c_char_p),
        ("y_format", c_char_p),
        ("no_legend", c_bool),
    ]


class CuiTextFxOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("font", c_int),
        ("size", c_float),
        ("color", CuiColor),
        ("width", CuiSize),
        ("nowrap", c_bool),
        ("speed", c_float),
        ("delay", c_float),
        ("caret", c_bool),
    ]


class CuiGradientTextOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("font", c_int),
        ("size", c_float),
        ("from_", CuiColor),
        ("to", CuiColor),
        ("animate", c_bool),
        ("width", CuiSize),
    ]


class CuiSpotlightOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("width", CuiSize),
        ("height", CuiSize),
        ("pad", c_float),
        ("gap", c_float),
        ("color", CuiColor),
        ("beam", c_bool),
    ]


class CuiLoaderOpts(Structure):
    _fields_ = [("_", c_int), ("style", c_int), ("size", c_float), ("color", CuiColor)]


class CuiDockOpts(Structure):
    _fields_ = [("_", c_int), ("size", c_float), ("magnify", c_float)]


class CuiDockItemOpts(Structure):
    _fields_ = [("_", c_int), ("color", CuiColor), ("running", c_bool), ("badge", c_int)]


class CuiTabBarItem(Structure):
    _fields_ = [("icon", c_char_p), ("label", c_char_p), ("badge", c_int)]


class CuiTabBarOpts(Structure):
    _fields_ = [("_", c_int), ("width", CuiSize), ("labels_on_selected_only", c_bool)]


class CuiTileOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("icon", c_char_p),
        ("detail", c_char_p),
        ("color", CuiColor),
        ("width", CuiSize),
        ("wide", c_bool),
    ]


class CuiWaveformOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("width", CuiSize),
        ("height", c_float),
        ("bar", c_float),
        ("gap", c_float),
        ("color", CuiColor),
    ]


class CuiNowPlaying(Structure):
    _fields_ = [
        ("title", c_char_p),
        ("artist", c_char_p),
        ("art", c_texture),
        ("art_color", CuiColor),
        ("position", c_float),
        ("duration", c_float),
        ("playing", c_bool),
    ]


class CuiNowPlayingOpts(Structure):
    _fields_ = [("_", c_int), ("width", CuiSize), ("compact", c_bool)]


class CuiReasoningOpts(Structure):
    _fields_ = [("_", c_int), ("thinking", c_bool), ("seconds", c_float), ("title", c_char_p)]


class CuiToolCallOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("status", c_int),
        ("icon", c_char_p),
        ("detail", c_char_p),
        ("input", c_char_p),
        ("output", c_char_p),
        ("seconds", c_float),
    ]


class CuiPlanStep(Structure):
    _fields_ = [("title", c_char_p), ("detail", c_char_p), ("status", c_int)]


class CuiAgentPlanOpts(Structure):
    _fields_ = [("_", c_int), ("title", c_char_p)]


class CuiAgentStatusOpts(Structure):
    _fields_ = [("_", c_int), ("status", c_int), ("seconds", c_float), ("icon", c_char_p)]


class CuiSource(Structure):
    _fields_ = [("title", c_char_p), ("url", c_char_p), ("snippet", c_char_p)]


class CuiContextOpts(Structure):
    _fields_ = [("_", c_int), ("parts", POINTER(CuiVizItem)), ("part_count", c_int), ("unit", c_char_p)]


class CuiResponseActionsOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("copy_text", c_char_p),
        ("vote", POINTER(c_int)),
        ("no_regenerate", c_bool),
        ("no_share", c_bool),
    ]


class CuiPromptSuggestion(Structure):
    _fields_ = [("icon", c_char_p), ("title", c_char_p), ("detail", c_char_p)]


class CuiPromptSuggestionsOpts(Structure):
    _fields_ = [("_", c_int), ("columns", c_int)]


class CuiModel(Structure):
    _fields_ = [("name", c_char_p), ("detail", c_char_p), ("badge", c_char_p), ("icon", c_char_p)]


class CuiModelPickerOpts(Structure):
    _fields_ = [("_", c_int), ("ghost", c_bool), ("placement", c_int)]


class CuiComposerOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("placeholder", c_char_p),
        ("busy", c_bool),
        ("attachments", POINTER(c_char_p)),
        ("attachment_count", c_int),
        ("removed", POINTER(c_int)),
        ("models", POINTER(CuiModel)),
        ("model_count", c_int),
        ("model", POINTER(c_int)),
        ("max_lines", c_int),
        ("width", CuiSize),
    ]


class CuiVoiceOrbOpts(Structure):
    _fields_ = [("_", c_int), ("size", c_float), ("color", CuiColor)]


class CuiKanbanMove(Structure):
    _fields_ = [("card", c_int), ("from_column", c_int), ("to_column", c_int), ("to_index", c_int)]


class CuiKanbanColumnOpts(Structure):
    _fields_ = [("_", c_int), ("dot", CuiColor), ("limit", c_int), ("width", c_float)]


class CuiCalEvent(Structure):
    _fields_ = [
        ("title", c_char_p),
        ("detail", c_char_p),
        ("day", c_int),
        ("start", c_float),
        ("end", c_float),
        ("tone", c_int),
    ]


class CuiWeekOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("start_hour", c_float),
        ("end_hour", c_float),
        ("hour_height", c_float),
        ("height", CuiSize),
        ("read_only", c_bool),
    ]


class CuiGanttTask(Structure):
    _fields_ = [
        ("name", c_char_p),
        ("owner", c_char_p),
        ("start", c_int),
        ("end", c_int),
        ("progress", c_float),
        ("tone", c_int),
        ("depends_on", c_int),
        ("milestone", c_bool),
    ]


class CuiGanttOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("day_width", c_float),
        ("row_height", c_float),
        ("height", CuiSize),
        ("today", c_int),
        ("read_only", c_bool),
    ]


class CuiHoverCardOpts(Structure):
    _fields_ = [("_", c_int), ("placement", c_int), ("width", c_float), ("delay", c_float)]


class CuiConfirmPopoverOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("title", c_char_p),
        ("description", c_char_p),
        ("confirm_label", c_char_p),
        ("cancel_label", c_char_p),
        ("danger", c_bool),
        ("placement", c_int),
    ]


class CuiExpandableTextOpts(Structure):
    _fields_ = [("_", c_int), ("lines", c_int), ("size", c_float), ("color", CuiColor), ("fade_to", CuiColor)]


class CuiExpandableCardOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("description", c_char_p),
        ("icon", c_char_p),
        ("badge", c_char_p),
        ("badge_tone", c_int),
    ]


class CuiTocItem(Structure):
    _fields_ = [("title", c_char_p), ("anchor", c_char_p), ("level", c_int)]


class CuiBannerOpts(Structure):
    _fields_ = [("_", c_int), ("tone", c_int), ("icon", c_char_p), ("action", c_char_p), ("dismissible", c_bool)]


class CuiCountdownOpts(Structure):
    _fields_ = [("_", c_int), ("hide_days", c_bool), ("compact", c_bool)]


class CuiCheckStep(Structure):
    _fields_ = [("title", c_char_p), ("description", c_char_p), ("action", c_char_p), ("done", c_bool)]


class CuiChecklistOpts(Structure):
    _fields_ = [("_", c_int), ("title", c_char_p), ("description", c_char_p)]


class CuiMultiSelectOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("label", c_char_p),
        ("placeholder", c_char_p),
        ("icons", POINTER(c_char_p)),
        ("searchable", c_bool),
        ("max_chips", c_int),
        ("width", CuiSize),
    ]


class CuiTimeOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("label", c_char_p),
        ("twelve_hour", c_bool),
        ("minute_step", c_int),
        ("width", CuiSize),
    ]


class CuiWheelOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("rows", c_int),
        ("width", CuiSize),
        ("loop", c_bool),
        ("join_left", c_bool),
        ("join_right", c_bool),
    ]


class CuiRulerOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("step", c_float),
        ("major_every", c_int),
        ("spacing", c_float),
        ("format", c_char_p),
        ("unit", c_char_p),
        ("width", CuiSize),
    ]


class CuiHistogramOpts(Structure):
    _fields_ = [("_", c_int), ("height", c_float), ("format", c_char_p)]


class CuiSignatureOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("width", CuiSize),
        ("height", c_float),
        ("placeholder", c_char_p),
        ("ink", CuiColor),
    ]


class CuiDropzoneOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("title", c_char_p),
        ("description", c_char_p),
        ("icon", c_char_p),
        ("accept", c_char_p),
        ("height", c_float),
        ("width", CuiSize),
        ("compact", c_bool),
    ]


class CuiInlineEditOpts(Structure):
    _fields_ = [("_", c_int), ("font", c_int), ("size", c_float), ("placeholder", c_char_p), ("width", CuiSize)]


class CuiScrubOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("step", c_float),
        ("format", c_char_p),
        ("suffix", c_char_p),
        ("icon", c_char_p),
        ("width", CuiSize),
    ]


class CuiMoneyOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("label", c_char_p),
        ("symbol", c_char_p),
        ("code", c_char_p),
        ("decimals", c_int),
        ("width", CuiSize),
        ("hint", c_char_p),
    ]


class CuiKeyCombo(Structure):
    _fields_ = [("mods", c_int), ("key", c_int)]


class CuiShortcutRecorderOpts(Structure):
    _fields_ = [("_", c_int), ("placeholder", c_char_p), ("width", CuiSize)]


class CuiNodeView(Structure):
    _fields_ = [("x", c_float), ("y", c_float), ("zoom", c_float)]


class CuiNodeEditorOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("width", CuiSize),
        ("height", CuiSize),
        ("min_zoom", c_float),
        ("max_zoom", c_float),
        ("no_grid", c_bool),
        ("minimap", c_bool),
    ]


class CuiNodeOpts(Structure):
    _fields_ = [("_", c_int), ("width", c_float), ("icon", c_char_p)]


class CuiPinOpts(Structure):
    _fields_ = [("_", c_int), ("type", c_int)]


class CuiMenuBarOpts(Structure):
    _fields_ = [("_", c_int), ("no_border", c_bool)]


class CuiMenuBarMenuOpts(Structure):
    _fields_ = [("_", c_int), ("mnemonic", c_char), ("width", c_float), ("disabled", c_bool)]


class CuiToolbarOpts(Structure):
    _fields_ = [("_", c_int), ("no_border", c_bool)]


class CuiToolOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("label", c_char_p),
        ("tooltip", c_char_p),
        ("shortcut", c_char_p),
        ("toggle", POINTER(c_bool)),
        ("disabled", c_bool),
    ]


class CuiStatusBarOpts(Structure):
    _fields_ = [("_", c_int), ("no_border", c_bool)]


class CuiStatusItemOpts(Structure):
    _fields_ = [("_", c_int), ("icon", c_char_p), ("tone", c_int), ("tooltip", c_char_p), ("disabled", c_bool)]


class CuiStatusProgressOpts(Structure):
    _fields_ = [("_", c_int), ("label", c_char_p), ("indeterminate", c_bool), ("width", c_float)]


class CuiDocTab(Structure):
    _fields_ = [("title", c_char_p), ("icon", c_char_p), ("tooltip", c_char_p), ("dirty", c_bool)]


class CuiDocTabsOpts(Structure):
    _fields_ = [("_", c_int), ("shortcuts", c_bool), ("no_close", c_bool), ("no_reorder", c_bool)]


class CuiInspectorOpts(Structure):
    _fields_ = [("_", c_int), ("width", CuiSize), ("label_width", c_float)]


class CuiPropOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("min", c_float),
        ("max", c_float),
        ("step", c_float),
        ("format", c_char_p),
        ("suffix", c_char_p),
        ("placeholder", c_char_p),
        ("tooltip", c_char_p),
        ("disabled", c_bool),
        ("checkbox", c_bool),
    ]


class CuiLogViewOpts(Structure):
    _fields_ = [
        ("_", c_int),
        ("width", CuiSize),
        ("height", c_float),
        ("timestamps", c_bool),
        ("no_toolbar", c_bool),
        ("size", c_float),
    ]


# ---------------------------------------------------------------------------
# Callback Function Pointer Types
# ---------------------------------------------------------------------------

GlLoaderFn = CFUNCTYPE(c_void_p, c_char_p)
TexCreateFn = CFUNCTYPE(c_texture, c_void_p, c_int, c_int, c_int, c_void_p)
TexUpdateFn = CFUNCTYPE(None, c_void_p, c_texture, c_int, c_int, c_int, c_int, c_void_p, c_int)
TexDestroyFn = CFUNCTYPE(None, c_void_p, c_texture)

PlatSetClipFn = CFUNCTYPE(None, c_void_p, c_char_p)
PlatGetClipFn = CFUNCTYPE(c_char_p, c_void_p)
PlatSetCursorFn = CFUNCTYPE(None, c_void_p, c_int)
PlatSetImeFn = CFUNCTYPE(None, c_void_p, c_float, c_float, c_float, c_float)

CanvasTrampFn = CFUNCTYPE(None, c_void_p, c_float, c_float, c_float, c_float, c_size_t)
AppFrameFn = CFUNCTYPE(None, c_void_p, c_void_p)


# ---------------------------------------------------------------------------
# Fast Conversion Helpers (used by widget modules)
# ---------------------------------------------------------------------------

def to_c_color(c: ColorLike) -> CuiColor:
    if c is None:
        return CuiColor(0, 0, 0, 0)
    if isinstance(c, Color):
        return CuiColor(c.r, c.g, c.b, c.a)
    if isinstance(c, Token):
        return CuiColor(int(c), 0xC5, 0x1D, 0)
    if isinstance(c, int):
        return CuiColor((c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF, 255)
    if isinstance(c, str):
        col = Color.hex(c)
        return CuiColor(col.r, col.g, col.b, col.a)
    if isinstance(c, tuple):
        if len(c) == 3:
            return CuiColor(int(c[0]) & 0xFF, int(c[1]) & 0xFF, int(c[2]) & 0xFF, 255)
        if len(c) == 4:
            return CuiColor(int(c[0]) & 0xFF, int(c[1]) & 0xFF, int(c[2]) & 0xFF, int(c[3]) & 0xFF)
    raise TypeError(f"Unsupported color value: {c!r}")


def to_packed_color(c: ColorLike) -> int:
    if c is None:
        return 0
    if isinstance(c, Color):
        return c._packed()
    cc = to_c_color(c)
    return cc.r | (cc.g << 8) | (cc.b << 16) | (cc.a << 24)


def to_c_size(s: SizeLike) -> CuiSize:
    if s is None:
        return CuiSize(0, 0.0)
    if isinstance(s, Size):
        return CuiSize(int(s.kind), s.value)
    if isinstance(s, (int, float)):
        return CuiSize(int(SizeKind.FIXED), float(s))
    raise TypeError(f"Unsupported size value: {s!r}")


def to_size_pair(s: SizeLike) -> Tuple[int, float]:
    if s is None:
        return 0, 0.0
    if isinstance(s, Size):
        return int(s.kind), s.value
    if isinstance(s, (int, float)):
        return int(SizeKind.FIXED), float(s)
    raise TypeError(f"Unsupported size value: {s!r}")


def to_corners_4(c: CornersLike) -> Tuple[float, float, float, float]:
    if isinstance(c, Corners):
        return c.tl, c.tr, c.br, c.bl
    if isinstance(c, (int, float)):
        v = float(c)
        return v, v, v, v
    if isinstance(c, tuple) and len(c) == 4:
        return float(c[0]), float(c[1]), float(c[2]), float(c[3])
    raise TypeError(f"Unsupported corners value: {c!r}")


def to_c_corners(c: CornersLike) -> CuiCorners:
    tl, tr, br, bl = to_corners_4(c)
    return CuiCorners(tl, tr, br, bl)


def to_c_date(d: Date) -> CuiDate:
    return CuiDate(int(d.year), int(d.month), int(d.day))


def to_c_date_range(dr: DateRange) -> CuiDateRange:
    return CuiDateRange(to_c_date(dr.start), to_c_date(dr.end))


def encode_opt(s: Optional[str], keep: List[Any]) -> Optional[bytes]:
    if s is None:
        return None
    b = s.encode("utf-8")
    keep.append(b)
    return b


def encode_str(s: str, keep: List[Any]) -> bytes:
    b = s.encode("utf-8")
    keep.append(b)
    return b


def encode_str_array(items: Optional[Sequence[Optional[str]]], keep: List[Any]):
    if not items:
        return None, 0
    n = len(items)
    arr = (c_char_p * n)()
    for i, item in enumerate(items):
        if item is not None:
            b = item.encode("utf-8")
            keep.append(b)
            arr[i] = b
        else:
            arr[i] = None
    keep.append(arr)
    return arr, n


def make_text_buffer(value: str, min_cap: int = 256) -> Tuple[Any, int]:
    raw = value.encode("utf-8")
    cap = max(min_cap, len(raw) * 2 + 64)
    buf = ctypes.create_string_buffer(raw, cap)
    return buf, cap


# ---------------------------------------------------------------------------
# Prototype Binding Table
# ---------------------------------------------------------------------------

def bind_prototypes(lib: ctypes.CDLL) -> None:
    """Bind argtypes & restypes once when ``libnexa_cui`` is loaded."""
    P = POINTER

    sigs = [
        # Bridge helpers
        ("nexa_version", [], c_char_p),
        ("nexa_features", [], c_uint32),
        ("nexa_ctx_create", [c_int, c_int, c_bool, c_void_p, c_void_p], c_void_p),
        ("nexa_ctx_set_sw_renderer", [c_void_p, c_void_p], None),
        ("nexa_ctx_set_gl_renderer", [c_void_p, c_void_p], None),
        ("nexa_ctx_set_custom_renderer", [c_void_p, c_void_p, c_void_p, c_void_p, c_void_p], None),
        ("nexa_set_platform", [c_void_p, c_void_p, c_void_p, c_void_p, c_void_p, c_void_p], c_void_p),
        ("nexa_free_platform", [c_void_p, c_void_p], None),
        ("nexa_viewport_size", [c_void_p, P(c_float), P(c_float)], None),
        ("nexa_app_size", [c_void_p, P(c_float), P(c_float)], None),
        ("nexa_mouse_pos", [c_void_p, P(c_float), P(c_float)], None),
        ("nexa_last_rect", [c_void_p, P(c_float)], None),
        ("nexa_get_rect", [c_void_p, c_uint32, P(c_float)], None),
        ("nexa_measure_text", [c_void_p, c_int, c_float, c_char_p, c_int, P(c_float)], None),
        ("nexa_color_of", [c_void_p, c_uint32], c_uint32),
        ("nexa_token_color", [c_void_p, c_int], c_uint32),
        ("nexa_oklch", [c_float, c_float, c_float, c_float], c_uint32),
        ("nexa_mix", [c_uint32, c_uint32, c_float], c_uint32),
        ("nexa_alpha", [c_uint32, c_float], c_uint32),
        ("nexa_color_picker", [c_void_p, c_char_p, P(c_uint32)], c_bool),
        ("nexa_icon", [c_void_p, c_char_p, c_float, c_uint32], None),
        ("nexa_skeleton", [c_void_p, c_int, c_float, c_float], None),
        ("nexa_virtual_list_begin", [c_void_p, c_char_p, c_int, c_float, c_int, c_float, P(c_int), P(c_int)], None),
        ("nexa_sparkline", [c_void_p, P(c_float), c_int, c_int, c_float, c_float, c_uint32], None),
        ("nexa_date_today", [P(c_int)], None),
        ("nexa_date_to_days", [c_int, c_int, c_int], c_int),
        ("nexa_date_from_days", [c_int, P(c_int)], None),
        ("nexa_calendar_heatmap", [c_void_p, c_char_p, c_int, c_int, c_int, P(c_float), c_int, P(CuiCalendarHeatmapOpts)], c_int),
        ("nexa_week_calendar", [c_void_p, c_char_p, c_int, c_int, c_int, P(CuiCalEvent), c_int, P(CuiWeekOpts)], c_int),
        ("nexa_gantt", [c_void_p, c_char_p, P(CuiGanttTask), c_int, c_int, c_int, c_int, c_int, P(CuiGanttOpts)], c_int),
        ("nexa_shortcut_label", [c_void_p, c_int, c_int], c_char_p),
        ("nexa_doc_tabs", [c_void_p, c_char_p, P(CuiDocTab), c_int, P(c_int), P(CuiDocTabsOpts), P(c_int)], None),
        ("nexa_prop_color", [c_void_p, c_char_p, P(c_uint32), P(CuiPropOpts)], c_bool),
        ("nexa_log_create", [c_int, c_size_t], c_void_p),
        ("nexa_log_destroy", [c_void_p], None),
        ("nexa_log_set_now", [c_void_p, c_double], None),
        ("nexa_log_count", [c_void_p], c_int),
        ("nexa_log_total", [c_void_p], c_uint64),
        ("nexa_log_line_at", [c_void_p, c_int, P(c_double), P(c_int), P(c_char_p), P(c_int)], c_bool),
        ("nexa_draw_rect", [c_void_p, c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_uint32], None),
        ("nexa_draw_rect_border", [c_void_p, c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_uint32, c_uint32, c_float], None),
        ("nexa_draw_rect_gradient", [c_void_p, c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_uint32, c_uint32], None),
        ("nexa_draw_shadow", [c_void_p, c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_uint32], None),
        ("nexa_draw_line", [c_void_p, c_float, c_float, c_float, c_float, c_float, c_uint32], None),
        ("nexa_draw_polyline", [c_void_p, P(c_float), c_int, c_float, c_uint32, c_bool], None),
        ("nexa_draw_polygon", [c_void_p, P(c_float), c_int, c_uint32], None),
        ("nexa_draw_circle", [c_void_p, c_float, c_float, c_float, c_uint32], None),
        ("nexa_draw_arc", [c_void_p, c_float, c_float, c_float, c_float, c_float, c_float, c_uint32], None),
        ("nexa_draw_text", [c_void_p, c_int, c_float, c_float, c_float, c_uint32, c_char_p, c_int], None),
        ("nexa_draw_icon", [c_void_p, c_char_p, c_float, c_float, c_float, c_float, c_float, c_uint32], None),
        ("nexa_draw_image", [c_void_p, c_texture, c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_uint32], None),
        ("nexa_push_clip", [c_void_p, c_float, c_float, c_float, c_float], None),
        ("nexa_canvas", [c_void_p, c_char_p, c_int, c_float, c_int, c_float, c_void_p, c_size_t, P(c_float), P(c_int), P(c_float)], None),

        # Renderers
        ("cui_sw_create", [], c_void_p),
        ("cui_sw_destroy", [c_void_p], None),
        ("cui_sw_render", [c_void_p, P(CuiDrawData), c_void_p, c_int, c_int, c_int, c_int], None),
        ("cui_sw_set_threads", [c_void_p, c_int], None),
        ("cui_write_png", [c_char_p, c_void_p, c_int, c_int, c_int], c_bool),
        ("cui_gl_create", [c_void_p], c_void_p),
        ("cui_gl_destroy", [c_void_p], None),
        ("cui_gl_render", [c_void_p, P(CuiDrawData), c_bool], None),
        ("cui_gl_read_pixels", [c_void_p, c_int, c_int, c_void_p], None),

        # App layer
        ("cui_app_create", [P(CuiAppDesc)], c_void_p),
        ("cui_app_destroy", [c_void_p], None),
        ("cui_app_frame", [c_void_p], c_bool),
        ("cui_app_ui", [c_void_p], c_void_p),
        ("cui_app_run", [P(CuiAppDesc), c_void_p, c_void_p], c_int),
        ("cui_app_quit", [c_void_p], None),
        ("cui_app_wake", [c_void_p], None),
        ("cui_app_set_title", [c_void_p, c_char_p], None),
        ("cui_app_set_size", [c_void_p, c_int, c_int], None),
        ("cui_app_is_software", [c_void_p], c_bool),
        ("cui_app_native_window", [c_void_p], c_void_p),
        ("cui_app_backend", [c_void_p], c_char_p),
        ("cui_app_file_dialog", [c_void_p, P(CuiFileDialogOpts), c_char_p, c_size_t], c_bool),
        ("cui_app_open_url", [c_char_p], c_bool),
        ("cui_app_screenshot", [c_void_p, c_void_p, c_int, c_int], c_bool),

        # Context & frame
        ("cui_destroy", [c_void_p], None),
        ("cui_set_viewport", [c_void_p, c_float, c_float, c_float], None),
        ("cui_dpi_scale", [c_void_p], c_float),
        ("cui_begin_frame", [c_void_p, c_float], None),
        ("cui_end_frame", [c_void_p], None),
        ("cui_needs_redraw", [c_void_p], c_bool),
        ("cui_next_wakeup", [c_void_p], c_float),
        ("cui_request_redraw", [c_void_p], None),
        ("cui_time", [c_void_p], c_double),
        ("cui_delta_time", [c_void_p], c_float),
        ("cui_frame_count", [c_void_p], c_uint64),
        ("cui_get_draw_data", [c_void_p], P(CuiDrawData)),

        # Input & queries
        ("cui_input_mouse_move", [c_void_p, c_float, c_float], None),
        ("cui_input_mouse_button", [c_void_p, c_int, c_bool], None),
        ("cui_input_mouse_leave", [c_void_p], None),
        ("cui_input_scroll", [c_void_p, c_float, c_float], None),
        ("cui_input_key", [c_void_p, c_int, c_bool, c_int], None),
        ("cui_input_text", [c_void_p, c_char_p], None),
        ("cui_input_focus", [c_void_p, c_bool], None),
        ("cui_input_file_hover", [c_void_p, c_bool, c_float, c_float], None),
        ("cui_input_file_drop", [c_void_p, P(c_char_p), c_int, c_float, c_float], None),
        ("cui_dropped_file_count", [c_void_p], c_int),
        ("cui_dropped_file", [c_void_p, c_int], c_char_p),
        ("cui_file_drag_active", [c_void_p], c_bool),
        ("cui_get_cursor", [c_void_p], c_int),
        ("cui_key_pressed", [c_void_p, c_int], c_bool),
        ("cui_key_down", [c_void_p, c_int], c_bool),
        ("cui_shortcut", [c_void_p, c_int, c_int], c_bool),
        ("cui_key_mods", [c_void_p], c_int),
        ("cui_mouse_down", [c_void_p, c_int], c_bool),
        ("cui_mouse_clicked", [c_void_p, c_int], c_bool),
        ("cui_wants_keyboard", [c_void_p], c_bool),
        ("cui_wants_mouse", [c_void_p], c_bool),

        # Theme & fonts
        ("cui_set_theme", [c_void_p, c_int], None),
        ("cui_get_theme_mode", [c_void_p], c_int),
        ("cui_set_accent", [c_void_p, c_int], None),
        ("cui_get_accent", [c_void_p], c_int),
        ("cui_theme_get", [c_void_p], P(CuiTheme)),
        ("cui_set_reduced_motion", [c_void_p, c_bool], None),
        ("cui_accent_name", [c_int], c_char_p),
        ("cui_font_load_memory", [c_void_p, c_void_p, c_size_t, c_bool], c_int),
        ("cui_font_load_file", [c_void_p, c_char_p], c_int),
        ("cui_font_set_role", [c_void_p, c_int, c_int], None),
        ("cui_font_add_fallback", [c_void_p, c_int, c_int], None),

        # Layout & identity
        ("cui_box_begin", [c_void_p, P(CuiBox)], c_uint32),
        ("cui_box_end", [c_void_p], None),
        ("cui_row_begin", [c_void_p, P(CuiBox)], c_uint32),
        ("cui_column_begin", [c_void_p, P(CuiBox)], c_uint32),
        ("cui_spacer", [c_void_p], None),
        ("cui_gap", [c_void_p, c_float], None),
        ("cui_separator", [c_void_p], None),
        ("cui_card_begin", [c_void_p, P(CuiCardOpts)], c_bool),
        ("cui_card_end", [c_void_p], None),
        ("cui_scroll_begin", [c_void_p, P(CuiScrollOpts)], None),
        ("cui_scroll_end", [c_void_p], None),
        ("cui_scroll_to", [c_void_p, c_char_p, c_float], None),
        ("cui_split_begin", [c_void_p, c_char_p, P(c_float), P(CuiSplitOpts)], None),
        ("cui_split_next", [c_void_p], None),
        ("cui_split_end", [c_void_p], None),
        ("cui_make_id", [c_void_p, c_char_p], c_uint32),
        ("cui_push_id", [c_void_p, c_char_p], None),
        ("cui_push_id_int", [c_void_p, c_int], None),
        ("cui_pop_id", [c_void_p], None),
        ("cui_last_id", [c_void_p], c_uint32),
        ("cui_last_hovered", [c_void_p], c_bool),
        ("cui_is_disabled", [c_void_p], c_bool),
        ("cui_push_disabled", [c_void_p, c_bool], None),
        ("cui_pop_disabled", [c_void_p], None),

        # Text
        ("cui_text_ex", [c_void_p, c_char_p, P(CuiTextOpts)], None),
        ("cui_heading", [c_void_p, c_char_p, c_int], None),
        ("cui_label", [c_void_p, c_char_p], None),
        ("cui_secondary", [c_void_p, c_char_p], None),
        ("cui_muted", [c_void_p, c_char_p], None),
        ("cui_code", [c_void_p, c_char_p], None),
        ("cui_kbd", [c_void_p, c_char_p], None),
        ("cui_link", [c_void_p, c_char_p], c_bool),

        # Buttons & selection
        ("cui_button_ex", [c_void_p, c_char_p, P(CuiButtonOpts)], c_bool),
        ("cui_icon_button_ex", [c_void_p, c_char_p, P(CuiButtonOpts)], c_bool),
        ("cui_segmented_ex", [c_void_p, c_char_p, P(c_char_p), c_int, P(c_int), P(CuiSegmentedOpts)], c_bool),
        ("cui_checkbox_ex", [c_void_p, c_char_p, P(c_bool), P(CuiCheckOpts)], c_bool),
        ("cui_switch_ex", [c_void_p, c_char_p, P(c_bool), P(CuiCheckOpts)], c_bool),
        ("cui_radio_ex", [c_void_p, c_char_p, P(c_int), c_int, P(CuiCheckOpts)], c_bool),
        ("cui_radio_group", [c_void_p, c_char_p, P(c_char_p), c_int, P(c_int)], c_bool),
        ("cui_slider_ex", [c_void_p, c_char_p, P(c_float), c_float, c_float, P(CuiSliderOpts)], c_bool),
        ("cui_range_slider", [c_void_p, c_char_p, P(c_float), P(c_float), c_float, c_float], c_bool),
        ("cui_rating", [c_void_p, c_char_p, P(c_int), c_int], c_bool),
        ("cui_chip_ex", [c_void_p, c_char_p, P(c_bool), P(CuiChipOpts)], c_bool),

        # Text inputs & numbers
        ("cui_input_ex", [c_void_p, c_char_p, c_char_p, c_size_t, P(CuiInputOpts)], c_int),
        ("cui_textarea_ex", [c_void_p, c_char_p, c_char_p, c_size_t, P(CuiInputOpts)], c_int),
        ("cui_search_ex", [c_void_p, c_char_p, c_char_p, c_size_t, P(CuiInputOpts)], c_int),
        ("cui_number_ex", [c_void_p, c_char_p, P(c_double), c_double, c_double, P(CuiNumberOpts)], c_bool),

        # Select & pickers
        ("cui_select_ex", [c_void_p, c_char_p, P(c_char_p), c_int, P(c_int), P(CuiSelectOpts)], c_bool),
        ("cui_calendar", [c_void_p, c_char_p, P(CuiDate)], c_bool),
        ("cui_date_picker_ex", [c_void_p, c_char_p, P(CuiDate), P(CuiDateOpts)], c_bool),
        ("cui_multi_select_ex", [c_void_p, c_char_p, P(c_char_p), c_int, P(c_bool), P(CuiMultiSelectOpts)], c_bool),
        ("cui_range_calendar", [c_void_p, c_char_p, P(CuiDateRange), c_int], c_bool),
        ("cui_date_range_picker_ex", [c_void_p, c_char_p, P(CuiDateRange), P(CuiDateRangeOpts)], c_bool),
        ("cui_time_picker_ex", [c_void_p, c_char_p, P(c_int), P(c_int), P(CuiTimeOpts)], c_bool),
        ("cui_wheel_picker_ex", [c_void_p, c_char_p, P(c_char_p), c_int, P(c_int), P(CuiWheelOpts)], c_bool),
        ("cui_time_dial", [c_void_p, c_char_p, P(c_int), P(c_int), c_float], c_bool),
        ("cui_ruler_slider_ex", [c_void_p, c_char_p, P(c_float), c_float, c_float, P(CuiRulerOpts)], c_bool),
        ("cui_histogram_slider_ex", [c_void_p, c_char_p, P(c_float), c_int, P(c_float), P(c_float), c_float, c_float, P(CuiHistogramOpts)], c_bool),

        # Navigation
        ("cui_tabs_ex", [c_void_p, c_char_p, P(c_char_p), c_int, P(c_int), P(CuiTabsOpts)], c_bool),
        ("cui_nav_item_ex", [c_void_p, c_char_p, P(CuiNavOpts)], c_bool),
        ("cui_nav_section", [c_void_p, c_char_p], None),
        ("cui_breadcrumb", [c_void_p, P(c_char_p), c_int], c_int),
        ("cui_pagination", [c_void_p, c_char_p, P(c_int), c_int], c_bool),
        ("cui_stepper", [c_void_p, P(c_char_p), c_int, c_int], None),
        ("cui_toc", [c_void_p, c_char_p, P(CuiTocItem), c_int], c_int),
        ("cui_toc_anchor", [c_void_p, c_char_p], None),

        # Menus, popovers, dialogs, sheets, toasts, alerts
        ("cui_popover_begin", [c_void_p, c_char_p, P(CuiPopoverOpts)], c_bool),
        ("cui_popover_end", [c_void_p], None),
        ("cui_popover_open", [c_void_p, c_char_p], None),
        ("cui_popover_close", [c_void_p, c_char_p], None),
        ("cui_popover_toggle", [c_void_p, c_char_p], None),
        ("cui_popover_is_open", [c_void_p, c_char_p], c_bool),
        ("cui_menu_begin", [c_void_p, c_char_p, P(CuiMenuOpts)], c_bool),
        ("cui_menu_end", [c_void_p], None),
        ("cui_context_menu_begin", [c_void_p, c_char_p], c_bool),
        ("cui_context_menu_end", [c_void_p], None),
        ("cui_menu_item_ex", [c_void_p, c_char_p, P(CuiMenuItemOpts)], c_bool),
        ("cui_menu_separator", [c_void_p], None),
        ("cui_menu_label", [c_void_p, c_char_p], None),
        ("cui_tooltip", [c_void_p, c_char_p], None),
        ("cui_dialog_begin", [c_void_p, c_char_p, P(c_bool), P(CuiDialogOpts)], c_bool),
        ("cui_dialog_end", [c_void_p], None),
        ("cui_dialog_footer_begin", [c_void_p], None),
        ("cui_dialog_footer_end", [c_void_p], None),
        ("cui_sheet_begin", [c_void_p, c_char_p, P(c_bool), P(CuiSheetOpts)], c_bool),
        ("cui_sheet_end", [c_void_p], None),
        ("cui_toast_ex", [c_void_p, c_char_p, P(CuiToastOpts)], c_int),
        ("cui_toast_action_clicked", [c_void_p, c_int], c_bool),
        ("cui_toast_dismiss", [c_void_p, c_int], None),
        ("cui_alert_ex", [c_void_p, c_char_p, P(CuiAlertOpts)], c_bool),
        ("cui_hover_card_begin", [c_void_p, c_char_p, P(CuiHoverCardOpts)], c_bool),
        ("cui_hover_card_end", [c_void_p], None),
        ("cui_confirm_popover_ex", [c_void_p, c_char_p, P(CuiConfirmPopoverOpts)], c_bool),
        ("cui_expandable_text_ex", [c_void_p, c_char_p, c_char_p, P(CuiExpandableTextOpts)], c_bool),
        ("cui_expandable_card_begin", [c_void_p, c_char_p, P(c_bool), P(CuiExpandableCardOpts)], c_bool),
        ("cui_expandable_card_end", [c_void_p], None),
        ("cui_banner_ex", [c_void_p, c_char_p, P(c_bool), P(CuiBannerOpts)], c_bool),
        ("cui_countdown_ex", [c_void_p, c_char_p, c_double, P(CuiCountdownOpts)], None),
        ("cui_checklist_ex", [c_void_p, c_char_p, P(CuiCheckStep), c_int, P(CuiChecklistOpts)], c_int),

        # Feedback & display
        ("cui_progress_ex", [c_void_p, c_float, P(CuiProgressOpts)], None),
        ("cui_progress_ring", [c_void_p, c_char_p, c_float, c_float], None),
        ("cui_spinner", [c_void_p, c_float], None),
        ("cui_badge_ex", [c_void_p, c_char_p, P(CuiBadgeOpts)], None),
        ("cui_avatar_ex", [c_void_p, c_char_p, P(CuiAvatarOpts)], None),
        ("cui_avatar_group", [c_void_p, P(c_char_p), c_int, c_int, c_float], None),
        ("cui_empty_state_ex", [c_void_p, c_char_p, P(CuiEmptyOpts)], c_bool),
        ("cui_metric_ex", [c_void_p, c_char_p, c_char_p, P(CuiMetricOpts)], None),
        ("cui_meter", [c_void_p, c_char_p, c_float, c_float, c_char_p], None),
        ("cui_timeline_item_ex", [c_void_p, c_char_p, P(CuiTimelineOpts)], None),

        # Data display, tables, grid, code
        ("cui_accordion_begin", [c_void_p, c_char_p, P(c_bool)], c_bool),
        ("cui_accordion_end", [c_void_p], None),
        ("cui_tree_begin", [c_void_p, c_char_p, P(c_bool), P(CuiTreeOpts)], c_bool),
        ("cui_tree_end", [c_void_p], None),
        ("cui_tree_clicked", [c_void_p], c_bool),
        ("cui_list_item_ex", [c_void_p, c_char_p, P(CuiListItemOpts)], c_bool),
        ("cui_virtual_list_end", [c_void_p], None),
        ("cui_table_begin_ex", [c_void_p, c_char_p, P(CuiTableColumn), c_int, P(CuiTableOpts)], c_bool),
        ("cui_table_row", [c_void_p, c_bool], c_bool),
        ("cui_table_cell", [c_void_p], None),
        ("cui_table_cell_text", [c_void_p, c_char_p], None),
        ("cui_table_end", [c_void_p], None),
        ("cui_data_grid_begin_ex", [c_void_p, c_char_p, P(CuiGridColumn), c_int, c_int, P(c_int), P(c_int), P(CuiGridOpts)], c_bool),
        ("cui_data_grid_row", [c_void_p, c_int], c_bool),
        ("cui_data_grid_cell", [c_void_p], None),
        ("cui_data_grid_cell_text", [c_void_p, c_char_p], None),
        ("cui_data_grid_cell_edit", [c_void_p, c_char_p, c_size_t], c_bool),
        ("cui_data_grid_edit", [c_void_p, c_char_p, c_size_t], c_bool),
        ("cui_data_grid_end", [c_void_p], None),
        ("cui_tree_cell", [c_void_p, c_char_p, c_int, c_bool, P(c_bool), c_char_p], c_bool),
        ("cui_filter_bar", [c_void_p, c_char_p, P(CuiFilterField), c_int, P(c_uint32), c_char_p, c_size_t], c_bool),
        ("cui_code_block_ex", [c_void_p, c_char_p, c_char_p, P(CuiCodeOpts)], None),
        ("cui_json_view_ex", [c_void_p, c_char_p, c_char_p, P(CuiJsonOpts)], c_bool),

        # Images
        ("cui_image_create", [c_void_p, c_int, c_int, c_void_p], c_texture),
        ("cui_image_load", [c_void_p, c_char_p, P(c_int), P(c_int)], c_texture),
        ("cui_image_destroy", [c_void_p, c_texture], None),
        ("cui_image_ex", [c_void_p, c_texture, P(CuiImageOpts)], None),

        # Charts & Viz
        ("cui_line_chart_ex", [c_void_p, c_char_p, P(CuiSeries), c_int, P(CuiChartOpts)], None),
        ("cui_bar_chart_ex", [c_void_p, c_char_p, P(CuiSeries), c_int, P(CuiChartOpts)], None),
        ("cui_donut_chart_ex", [c_void_p, c_char_p, P(c_float), P(c_char_p), c_int, P(CuiChartOpts)], None),
        ("cui_gauge", [c_void_p, c_char_p, c_float, c_float], None),
        ("cui_heatmap_ex", [c_void_p, c_char_p, P(c_float), c_int, c_int, P(CuiHeatmapOpts)], c_int),
        ("cui_treemap_ex", [c_void_p, c_char_p, P(CuiVizItem), c_int, P(CuiTreemapOpts)], c_int),
        ("cui_radar_chart_ex", [c_void_p, c_char_p, P(CuiSeries), c_int, P(c_char_p), c_int, P(CuiRadarOpts)], c_int),
        ("cui_funnel_ex", [c_void_p, c_char_p, P(CuiVizItem), c_int, P(CuiFunnelOpts)], c_int),
        ("cui_sankey_ex", [c_void_p, c_char_p, P(c_char_p), c_int, P(CuiSankeyLink), c_int, P(CuiSankeyOpts)], c_int),
        ("cui_waffle_ex", [c_void_p, c_char_p, P(CuiVizItem), c_int, P(CuiWaffleOpts)], c_int),
        ("cui_split_bar_ex", [c_void_p, c_char_p, P(CuiVizItem), c_int, P(CuiSplitBarOpts)], c_int),
        ("cui_bar_list_ex", [c_void_p, c_char_p, P(CuiVizItem), c_int, P(CuiBarListOpts)], c_int),
        ("cui_activity_rings_ex", [c_void_p, c_char_p, P(CuiVizItem), c_int, P(CuiRingsOpts)], c_int),
        ("cui_scatter_chart_ex", [c_void_p, c_char_p, P(CuiScatterSeries), c_int, P(CuiScatterOpts)], c_int),

        # Extended actions, inputs, capture
        ("cui_command_palette", [c_void_p, P(c_bool), P(CuiCommand), c_int], c_int),
        ("cui_radio_cards_ex", [c_void_p, c_char_p, P(CuiChoice), c_int, P(c_int), P(CuiRadioCardsOpts)], c_bool),
        ("cui_tag_input_ex", [c_void_p, c_char_p, c_char_p, c_size_t, P(CuiTagOpts)], c_bool),
        ("cui_otp_input", [c_void_p, c_char_p, c_char_p, c_int], c_bool),
        ("cui_button_group_begin", [c_void_p], None),
        ("cui_button_group_end", [c_void_p], None),
        ("cui_copy_button", [c_void_p, c_char_p, c_char_p], c_bool),
        ("cui_hold_button_ex", [c_void_p, c_char_p, P(CuiHoldOpts)], c_bool),
        ("cui_password_strength", [c_void_p, c_char_p], c_int),
        ("cui_reorder_begin", [c_void_p, c_char_p, P(c_int), c_int], None),
        ("cui_reorder_end", [c_void_p], c_bool),
        ("cui_reorder_item_begin", [c_void_p, c_int], None),
        ("cui_reorder_item_end", [c_void_p], None),
        ("cui_split_button_ex", [c_void_p, c_char_p, P(c_char_p), c_int, P(CuiSplitButtonOpts)], c_int),
        ("cui_toggle_group_ex", [c_void_p, c_char_p, P(c_char_p), c_int, P(c_bool), P(CuiToggleGroupOpts)], c_bool),
        ("cui_confirm_button_ex", [c_void_p, c_char_p, P(CuiConfirmOpts)], c_bool),
        ("cui_status_button_ex", [c_void_p, c_char_p, c_int, P(CuiStatusButtonOpts)], c_bool),
        ("cui_reactions", [c_void_p, c_char_p, P(CuiReaction), c_int], c_int),
        ("cui_speed_dial_ex", [c_void_p, c_char_p, P(CuiSpeedAction), c_int, P(CuiSpeedDialOpts)], c_int),
        ("cui_theme_switcher", [c_void_p, P(c_int), c_bool], c_bool),
        ("cui_theme_toggle", [c_void_p], c_bool),
        ("cui_user_menu_begin", [c_void_p, c_char_p, P(CuiUserMenuOpts)], c_bool),
        ("cui_user_menu_end", [c_void_p], None),
        ("cui_swipe_item_begin", [c_void_p, c_char_p, P(CuiSwipeAction), c_int, P(CuiSwipeAction), c_int], None),
        ("cui_swipe_item_end", [c_void_p], c_int),
        ("cui_signature_pad_ex", [c_void_p, c_char_p, P(CuiSignatureOpts)], c_bool),
        ("cui_signature_points", [c_void_p, c_char_p, P(P(CuiVec2)), P(P(c_int)), P(c_int)], c_int),
        ("cui_signature_clear", [c_void_p, c_char_p], None),
        ("cui_dropzone_ex", [c_void_p, c_char_p, P(CuiDropzoneOpts)], c_int),
        ("cui_path_has_extension", [c_char_p, c_char_p], c_bool),
        ("cui_avatar_upload", [c_void_p, c_char_p, c_char_p, P(c_texture), c_float], c_int),
        ("cui_inline_edit_ex", [c_void_p, c_char_p, c_char_p, c_size_t, P(CuiInlineEditOpts)], c_int),
        ("cui_scrub_ex", [c_void_p, c_char_p, P(c_float), c_float, c_float, P(CuiScrubOpts)], c_bool),
        ("cui_money_input_ex", [c_void_p, c_char_p, P(c_double), P(CuiMoneyOpts)], c_bool),
        ("cui_shortcut_recorder_ex", [c_void_p, c_char_p, P(CuiKeyCombo), P(CuiShortcutRecorderOpts)], c_bool),
        ("cui_key_name", [c_int], c_char_p),

        # Social & Media
        ("cui_chat_message_ex", [c_void_p, c_char_p, P(CuiChatOpts)], None),
        ("cui_chat_divider", [c_void_p, c_char_p], None),
        ("cui_typing_indicator", [c_void_p, c_char_p], None),
        ("cui_comment_ex", [c_void_p, c_char_p, c_char_p, c_char_p, P(CuiCommentOpts)], c_int),
        ("cui_presence", [c_void_p, c_char_p, P(CuiPresenceUser), c_int, c_int, c_float], None),
        ("cui_carousel_begin", [c_void_p, c_char_p, c_int, P(c_int), P(CuiCarouselOpts)], c_bool),
        ("cui_carousel_slide_begin", [c_void_p], None),
        ("cui_carousel_slide_end", [c_void_p], None),
        ("cui_carousel_end", [c_void_p], None),
        ("cui_image_compare_ex", [c_void_p, c_char_p, c_texture, c_texture, P(c_float), P(CuiCompareOpts)], c_bool),
        ("cui_card_stack_begin", [c_void_p, c_char_p, c_int, P(CuiCardStackOpts)], None),
        ("cui_card_stack_item_begin", [c_void_p, c_int], None),
        ("cui_card_stack_item_end", [c_void_p], None),
        ("cui_card_stack_end", [c_void_p], c_int),
        ("cui_counter_ex", [c_void_p, c_char_p, c_double, P(CuiCounterOpts)], None),
        ("cui_ticker_ex", [c_void_p, c_char_p, P(CuiTickerItem), c_int, P(CuiTickerOpts)], None),

        # Motion, dock, tab bar, tiles, waveform, player
        ("cui_shimmer_text_ex", [c_void_p, c_char_p, P(CuiTextFxOpts)], None),
        ("cui_typewriter_ex", [c_void_p, c_char_p, c_char_p, P(CuiTextFxOpts)], c_bool),
        ("cui_text_reveal_ex", [c_void_p, c_char_p, c_char_p, P(CuiTextFxOpts)], None),
        ("cui_word_rotate_ex", [c_void_p, c_char_p, P(c_char_p), c_int, c_float, P(CuiTextFxOpts)], None),
        ("cui_number_roll_ex", [c_void_p, c_char_p, c_char_p, P(CuiTextFxOpts)], None),
        ("cui_gradient_text_ex", [c_void_p, c_char_p, P(CuiGradientTextOpts)], None),
        ("cui_spotlight_begin", [c_void_p, c_char_p, P(CuiSpotlightOpts)], None),
        ("cui_spotlight_end", [c_void_p], None),
        ("cui_loader_ex", [c_void_p, P(CuiLoaderOpts)], None),
        ("cui_dock_begin", [c_void_p, c_char_p, P(CuiDockOpts)], None),
        ("cui_dock_item_ex", [c_void_p, c_char_p, c_char_p, P(CuiDockItemOpts)], c_bool),
        ("cui_dock_separator", [c_void_p], None),
        ("cui_dock_end", [c_void_p], None),
        ("cui_tab_bar_ex", [c_void_p, c_char_p, P(CuiTabBarItem), c_int, P(c_int), P(CuiTabBarOpts)], c_bool),
        ("cui_control_tile_ex", [c_void_p, c_char_p, P(c_bool), P(CuiTileOpts)], c_bool),
        ("cui_waveform_ex", [c_void_p, c_char_p, P(c_float), c_int, P(c_float), P(CuiWaveformOpts)], c_bool),
        ("cui_now_playing_ex", [c_void_p, c_char_p, P(CuiNowPlaying), P(CuiNowPlayingOpts)], c_int),

        # AI interfaces
        ("cui_reasoning_begin", [c_void_p, c_char_p, P(CuiReasoningOpts)], c_bool),
        ("cui_reasoning_end", [c_void_p], None),
        ("cui_tool_call_ex", [c_void_p, c_char_p, c_char_p, P(CuiToolCallOpts)], None),
        ("cui_agent_plan_ex", [c_void_p, c_char_p, P(CuiPlanStep), c_int, P(CuiAgentPlanOpts)], c_int),
        ("cui_agent_status_ex", [c_void_p, c_char_p, P(CuiAgentStatusOpts)], None),
        ("cui_source_list", [c_void_p, c_char_p, P(CuiSource), c_int], c_int),
        ("cui_citation", [c_void_p, c_int, P(CuiSource)], c_bool),
        ("cui_context_meter_ex", [c_void_p, c_char_p, c_float, c_float, P(CuiContextOpts)], None),
        ("cui_response_actions_ex", [c_void_p, c_char_p, P(CuiResponseActionsOpts)], c_int),
        ("cui_prompt_suggestions_ex", [c_void_p, c_char_p, P(CuiPromptSuggestion), c_int, P(CuiPromptSuggestionsOpts)], c_int),
        ("cui_model_picker_ex", [c_void_p, c_char_p, P(CuiModel), c_int, P(c_int), P(CuiModelPickerOpts)], c_bool),
        ("cui_chat_composer_ex", [c_void_p, c_char_p, c_char_p, c_size_t, P(CuiComposerOpts)], c_int),
        ("cui_voice_orb_ex", [c_void_p, c_char_p, c_int, c_float, P(CuiVoiceOrbOpts)], c_bool),

        # Planning
        ("cui_kanban_begin", [c_void_p, c_char_p], None),
        ("cui_kanban_column_begin_ex", [c_void_p, c_char_p, c_int, P(CuiKanbanColumnOpts)], c_bool),
        ("cui_kanban_card_begin", [c_void_p, c_int], c_bool),
        ("cui_kanban_card_end", [c_void_p], None),
        ("cui_kanban_column_end", [c_void_p], None),
        ("cui_kanban_end", [c_void_p, P(CuiKanbanMove)], c_bool),

        # Node editor
        ("cui_node_editor_begin_ex", [c_void_p, c_char_p, P(CuiNodeView), P(CuiNodeEditorOpts)], c_bool),
        ("cui_node_editor_end", [c_void_p], None),
        ("cui_node_begin_ex", [c_void_p, c_int, P(c_float), P(c_float), c_char_p, P(CuiNodeOpts)], c_bool),
        ("cui_node_end", [c_void_p], None),
        ("cui_node_input_ex", [c_void_p, c_int, c_char_p, P(CuiPinOpts)], c_bool),
        ("cui_node_output_ex", [c_void_p, c_int, c_char_p, P(CuiPinOpts)], c_bool),
        ("cui_node_content_begin", [c_void_p], None),
        ("cui_node_content_end", [c_void_p], None),
        ("cui_node_link", [c_void_p, c_int, c_int, c_int], c_bool),
        ("cui_node_link_created", [c_void_p, P(c_int), P(c_int)], c_bool),
        ("cui_node_link_removed", [c_void_p, P(c_int)], c_bool),
        ("cui_node_deleted", [c_void_p, P(c_int)], c_bool),

        # App chrome & Tool panels
        ("cui_menu_bar_begin", [c_void_p, c_char_p, P(CuiMenuBarOpts)], None),
        ("cui_menu_bar_end", [c_void_p], None),
        ("cui_menu_bar_menu_begin", [c_void_p, c_char_p, P(CuiMenuBarMenuOpts)], c_bool),
        ("cui_menu_bar_menu_end", [c_void_p], None),
        ("cui_toolbar_begin", [c_void_p, c_char_p, P(CuiToolbarOpts)], None),
        ("cui_toolbar_end", [c_void_p], None),
        ("cui_toolbar_button_ex", [c_void_p, c_char_p, P(CuiToolOpts)], c_bool),
        ("cui_toolbar_separator", [c_void_p], None),
        ("cui_toolbar_spacer", [c_void_p], None),
        ("cui_status_bar_begin", [c_void_p, c_char_p, P(CuiStatusBarOpts)], None),
        ("cui_status_bar_end", [c_void_p], None),
        ("cui_status_bar_spacer", [c_void_p], None),
        ("cui_status_bar_text_ex", [c_void_p, c_char_p, P(CuiStatusItemOpts)], None),
        ("cui_status_bar_item_ex", [c_void_p, c_char_p, P(CuiStatusItemOpts)], c_bool),
        ("cui_status_bar_progress_ex", [c_void_p, c_float, P(CuiStatusProgressOpts)], None),
        ("cui_inspector_begin_ex", [c_void_p, c_char_p, P(CuiInspectorOpts)], c_bool),
        ("cui_inspector_end", [c_void_p], None),
        ("cui_inspector_group", [c_void_p, c_char_p, P(c_bool)], c_bool),
        ("cui_prop_float_ex", [c_void_p, c_char_p, P(c_float), P(CuiPropOpts)], c_bool),
        ("cui_prop_int_ex", [c_void_p, c_char_p, P(c_int), P(CuiPropOpts)], c_bool),
        ("cui_prop_text_ex", [c_void_p, c_char_p, c_char_p, c_size_t, P(CuiPropOpts)], c_bool),
        ("cui_prop_bool_ex", [c_void_p, c_char_p, P(c_bool), P(CuiPropOpts)], c_bool),
        ("cui_prop_enum_ex", [c_void_p, c_char_p, P(c_char_p), c_int, P(c_int), P(CuiPropOpts)], c_bool),
        ("cui_prop_vec_ex", [c_void_p, c_char_p, P(c_float), c_int, P(CuiPropOpts)], c_bool),
        ("cui_log_append_text", [c_void_p, c_int, c_double, c_char_p, c_int], None),
        ("cui_log_clear", [c_void_p], None),
        ("cui_log_view_ex", [c_void_p, c_char_p, c_void_p, P(CuiLogViewOpts)], None),

        # Clip, state & spring animations
        ("cui_pop_clip", [c_void_p], None),
        ("cui_state", [c_void_p, c_uint32, c_size_t], c_void_p),
        ("cui_animate", [c_void_p, c_uint32, c_float], c_float),
        ("cui_animate_spring", [c_void_p, c_uint32, c_float, c_float, c_float], c_float),
    ]

    for name, argtypes, restype in sigs:
        fn = getattr(lib, name)
        fn.argtypes = argtypes
        fn.restype = restype
