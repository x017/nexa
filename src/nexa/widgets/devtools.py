"""CUI 1.3's developer-tool components: problems, pipelines, traces, coverage…

These are data-driven views.  You hand each one a sequence of plain dicts (or
any object with matching attributes) whose keys are the C struct's field names,
e.g. ``{"message": "unused import", "severity": "warning", "line": 12}``.  The
same name appears on the result so the shapes stay predictable:

    >>> res = ui.problems("problems", [{"message": "bad", "severity": "error"}])
    >>> res.selected
    -1

Strings are encoded for you, enums accept their Python or int value, and a
``Sequence`` fills a fixed array or a ``float*``/``char**`` field.
"""

from __future__ import annotations

import ctypes
from ctypes import c_size_t
from typing import Any, Dict, List, NamedTuple, Optional, Sequence

from .._cdefs import (
    CuiApiEndpoint,
    CuiApiExplorerOpts,
    CuiApiExplorerResult,
    CuiBlameCommit,
    CuiBlameOpts,
    CuiBlameResult,
    CuiCommit,
    CuiCommitGraphOpts,
    CuiCommitGraphResult,
    CuiCoverageFile,
    CuiCoverageOpts,
    CuiCoverageResult,
    CuiDiagnostic,
    CuiFeatureFlag,
    CuiFeatureFlagsOpts,
    CuiFeatureFlagsResult,
    CuiGraphEdge,
    CuiGraphNode,
    CuiGraphOpts,
    CuiGraphResult,
    CuiHistogramSeries,
    CuiKeymapBinding,
    CuiKeymapOpts,
    CuiKeymapResult,
    CuiKvEditorOpts,
    CuiNetRequest,
    CuiPipelineJob,
    CuiPipelineOpts,
    CuiPipelineResult,
    CuiProblemsOpts,
    CuiProblemsResult,
    CuiQueryField,
    CuiQueryNode,
    CuiQueryOpts,
    CuiRegexTesterOpts,
    CuiRegexTesterResult,
    CuiRequestBarOpts,
    CuiRequestBarResult,
    CuiScheduleOpts,
    CuiScheduleResult,
    CuiStackFrame,
    CuiStackTraceOpts,
    CuiStackTraceResult,
    CuiTestExplorerOpts,
    CuiTestExplorerResult,
    CuiTestItem,
    CuiTimeHistogramOpts,
    CuiTimeHistogramResult,
    CuiTraceOpts,
    CuiTraceResult,
    CuiTraceSpan,
    CuiTraceTrack,
    CuiTraceView,
    CuiUptimeOpts,
    CuiUptimeResult,
    CuiUptimeService,
    CuiWaterfallOpts,
    CuiWaterfallResult,
    to_c_date,
    to_c_size,
)
from .._lib import get_cdll
from ..types import Date, JobStatus, Key, Mod, QueryType, Severity, SizeLike, Tone

_ENUM_HINTS = {
    "severity": Severity,
    "status": JobStatus,
    "tone": Tone,
    "type": QueryType,
    "mods": Mod,
    "key": Key,
}


