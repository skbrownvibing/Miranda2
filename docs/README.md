# Docs

Documentation for [Reply or Die](../README.md).

- [`prd.md`](prd.md) — product spec, decision rules, scoring model
- [`screenshots/`](screenshots/) — images used in the top-level README
- `Reply or Die *_standalone_*.html` — design references (work-in-progress, will be consolidated)

For setup and usage, see the top-level [README](../README.md).
For working-style instructions for AI agents, see [`AGENTS.md`](../AGENTS.md).
For change history, see [`CHANGELOG.md`](../CHANGELOG.md).
## How it works
1. Run the local Mac export script to generate JSON from iMessage data
2. Open the local web app and load the exported JSON
3. Review the action list, score, and trends

## API + deployment notes (Vercel)
The frontend calls `POST /api/ai-suggest-reply` (same origin by default). If your static frontend is hosted on a different origin, configure CORS allowlisting.

### Required env vars
- `OPENAI_API_KEY` — server-side OpenAI key
- `MIRANDA2_AI_MODEL` — default model used when request does not provide one

### Recommended security env vars
- `MIRANDA2_ALLOWED_MODELS` — comma-separated model allowlist (example: `gpt-4.1-mini,gpt-4.1`)
- `MIRANDA2_ALLOWED_ORIGINS` — comma-separated CORS origin allowlist (example: `https://your-frontend.vercel.app`)
- `MIRANDA2_MAX_PROMPT_CHARS` — max accepted prompt length (default: `2500`)
- `MIRANDA2_MAX_BODY_BYTES` — max accepted request body bytes (default: `12000`)
- `MIRANDA2_RATE_LIMIT_MAX_REQUESTS` — IP cap per window (default: `20`)
- `MIRANDA2_RATE_LIMIT_WINDOW_SECONDS` — rate-limit window seconds (default: `60`)
- `UPSTASH_REDIS_REST_URL` + `UPSTASH_REDIS_REST_TOKEN` — optional Upstash/Vercel KV REST rate-limit backend

### Runtime behavior summary
- request-size and prompt-length guardrails are enforced
- IP-based rate limit is enforced (Upstash when configured; in-memory fallback otherwise)
- CORS only allows origins from `MIRANDA2_ALLOWED_ORIGINS`
- upstream provider errors are sanitized before returning to clients

## Export command notes
`export.command` supports:
- `--help`
- `--version`
- `MIRANDA2_OUTPUT_PATH` override for JSON output path (default still `~/Desktop/miranda2_messages.json`)
- `MIRANDA2_CHAT_DB_PATH` override for chat DB path (useful for smoke tests)

## Docs
- Product spec: `docs/prd.md`
- Change history: `CHANGELOG.md`
- Agent instructions: `AGENTS.md`

## Current status
Early-stage learning project. Product logic and UX are evolving quickly.
