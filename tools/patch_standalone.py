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
  3. REPLIED dataset — the design tool ships 14 hardcoded "Replied this
     week" rows (Mom / Wesley / Bea / …). We replace it with the 8
     conversations from data/miranda_demo.json that have
     i_replied_last:true so the iframe's archive view matches the names
     the rest of the app uses.
  4. Mark unread → Mark reply needed — the archive footer button on
     replied threads said "Mark unread" and called a no-op. We rename it
     to "Mark reply needed" and make restoreThread() actually move the
     thread out of REPLIED and into CONTACTS ("Waiting on you").

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

# ---- Patch 3: REPLIED dataset → demo data from miranda_demo.json ----
# Names / phones / lastText come from data/miranda_demo.json (the 8
# conversations with i_replied_last:true). whenLabel is hardcoded to give
# the archive list a realistic spread across the week — the iframe is
# self-contained and doesn't see the parent app's time-shifted timestamps.

REPLIED_DEMO_MARKER = "REPLIED_DEMO_DATA (Reply or Die)"

REPLIED_LITERAL_START = (
    "// ───── REPLIED THIS WEEK (14) — I sent the last message ─────\\n"
    "const REPLIED = [\\n"
)
REPLIED_LITERAL_END = "\\n];\\n\\n// ───── DISMISSED"

REPLIED_LITERAL_REPLACEMENT = (
    "// ───── REPLIED THIS WEEK — REPLIED_DEMO_DATA (Reply or Die): "
    "populated from data/miranda_demo.json (i_replied_last:true). "
    "See tools/patch_standalone.py. ─────\\n"
    "const REPLIED = [\\n"
    "  { id:'iMessage;-;+12125550111', name:'Rachel Green',     phone:'+12125550111', lastText:'Always.',                                  whenLabel:'Replied 12m ago' },\\n"
    "  { id:'iMessage;-;+12125550112', name:'Blair Waldorf',    phone:'+12125550112', lastText:'Do we need to dress up?',                  whenLabel:'Replied 1h ago' },\\n"
    "  { id:'iMessage;-;+12125550113', name:'Jess Day',         phone:'+12125550113', lastText:'Honestly yes.',                            whenLabel:'Replied 3h ago' },\\n"
    "  { id:'iMessage;-;+12125550114', name:'Joey Tribbiani',   phone:'+12125550114', lastText:'How many sandwiches are we talking?',      whenLabel:'Replied yesterday' },\\n"
    "  { id:'iMessage;+;chat1002',     name:'Regina George',    phone:'+13125550102', lastText:'That feels right.',                        whenLabel:'Replied yesterday' },\\n"
    "  { id:'iMessage;+;chat1003',     name:'Lorelai Gilmore',  phone:'+13125550103', lastText:'On my way.',                               whenLabel:'Replied 2d ago' },\\n"
    "  { id:'iMessage;-;+12125550115', name:'Elaine Benes',     phone:'+12125550115', lastText:'Also I support the anti-dancing stance.',  whenLabel:'Replied 3d ago' },\\n"
    "  { id:'iMessage;-;+12125550116', name:'Miranda Priestly', phone:'+12125550116', lastText:'Understood.',                              whenLabel:'Replied 5d ago' },\\n"
    "];\\n"
    "\\n// ───── DISMISSED"
)

# ---- Patch 4: "Mark unread" → "Mark reply needed" + working restoreThread ----

MARK_REPLY_MARKER = "MARK_REPLY_NEEDED (Reply or Die)"

MARK_UNREAD_OLD = (
    "${isReplied?'Mark unread':isDismissed?'Restore to inbox'"
    ":'Mark as not spam'}"
)
MARK_UNREAD_NEW = (
    "${isReplied?'Mark reply needed':isDismissed?'Restore to inbox'"
    ":'Mark as not spam'}"
)

