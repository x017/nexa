"""AI Agent Assistant with live non-blocking background token streaming (port of assistant.c)."""

from __future__ import annotations

import time
from typing import Iterator

import yapps as ui


MODELS = [
    ui.Model("Atlas Pro", "Deep reasoning, code & citations", badge="New", icon=ui.Icon.LAYERS),
    ui.Model("Atlas Fast", "Sub-second interactive responses", icon=ui.Icon.ZAP),
    ui.Model("Atlas Local", "On-device quantized runtime", icon=ui.Icon.CPU),
]

SOURCES = [
    ui.Source(
        "Immediate-mode UI layout in a single pass",
        "https://fieldnotes.dev/immediate-mode",
        "Single-pass constraint propagation and batched SDF quad rendering.",
    ),
    ui.Source(
        "Critically damped springs for responsive interfaces",
        "https://motionbook.dev/springs",
        "Preserving continuous velocity across interrupted user gestures.",
    ),
]

SUGGESTIONS = [
    ui.PromptSuggestion("Explain why yapps binaries stay under 1 MB", detail="Architecture & linker GC", icon=ui.Icon.ZAP),
    ui.PromptSuggestion("Draft an asyncio streaming WebSocket client", detail="Python concurrency pattern", icon=ui.Icon.CODE),
    ui.PromptSuggestion("Compare software vs OpenGL 3.3 rasterizer", detail="Rendering pipeline", icon=ui.Icon.LAYERS),
]


