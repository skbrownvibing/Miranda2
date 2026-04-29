# Local export runner (minimal)

This tiny local helper lets the web app run `export.command` and then reload JSON.

## Start it

From the repo root:

```bash
python3 tools/runner/local_export_runner.py
```

It listens on `http://127.0.0.1:8765` and exposes one endpoint:

- `POST /run-export` → runs `export.command`, waits for completion, and returns status JSON.

## Notes

- **Loopback-only bind:** the runner binds to `127.0.0.1` only, not `0.0.0.0`, so it is reachable only from the same machine.
- Localhost only (no cloud service).
- Keep this terminal open while using **Run export + reload**.
- Press `Ctrl+C` to stop; the runner now handles `KeyboardInterrupt` cleanly.
- If runner is unavailable, app fallback **Reload current JSON** still works.

## Optional environment overrides

- `MIRANDA2_OUTPUT_PATH` — path the runner checks for exported JSON metadata (default: `~/Desktop/miranda2_messages.json`).
