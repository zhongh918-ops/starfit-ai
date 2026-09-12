#!/bin/bash
# Portable exclusive lock for git publish scripts (macOS has no flock).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOCKDIR="$ROOT/output/git.lockdir"
mkdir -p "$ROOT/output"

cleanup() {
  rmdir "$LOCKDIR" 2>/dev/null || true
}

for _ in $(seq 1 40); do
  if mkdir "$LOCKDIR" 2>/dev/null; then
    trap cleanup EXIT INT TERM
    "$@"
    exit $?
  fi
  sleep 1
done

echo "timed out waiting for git lock" >&2
exit 1
