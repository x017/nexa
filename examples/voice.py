"""Talk — the CUI post-1.4 voice components in one window.

``voice_wave`` (clip mode with a live playhead), ``voice_note`` (play/pause,
seek, speed chip), ``voice_session`` (listening/thinking/speaking timeline)
and the chat composer's built-in ``mic`` recorder.

    python examples/voice.py

The audio is synthetic: levels come from a sine envelope, playback position
advances with wall time, and clicking a waveform seeks it.  Runs headless with
``NEXA_HEADLESS=1 CUI_SCREENSHOT=out.png``.
"""

from __future__ import annotations

import math
import time

import nexa as ui


def _levels(count: int, seed_phase: float = 0.0) -> list:
    """A synthetic loudness envelope, 0..1, oldest first."""
    out = []
    for i in range(count):
        t = i / max(count - 1, 1)
        env = math.sin(t * math.pi) ** 0.7
        wob = 0.55 + 0.45 * math.sin(t * 40.0 + seed_phase)
        out.append(max(0.02, min(1.0, env * wob)))
    return out


def main() -> None:
    started = time.time()
    clip = _levels(160, 1.0)
    note_levels = _levels(72, 2.5)
    muted = [False]
    recording = False
    composer_text = ""

    def draw(ctx: ui.UI) -> None:
        nonlocal recording, composer_text
        elapsed = time.time() - started
        ctx.request_redraw()  # waveforms and playback keep moving

        with ctx.column(width=ui.FILL, height=ui.FILL, pad=20, gap=14, bg=ui.Color.BACKGROUND):
            with ctx.row(align=ui.Align.CENTER, width=ui.FILL):
                ctx.heading("Talk", level=2)
                ctx.badge("voice", tone=ui.Tone.TEAL, dot=True)
                ctx.spacer()
                ctx.secondary("one dot waveform, real levels only")

            with ctx.row(width=ui.FILL, gap=16):
                # ---- clip waveform -------------------------------------
                with ctx.card(width=ui.GROW(3), pad=16, gap=10):
                    ctx.secondary("Waveform — click to seek")
                    progress = (elapsed * 0.14) % 1.0
                    new_progress = ctx.voice_wave(
                        "clip", clip, clip=True, progress=progress, width=ui.FILL, color="#22d3ee"
                    )
                    with ctx.row(width=ui.FILL):
                        ctx.text(f"{progress * 42:5.1f}s / 42.0s", size=11, color=ui.Color.TEXT_MUTED)
                        ctx.spacer()
                        if new_progress != progress:
                            ctx.text("seeked!", size=11, color=ui.Color.ACCENT)

                    ctx.secondary("Two voices, one timeline")
                    owners = [0 if (i % 24) < 14 else 1 for i in range(64)]
                    ctx.voice_wave("duet", clip[:64], owners=owners, width=ui.FILL)

                # ---- note + session ------------------------------------
                with ctx.card(width=ui.GROW(2), pad=16, gap=10):
                    ctx.secondary("Voice note")
                    playing = (int(elapsed) % 7) < 4
                    note = ctx.voice_note(
                        "note", note_levels, 6.5,
                        position=(elapsed % 6.5) if playing else 1.2,
                        speed=1.5, playing=playing, mine=True, width=ui.FILL,
                    )
                    ctx.text(
                        f"{note.position:4.1f}s of 6.5s · {note.speed:g}x · "
                        + ("playing" if note.playing else "paused"),
                        size=11, color=ui.Color.TEXT_MUTED,
                    )

                    ctx.secondary("Session")
                    phase = int(elapsed / 2.5) % 3
                    state = (ui.VoiceState.LISTENING, ui.VoiceState.THINKING, ui.VoiceState.SPEAKING)[phase]
                    ctx.voice_session(
                        "sess", state, _levels(48, elapsed),
                        label="with Nexa", you="you", assistant="nexa",
                        transcript="How far along is the sync?",
                        upcoming="Pulling the 69 commits now…" if state != ui.VoiceState.SPEAKING else None,
                        muted=muted, width=ui.FILL,
                    )
                    if ctx.switch("Mute", muted[0]):
                        muted[0] = not muted[0]

            # ---- composer with mic -------------------------------------
            with ctx.card(width=ui.FILL, pad=14, gap=8):
                ctx.secondary("Composer with microphone")
                levels = _levels(32, elapsed * 6.0)
                res = ctx.chat_composer(
                    "composer", composer_text,
                    placeholder="Say something…", mic=True,
                    recording=recording, levels=levels if recording else None,
                    record_seconds=(elapsed % 60) if recording else 0.0,
                )
                composer_text = res.text
                if res.flags & ui.ComposerFlags.RECORD:
                    recording = True
                elif res.flags & ui.ComposerFlags.CANCEL:
                    recording = False
                elif res.flags & (ui.ComposerFlags.VOICE | ui.ComposerFlags.SEND):
                    recording = False
                    ctx.toast(
                        "Sent", description=(res.text or "voice message")[:60], tone=ui.Tone.SUCCESS
                    )

    with ui.App("Talk — nexa", width=1000, height=760, theme=ui.ThemeMode.DARK, accent=ui.Accent.CORAL) as app:
        app.run(draw)


if __name__ == "__main__":
    main()
