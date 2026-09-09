#!/usr/bin/env python3
"""StarFit AI live website: serve UI + refresh TrendRadar hot lists."""
from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from engine import campaign_for, load_state, match_product

ROOT = Path(__file__).resolve().parent
TRENDRADAR = Path.home() / "Tools/TrendRadar"
UV = Path("/Library/Frameworks/Python.framework/Versions/3.13/bin/uv")
PORT = int(os.environ.get("STARFIT_PORT", "8765"))
HOST = os.environ.get("STARFIT_HOST", "127.0.0.1")

_lock = threading.Lock()
_refresh = {"running": False, "log": "", "started_at": None, "error": None}


def _json(handler, code, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _run_crawl():
    with _lock:
        if _refresh["running"]:
            return
        _refresh.update({"running": True, "log": "正在抓取 11 平台热榜…", "error": None, "started_at": time.time()})
    try:
        env = os.environ.copy()
        env["BROWSER"] = "/usr/bin/true"
        env["PATH"] = f"{UV.parent}:{env.get('PATH', '')}"
        proc = subprocess.run(
            [str(UV), "run", "python", "-m", "trendradar"],
            cwd=str(TRENDRADAR),
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        log = (proc.stdout or "")[-1500:]
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or proc.stdout or "crawl failed")[-800:])
        load_state()
        with _lock:
            _refresh.update({"running": False, "log": "热榜已更新", "error": None})
            _refresh["log"] = log[-400:] or "热榜已更新"
    except Exception as exc:  # noqa: BLE001
        with _lock:
            _refresh.update({"running": False, "error": str(exc), "log": "抓取失败"})


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        print(f"[starfit] {self.address_string()} {fmt % args}")

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/state":
            _json(self, 200, load_state())
            return
        if parsed.path == "/api/refresh/status":
            with _lock:
                _json(self, 200, dict(_refresh))
            return
        if parsed.path == "/api/match":
            qs = parse_qs(parsed.query)
            pid = (qs.get("product") or ["cold-brew"])[0]
            state = load_state()
            product = next((p for p in state["products"] if p["id"] == pid), state["products"][0])
            result = match_product(product, state["trends"], state["celebrities"])
            top = result["ranked"][0]["celeb"]["name"]
            result["campaign"] = campaign_for(product, top)
            result["meta"] = state["meta"]
            _json(self, 200, result)
            return
        if parsed.path in ("/", "/index.html"):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/refresh":
            with _lock:
                already = _refresh["running"]
            if not already:
                threading.Thread(target=_run_crawl, daemon=True).start()
            _json(self, 202 if not already else 200, {"ok": True, "running": True})
            return
        self.send_error(404)


def main():
    os.chdir(ROOT)
    load_state()
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"StarFit AI 实时站: http://{HOST}:{PORT}/")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
