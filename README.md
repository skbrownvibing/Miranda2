# Reply or Die

A local-first Mac tool for measuring and improving your text responsiveness from iMessage exports.

**[Try the demo →](https://replyordie.vercel.app/)** (no Mac required, uses synthetic data)

![Hero screenshot](docs/screenshots/hero.png)

## What it does

- Surfaces the 1:1 personal conversations that are actually waiting on you
- Filters out spam, group chats, and automated logistics texts
- Computes a 0–100 responsiveness score over a time window you choose
- Tracks score history so you can see whether you're getting better
- Lets you dismiss conversations you don't owe a reply to

## How it works

Two pieces, both local:

1. A Mac export script (`export.command`) reads your iMessage SQLite database and writes a normalized JSON file to your Desktop.
2. A single-file web app (`index.html`) reads that JSON, classifies conversations, and shows the action list, score, and history.

Optional add-ons:

- A tiny Python helper (`tools/runner/local_export_runner.py`) exposes a `127.0.0.1` endpoint so the web app can re-run the export with one click.
- A serverless function (`api/ai-suggest-reply.js`) drafts short replies via Anthropic Claude. Opt-in only.

## Privacy

- All your iMessage data stays on your Mac (browser `localStorage` plus `~/Desktop/replyordie_messages.json`).
- The web app does not upload your conversations anywhere.
- The local export runner binds to `127.0.0.1` only; nothing on your network can reach it.
- The AI Suggest Reply feature is opt-in. When you use it, only the prompt text you choose is sent to Anthropic Claude through your own deployed function.
- Demo mode uses synthetic data bundled in `data/miranda_demo.json` — no Mac or Full Disk Access required.

## Getting started

### Try the demo

Open https://replyordie.vercel.app/ and click **Try demo**. Or clone the repo and open `index.html` directly in a browser.

### Run on your real iMessage data

1. Grant **Full Disk Access** to Terminal (System Settings → Privacy & Security → Full Disk Access).
2. Double-click `export.command`. It will write `~/Desktop/replyordie_messages.json`.
3. Open `index.html` (or the deployed URL) and drop the JSON file onto the start screen.

### Optional: one-click refresh

In a terminal at the repo root:

```bash
python3 tools/runner/local_export_runner.py
```

Keep that terminal open. The app's **Run export + reload** button will then re-run the exporter without you having to touch the Finder.

### Optional: AI Suggest Reply

Deploy `api/ai-suggest-reply.js` to Vercel with `ANTHROPIC_API_KEY` set in the project's environment variables (get a key from https://console.anthropic.com/settings/keys). The deployed endpoint is the one the app calls when you click **Suggest reply**. Override the default model by setting `MIRANDA2_AI_MODEL` (defaults to `claude-sonnet-4-6`).

## Project layout

```
.
├── index.html                      # The web app (single-file local-first)
├── export.command                  # Mac iMessage exporter (bash + Python)
├── api/
│   └── ai-suggest-reply.js         # Optional Vercel function for AI replies
├── tools/
│   └── runner/                     # Optional localhost export runner
├── data/
│   └── miranda_demo.json           # Synthetic data for the public demo
├── docs/
│   ├── prd.md                      # Product spec and decision rules
│   └── README.md                   # Docs index
├── AGENTS.md                       # Working-style instructions for AI agents
├── CHANGELOG.md
└── LICENSE
```

## Status & limitations

Early-stage learning project. Things to know:

- macOS only — depends on the iMessage SQLite schema.
- Export-based — no live sync, you re-run the exporter when you want fresh data.
- Spam, automated, and personal classification is heuristic and user-overridable.
- The web app is one large `index.html`; there is no build step.

See `docs/prd.md` for the full product spec, scoring rules, and roadmap.

## License

MIT — see [`LICENSE`](LICENSE).
