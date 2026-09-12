#!/bin/bash
# Keep localhost:8765 on a public HTTPS tunnel, and publish a fixed entry URL.
set -euo pipefail
export PATH="$HOME/.local/bin:/Library/Frameworks/Python.framework/Versions/3.13/bin:/usr/bin:/usr/sbin:/bin"
export BROWSER="/usr/bin/true"
export http_proxy="" https_proxy="" HTTP_PROXY="" HTTPS_PROXY="" ALL_PROXY="" all_proxy=""
export no_proxy="*" NO_PROXY="*"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export ROOT
BIN="$ROOT/.tools/cloudflared"
LOG="$ROOT/output/tunnel.log"
URL_FILE="$ROOT/output/public-url.txt"
JSON="$ROOT/live-url.json"
PY="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"
mkdir -p "$ROOT/.tools" "$ROOT/output"

if [[ ! -x "$BIN" ]]; then
  ARCH="$(uname -m)"
  if [[ "$ARCH" == "arm64" ]]; then
    URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-arm64.tgz"
  else
    URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz"
  fi
  curl -fsSL "$URL" | tar -xz -C "$ROOT/.tools"
  chmod +x "$BIN"
fi

if ! lsof -nP -iTCP:8765 -sTCP:LISTEN >/dev/null 2>&1; then
  cd "$ROOT"
  STARFIT_HOST=0.0.0.0 "$PY" app.py >>"$ROOT/output/app.log" 2>&1 &
  sleep 1
fi

publish_url() {
  local url="$1"
  echo "$url" > "$URL_FILE"
  "$PY" - <<PY
import json
from datetime import datetime, timezone
from pathlib import Path
p = Path(r"""$JSON""")
data = {
    "url": """$url""",
    "work": """$url""" + "/work",
    "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY
  "$ROOT/scripts/with-git-lock.sh" bash -c '
    cd "$ROOT"
    git add -- live-url.json
    if git diff --cached --quiet -- live-url.json; then
      exit 0
    fi
    git commit -m "Update live tunnel URL"
    git push origin main
    curl -fsS "https://purge.jsdelivr.net/gh/zhongh918-ops/starfit-ai@main/live-url.json" >/dev/null || true
    curl -fsS "https://purge.jsdelivr.net/gh/zhongh918-ops/starfit-ai@main/live.html" >/dev/null || true
  ' || true
}

: > "$LOG"
"$BIN" tunnel --no-autoupdate --url "http://127.0.0.1:8765" >>"$LOG" 2>&1 &
CF_PID=$!
cleanup() {
  kill "$CF_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

published=""
for _ in $(seq 1 45); do
  if ! kill -0 "$CF_PID" 2>/dev/null; then
    echo "cloudflared exited before a public URL appeared" >&2
    tail -40 "$LOG" >&2 || true
    exit 1
  fi
  url="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" | head -1 || true)"
  if [[ -n "$url" && "$url" != "$published" ]]; then
    published="$url"
    publish_url "$url"
    echo "public: $url/work"
  fi
  if [[ -n "$published" ]]; then
    break
  fi
  sleep 2
done

if [[ -z "$published" ]]; then
  echo "timed out waiting for tunnel URL" >&2
  tail -40 "$LOG" >&2 || true
  exit 1
fi

wait "$CF_PID"
