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

- Localhost only (no cloud service).
- Keep this terminal open while using **Run export + reload**.
- If runner is unavailable, app fallback **Reload current JSON** still works.
