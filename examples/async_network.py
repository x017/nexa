"""Asyncio + Loopback HTTP Networking Example.

Spins up a zero-dependency local HTTP JSON/stream endpoint on 127.0.0.1:0 and
drives a nexa UI cooperatively inside ``asyncio`` via ``await app.run_async(...)``
alongside a ``Channel`` and ``LogBuffer``.
"""

from __future__ import annotations

import asyncio
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import nexa as ui


class _LocalMetricsHandler(BaseHTTPRequestHandler):
    req_count = 0

    def do_GET(self) -> None:
        _LocalMetricsHandler.req_count += 1
        payload = json.dumps({
            "request_id": _LocalMetricsHandler.req_count,
            "latency_ms": round(2.4 + (_LocalMetricsHandler.req_count * 1.7) % 9.5, 2),
            "throughput_rps": 1420 + (_LocalMetricsHandler.req_count * 83) % 600,
            "timestamp": time.time(),
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args) -> None:
        pass


async def async_main(max_frames: int | None = None) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _LocalMetricsHandler)
    port = server.server_address[1]
    srv_thread = threading.Thread(target=server.serve_forever, daemon=True)
    srv_thread.start()

    app = ui.App("Async Networking — nexa", width=920, height=620, theme=ui.ThemeMode.DARK)
    runner = ui.BackgroundRunner.for_app(app)
    channel: ui.Channel[dict] = ui.Channel(wake=app.wake)
    log = ui.LogBuffer(max_lines=512)
    url = f"http://127.0.0.1:{port}/metrics"
    log.info(f"Started local loopback telemetry server at {url}")

    latencies = [4.2, 5.1, 3.8, 6.4, 4.9, 5.5]
    rps = 1420
    auto_poll = True
    req_task: ui.TaskHandle | None = None

    async def periodic_poller() -> None:
        while True:
            await asyncio.sleep(0.25)
            if auto_poll:
                # Non-blocking fetch via asyncio.to_thread -> pushes to Channel -> wakes UI!
                data = await asyncio.to_thread(
                    lambda: json.loads(__import__("urllib.request").request.urlopen(url, timeout=3).read().decode())
                )
                channel.send(data)

    poller = asyncio.create_task(periodic_poller())

    def draw(ctx: ui.UI) -> None:
        nonlocal rps, auto_poll, req_task
        for pkt in channel.drain():
            latencies.append(float(pkt["latency_ms"]))
            if len(latencies) > 32:
                latencies.pop(0)
            rps = int(pkt["throughput_rps"])
            log.info(f"GET /metrics -> #{pkt['request_id']} ({pkt['latency_ms']} ms, {rps} req/s)")

        with ctx.column(width=ui.FILL, height=ui.FILL, bg=ui.Color.BACKGROUND, pad=24, gap=16):
            with ctx.row(align=ui.Align.CENTER, gap=12):
                ctx.heading("Cooperative Asyncio + HTTP Telemetry", level=2)
                ctx.spacer()
                auto_poll = ctx.switch("Auto-poll (250ms)", auto_poll)
                if ctx.status_button(
                    "Fetch Snapshot",
                    req_task.button_status if req_task else ui.Status.IDLE,
                    icon=ui.Icon.REFRESH_CW,
                ):
                    req_task = runner.fetch_json(url, on_done=channel.send)

            with ctx.row(gap=16, width=ui.FILL):
                with ctx.card(width=ui.GROW(1), pad=18, gap=6):
                    ctx.secondary("Throughput")
                    ctx.number_roll("rps_roll", f"{rps:,} req/s", font=ui.FontRole.DISPLAY, size=26)
                with ctx.card(width=ui.GROW(2), pad=18, gap=8):
                    ctx.secondary("Loopback Latency (ms)")
                    ctx.line_chart("lat_chart", [ui.Series("ms", latencies)], height=120, area=True, smooth=True)

            ctx.log_view("net_log", log, width=ui.FILL, height=220, timestamps=True)

    try:
        await app.run_async(draw, max_frames=max_frames)
    finally:
        poller.cancel()
        runner.close()
        app.close()
        log.close()
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    asyncio.run(async_main())