def _fill(struct: Any, data: Any, keep: list) -> None:
    """Copy ``data`` (a dict or an object's attributes) into a ctypes struct."""
    if data is None:
        return
    fields = dict(struct._fields_)
    if isinstance(data, dict):
        pairs = list(data.items())
    else:
        pairs = [(name, getattr(data, name)) for name in fields if hasattr(data, name)]
    for name, value in pairs:
        if name not in fields or value is None:
            continue
        ftype = fields[name]
        is_int = ftype in (ctypes.c_int, ctypes.c_uint, ctypes.c_uint32)
        if isinstance(value, str) and name == "key" and is_int:
            value = int(_key_from_string(value))
        elif isinstance(value, str) and name == "mods" and is_int:
            value = int(_mod_from_string(value))
        elif isinstance(value, str) and is_int:
            enum = _ENUM_HINTS.get(name)
            member = getattr(enum, value.upper(), None) if enum is not None else None
            if member is None:
                choices = [m.name for m in enum] if enum is not None else "an int"
                raise TypeError(f"{name}={value!r} is not a number; pass {choices}")
            value = int(member)
        elif isinstance(value, str):
            value = value.encode("utf-8")
        elif isinstance(value, (bytes, bytearray)):
            value = bytes(value)
        elif isinstance(ftype, type) and issubclass(ftype, ctypes.Structure) and isinstance(value, (dict, object)):
            if isinstance(value, (dict,)) or hasattr(value, "__dict__") or isinstance(value, ctypes.Structure):
                if not isinstance(value, ctypes.Structure):
                    nested = ftype()
                    _fill(nested, value, keep)
                    setattr(struct, name, nested)
                    continue
        elif isinstance(value, (ctypes.Structure, ctypes.Array, ctypes._Pointer, int, float, bool)):
            pass
        elif hasattr(value, "value") and not isinstance(value, (list, tuple)):
            value = int(value)  # IntEnum
        array_len = getattr(ftype, "_length_", None)
        if array_len and isinstance(value, (list, tuple)):
            if value and isinstance(value[0], dict):
                arr = (ftype._type_ * array_len)()
                for i, item in enumerate(list(value)[:array_len]):
                    _fill(arr[i], item, keep)
            else:
                arr = (ftype._type_ * array_len)()
                for i, item in enumerate(list(value)[:array_len]):
                    arr[i] = item.encode("utf-8") if isinstance(item, str) else item
            keep.append(arr)
            setattr(struct, name, arr)
            continue
        if isinstance(ftype, type) and issubclass(ftype, ctypes._Pointer) and isinstance(value, (int, float)):
            scalar = (ctypes.c_float if isinstance(value, float) else ctypes.c_int)(value)
            keep.append(scalar)
            setattr(struct, name, ctypes.cast(ctypes.byref(scalar), ftype))
            continue
        if isinstance(ftype, type) and issubclass(ftype, ctypes._Pointer) and isinstance(value, (list, tuple)):
            elem = ftype._type_
            if isinstance(elem, type) and issubclass(elem, ctypes.Structure):
                arr = (elem * max(1, len(value)))()
                for i, item in enumerate(value):
                    _fill(arr[i], item, keep)
            elif isinstance(elem, ctypes.c_char_p):
                arr = (ctypes.c_char_p * (len(value) + 1))()
                for i, item in enumerate(value):
                    arr[i] = item.encode("utf-8") if isinstance(item, str) else item
            else:
                arr = (elem * max(1, len(value)))()
                for i, item in enumerate(value):
                    arr[i] = item
            keep.append(arr)
            setattr(struct, name, ctypes.cast(arr, ftype))
            count_field = f"{name}_count"
            if count_field in fields:
                setattr(struct, count_field, len(value))
            continue
        setattr(struct, name, value)


def _mod_from_string(text: str) -> Mod:
    """``"ctrl+shift"`` (or ``"CTRL"``) to a :class:`Mod` bit flag."""
    flags = Mod(0)
    for part in text.replace("+", " ").replace("-", " ").split():
        member = getattr(Mod, part.upper().replace("CMD", "META").replace("OPTION", "ALT"), None)
        if member is None:
            raise TypeError(f"unknown modifier {part!r}; use ctrl, shift, alt or meta")
        flags |= member
    return flags


def _key_from_string(text: str) -> Key:
    """``"K"``, ``"F5"`` or ``"Enter"`` to a :class:`Key` member."""
    member = getattr(Key, text.upper(), None)
    if member is None:
        raise TypeError(f"unknown key {text!r}")
    return member


def _sel(value: int, keep: list) -> tuple:
    """``(cell, pointer)`` for the ``int *selected`` fields of the tool options."""
    cell = ctypes.c_int(int(value))
    keep.append(cell)
    return cell, ctypes.cast(ctypes.byref(cell), ctypes.POINTER(ctypes.c_int))


def _pack(cls: Any, items: Optional[Sequence[Any]], keep: list, *, null_terminated: bool = False) -> tuple:
    """``(array, count)`` for a sequence of dicts, keeping the buffers alive."""
    items = list(items or ())
    count = len(items)
    if not count:
        return None, 0
    extra = 1 if null_terminated else 0
    array = (cls * (count + extra))()
    for i, item in enumerate(items):
        _fill(array[i], item, keep)
    keep.append(array)
    return array, count


def _opts(cls: Any, kwargs: Dict[str, Any], keep: list, **defaults: Any) -> Any:
    opts = cls()
    _fill(opts, {**defaults, **kwargs}, keep)
    return opts


class ProblemsResult(NamedTuple):
    selected: int
    activated: int
    shown: int


class PipelineResult(NamedTuple):
    clicked: int
    hovered: int
    selected: int


class ScheduleResult(NamedTuple):
    cron: str
    changed: bool
    valid: bool
    next: int


class KeymapResult(NamedTuple):
    clicked: int
    conflicts: int


class CommitGraphResult(NamedTuple):
    clicked: int
    activated: int
    hovered: int
    selected: int