RESTORE_OLD = "function restoreThread() { /* visual no-op for prototype */ }"
RESTORE_NEW = (
    "function restoreThread() {\\n"
    "  // PATCHED MARK_REPLY_NEEDED (Reply or Die): for Replied-this-week\\n"
    "  // threads, move the row back into CONTACTS (\\\"Waiting on you\\\")\\n"
    "  // and switch the rail filter. Dismissed / auto-filtered remain a\\n"
    "  // visual no-op. See tools/patch_standalone.py.\\n"
    "  if (!selectedContact) return;\\n"
    "  const idx = REPLIED.indexOf(selectedContact);\\n"
    "  if (idx === -1) return;\\n"
    "  const c = selectedContact;\\n"
    "  REPLIED.splice(idx, 1);\\n"
    "  const promoted = {\\n"
    "    id: c.id, name: c.name, phone: c.phone,\\n"
    "    photo: null,\\n"
    "    lastText: c.lastText,\\n"
    "    waitH: 1,\\n"
    "    msgs: [{ me: true, t: c.lastText, ago: 'just now' }],\\n"
    "    ai: ''\\n"
    "  };\\n"
    "  CONTACTS.unshift(promoted);\\n"
    "  selectedContact = promoted;\\n"
    "  currentFilter = 'all';\\n"
    "  document.querySelectorAll('.rail-chip[data-filter]').forEach(b => {\\n"
    "    b.classList.toggle('active', b.dataset.filter === 'all');\\n"
    "  });\\n"
    "  renderMsgList();\\n"
    "  renderThread();\\n"
    "}"
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


def _patch_replied_demo_data(text: str) -> tuple[str, str]:
    """Returns (new_text, status_message). Raises ValueError if unpatchable."""
    if REPLIED_DEMO_MARKER in text:
        return text, "REPLIED already populated from demo data"

    start = text.find(REPLIED_LITERAL_START)
    end = text.find(REPLIED_LITERAL_END)
    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            "REPLIED literal anchors not found. The design upload changed "
            "the surrounding code shape; re-derive REPLIED_LITERAL_START / "
            "REPLIED_LITERAL_END in tools/patch_standalone.py."
        )
    span_end = end + len(REPLIED_LITERAL_END)
    new_text = text[:start] + REPLIED_LITERAL_REPLACEMENT + text[span_end:]
    return new_text, "patched: REPLIED uses miranda_demo.json names"


def _patch_mark_reply_needed(text: str) -> tuple[str, str]:
    """Returns (new_text, status_message). Raises ValueError if unpatchable."""
    if MARK_REPLY_MARKER in text:
        return text, "Mark reply needed already patched"

    # 4a — rename the archive footer button
    n_btn = text.count(MARK_UNREAD_OLD)
    if n_btn == 0:
        raise ValueError(
            "'Mark unread' ternary not found. The design upload changed "
            "the archive footer markup; re-derive MARK_UNREAD_OLD in "
            "tools/patch_standalone.py."
        )
    if n_btn > 1:
        raise ValueError(f"'Mark unread' ternary found {n_btn} times; expected 1")
    new_text = text.replace(MARK_UNREAD_OLD, MARK_UNREAD_NEW, 1)

    # 4b — replace the no-op restoreThread with the real implementation
    n_fn = new_text.count(RESTORE_OLD)
    if n_fn == 0:
        raise ValueError(
            "no-op restoreThread() not found. The design upload changed "
            "the function body; re-derive RESTORE_OLD in "
            "tools/patch_standalone.py."
        )
    if n_fn > 1:
        raise ValueError(f"no-op restoreThread() found {n_fn} times; expected 1")
    new_text = new_text.replace(RESTORE_OLD, RESTORE_NEW, 1)

    return new_text, "patched: Mark reply needed + restoreThread"


def main() -> int:
    if not TARGET.exists():
        print(f"error: {TARGET} not found", file=sys.stderr)
        return 2
    text = TARGET.read_text(encoding="utf-8")
    original_text = text

    for patcher in (
        _patch_regen_ai,
        _patch_cut_groups,
        _patch_replied_demo_data,
        _patch_mark_reply_needed,
    ):
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
