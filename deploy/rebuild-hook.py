#!/usr/bin/env python3
"""Tiny webhook that rebuilds the Astro site on the server.

POST /rebuild with header X-Hook-Secret -> runs build-web.sh (debounced, serialized).
Listens on 127.0.0.1:9000 only; the CMS container reaches it via host.docker.internal.
Run via deploy/systemd/grabnar-rebuild.service.
"""

import json
import os
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

SECRET = os.environ.get("HOOK_SECRET", "")
BUILD_SCRIPT = os.environ.get("BUILD_SCRIPT", "/srv/grabnar/repo/deploy/build-web.sh")
DEBOUNCE = float(os.environ.get("DEBOUNCE_SECONDS", "60"))
LOG = os.environ.get("BUILD_LOG", "/srv/grabnar/logs/build.log")

_lock = threading.Lock()
_timer: threading.Timer | None = None
_pending_reasons: list[str] = []


def _run_build() -> None:
    global _timer
    with _lock:
        reasons = ", ".join(_pending_reasons) or "manual"
        _pending_reasons.clear()
        _timer = None
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as log:
        log.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} rebuild ({reasons})\n")
        log.flush()
        result = subprocess.run([BUILD_SCRIPT], stdout=log, stderr=subprocess.STDOUT)
        log.write(f"=== exit {result.returncode}\n")


def schedule(reason: str) -> None:
    global _timer
    with _lock:
        _pending_reasons.append(reason)
        if _timer is None:
            _timer = threading.Timer(DEBOUNCE, _run_build)
            _timer.daemon = True
            _timer.start()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path.rstrip("/") != "/rebuild":
            return self._reply(404, {"error": "not found"})
        if not SECRET or self.headers.get("X-Hook-Secret") != SECRET:
            return self._reply(403, {"error": "forbidden"})
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            body = {}
        schedule(str(body.get("reason", "unknown")))
        self._reply(202, {"scheduled": True, "debounce_seconds": DEBOUNCE})

    def do_GET(self):
        self._reply(200, {"ok": True, "pending": len(_pending_reasons)})

    def _reply(self, code: int, payload: dict) -> None:
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):  # quieter journal
        if "/rebuild" in fmt % args:
            super().log_message(fmt, *args)


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", int(os.environ.get("PORT", "9000"))), Handler).serve_forever()
