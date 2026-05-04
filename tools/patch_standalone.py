#!/usr/bin/env python3
"""Re-apply the Reply or Die standalone patches after a fresh design upload.

The Inbox iframe loads docs/standalone.html. That file is exported from a
design tool and ships with hardcoded behavior that we patch:

1. regenAi() picks at random from a 3-element alts array. We patch it to
   call window.parent.miranda2RegenAi() instead, so the AI Regenerate button
   uses the real /api/ai-suggest-reply backend.

2. The Dismiss button in the thread footer ships with no onclick handler at
   all (i.e., clicking it does nothing). We patch it to call dismissThread(),
   which we also inject. dismissThread() removes the contact from the
   iframe's CONTACTS list and notifies the host via
   window.parent.miranda2DismissThread() so the host can persist dismissal
   state and update its score.

Whenever the standalone file is re-uploaded, run:

    python3 tools/patch_standalone.py

Idempotent: a no-op for parts already patched. Exits non-zero if a section
that should be patched can't be located (which means the design tool changed
the surrounding code shape and the patch needs to be revisited).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "docs" / "standalone.html"

# ---------------------------------------------------------------------------
# Patch 1: regenAi() bridge to the host's AI backend.
# ---------------------------------------------------------------------------
REGEN_ORIGINAL = (
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

REGEN_PATCHED = (
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

# ---------------------------------------------------------------------------
# Patch 2: Dismiss button onclick + dismissThread() function.
# ---------------------------------------------------------------------------
DISMISS_BTN_ORIGINAL = '<button class=\\"dismiss-btn\\">Dismiss<\\u002Fbutton>'
DISMISS_BTN_PATCHED = (
    '<button class=\\"dismiss-btn\\" onclick=\\"dismissThread()\\">'
    'Dismiss<\\u002Fbutton>'
)

# Anchor we splice the new function in front of. After the patch this becomes
# part of the patched body.
DISMISS_FN_ANCHOR = (
    "window.location.href = 'sms:' + phone;\\n  }\\n}\\n\\n"
    "function regenAi() {"
)
DISMISS_FN_INSERT = (
    "function dismissThread() {\\n"
    "  // PATCHED (Reply or Die): wires the design's Dismiss button to the host app.\\n"
    "  // If you re-upload this standalone, re-apply via tools/patch_standalone.py.\\n"
    "  const sc = (typeof selectedContact !== 'undefined') ? selectedContact : null;\\n"
    "  if (!sc) return;\\n"
    "  try {\\n"
    "    const fn = window.parent && window.parent.miranda2DismissThread;\\n"
    "    if (typeof fn === 'function') fn(sc);\\n"
    "  } catch (e) {}\\n"
    "  if (typeof CONTACTS !== 'undefined' && Array.isArray(CONTACTS)) {\\n"
    "    const idx = CONTACTS.findIndex(c => c && c.id === sc.id);\\n"
    "    if (idx >= 0) CONTACTS.splice(idx, 1);\\n"
    "  }\\n"
    "  selectedContact = (typeof CONTACTS !== 'undefined' && CONTACTS.length) ? CONTACTS[0] : null;\\n"
    "  try { renderMsgList(); } catch (e) {}\\n"
    "  try { renderThread(); } catch (e) {}\\n"
    "}"
)
DISMISS_FN_PATCHED_ANCHOR = (
    "window.location.href = 'sms:' + phone;\\n  }\\n}\\n\\n"
    + DISMISS_FN_INSERT
    + "\\n\\nfunction regenAi() {"
)


def patch_regenai(text: str) -> tuple[str, str]:
    """Returns (new_text, status) where status is 'patched', 'noop', or 'error:<msg>'."""
    if REGEN_PATCHED in text and not any(m in text for m in CANNED_MARKERS):
        return text, "noop"
    matches = text.count(REGEN_ORIGINAL)
    if matches == 0:
        canned = [m for m in CANNED_MARKERS if m in text]
        if canned:
            return text, (
                "error: canned alts present but original regenAi() block not found. "
                "The design upload changed the surrounding code; re-derive the patch by "
                f"hand and update tools/patch_standalone.py. Canned strings: {canned}"
            )
        return text, "error: nothing to patch (no original regenAi(), no canned alts)"
    if matches > 1:
        return text, f"error: original regenAi() block found {matches} times; expected 1"
    return text.replace(REGEN_ORIGINAL, REGEN_PATCHED, 1), "patched"


def patch_dismiss(text: str) -> tuple[str, str]:
    btn_already = DISMISS_BTN_PATCHED in text
    fn_already = "function dismissThread()" in text

    if btn_already and fn_already:
        return text, "noop"

    # Button onclick.
    if not btn_already:
        n = text.count(DISMISS_BTN_ORIGINAL)
        if n == 0:
            return text, (
                "error: original dismiss-btn markup not found. The design upload "
                "changed the thread-foot; re-derive the patch by hand and update "
                "tools/patch_standalone.py."
            )
        if n > 1:
            return text, f"error: dismiss-btn markup found {n} times; expected 1"
        text = text.replace(DISMISS_BTN_ORIGINAL, DISMISS_BTN_PATCHED, 1)

    # Function injection.
    if not fn_already:
        n = text.count(DISMISS_FN_ANCHOR)
        if n == 0:
            return text, (
                "error: anchor for dismissThread() injection not found. The design "
                "upload changed copyAndOpenImessage()/regenAi() neighborhood; "
                "re-derive the patch by hand."
            )
        if n > 1:
            return text, f"error: dismissThread() anchor found {n} times; expected 1"
        text = text.replace(DISMISS_FN_ANCHOR, DISMISS_FN_PATCHED_ANCHOR, 1)

    return text, "patched"


def main() -> int:
    if not TARGET.exists():
        print(f"error: {TARGET} not found", file=sys.stderr)
        return 2
    text = TARGET.read_text(encoding="utf-8")
    original = text

    text, regen_status = patch_regenai(text)
    if regen_status.startswith("error"):
        print(f"regenAi: {regen_status}", file=sys.stderr)
        return 1
    print(f"regenAi: {regen_status}")

    text, dismiss_status = patch_dismiss(text)
    if dismiss_status.startswith("error"):
        print(f"dismiss: {dismiss_status}", file=sys.stderr)
        return 1
    print(f"dismiss: {dismiss_status}")

    if text != original:
        TARGET.write_text(text, encoding="utf-8")
        print(f"wrote {TARGET.name}")
    else:
        print(f"no changes: {TARGET.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