class GraphResult(NamedTuple):
    clicked: int
    activated: int
    hovered: int
    selected: int


class WaterfallResult(NamedTuple):
    clicked: int
    activated: int
    hovered: int
    selected: int


class TraceResult(NamedTuple):
    view: CuiTraceView
    selected: int
    selection_changed: bool
    view_changed: bool
    hovered: int


class RegexTesterResult(NamedTuple):
    pattern: str
    text: str
    valid: bool
    matches: int
    error: str


class TestExplorerResult(NamedTuple):
    selected: int
    activated: int
    run: int
    run_all: bool
    passed: int
    failed: int
    skipped: int
    total: int


class StackTraceResult(NamedTuple):
    clicked: int


class RequestBarResult(NamedTuple):
    method: int
    url: str
    send: bool
    cancel: bool
    changed: bool


class UptimeResult(NamedTuple):
    service: int
    day: int


class TimeHistogramResult(NamedTuple):
    sel_start: float
    sel_end: float
    selection_changed: bool
    hovered: int


class CoverageResult(NamedTuple):
    activated: int
    lines: int


class BlameResult(NamedTuple):
    clicked: int
    hovered: int


class FeatureFlagsResult(NamedTuple):
    flag: int
    env: int


class ApiExplorerResult(NamedTuple):
    selected: int
    try_it: bool
    current: int


class KvEditorResult(NamedTuple):
    pairs: List[Dict[str, Any]]
    changed: bool


class QueryBuilderResult(NamedTuple):
    nodes: List[Dict[str, Any]]
    changed: bool


