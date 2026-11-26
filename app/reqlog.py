"""Pure-ASGI middleware: one JSON log line per request, 500 on unhandled errors."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path


class RequestLogMiddleware:
    def __init__(self, app, log_path: str):
        self.app = app
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, record: dict) -> None:
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        start = time.perf_counter()
        state = {"status": 500, "started": False}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                state["status"] = message["status"]
                state["started"] = True
            await send(message)

        record = {"ts": datetime.now(timezone.utc).isoformat(), "level": "info",
                  "event": "request", "method": scope["method"], "path": scope["path"]}
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            record.update(level="error", event="unhandled_error",
                          error=f"{type(exc).__name__}: {exc}")
            state["status"] = 500
            if not state["started"]:
                await send({"type": "http.response.start", "status": 500,
                            "headers": [(b"content-type", b"text/plain; charset=utf-8")]})
                await send({"type": "http.response.body", "body": b"Internal Server Error"})
        record["status"] = state["status"]
        record["ms"] = round((time.perf_counter() - start) * 1000, 2)
        self.write(record)
