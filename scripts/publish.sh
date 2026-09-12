#!/bin/bash
# Crawl TrendRadar, rebuild StarFit snapshot, push GitHub Pages.
set -euo pipefail
export PATH="$HOME/.local/bin:/Library/Frameworks/Python.framework/Versions/3.13/bin:/usr/bin:/usr/sbin:/bin"
export BROWSER="/usr/bin/true"
ROOT="/Users/zhonghui/WorkBuddy AI/2026-09-05-11-38-40/starfit-ai"
TR="$HOME/Tools/TrendRadar"
UV="/Library/Frameworks/Python.framework/Versions/3.13/bin/uv"
LOG="$ROOT/output/publish.log"
mkdir -p "$ROOT/output"
exec >>"$LOG" 2>&1
echo "==== $(date '+%Y-%m-%d %H:%M:%S') ===="
export http_proxy="" https_proxy="" HTTP_PROXY="" HTTPS_PROXY="" ALL_PROXY="" all_proxy=""
export no_proxy="*" NO_PROXY="*"
cd "$TR"
"$UV" run python -m trendradar
cd "$ROOT"
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 -c "from engine import load_state; load_state()"
(
  flock 9
  git add data/state.json data/youth_trends.json data/meta.json
  if git diff --cached --quiet; then
    echo "no snapshot change"
    exit 0
  fi
  git commit -m "Update TrendRadar snapshot $(date '+%Y-%m-%d %H:%M')"
  git push origin main
  curl -fsS "https://purge.jsdelivr.net/gh/zhongh918-ops/starfit-ai@main/index.html" || true
  curl -fsS "https://purge.jsdelivr.net/gh/zhongh918-ops/starfit-ai@main/data/state.json" || true
  echo "published"
) 9>"$ROOT/output/git.lock"
