# Concurrency, Multithreading, `asyncio`, & Networking

Desktop GUIs freeze the moment you run a slow HTTP request, SQLite query, or LLM stream on the UI thread.

`nexa` is engineered from the C99 layer up for responsive, zero-CPU-idle concurrency:
1. **Every native C call releases Python's GIL**, so background Python threads run in parallel during layout and software rasterization.
2. **Cross-thread OS wakeup (`app.wake()`)**: When your app is idle, it sleeps inside the OS event queue at **0% CPU**. Calling `app.wake()` from *any* thread writes to a wakeup pipe (`X11`), posts `WM_NULL` (`Win32`), or posts an `NSEvent` (`Cocoa`) to render a new frame immediately.
3. **UI-thread callback marshaling (`app.call_soon_threadsafe(fn)`)**: Schedules state mutations to execute cleanly on the UI thread right before the next frame—eliminating race conditions without manual locks!

---

## Pattern 1: `BackgroundRunner` (Threads, Streaming & HTTP JSON)

`ui.BackgroundRunner.for_app(app)` (or `self.runner` inside any OOP `ui.Application`) manages a bounded pool of daemon threads and delivers `on_done`, `on_item`, and `on_error` callbacks **on the UI thread**, waking the window automatically.

### Complete Runnable Example: Async Job + Token Streaming

```python
import time
from typing import Iterator
import nexa as ui

def main() -> None:
    app = ui.App("Background Workers", width=680, height=440, theme=ui.ThemeMode.DARK, accent=ui.Accent.VIOLET)
    runner = ui.BackgroundRunner.for_app(app, max_workers=4)

    result_text = "Click a button to start background work."
    stream_buf = ""
    job_handle: ui.TaskHandle[str] | None = None
    stream_handle: ui.TaskHandle[None] | None = None

    def compute_report() -> str:
        time.sleep(0.4)  # Runs off-thread; UI stays silky smooth at 60fps!
        return "Compiled 42 modules in 0.40s"

    def token_generator() -> Iterator[str]:
        for word in ["Streaming", "tokens", "safely", "onto", "the", "UI", "thread!"]:
            time.sleep(0.06)
            yield word + " "

    def draw(ctx: ui.UI) -> None:
        nonlocal result_text, stream_buf, job_handle, stream_handle

        with ctx.column(width=ui.FILL, height=ui.FILL, pad=24, gap=16, bg=ui.Color.BACKGROUND):
            ctx.heading("Non-Blocking Background Runner", level=2)

            with ctx.row(gap=12, align=ui.Align.CENTER):
                # TaskHandle.button_status maps PENDING/RUNNING/DONE/FAILED -> StatusButton states!
                btn_state = job_handle.button_status if job_handle else ui.Status.IDLE
                if ctx.status_button("Run Background Job", btn_state, icon=ui.Icon.PLAY):
                    def _on_done(msg: str) -> None:
                        nonlocal result_text
                        result_text = msg
                    job_handle = runner.submit(compute_report, on_done=_on_done)

                streaming = stream_handle is not None and stream_handle.running
                if not streaming:
                    if ctx.button("Stream Tokens", icon=ui.Icon.SPARKLES):
                        stream_buf = ""
                        def _on_tok(tok: str) -> None:
                            nonlocal stream_buf
                            stream_buf += tok
                        stream_handle = runner.stream(token_generator, on_item=_on_tok)
                else:
                    if ctx.button("Stop Stream", variant=ui.ButtonVariant.DANGER, icon=ui.Icon.X):
                        stream_handle.cancel()

            with ctx.card(pad=16, gap=8, width=ui.FILL):
                ctx.secondary("Job Result")
                ctx.text(result_text)

            with ctx.card(pad=16, gap=8, width=ui.FILL):
                ctx.secondary("Live Token Stream")
                ctx.text(stream_buf or "Idle...")

    try:
        app.run(draw)
    finally:
        runner.close()
        app.close()

if __name__ == "__main__":
    main()
```

### Built-in Zero-Dependency HTTP Helpers (`fetch_json` & `fetch_bytes`)

Need to call a REST API without pulling in third-party packages? `BackgroundRunner` includes stdlib `urllib`-backed `fetch_json` and `fetch_bytes`:

```python
handle = runner.fetch_json(
    "https://api.example.com/v1/items",
    method="POST",
    payload={"limit": 25},
    headers={"Authorization": "Bearer ..."},
    timeout=10.0,
    on_done=lambda data: state.update({"items": data}),
    on_error=lambda err: ctx.toast(str(err), tone=ui.Tone.DANGER),
)
```

---

## Pattern 2: Producer-Consumer `Channel[T]` & Thread-Safe `LogBuffer`

When a long-lived background thread (e.g., a WebSocket listener, serial port reader, or file watcher) emits high-frequency events:

- **`ui.Channel(maxsize=256, wake=app.wake)`**: Thread-safe MPSC queue. Background threads call `channel.send(item)` (or non-blocking `channel.try_send(item)`), and your `draw()` function drains all queued items in one fast batch via `for msg in channel.drain():`.
- **`ui.LogBuffer(max_lines=4096)`**: C-heap ring buffer protected by a lightweight lock. Any thread can call `log.info(...)`, `log.warn(...)`, `log.error(...)` directly while `ctx.log_view("console", log)` renders filterable, auto-scrolling logs at 60fps!

---

## Pattern 3: Cooperative Single-Thread `asyncio` (`await app.run_async(...)`)

Already using `httpx.AsyncClient`, `aiohttp`, `websockets`, or `asyncio.StreamReader`? Run `nexa` **cooperatively inside your existing `asyncio` event loop**—zero extra threads, zero locks!

```python
import asyncio
import nexa as ui

async def main() -> None:
    app = ui.App("Asyncio Cooperative UI", width=560, height=320, theme=ui.ThemeMode.DARK, accent=ui.Accent.BLUE)
    ticks = 0
    status = "Waiting for async task..."

    async def background_poller() -> None:
        nonlocal ticks, status
        while True:
            await asyncio.sleep(0.5)
            ticks += 1
            status = f"Async heartbeat #{ticks}"
            app.wake()  # Triggers an immediate UI frame!

    poller = asyncio.create_task(background_poller())

    def draw(ctx: ui.UI) -> None:
        with ctx.column(width=ui.FILL, height=ui.FILL, pad=24, gap=12, bg=ui.Color.BACKGROUND):
            ctx.heading("Cooperative asyncio + nexa", level=2)
            ctx.badge(status, tone=ui.Tone.INFO, dot=True)

    try:
        await app.run_async(draw)
    finally:
        poller.cancel()
        app.close()

if __name__ == "__main__":
    asyncio.run(main())
```

OOP `ui.Application` subclasses also support `await MyApp().run_async()` out of the box!

---

## Pattern 4: Dedicated-Thread `AsyncBridge`

If your main thread runs synchronous `app.run(draw)` (ensuring the OS window loop never waits on a slow coroutine) while third-party `async def` coroutines or async generators run on a dedicated background `asyncio` event loop thread, use `nexa.aio.AsyncBridge`:

```python
from nexa.aio import AsyncBridge

bridge = AsyncBridge.for_app(app)  # Or `self.async_bridge` on any `ui.Application`!

# Schedule a coroutine on the background asyncio loop; `on_done` runs on the UI thread:
handle = bridge.spawn(fetch_user_profile(user_id), on_done=lambda prof: set_profile(prof))

# Stream an async generator (`async for chunk in ...`) onto the UI thread:
stream_h = bridge.stream(llm_client.stream_chat(messages), on_item=chunks.append)
```
