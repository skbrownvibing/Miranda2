#!/usr/bin/env python3
"""Minimal local runner for Miranda2 refresh.

Runs export.command and serves HTTP on 127.0.0.1 only (localhost loopback).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8765
OUTPUT_PATH = Path(os.path.expanduser(os.environ.get("MIRANDA2_OUTPUT_PATH", "~/Desktop/miranda2_messages.json")))
REPO_ROOT = Path(__file__).resolve().parents[2]
EXPORT_CMD = REPO_ROOT / "export.command"

_state_lock = threading.Lock()
_last_hash = None


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._json(204, {})

    def do_POST(self):
        if self.path != "/run-export":
            self._json(404, {"ok": False, "error": "Not found"})
            return
        if not EXPORT_CMD.exists():
            self._json(500, {"ok": False, "error": f"Missing export.command at {EXPORT_CMD}"})
            return

        with _state_lock:
            global _last_hash
            before_hash = _sha256(OUTPUT_PATH)
            if _last_hash is None:
                _last_hash = before_hash

            try:
                proc = subprocess.run(
                    ["/bin/bash", str(EXPORT_CMD)],
                    cwd=str(REPO_ROOT),
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except Exception as ex:
                self._json(500, {"ok": False, "error": f"Runner failed to launch export.command: {ex}"})
                return

            after_hash = _sha256(OUTPUT_PATH)
            changed = (before_hash != after_hash) if before_hash is not None else (after_hash is not None)
            _last_hash = after_hash

            if proc.returncode != 0:
                self._json(
                    500,
                    {
                        "ok": False,
                        "error": "export.command failed",
                        "exit_code": proc.returncode,
                        "stdout": proc.stdout[-4000:],
                        "stderr": proc.stderr[-4000:],
                    },
                )
                return

            mtime = OUTPUT_PATH.stat().st_mtime if OUTPUT_PATH.exists() else None
            self._json(
                200,
                {
                    "ok": True,
                    "changed": changed,
                    "output_path": str(OUTPUT_PATH),
                    "output_mtime": mtime,
                    "exit_code": proc.returncode,
                },
            )


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Miranda2 local export runner listening on http://{HOST}:{PORT}")
    print("Binding is loopback-only (127.0.0.1), so this is not reachable from other devices.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down local export runner...")
    finally:
        server.server_close()
