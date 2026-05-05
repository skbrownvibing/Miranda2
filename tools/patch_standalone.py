#!/usr/bin/env python3
"""Re-apply the Reply or Die standalone patches after a fresh design upload.

The Inbox iframe loads docs/standalone.html. That file is exported from a
design tool and ships with hardcoded demo behavior that we override:

  1. regenAi() — the design tool's version picks at random from a 3-element
     alts array. We rewrite it to call window.parent.miranda2RegenAi() so
     the AI Regenerate button uses the real /api/ai-suggest-reply backend.
  2. Group chats — the design tool ships a "Group chats" rail chip plus a
     hardcoded GROUPS dataset. We don't generate AI drafts for groups, so
     a Group-chats filter on the inbox rail is a dead end. Patch removes
     the rail chip and zeroes out the GROUPS array.
  3. FDA step framing — the design ships a Step 2 that asks the user to
     toggle "Reply or Die" in Full Disk Access and claims the app will
     auto-detect. The real flow needs Terminal (the app the export.command
     runs in) to have FDA, and there is no auto-detection — the user must
     confirm. Patch rewrites the instruction copy, the highlighted mock
     row, and the Continue button label.

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

# ---- Patch 1: regenAi → backend bridge ----

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

# ---- Patch 2: Cut group chats ----
# Removes the "Group chats" rail-chip button from the inbox rail and replaces
# the hardcoded `const GROUPS = [ ... ];` literal with `const GROUPS = [];`.
# `filteredContacts()` and `findEntry()` already tolerate an empty GROUPS array
# (they just return nothing for that filter), and the rail-chip click handler
# only iterates buttons that exist in the DOM, so dropping the button is safe.

GROUPS_CUT_MARKER = "GROUPS_CUT (Reply or Die)"

GROUP_CHIP_OLD = (
    "            <button class=\\\"rail-chip\\\" data-filter=\\\"group\\\">"
    "<span>Group chats<\\u002Fspan>"
    "<span class=\\\"ct\\\" id=\\\"ct-group\\\">1<\\u002Fspan>"
    "<\\u002Fbutton>\\n"
)

GROUPS_LITERAL_START = "const GROUPS = [\\n"
GROUPS_LITERAL_END = "\\n];\\n\\n// ───── REPLIED THIS WEEK"
GROUPS_LITERAL_REPLACEMENT = (
    "const GROUPS = []; "
    "/* GROUPS_CUT (Reply or Die): group chats cut entirely — see "
    "tools/patch_standalone.py. */\\n"
    "\\n// ───── REPLIED THIS WEEK"
)


def _patch_regen_ai(text: str) -> tuple[str, str]:
    """Returns (new_text, status_message). Raises ValueError if unpatchable."""
    if PATCHED in text and not any(m in text for m in CANNED_MARKERS):
        return text, "regenAi already patched"
    matches = text.count(ORIGINAL)
    if matches == 0:
        canned = [m for m in CANNED_MARKERS if m in text]
        if canned:
            raise ValueError(
                "canned alts present but original regenAi() block not found.\n"
                "  The design upload changed the surrounding code; re-derive "
                "the patch by hand and update tools/patch_standalone.py.\n"
                f"  Canned strings still in file: {canned}"
            )
        raise ValueError("nothing to patch (no regenAi original block, no canned alts).")
    if matches > 1:
        raise ValueError(f"original regenAi() block found {matches} times; expected 1")
    return text.replace(ORIGINAL, PATCHED, 1), "patched regenAi"


def _patch_cut_groups(text: str) -> tuple[str, str]:
    """Returns (new_text, status_message). Raises ValueError if unpatchable."""
    if GROUPS_CUT_MARKER in text:
        return text, "groups already cut"

    # 2a — remove the rail chip
    n_chip = text.count(GROUP_CHIP_OLD)
    if n_chip == 0:
        raise ValueError(
            "Group-chats rail chip not found. The design upload changed the "
            "rail-chip markup; re-derive GROUP_CHIP_OLD in tools/patch_standalone.py."
        )
    if n_chip > 1:
        raise ValueError(f"Group-chats rail chip found {n_chip} times; expected 1")
    new_text = text.replace(GROUP_CHIP_OLD, "", 1)

    # 2b — nullify the GROUPS array
    start = new_text.find(GROUPS_LITERAL_START)
    end = new_text.find(GROUPS_LITERAL_END)
    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            "GROUPS literal anchors not found. The design upload changed the "
            "surrounding code shape; re-derive GROUPS_LITERAL_START / "
            "GROUPS_LITERAL_END in tools/patch_standalone.py."
        )
    span_end = end + len(GROUPS_LITERAL_END)
    new_text = new_text[:start] + GROUPS_LITERAL_REPLACEMENT + new_text[span_end:]

    return new_text, "patched: cut group chats"


# ---- Patch 3: Reframe FDA step around Terminal ----
# The design ships Step 2 telling the user to toggle "Reply or Die" in
# Full Disk Access and claims the app will auto-detect the change. The
# real flow grants FDA to Terminal (the app the export.command uses).
# This patch:
#   - rewrites instruction copy ("Toggle Reply or Die on" -> "Toggle Terminal on",
#     "Find Reply or Die" -> "Find Terminal", and replaces the auto-detect
#     promise with a click-to-confirm sentence)
#   - removes the pre-granted "Terminal on" mock row
#   - renames the highlighted mock row "Reply or Die" -> "Terminal"
#   - relabels the disabled Continue button to "I've given Terminal access"
#     and removes the disabled attribute

FDA_PATCHES = [
    (
        "Toggle Reply or Die on",
        "Toggle Terminal on",
    ),
    (
        "Find <em>Reply or Die<\\u002Fem> in the list and flip the switch.",
        "Find <em>Terminal<\\u002Fem> in the list and flip the switch.",
    ),
    (
        "We'll detect the change automatically. Then click continue.",
        # The standalone HTML body lives inside a JSON-string bundler
        # template, so embedded double quotes must stay JSON-escaped.
        "Once it's flipped, click the \\\"I've given Terminal access\\\" button below.",
    ),
    (
        "Waiting for permission…",
        "Flip the Terminal switch in System Settings",
    ),
    (
        "<div class=\\\"mock-row\\\"><div class=\\\"mock-dot g\\\"><\\u002Fdiv><span>Terminal<\\u002Fspan>"
        "<div class=\\\"mock-switch on\\\"><span><\\u002Fspan><\\u002Fdiv><\\u002Fdiv>\\n                  ",
        "",
    ),
    (
        "<div class=\\\"mock-row highlight\\\"><div class=\\\"mock-dot a\\\"><\\u002Fdiv>"
        "<span>Reply or Die<\\u002Fspan><div class=\\\"mock-switch\\\" id=\\\"fdaSwitch\\\">",
        "<div class=\\\"mock-row highlight\\\"><div class=\\\"mock-dot a\\\"><\\u002Fdiv>"
        "<span>Terminal<\\u002Fspan><div class=\\\"mock-switch\\\" id=\\\"fdaSwitch\\\">",
    ),
    (
        "<button class=\\\"btn btn-primary\\\" id=\\\"fdaContinue\\\" disabled=\\\"\\\" onclick=\\\"setupGo(3)\\\">"
        "<span>Continue<\\u002Fspan><span class=\\\"arrow\\\">→<\\u002Fspan><\\u002Fbutton>",
        "<button class=\\\"btn btn-primary\\\" id=\\\"fdaContinue\\\" onclick=\\\"setupGo(3)\\\">"
        "<span>I’ve given Terminal access<\\u002Fspan><span class=\\\"arrow\\\">→<\\u002Fspan><\\u002Fbutton>",
    ),
]


FDA_DONE_MARKER = "I’ve given Terminal access"


def _patch_fda_terminal(text: str) -> tuple[str, str]:
    """Returns (new_text, status_message). Raises ValueError if unpatchable."""
    if FDA_DONE_MARKER in text and not any(old in text for old, _ in FDA_PATCHES):
        return text, "FDA-terminal already patched"
    out = text
    for old, new in FDA_PATCHES:
        n = out.count(old)
        if n == 0:
            # Already-patched anchor: skip if the target state is present
            # (or, for deletions, the old text being absent is enough).
            if not new or new in out:
                continue
            raise ValueError(f"FDA-terminal anchor not found: {old[:80]!r}")
        if n > 1:
            raise ValueError(f"FDA-terminal anchor found {n} times: {old[:80]!r}")
        out = out.replace(old, new, 1)
    return out, "patched FDA step around Terminal"


def main() -> int:
    if not TARGET.exists():
        print(f"error: {TARGET} not found", file=sys.stderr)
        return 2
    text = TARGET.read_text(encoding="utf-8")
    original_text = text

    for patcher in (_patch_regen_ai, _patch_cut_groups, _patch_fda_terminal):
        try:
            text, msg = patcher(text)
            print(msg)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1

    if text != original_text:
        TARGET.write_text(text, encoding="utf-8")
        print(f"wrote {TARGET.name}")
    else:
        print(f"no changes: {TARGET.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