class DevtoolsMixin:
    """Developer-tool views (CUI 1.3): traces, pipelines, coverage, graphs…"""

    # -- diagnostics -----------------------------------------------------
    def problems(
        self,
        id: str,
        diagnostics: Sequence[Any],
        *,
        width: SizeLike = 380.0,
        height: float = 240.0,
        no_toolbar: bool = False,
    ) -> ProblemsResult:
        """A filterable problems panel; returns the selected/activated row."""
        keep = self._frame_keepalive
        array, count = _pack(CuiDiagnostic, diagnostics, keep)
        opts = _opts(CuiProblemsOpts, {}, keep, width=to_c_size(width), height=height, no_toolbar=no_toolbar)
        out = CuiProblemsResult()
        self._lib.nexa_problems_ex(self._ctx, id.encode("utf-8"), array, count, opts, ctypes.byref(out))
        return ProblemsResult(out.selected, out.activated, out.shown)

    # -- CI --------------------------------------------------------------
    def pipeline(
        self,
        id: str,
        stages: Sequence[str],
        jobs: Sequence[Any] = (),
        *,
        width: SizeLike = 380.0,
        selected: int = -1,
    ) -> PipelineResult:
        """A CI pipeline: columns of stage badges with the jobs inside them."""
        keep = self._frame_keepalive
        labels = (ctypes.c_char_p * (len(stages) + 1))()
        for i, stage in enumerate(stages):
            labels[i] = stage.encode("utf-8") if isinstance(stage, str) else stage
        keep.append(labels)
        job_array, job_count = _pack(CuiPipelineJob, jobs, keep)
        cell, ptr = _sel(selected, keep)
        opts = _opts(CuiPipelineOpts, {}, keep, width=to_c_size(width), selected=ptr)
        out = CuiPipelineResult()
        self._lib.nexa_pipeline_ex(
            self._ctx, id.encode("utf-8"), labels, len(stages), job_array, job_count, opts, ctypes.byref(out)
        )
        return PipelineResult(out.clicked, out.hovered, cell.value)

    # -- schedules -------------------------------------------------------
    def schedule_picker(
        self,
        id: str,
        cron: str = "0 9 * * *",
        *,
        width: SizeLike = 380.0,
        now: int = 0,
        utc: bool = False,
        next_count: int = 3,
    ) -> ScheduleResult:
        """Cron builder with a plain-language description and the next run times."""
        keep = self._frame_keepalive
        cap = 256
        buf = ctypes.create_string_buffer(cron.encode("utf-8"), cap)
        keep.append(buf)
        opts = _opts(
            CuiScheduleOpts, {}, keep, width=to_c_size(width), now=int(now), utc=utc, next_count=next_count
        )
        out = CuiScheduleResult()
        self._lib.nexa_schedule_picker_ex(self._ctx, id.encode("utf-8"), buf, c_size_t(cap), opts, ctypes.byref(out))
        return ScheduleResult(buf.value.decode("utf-8", "replace"), out.changed, out.valid, out.next)

    # -- shortcuts -------------------------------------------------------
    def keymap(
        self,
        id: str,
        bindings: Sequence[Any],
        *,
        width: SizeLike = 360.0,
        categories: Sequence[str] = (),
        mods: Sequence[int] = (),
        no_function_row: bool = False,
    ) -> KeymapResult:
        """A searchable shortcuts cheatsheet grouped by category."""
        keep = self._frame_keepalive
        array, count = _pack(CuiKeymapBinding, bindings, keep)
        cats = (ctypes.c_char_p * (len(categories) + 1))() if categories else None
        if cats is not None:
            for i, name in enumerate(categories):
                cats[i] = name.encode("utf-8")
            keep.append(cats)
        mods_arr = None
        if mods:
            mods_arr = (ctypes.c_int * len(mods))(*mods)
            keep.append(mods_arr)
        opts = _opts(
            CuiKeymapOpts,
            {},
            keep,
            width=to_c_size(width),
            categories=ctypes.cast(cats, ctypes.POINTER(ctypes.c_char_p)) if cats else None,
            category_count=len(categories),
            mods=ctypes.cast(mods_arr, ctypes.POINTER(ctypes.c_int)) if mods_arr else None,
            no_function_row=no_function_row,
        )
        out = CuiKeymapResult()
        self._lib.nexa_keymap_ex(self._ctx, id.encode("utf-8"), array, count, opts, ctypes.byref(out))
        return KeymapResult(out.clicked, out.conflicts)

    # -- git -------------------------------------------------------------
    def commit_graph(
        self,
        id: str,
        commits: Sequence[Any],
        *,
        width: SizeLike = 380.0,
        height: float = 280.0,
        selected: int = -1,
    ) -> CommitGraphResult:
        """A git history graph with lanes, refs and merges."""
        keep = self._frame_keepalive
        array, count = _pack(CuiCommit, commits, keep)
        cell, ptr = _sel(selected, keep)
        opts = _opts(CuiCommitGraphOpts, {}, keep, width=to_c_size(width), height=height, selected=ptr)
        out = CuiCommitGraphResult()
        self._lib.nexa_commit_graph_ex(self._ctx, id.encode("utf-8"), array, count, opts, ctypes.byref(out))
        return CommitGraphResult(out.clicked, out.activated, out.hovered, cell.value)

    def graph_view(
        self,
        id: str,
        nodes: Sequence[Any],
        edges: Sequence[Any] = (),
        *,
        width: SizeLike = 420.0,
        height: float = 280.0,
        top_down: bool = True,
        selected: int = -1,
    ) -> GraphResult:
        """A dependency/flow graph; edges are ``{"from": 0, "to": 1}``."""
        keep = self._frame_keepalive
        node_array, node_count = _pack(CuiGraphNode, nodes, keep)
        edge_array, edge_count = _pack(CuiGraphEdge, edges, keep)
        cell, ptr = _sel(selected, keep)
        opts = _opts(CuiGraphOpts, {}, keep, width=to_c_size(width), height=height, top_down=top_down, selected=ptr)
        out = CuiGraphResult()
        self._lib.nexa_graph_view_ex(
            self._ctx, id.encode("utf-8"), node_array, node_count, edge_array, edge_count, opts, ctypes.byref(out)
        )
        return GraphResult(out.clicked, out.activated, out.hovered, cell.value)

    # -- network & tracing -----------------------------------------------
    def waterfall(
        self,
        id: str,
        requests: Sequence[Any],
        *,
        width: SizeLike = 420.0,
        height: float = 260.0,
        selected: int = -1,
        dom_loaded: float = -1.0,
        loaded: float = -1.0,
    ) -> WaterfallResult:
        """A DevTools-style network waterfall; ``timing`` is the 6-phase breakdown."""
        keep = self._frame_keepalive
        array, count = _pack(CuiNetRequest, requests, keep)
        cell, ptr = _sel(selected, keep)
        opts = _opts(
            CuiWaterfallOpts,
            {},
            keep,
            width=to_c_size(width),
            height=height,
            selected=ptr,
            dom_loaded=dom_loaded,
            loaded=loaded,
        )
        out = CuiWaterfallResult()
        self._lib.nexa_waterfall_ex(self._ctx, id.encode("utf-8"), array, count, opts, ctypes.byref(out))
        return WaterfallResult(out.clicked, out.activated, out.hovered, cell.value)

    def trace_view(
        self,
        id: str,
        tracks: Sequence[Any],
        spans: Sequence[Any],
        view: Optional[Any] = None,
        selected: int = -1,
        *,
        width: SizeLike = 460.0,
        height: float = 260.0,
        row_height: float = 20.0,
        markers: Sequence[float] = (),
    ) -> TraceResult:
        """A flame/timeline trace viewer with zoom, pan and range marks."""
        keep = self._frame_keepalive
        track_array, track_count = _pack(CuiTraceTrack, tracks, keep)
        span_array, span_count = _pack(CuiTraceSpan, spans, keep)
        c_view = CuiTraceView()
        if view is not None:
            _fill(c_view, view, keep)
        marks = None
        if markers:
            marks = (ctypes.c_double * len(markers))(*markers)
            keep.append(marks)
        opts = _opts(
            CuiTraceOpts,
            {},
            keep,
            width=to_c_size(width),
            height=height,
            row_height=row_height,
            markers=ctypes.cast(marks, ctypes.POINTER(ctypes.c_double)) if marks else None,
            marker_count=len(markers),
        )
        c_selected = ctypes.c_int(int(selected))
        out = CuiTraceResult()
        self._lib.nexa_trace_view_ex(
            self._ctx,
            id.encode("utf-8"),
            track_array,
            track_count,
            span_array,
            span_count,
            ctypes.byref(c_view),
            ctypes.byref(c_selected),
            opts,
            ctypes.byref(out),
        )
        return TraceResult(c_view, c_selected.value, out.selection_changed, out.view_changed, out.hovered)

    # -- debugging -------------------------------------------------------
    def regex_tester(
        self,
        id: str,
        pattern: str = "",
        text: str = "",
        *,
        width: SizeLike = 420.0,
        height: float = 240.0,
        flags: int = 0,
    ) -> RegexTesterResult:
        """Live regex playground: pattern and text are editable, matches highlighted."""
        keep = self._frame_keepalive
        pcap, tcap = 512, 4096
        pbuf = ctypes.create_string_buffer(pattern.encode("utf-8"), pcap)
        tbuf = ctypes.create_string_buffer(text.encode("utf-8"), tcap)
        keep.extend((pbuf, tbuf))
        opts = _opts(CuiRegexTesterOpts, {}, keep, width=to_c_size(width), height=height, flags=int(flags))
        out = CuiRegexTesterResult()
        self._lib.nexa_regex_tester_ex(
            self._ctx, id.encode("utf-8"), pbuf, c_size_t(pcap), tbuf, c_size_t(tcap), opts, ctypes.byref(out)
        )
        error = out.error.decode("utf-8", "replace") if out.error else ""
        return RegexTesterResult(
            pbuf.value.decode("utf-8", "replace"), tbuf.value.decode("utf-8", "replace"), out.valid, out.matches, error
        )

    def test_explorer(
        self,
        id: str,
        items: Sequence[Any],
        *,
        width: SizeLike = 380.0,
        height: float = 280.0,
    ) -> TestExplorerResult:
        """A test tree with pass/fail badges and per-suite run buttons."""
        keep = self._frame_keepalive
        array, count = _pack(CuiTestItem, items, keep)
        opts = _opts(CuiTestExplorerOpts, {}, keep, width=to_c_size(width), height=height)
        out = CuiTestExplorerResult()
        self._lib.nexa_test_explorer_ex(self._ctx, id.encode("utf-8"), array, count, opts, ctypes.byref(out))
        return TestExplorerResult(
            out.selected, out.activated, out.run, bool(out.run_all), out.passed, out.failed, out.skipped, out.total
        )

    def stack_trace(
        self,
        id: str,
        frames: Sequence[Any],
        *,
        width: SizeLike = 460.0,
        title: str = "",
        message: str = "",
        lang: str = "",
    ) -> StackTraceResult:
        """A formatted stack trace; frames carry the source lines they show."""
        keep = self._frame_keepalive
        array, count = _pack(CuiStackFrame, frames, keep)
        opts = _opts(CuiStackTraceOpts, {}, keep, width=to_c_size(width), title=title, message=message, lang=lang)
        out = CuiStackTraceResult()
        self._lib.nexa_stack_trace_ex(self._ctx, id.encode("utf-8"), array, count, opts, ctypes.byref(out))
        return StackTraceResult(out.clicked)

    # -- HTTP ------------------------------------------------------------
    def request_bar(
        self,
        id: str,
        method: int = 0,
        url: str = "",
        *,
        width: SizeLike = 460.0,
        loading: bool = False,
        placeholder: str = "Enter a URL",
    ) -> RequestBarResult:
        """A method picker + URL field + Send button (the top of an API client)."""
        keep = self._frame_keepalive
        cap = 2048
        buf = ctypes.create_string_buffer(url.encode("utf-8"), cap)
        keep.append(buf)
        c_method = ctypes.c_int(int(method))
        opts = _opts(
            CuiRequestBarOpts,
            {},
            keep,
            width=to_c_size(width),
            loading=loading,
            placeholder=placeholder,
        )
        out = CuiRequestBarResult()
        self._lib.nexa_request_bar_ex(
            self._ctx, id.encode("utf-8"), ctypes.byref(c_method), buf, c_size_t(cap), opts, ctypes.byref(out)
        )
        return RequestBarResult(c_method.value, buf.value.decode("utf-8", "replace"), out.send, out.cancel, out.changed)

    def api_explorer(
        self,
        id: str,
        endpoints: Sequence[Any],
        *,
        width: SizeLike = 420.0,
        height: float = 300.0,
        selected: int = -1,
    ) -> ApiExplorerResult:
        """Browsable API reference; ``params`` is a list of ``{"name": …, "type": …}``."""
        keep = self._frame_keepalive
        array, count = _pack(CuiApiEndpoint, endpoints, keep)
        cell, ptr = _sel(selected, keep)
        opts = _opts(CuiApiExplorerOpts, {}, keep, width=to_c_size(width), height=height, selected=ptr)
        out = CuiApiExplorerResult()
        self._lib.nexa_api_explorer_ex(self._ctx, id.encode("utf-8"), array, count, opts, ctypes.byref(out))
        return ApiExplorerResult(out.selected, bool(out.try_it), cell.value)

    def feature_flags(
        self,
        id: str,
        flags: Sequence[Any],
        envs: Sequence[str] = (),
        *,
        width: SizeLike = 400.0,
        height: float = 260.0,
    ) -> FeatureFlagsResult:
        """Flag table with per-environment switches (``on``/``rollout`` are 8-slot lists)."""
        keep = self._frame_keepalive
        array, count = _pack(CuiFeatureFlag, flags, keep)
        env_array = None
        if envs:
            env_array = (ctypes.c_char_p * (len(envs) + 1))()
            for i, name in enumerate(envs):
                env_array[i] = name.encode("utf-8")
            keep.append(env_array)
        opts = _opts(CuiFeatureFlagsOpts, {}, keep, width=to_c_size(width), height=height)
        out = CuiFeatureFlagsResult()
        self._lib.nexa_feature_flags_ex(
            self._ctx,
            id.encode("utf-8"),
            array,
            count,
            ctypes.cast(env_array, ctypes.POINTER(ctypes.c_char_p)) if env_array else None,
            len(envs),
            opts,
            ctypes.byref(out),
        )
        return FeatureFlagsResult(out.flag, out.env)

    # -- operations ------------------------------------------------------
    def uptime_bars(
        self,
        id: str,
        services: Sequence[Any],
        *,
        width: SizeLike = 380.0,
        last_day: Optional[Date] = None,
    ) -> UptimeResult:
        """Status-page uptime bars; each service carries its daily uptime list."""
        keep = self._frame_keepalive
        items = list(services)
        array = (CuiUptimeService * max(1, len(items)))()
        for i, item in enumerate(items):
            data = dict(item) if isinstance(item, dict) else {
                key: getattr(item, key) for key in ("name", "days", "day_count") if hasattr(item, key)
            }
            days = data.pop("days", ())
            if days:
                day_arr = (ctypes.c_float * len(days))(*days)
                keep.append(day_arr)
                data["days"] = ctypes.cast(day_arr, ctypes.POINTER(ctypes.c_float))
                data["day_count"] = len(days)
            _fill(array[i], data, keep)
        keep.append(array)
        opts = _opts(CuiUptimeOpts, {}, keep, width=to_c_size(width))
        if last_day is not None:
            opts.last_day = to_c_date(last_day)
        out = CuiUptimeResult()
        self._lib.nexa_uptime_ex(self._ctx, id.encode("utf-8"), array, len(items), opts, ctypes.byref(out))
        return UptimeResult(out.service, out.day)

    def time_histogram(
        self,
        id: str,
        start: float,
        bucket_seconds: float,
        series: Sequence[Any],
        selected: Optional[Sequence[float]] = None,
        *,
        width: SizeLike = 460.0,
        height: float = 160.0,
        utc: bool = False,
    ) -> TimeHistogramResult:
        """Stacked bars over time with a draggable selection; ``counts`` per series."""
        keep = self._frame_keepalive
        items = list(series)
        array = (CuiHistogramSeries * max(1, len(items)))()
        for i, item in enumerate(items):
            data = dict(item) if isinstance(item, dict) else {
                key: getattr(item, key) for key in ("name", "counts", "tone") if hasattr(item, key)
            }
            counts = data.pop("counts", ())
            if counts:
                count_arr = (ctypes.c_float * len(counts))(*counts)
                keep.append(count_arr)
                data["counts"] = ctypes.cast(count_arr, ctypes.POINTER(ctypes.c_float))
            _fill(array[i], data, keep)
        keep.append(array)
        opts = _opts(CuiTimeHistogramOpts, {}, keep, width=to_c_size(width), height=height, utc=utc)
        sel_start = ctypes.c_double(float(selected[0]) if selected else 0.0)
        sel_end = ctypes.c_double(float(selected[1]) if selected else 0.0)
        out = CuiTimeHistogramResult()
        self._lib.nexa_time_histogram_ex(
            self._ctx,
            id.encode("utf-8"),
            ctypes.c_double(float(start)),
            ctypes.c_double(float(bucket_seconds)),
            len(items[0]["counts"]) if items and isinstance(items[0], dict) and items[0].get("counts") else 0,
            array,
            len(items),
            ctypes.byref(sel_start),
            ctypes.byref(sel_end),
            opts,
            ctypes.byref(out),
        )
        return TimeHistogramResult(sel_start.value, sel_end.value, bool(out.selection_changed), out.hovered)

    def coverage(
        self,
        id: str,
        files: Sequence[Any],
        *,
        width: SizeLike = 420.0,
        height: float = 260.0,
        low: float = 0.5,
        high: float = 0.8,
    ) -> CoverageResult:
        """A coverage report with per-file heat bars."""
        keep = self._frame_keepalive
        array, count = _pack(CuiCoverageFile, files, keep)
        opts = _opts(CuiCoverageOpts, {}, keep, width=to_c_size(width), height=height, low=low, high=high)
        out = CuiCoverageResult()
        self._lib.nexa_coverage_ex(self._ctx, id.encode("utf-8"), array, count, opts, ctypes.byref(out))
        return CoverageResult(out.activated, out.lines)

    def blame(
        self,
        id: str,
        lines: Sequence[str],
        line_commit: Sequence[int],
        commits: Sequence[Any],
        *,
        width: SizeLike = 460.0,
        height: float = 300.0,
        lang: str = "",
        now: int = 0,
        first_line: int = 1,
    ) -> BlameResult:
        """``git blame``: each source line tinted by the commit that last touched it."""
        keep = self._frame_keepalive
        text = (ctypes.c_char_p * (len(lines) + 1))()
        for i, line in enumerate(lines):
            text[i] = line.encode("utf-8") if isinstance(line, str) else line
        commits_of = (ctypes.c_int * max(1, len(line_commit)))(*line_commit)
        keep.extend((text, commits_of))
        array, count = _pack(CuiBlameCommit, commits, keep)
        opts = _opts(CuiBlameOpts, {}, keep, width=to_c_size(width), height=height, lang=lang, now=int(now), first_line=first_line)
        out = CuiBlameResult()
        self._lib.nexa_blame_ex(
            self._ctx,
            id.encode("utf-8"),
            text,
            commits_of,
            len(lines),
            array,
            count,
            opts,
            ctypes.byref(out),
        )
        return BlameResult(out.clicked, out.hovered)

    # -- editors ---------------------------------------------------------
    def kv_editor(
        self,
        id: str,
        pairs: Sequence[Any] = (),
        *,
        capacity: int = 32,
        key_placeholder: str = "Key",
        value_placeholder: str = "Value",
        no_toggles: bool = False,
        no_secrets: bool = False,
        read_only: bool = False,
        width: SizeLike = 320.0,
    ) -> KvEditorResult:
        """Editable key/value rows (env vars, headers); returns the new rows."""
        keep = self._frame_keepalive
        from .._cdefs import CuiKvPair

        items = list(pairs)
        capacity = max(capacity, len(items))
        array = (CuiKvPair * capacity)()
        for i, item in enumerate(items):
            _fill(array[i], item, keep)
        keep.append(array)
        count = ctypes.c_int(len(items))
        opts = _opts(
            CuiKvEditorOpts,
            {},
            keep,
            key_placeholder=key_placeholder,
            value_placeholder=value_placeholder,
            no_toggles=no_toggles,
            no_secrets=no_secrets,
            read_only=read_only,
            width=to_c_size(width),
        )
        changed = bool(
            self._lib.cui_kv_editor_ex(
                self._ctx, id.encode("utf-8"), array, ctypes.byref(count), capacity, opts
            )
        )
        rows = []
        for i in range(max(0, min(count.value, capacity))):
            rows.append(
                {
                    "key": array[i].key.decode("utf-8", "replace") if array[i].key else "",
                    "value": array[i].value.decode("utf-8", "replace") if array[i].value else "",
                    "enabled": bool(array[i].enabled),
                    "secret": bool(array[i].secret),
                }
            )
        return KvEditorResult(rows, changed)

    def query_builder(
        self,
        id: str,
        fields: Sequence[Any],
        nodes: Sequence[Any] = (),
        *,
        capacity: int = 32,
        width: SizeLike = 420.0,
        max_depth: int = 6,
        read_only: bool = False,
    ) -> QueryBuilderResult:
        """Nested AND/OR rule builder; returns the edited tree."""
        keep = self._frame_keepalive
        field_array, field_count = _pack(CuiQueryField, fields, keep)
        items = list(nodes)
        capacity = max(capacity, len(items))
        node_array = (CuiQueryNode * capacity)()
        for i, item in enumerate(items):
            _fill(node_array[i], item, keep)
        keep.append(node_array)
        count = ctypes.c_int(len(items))
        opts = _opts(CuiQueryOpts, {}, keep, width=to_c_size(width), max_depth=max_depth, read_only=read_only)
        changed = bool(
            self._lib.cui_query_builder_ex(
                self._ctx,
                id.encode("utf-8"),
                field_array,
                field_count,
                node_array,
                ctypes.byref(count),
                capacity,
                opts,
            )
        )
        rows = []
        for i in range(max(0, min(count.value, capacity))):
            node = node_array[i]
            rows.append(
                {
                    "depth": node.depth,
                    "group": bool(node.group),
                    "any": bool(node.any),
                    "field": node.field,
                    "op": node.op,
                    "value": node.value.decode("utf-8", "replace").split("\0", 1)[0],
                }
            )
        return QueryBuilderResult(rows, changed)


