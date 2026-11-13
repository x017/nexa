"""AI & LLM agent interface components: reasoning, tool calls, plans, sources, composer, voice orb."""

from __future__ import annotations

import ctypes
from ctypes import c_float, c_int
from typing import Optional, Sequence, Tuple

from .._cdefs import (
    CuiAgentPlanOpts,
    CuiAgentStatusOpts,
    CuiComposerOpts,
    CuiContextOpts,
    CuiModel,
    CuiModelPickerOpts,
    CuiPlanStep,
    CuiPromptSuggestion,
    CuiPromptSuggestionsOpts,
    CuiReasoningOpts,
    CuiResponseActionsOpts,
    CuiSource,
    CuiToolCallOpts,
    CuiVizItem,
    CuiVoiceOrbOpts,
    encode_opt,
    encode_str,
    encode_str_array,
    make_text_buffer,
    to_c_color,
    to_c_size,
)
from ..scopes import ConditionalScope
from ..types import (
    ColorLike,
    ComposerFlags,
    ComposerResult,
    ModelInfo,
    Placement,
    PlanStep,
    PromptSuggestion,
    ResponseActionFlags,
    SizeLike,
    Source,
    TaskStatus,
    VizItem,
    VoiceState,
)


class AIMixin:
    __slots__ = ()

    def reasoning(
        self,
        id: str,
        *,
        thinking: bool = False,
        seconds: float = 0.0,
        title: Optional[str] = None,
    ) -> ConditionalScope:
        keep = self._frame_keepalive
        opts = CuiReasoningOpts()
        opts.thinking = bool(thinking)
        opts.seconds = float(seconds)
        opts.title = encode_opt(title, keep)
        keep.append(opts)
        vis = bool(self._lib.cui_reasoning_begin(self._ctx, encode_str(id, keep), ctypes.byref(opts)))
        return ConditionalScope(self._ctx, self._lib.cui_reasoning_end, vis)

    def tool_call(
        self,
        id: str,
        name: str,
        *,
        status: TaskStatus = TaskStatus.DONE,
        icon: Optional[str] = None,
        detail: Optional[str] = None,
        input_text: Optional[str] = None,
        output_text: Optional[str] = None,
        seconds: float = 0.0,
    ) -> None:
        keep = self._frame_keepalive
        opts = CuiToolCallOpts()
        opts.status = int(status)
        opts.icon = encode_opt(icon, keep)
        opts.detail = encode_opt(detail, keep)
        opts.input = encode_opt(input_text, keep)
        opts.output = encode_opt(output_text, keep)
        opts.seconds = float(seconds)
        keep.append(opts)
        self._lib.cui_tool_call_ex(self._ctx, encode_str(id, keep), encode_str(name, keep), ctypes.byref(opts))

    def agent_plan(
        self,
        id: str,
        steps: Sequence[PlanStep],
        *,
        title: Optional[str] = None,
    ) -> int:
        keep = self._frame_keepalive
        n = len(steps)
        arr = (CuiPlanStep * n)()
        for i, st in enumerate(steps):
            arr[i].title = encode_str(st.title, keep)
            arr[i].detail = encode_opt(st.detail, keep)
            arr[i].status = int(st.status)
        opts = CuiAgentPlanOpts(0, encode_opt(title, keep))
        keep.extend((arr, opts))
        return int(self._lib.cui_agent_plan_ex(self._ctx, encode_str(id, keep), arr, n, ctypes.byref(opts)))

    def agent_status(
        self,
        text: str,
        *,
        status: TaskStatus = TaskStatus.RUNNING,
        seconds: float = 0.0,
        icon: Optional[str] = None,
    ) -> None:
        keep = self._frame_keepalive
        opts = CuiAgentStatusOpts()
        opts.status = int(status)
        opts.seconds = float(seconds)
        opts.icon = encode_opt(icon, keep)
        keep.append(opts)
        self._lib.cui_agent_status_ex(self._ctx, encode_str(text, keep), ctypes.byref(opts))

    def source_list(self, id: str, sources: Sequence[Source]) -> int:
        keep = self._frame_keepalive
        n = len(sources)
        arr = (CuiSource * n)()
        for i, src in enumerate(sources):
            arr[i].title = encode_str(src.title, keep)
            arr[i].url = encode_opt(src.url, keep)
            arr[i].snippet = encode_opt(src.snippet, keep)
        keep.append(arr)
        clicked = int(self._lib.cui_source_list(self._ctx, encode_str(id, keep), arr, n))
        self._record_change(clicked >= 0)
        return clicked

    def citation(self, number: int, source: Source) -> bool:
        keep = self._frame_keepalive
        c_src = CuiSource(
            encode_str(source.title, keep),
            encode_opt(source.url, keep),
            encode_opt(source.snippet, keep),
        )
        keep.append(c_src)
        clicked = bool(self._lib.cui_citation(self._ctx, int(number), ctypes.byref(c_src)))
        self._record_change(clicked)
        return clicked

    def context_meter(
        self,
        id: str,
        used: float,
        limit: float,
        *,
        parts: Optional[Sequence[VizItem]] = None,
        unit: Optional[str] = None,
    ) -> None:
        keep = self._frame_keepalive
        opts = CuiContextOpts()
        if parts:
            n = len(parts)
            arr = (CuiVizItem * n)()
            for i, p in enumerate(parts):
                arr[i].label = encode_str(p.label, keep)
                arr[i].value = float(p.value)
                arr[i].color = to_c_color(p.color)
            keep.append(arr)
            opts.parts = arr
            opts.part_count = n
        opts.unit = encode_opt(unit, keep)
        keep.append(opts)
        self._lib.cui_context_meter_ex(
            self._ctx, encode_str(id, keep), float(used), float(limit), ctypes.byref(opts)
        )

    def response_actions(
        self,
        id: str,
        *,
        copy_text: Optional[str] = None,
        vote: int = 0,
        no_regenerate: bool = False,
        no_share: bool = False,
    ) -> Tuple[ResponseActionFlags, int]:
        """Answer action bar; returns ``(flags, updated_vote)`` where vote is ``-1``, ``0``, or ``1``."""
        keep = self._frame_keepalive
        c_vote = c_int(int(vote))
        opts = CuiResponseActionsOpts()
        opts.copy_text = encode_opt(copy_text, keep)
        opts.vote = ctypes.pointer(c_vote)
        opts.no_regenerate = bool(no_regenerate)
        opts.no_share = bool(no_share)
        keep.extend((c_vote, opts))
        flags = ResponseActionFlags(int(self._lib.cui_response_actions_ex(
            self._ctx, encode_str(id, keep), ctypes.byref(opts)
        )))
        self._record_change(bool(flags))
        return flags, int(c_vote.value)

    def prompt_suggestions(
        self,
        id: str,
        items: Sequence[PromptSuggestion],
        *,
        columns: int = 0,
    ) -> int:
        keep = self._frame_keepalive
        n = len(items)
        arr = (CuiPromptSuggestion * n)()
        for i, it in enumerate(items):
            arr[i].icon = encode_opt(it.icon, keep)
            arr[i].title = encode_str(it.title, keep)
            arr[i].detail = encode_opt(it.detail, keep)
        opts = CuiPromptSuggestionsOpts(0, int(columns))
        keep.extend((arr, opts))
        chosen = int(self._lib.cui_prompt_suggestions_ex(
            self._ctx, encode_str(id, keep), arr, n, ctypes.byref(opts)
        ))
        self._record_change(chosen >= 0)
        return chosen

    def model_picker(
        self,
        id: str,
        models: Sequence[ModelInfo],
        selected: int,
        *,
        ghost: bool = False,
        placement: Placement = Placement.BOTTOM_START,
    ) -> int:
        keep = self._frame_keepalive
        n = len(models)
        arr = (CuiModel * n)()
        for i, m in enumerate(models):
            arr[i].name = encode_str(m.name, keep)
            arr[i].detail = encode_opt(m.detail, keep)
            arr[i].badge = encode_opt(m.badge, keep)
            arr[i].icon = encode_opt(m.icon, keep)
        c_sel = c_int(int(selected))
        opts = CuiModelPickerOpts(0, bool(ghost), int(placement))
        keep.extend((arr, opts))
        changed = bool(self._lib.cui_model_picker_ex(
            self._ctx, encode_str(id, keep), arr, n, ctypes.byref(c_sel), ctypes.byref(opts)
        ))
        self._record_change(changed)
        return int(c_sel.value)

    def chat_composer(
        self,
        id: str,
        text: str,
        *,
        placeholder: Optional[str] = None,
        busy: bool = False,
        attachments: Optional[Sequence[str]] = None,
        models: Optional[Sequence[ModelInfo]] = None,
        model: int = 0,
        max_lines: int = 0,
        width: SizeLike = None,
        max_bytes: int = 8192,
        mic: bool = False,
        recording: bool = False,
        levels: Optional[Sequence[float]] = None,
        record_seconds: float = 0.0,
    ) -> ComposerResult:
        """Chat composer. ``mic=True`` adds a microphone button; while
        ``recording`` it shows the recorder instead of the text — a recording
        dot, the time, the mic ``levels`` scrolling by, Cancel and Send, at
        the same height. The result flags carry ``RECORD``/``CANCEL``/``VOICE``
        (CUI post-1.4).
        """
        keep = self._frame_keepalive
        buf, cap = make_text_buffer(text, max_bytes)
        c_removed = c_int(-1)
        c_model = c_int(int(model))
        opts = CuiComposerOpts()
        opts.placeholder = encode_opt(placeholder, keep)
        opts.busy = bool(busy)
        opts.mic = bool(mic)
        opts.recording = bool(recording)
        if levels:
            lv = (c_float * len(levels))(*(float(v) for v in levels))
            opts.levels = lv
            opts.level_count = len(levels)
            keep.append(lv)
        opts.record_seconds = float(record_seconds)
        if attachments:
            att_arr, att_n = encode_str_array(attachments, keep)
            opts.attachments = att_arr
            opts.attachment_count = att_n
        opts.removed = ctypes.pointer(c_removed)
        if models:
            nm = len(models)
            m_arr = (CuiModel * nm)()
            for i, m in enumerate(models):
                m_arr[i].name = encode_str(m.name, keep)
                m_arr[i].detail = encode_opt(m.detail, keep)
                m_arr[i].badge = encode_opt(m.badge, keep)
                m_arr[i].icon = encode_opt(m.icon, keep)
            keep.append(m_arr)
            opts.models = m_arr
            opts.model_count = nm
            opts.model = ctypes.pointer(c_model)
        opts.max_lines = int(max_lines)
        opts.width = to_c_size(width)
        keep.extend((c_removed, c_model, opts))
        raw_flags = int(self._lib.cui_chat_composer_ex(
            self._ctx, encode_str(id, keep), buf, cap, ctypes.byref(opts)
        ))
        flags = ComposerFlags(raw_flags)
        new_text = buf.value.decode("utf-8", errors="replace")
        self._record_change(bool(flags) or new_text != text)
        if flags & ComposerFlags.SEND:
            self._last_submitted = True
        return ComposerResult(new_text, flags, int(c_model.value), int(c_removed.value))

    def voice_orb(
        self,
        id: str,
        state: VoiceState = VoiceState.IDLE,
        level: float = 0.0,
        *,
        size: float = 0.0,
        color: ColorLike = None,
        fg: ColorLike = None,
    ) -> bool:
        if fg is not None:
            color = fg
        keep = self._frame_keepalive
        opts = CuiVoiceOrbOpts()
        opts.size = float(size)
        opts.color = to_c_color(color)
        keep.append(opts)
        clicked = bool(self._lib.cui_voice_orb_ex(
            self._ctx, encode_str(id, keep), int(state), float(level), ctypes.byref(opts)
        ))
        self._record_change(clicked)
        return clicked
