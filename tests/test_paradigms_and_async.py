"""Tests for Functional API, OOP Components/Router/Store, Threading/Channels, Asyncio & Examples."""

from __future__ import annotations

import asyncio
import json
import os
import pathlib
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import nexa as ui
from nexa.aio import AsyncBridge


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_functional_api_and_oop_component_isolation() -> None:
    """Two OOP Component instances with identical internal widget labels must not collide on IDs."""

    class CounterCard(ui.Component):
        def __init__(self, key: str, start: int = 0) -> None:
            super().__init__(key)
            self.value = start
            self.mounted_count = 0
            self.btn_rect = ui.Rect()

        def on_mount(self, ctx: ui.UI) -> None:
            self.mounted_count += 1

        def build(self, ctx: ui.UI) -> int:
            # Functional top-level calls inside an OOP component work seamlessly too!
            with ui.card(pad=12, gap=8):
                ui.heading(f"Val: {self.value}", level=4)
                if ui.button("Increment"):  # Same label in both instances!
                    self.value += 1
                self.btn_id = ctx.last_id
            return self.value

    c1 = CounterCard("counter_a", 10)
    c2 = CounterCard("counter_b", 50)

    with ui.SoftwareRenderer() as sw, ui.UI(width=500, height=300, renderer=sw) as ctx:
        with ctx.frame():
            with ui.row(gap=16, pad=16):
                c1()
                c2()
        assert c1.mounted_count == 1 and c2.mounted_count == 1
        r1 = ctx.get_rect(c1.btn_id)
        r2 = ctx.get_rect(c2.btn_id)
        assert c1.btn_id != c2.btn_id and r1 != r2 and r2.w > 0

        # Click ONLY counter_b's "Increment" button!
        ctx.input_click(r2.x + 10, r2.y + 10)
        with ctx.frame():
            with ui.row(gap=16, pad=16):
                c1()
                c2()
        ctx.input_mouse_button(ui.MouseButton.LEFT, False)
        with ctx.frame():
            with ui.row(gap=16, pad=16):
                c1()
                c2()

        assert c1.value == 10
        assert c2.value == 51


def test_router_and_store_reactivity() -> None:
    events: list[str] = []

    class HomeView(ui.View):
        def on_enter(self, params: dict) -> None:
            events.append(f"enter:home:{params.get('tab', 0)}")

        def on_leave(self) -> None:
            events.append("leave:home")

        def build(self, ctx: ui.UI) -> None:
            ctx.text("Home View")

    class DetailView(ui.View):
        def on_enter(self, params: dict) -> None:
            events.append(f"enter:detail:{params['item_id']}")

        def on_leave(self) -> None:
            events.append("leave:detail")

        def build(self, ctx: ui.UI) -> None:
            ctx.text("Detail View")

    woken = []
    store = ui.Store({"count": 1}, wake=lambda: woken.append(True))
    seen = []
    unsub = store.subscribe(lambda s: seen.append(s["count"]))
    store.update(lambda s: {"count": s["count"] + 4})
    assert store.value["count"] == 5
    assert seen == [5] and len(woken) == 1
    unsub()

    router = ui.Router({"home": HomeView("home"), "detail": DetailView("detail")}, initial="home")
    assert router.current_name == "home"
    router.push("detail", item_id=99)
    assert router.current_name == "detail" and router.can_go_back
    assert router.back()
    assert router.current_name == "home" and router.can_go_forward
    assert router.forward()
    assert router.current_name == "detail"

    with ui.UI(width=300, height=200) as ctx:
        with ctx.frame():
            router.render(ctx)
    assert "enter:detail:99" in events