# ---- context-free query helpers ------------------------------------------


def query_text(fields: Sequence[Any], nodes: Sequence[Any]) -> str:
    """The human-readable form of a query tree: ``status is open and age > 3``."""
    keep: list = []
    field_array, field_count = _pack(CuiQueryField, fields, keep)
    node_array, node_count = _pack(CuiQueryNode, nodes, keep)
    cap = 2048
    buf = ctypes.create_string_buffer(cap)
    n = int(
        get_cdll().cui_query_text(field_array, field_count, node_array, node_count, ctypes.cast(buf, ctypes.c_char_p), c_size_t(cap))
    )
    return buf.raw[:n].decode("utf-8", "replace")


def query_match(fields: Sequence[Any], nodes: Sequence[Any], values: Sequence[str]) -> bool:
    """Whether ``values`` (one field value per field, in order) satisfies the query tree."""
    keep: list = []
    field_array, field_count = _pack(CuiQueryField, fields, keep)
    node_array, node_count = _pack(CuiQueryNode, nodes, keep)
    raw = (ctypes.c_char_p * (len(values) + 1))()
    for i, value in enumerate(values):
        raw[i] = value.encode("utf-8")
    keep.append(raw)
    return bool(get_cdll().cui_query_match(field_array, field_count, node_array, node_count, raw))


def query_op_name(query_type: int, op: int) -> str:
    """``"is not"``, ``">"``… — the label of an operator on a field type."""
    text = get_cdll().cui_query_op_name(int(query_type), int(op))
    return text.decode("utf-8", "replace") if text else ""


def trace_sort(spans: Sequence[Any]) -> None:
    """Sort trace spans in place is not possible across the FFI — use the C array form."""
    raise NotImplementedError("sort the span sequence in Python before passing it to trace_view()")


__all__ = [
    "DevtoolsMixin",
    "ProblemsResult",
    "PipelineResult",
    "ScheduleResult",
    "KeymapResult",
    "CommitGraphResult",
    "GraphResult",
    "WaterfallResult",
    "TraceResult",
    "RegexTesterResult",
    "TestExplorerResult",
    "StackTraceResult",
    "RequestBarResult",
    "UptimeResult",
    "TimeHistogramResult",
    "CoverageResult",
    "BlameResult",
    "FeatureFlagsResult",
    "ApiExplorerResult",
    "KvEditorResult",
    "QueryBuilderResult",
    "query_text",
    "query_match",
    "query_op_name",
]
