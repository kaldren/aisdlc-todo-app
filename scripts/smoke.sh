#!/usr/bin/env bash
# Start the app on a spare port with a throwaway DB + log, check /health, stop it.
set -euo pipefail
PORT="${PORT:-8765}"
TMP="$(mktemp -d)"
export TODO_DB="$TMP/smoke.db" TODO_LOG="$TMP/app.jsonl"
uv run uvicorn app.main:app --port "$PORT" >"$TMP/server.out" 2>&1 &
PID=$!
trap 'kill $PID 2>/dev/null || true' EXIT
for _ in $(seq 1 50); do
  curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 && break
  sleep 0.2
done
if curl -fsS "http://127.0.0.1:$PORT/health" | grep -q '"ok"'; then
  echo "smoke: GET /health ok"
else
  echo "smoke: GET /health FAILED"; cat "$TMP/server.out"; exit 1
fi