def test_threading_channels_background_runner_and_http() -> None:
    """Test thread-safe UI dispatch, MPSC Channel, BackgroundRunner streaming, and HTTP fetch."""

    class _EchoHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            n = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(n).decode("utf-8"))
            resp = json.dumps({"doubled": body["x"] * 2}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)

        def log_message(self, format: str, *args) -> None:
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), _EchoHandler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    try:
        with ui.App("ThreadTest", width=400, height=300, headless=True) as app:
            runner = ui.BackgroundRunner.for_app(app, max_workers=3)
            chan: ui.Channel[int] = ui.Channel(maxsize=16, wake=app.wake)

            ui_thread_id = threading.get_ident()
            callback_threads: list[int] = []
            http_results: list[dict] = []
            streamed: list[int] = []

            h_http = runner.fetch_json(
                f"http://127.0.0.1:{port}/echo",
                method="POST",
                payload={"x": 21},
                on_done=lambda data: (callback_threads.append(threading.get_ident()), http_results.append(data)),
            )

            h_stream = runner.stream(
                lambda: (i * 10 for i in range(1, 5)),
                on_item=lambda x: (callback_threads.append(threading.get_ident()), streamed.append(x)),
            )

            # Producer thread pushing into Channel
            def _producer() -> None:
                for k in range(5):
                    chan.send(k)

            threading.Thread(target=_producer, daemon=True).start()

            collected_chan: list[int] = []
            deadline = time.monotonic() + 5.0
            while time.monotonic() < deadline:
                assert app.frame(wait=True)
                app.ui.text("Frame")
                collected_chan.extend(chan.drain())
                if h_http.done and h_stream.done and len(collected_chan) == 5:
                    break

            assert http_results == [{"doubled": 42}]
            assert streamed == [10, 20, 30, 40]
            assert sorted(collected_chan) == [0, 1, 2, 3, 4]
            # Every completion/item callback MUST have executed on the UI thread!
            assert all(tid == ui_thread_id for tid in callback_threads)
            runner.close()
    finally:
        srv.shutdown()
        srv.server_close()


def test_cooperative_asyncio_and_async_bridge() -> None:
    """Verify both cooperative `await app.run_async(...)` and threaded `AsyncBridge`."""

    async def _coop() -> None:
        ticks = 0
        bg_flag = False

        async def _bg_coro(app_ref: ui.App) -> None:
            nonlocal bg_flag
            await asyncio.sleep(0.01)
            bg_flag = True
            app_ref.wake()

        with ui.App("AsyncCoop", width=320, height=200, headless=True) as app:
            task = asyncio.create_task(_bg_coro(app))

            def draw(ctx: ui.UI) -> None:
                nonlocal ticks
                ticks += 1
                ctx.heading(f"Tick {ticks}, bg={bg_flag}")
                if bg_flag and ticks >= 3:
                    app.quit()

            await app.run_async(draw, max_frames=30)
            await task
        assert bg_flag is True and ticks >= 3

    asyncio.run(_coop())

    # Test AsyncBridge from a synchronous UI loop
    with ui.App("AsyncBridgeTest", width=320, height=200, headless=True) as app:
        bridge = AsyncBridge.for_app(app)
        got: list[str] = []

        async def _agen():
            for tok in ("hello", "async", "world"):
                await asyncio.sleep(0.005)
                yield tok

        handle = bridge.stream(_agen(), on_item=got.append)
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline and not handle.done:
            app.frame(wait=True)
            app.ui.text(" ".join(got))
        # Drain final UI dispatch frame
        app.frame(wait=False)
        assert got == ["hello", "async", "world"]
        bridge.close()


def test_all_examples_execute_cleanly(tmp_path: pathlib.Path) -> None:
    """Every ported example in examples/ must render cleanly in headless mode."""
    examples_dir = REPO_ROOT / "examples"
    py_files = sorted(p for p in examples_dir.glob("*.py") if p.name != "async_network.py")
    assert len(py_files) >= 10

    for idx, ex in enumerate(py_files):
        out_png = tmp_path / f"{ex.stem}.png"
        env = dict(
            os.environ,
            NEXA_HEADLESS="1",
            PYTHONUTF8="1",
            CUI_SCREENSHOT=str(out_png),
            CUI_SCREENSHOT_FRAMES="4",
        )
        res = subprocess.run([sys.executable, str(ex)], env=env, capture_output=True, text=True, encoding="utf-8", timeout=20)
        assert res.returncode == 0, f"{ex.name} failed:\n{res.stderr}"
        assert out_png.is_file() and out_png.stat().st_size > 1000