def main() -> None:
    app = ui.App("Muse AI — yapps", width=1160, height=740, theme=ui.ThemeMode.DARK, accent=ui.Accent.VIOLET)
    runner = ui.BackgroundRunner.for_app(app)

    draft = ""
    model_idx = 0
    vote = 0
    attachments = ["architecture.md"]
    history: list[dict] = []
    active_stream: ui.TaskHandle | None = None

    def stream_agent_turn(prompt: str) -> None:
        nonlocal active_stream
        turn = {
            "prompt": prompt,
            "thinking": True,
            "think_sec": 0.0,
            "tool_status": ui.TaskStatus.RUNNING,
            "answer": "",
        }
        history.append(turn)
        t0 = time.monotonic()

        chunks = (
            f"Great question regarding **{prompt[:48]}**.\n\n"
            "1. Layout, text shaping, and SDF draw-list generation execute in compiled C99 while releasing Python's GIL.\n"
            "2. Only compact value objects cross the ABI boundary each frame, keeping CPU usage near 0% when idle.\n"
            "3. Background threads and asyncio tasks wake the native event loop via `app.wake()` as tokens arrive."
        ).split(" ")

        def _gen() -> Iterator[tuple[str, str, float]]:
            # Simulate thinking + tool execution + token stream off the UI thread!
            time.sleep(0.08)
            yield ("tool_done", "", time.monotonic() - t0)
            for word in chunks:
                time.sleep(0.015)
                yield ("token", word + " ", time.monotonic() - t0)

        def _on_item(ev: tuple[str, str, float]) -> None:
            kind, payload, elapsed = ev
            turn["think_sec"] = round(elapsed, 1)
            if kind == "tool_done":
                turn["thinking"] = False
                turn["tool_status"] = ui.TaskStatus.DONE
            else:
                turn["answer"] += payload

        active_stream = runner.stream(_gen, on_item=_on_item)

    def draw(ctx: ui.UI) -> None:
        nonlocal draft, model_idx, vote, active_stream
        busy = active_stream is not None and active_stream.running

        with ctx.row(width=ui.FILL, height=ui.FILL, bg=ui.Color.BACKGROUND):
            # Conversation workspace
            with ctx.column(width=ui.GROW(3), height=ui.FILL):
                with ctx.row(width=ui.FILL, pad_x=20, pad_y=12, gap=10, align=ui.Align.CENTER):
                    ctx.icon(ui.Icon.SPARKLES, 18, ui.Color.ACCENT)
                    ctx.text("Muse Agent", font=ui.FontRole.MEDIUM, size=15)
                    model_idx = ctx.model_picker("top_model", MODELS, model_idx, ghost=True)
                    ctx.spacer()
                    ctx.context_meter(
                        "ctx_ring", 18400, 128000, unit="tok",
                        parts=[ui.VizItem("System", 4200), ui.VizItem("Repo", 9800), ui.VizItem("Chat", 4400)],
                    )
                    ctx.theme_toggle()

                ctx.separator()

                with ctx.scroll("chat_scroll", width=ui.FILL, height=ui.FILL, pad=24, gap=18):
                    if not history:
                        ctx.heading("What shall we build today?", level=2)
                        chosen = ctx.prompt_suggestions("starters", SUGGESTIONS, columns=3)
                        if chosen >= 0:
                            stream_agent_turn(SUGGESTIONS[chosen].title)
                    else:
                        for i, turn in enumerate(history):
                            with ctx.id_scope(f"turn_{i}"):
                                ctx.chat_message(turn["prompt"], mine=True, time="Just now")
                                with ctx.reasoning("think", thinking=turn["thinking"], seconds=turn["think_sec"]) as r:
                                    if r:
                                        ctx.secondary("Inspecting C99 bridge symbols and frame allocator invariants...")
                                ctx.tool_call(
                                    "search_repo", "workspace.search",
                                    status=turn["tool_status"],
                                    detail="csrc/yapps_bridge.c",
                                    input_text='{"query": "cui_app_wake"}',
                                    output_text='{"matches": 6, "latency_ms": 4}',
                                    seconds=0.12,
                                )
                                if turn["answer"]:
                                    ctx.text(turn["answer"], selectable=True, width=ui.FILL)
                                    ctx.source_list("srcs", SOURCES)
                                    _, vote = ctx.response_actions("acts", copy_text=turn["answer"], vote=vote)

                # Composer bar
                with ctx.box(width=ui.FILL, pad_x=24, pad_bottom=18):
                    comp = ctx.chat_composer(
                        "composer", draft,
                        placeholder="Ask anything... (Enter to send)",
                        busy=busy,
                        attachments=attachments,
                        models=MODELS,
                        model=model_idx,
                    )
                    draft = comp.text
                    model_idx = comp.model
                    if 0 <= comp.removed < len(attachments):
                        attachments.pop(comp.removed)
                    if comp.sent and draft.strip():
                        q = draft.strip()
                        draft = ""
                        stream_agent_turn(q)
                    elif comp.stopped and active_stream is not None:
                        active_stream.cancel()

            # Right inspector rail
            with ctx.column(width=300, height=ui.FILL, bg=ui.Color.SURFACE_MUTED, pad=16, gap=16):
                ctx.agent_status(
                    "Streaming tokens..." if busy else "Ready",
                    status=ui.TaskStatus.RUNNING if busy else ui.TaskStatus.DONE,
                    seconds=active_stream.elapsed if active_stream else 0.0,
                )
                ctx.agent_plan(
                    "plan",
                    [
                        ui.PlanStep("Bind C99 shared library", status=ui.TaskStatus.DONE),
                        ui.PlanStep("Execute layout & SDF batching", status=ui.TaskStatus.DONE),
                        ui.PlanStep(
                            "Stream response chunks",
                            status=ui.TaskStatus.RUNNING if busy else ui.TaskStatus.DONE,
                        ),
                    ],
                    title="Execution Plan",
                )
                ctx.spacer()
                with ctx.card(pad=16, gap=10, align=ui.Align.CENTER):
                    ctx.secondary("Voice Mode")
                    ctx.voice_orb(
                        "orb",
                        ui.VoiceState.SPEAKING if busy else ui.VoiceState.IDLE,
                        level=0.65 if busy else 0.1,
                        size=72,
                    )

    try:
        app.run(draw)
    finally:
        runner.close()
        app.close()


if __name__ == "__main__":
    main()
