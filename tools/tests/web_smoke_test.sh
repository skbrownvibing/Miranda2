#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
PORT="${PORT:-8765}"
BASE="http://127.0.0.1:${PORT}"

cd "$ROOT_DIR"

python3 -m http.server "$PORT" --bind 127.0.0.1 >/dev/null 2>&1 &
SERVER_PID=$!

cleanup() {
  kill "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT

# Wait for server to start (up to ~5s)
for _ in $(seq 1 25); do
  if curl -fsS "${BASE}/index.html" -o /dev/null 2>/dev/null; then
    break
  fi
  sleep 0.2
done

check_200() {
  local path="$1"
  local code
  code="$(curl -s -o /dev/null -w '%{http_code}' "${BASE}${path}")"
  if [[ "$code" != "200" ]]; then
    echo "FAIL ${path} -> ${code}" >&2
    exit 1
  fi
  echo "ok   ${path}"
}

check_200 "/index.html"
check_200 "/app.css"
check_200 "/app.js"
check_200 "/docs/standalone.html"
check_200 "/data/miranda_demo.json"

# Verify index.html actually wires up the split assets
grep -q 'href="app.css"' index.html || { echo "FAIL index.html missing app.css link" >&2; exit 1; }
grep -q 'src="app.js"'   index.html || { echo "FAIL index.html missing app.js script" >&2; exit 1; }
echo "ok   index.html references app.css and app.js"

# Verify standalone iframe target matches what index.html references
grep -q 'src="docs/standalone.html"' index.html || { echo "FAIL index.html missing docs/standalone.html iframe" >&2; exit 1; }
echo "ok   index.html references docs/standalone.html"

# Optional: parse-check app.js if node is available
if command -v node >/dev/null 2>&1; then
  node --check app.js
  echo "ok   app.js parses"
else
  echo "skip node not installed; app.js parse check skipped"
fi

echo "ok"
