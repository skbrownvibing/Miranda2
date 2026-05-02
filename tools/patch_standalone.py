#!/usr/bin/env python3
"""Re-apply the Reply or Die standalone patch after a fresh design upload.

The Inbox iframe loads docs/standalone.html. That file is exported from a
design tool and ships with a hardcoded regenAi() that picks at random from a
3-element alts array. We patch it to call window.parent.miranda2RegenAi()
instead, so the AI Regenerate button uses the real /api/ai-suggest-reply
backend.

Whenever the standalone file is re-uploaded, run:

    python3 tools/patch_standalone.py

Idempotent: a no-op if the file is already patched. Exits non-zero if the
canned strings are present and the original block can't be located (which
means the design tool changed the surrounding code shape and the patch
needs to be revisited).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "docs" / "standalone.html"

ORIGINAL = (
    "function regenAi() {\\n"
    "  const body = document.getElementById('aiBody');\\n"
    "  if (!body) return;\\n"
    "  body.innerHTML = '<span class=\\\"cursor\\\"><\\u002Fspan>';\\n"
    "  setTimeout(() => {\\n"
    "    const alts = [\\n"
    "      'cannot commit. ask me again tomorrow',\\n"
    "      'noted. counter-proposal: tacos, 7pm, no drama',\\n"
    "      selectedContact.ai,\\n"
    "    ];\\n"
    "    body.textContent = alts[Math.floor(Math.random()*alts.length)];\\n"
    "  }, 700);\\n"
    "}"
)

PATCHED = (
    "function regenAi() {\\n"
    "  // PATCHED (Reply or Die): hardcoded alts removed; defer to parent host's\\n"
    "  // miranda2RegenAi() which calls the real /api/ai-suggest-reply backend.\\n"
    "  // If you re-upload this standalone from the design tool, re-apply this\\n"
    "  // patch (or run tools/patch_standalone.py).\\n"
    "  const body = document.getElementById('aiBody');\\n"
    "  if (!body) return;\\n"
    "  const sc = (typeof selectedContact !== 'undefined') ? selectedContact : null;\\n"
    "  body.innerHTML = '<span class=\\\"cursor\\\"><\\u002Fspan>';\\n"
    "  try {\\n"
    "    const fn = window.parent && window.parent.miranda2RegenAi;\\n"
    "    if (typeof fn === 'function') { fn(sc, body); return; }\\n"
    "  } catch (e) {}\\n"
    "  body.textContent = (sc && sc.ai) || 'AI service unavailable';\\n"
    "}"
)

CANNED_MARKERS = (
    "cannot commit. ask me again tomorrow",
    "noted. counter-proposal: tacos, 7pm, no drama",
)


def main() -> int:
    if not TARGET.exists():
        print(f"error: {TARGET} not found", file=sys.stderr)
        return 2
    text = TARGET.read_text(encoding="utf-8")

    if PATCHED in text and not any(m in text for m in CANNED_MARKERS):
        print(f"already patched: {TARGET.name}")
        return 0

    matches = text.count(ORIGINAL)
    if matches == 0:
        # Either the design tool changed the function, or someone edited it
        # by hand. Either way, the patch is no longer mechanical.
        canned = [m for m in CANNED_MARKERS if m in text]
        if canned:
            print(
                "error: canned alts present but original regenAi() block not found.\n"
                "       The design upload changed the surrounding code; re-derive "
                "the patch by hand and update tools/patch_standalone.py.\n"
                f"       Canned strings still in file: {canned}",
                file=sys.stderr,
            )
            return 1
        print("error: nothing to patch (no original block, no canned alts).", file=sys.stderr)
        return 1
    if matches > 1:
        print(f"error: original regenAi() block found {matches} times; expected 1", file=sys.stderr)
        return 1

    text = text.replace(ORIGINAL, PATCHED, 1)
    TARGET.write_text(text, encoding="utf-8")
    print(f"patched {TARGET.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
