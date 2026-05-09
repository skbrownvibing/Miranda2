#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

chmod +x export.command
rm -f export.zip
zip -q export.zip export.command
echo "Wrote $ROOT_DIR/export.zip"
