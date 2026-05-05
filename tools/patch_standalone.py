#!/usr/bin/env python3
"""Re-apply the Reply or Die standalone patches after a fresh design upload.

The Inbox iframe loads docs/standalone.html. That file is exported from a
design tool and ships with hardcoded demo behavior that we override:

  1. regenAi() — picks at random from a 3-element alts array; we patch it to
     call window.parent.miranda2RegenAi() so the AI Regenerate button uses
     the real /api/ai-suggest-reply backend.
  2. const GROUPS = [...] — hardcoded group-chat demo data; we patch it to
     fetch data/group_chats_demo.json at runtime so the "Group chats" rail
     chip in the inbox iframe shows the canonical demo and the data lives
     in a real, editable file in the repo.

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

# ---- Patch 2: GROUPS loader ----
# Replace the hardcoded `const GROUPS = [ ... ];` literal with a `let GROUPS = [];`
# stub plus an async loader that fetches data/group_chats_demo.json. Anchors:
#   start: literal `const GROUPS = [\n` inside the bundler/template JSON string
#   end:   literal `\n];\n\n// ───── REPLIED THIS WEEK` immediately after
# Both anchors are unique; the script errors loudly if they shift on re-upload.

GROUPS_MARKER = "GROUP_CHATS_LOADER (Reply or Die)"
GROUPS_START_ANCHOR = "const GROUPS = [\\n"
GROUPS_END_ANCHOR = "\\n];\\n\\n// ───── REPLIED THIS WEEK"

# Replacement JS, using single quotes only (no escaping needed for the JSON-encoded
# template string) and `\\n` for newlines so it lives correctly inside the bundle's
# template literal. Keep this code self-contained — it runs inside the iframe.
GROUPS_REPLACEMENT = (
    "let GROUPS = [];\\n"
    "/* GROUP_CHATS_LOADER (Reply or Die): hardcoded GROUPS replaced with data\\n"
    "   fetched from data/group_chats_demo.json. Re-applied by\\n"
    "   tools/patch_standalone.py whenever the standalone is re-uploaded. */\\n"
    "(async () => {\\n"
    "  try {\\n"
    "    const r = await fetch('../data/group_chats_demo.json', {cache:'no-cache'});\\n"
    "    if (!r.ok) return;\\n"
    "    const raw = await r.json();\\n"
    "    const arr = (raw && raw.groups) || [];\\n"
    "    GROUPS = arr.map(g => {\\n"
    "      const members = g.members || [];\\n"
    "      const messages = g.messages || [];\\n"
    "      const last = messages[messages.length - 1];\\n"
    "      const lastText = last\\n"
    "        ? (last.from_me ? 'You: ' + last.text : (last.from ? last.from + ': ' + last.text : last.text))\\n"
    "        : '';\\n"
    "      return {\\n"
    "        id: g.id,\\n"
    "        group: true,\\n"
    "        name: g.group_name + (members.length ? ' (' + members.length + ')' : ''),\\n"
    "        members: members,\\n"
    "        phone: 'Group · ' + members.length + ' people',\\n"
    "        waitH: typeof g.wait_hours === 'number' ? g.wait_hours : 12,\\n"
    "        lastText: lastText,\\n"
    "        msgs: messages.map(m => ({\\n"
    "          from: m.from,\\n"
    "          me: !!m.from_me,\\n"
    "          t: m.text,\\n"
    "          ago: m.ago || ''\\n"
    "        })),\\n"
    "        ai: g.suggested_reply || ''\\n"
    "      };\\n"
    "    });\\n"
    "    if (typeof renderMsgList === 'function') renderMsgList();\\n"
    "    if (typeof currentFilter !== 'undefined' && currentFilter === 'group' && typeof renderThread === 'function') {\\n"
    "      const list = (typeof filteredContacts === 'function') ? filteredContacts() : [];\\n"
    "      if (list.length) {\\n"
    "        if (!selectedContact || !GROUPS.includes(selectedContact)) selectedContact = list[0];\\n"
    "        renderThread();\\n"
    "      }\\n"
    "    }\\n"
    "  } catch (e) { console.warn('group_chats_demo load failed', e); }\\n"
    "})();\\n\\n// ───── REPLIED THIS WEEK"
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


# ---- Patch 3: Group-thread UI fix ----
# We don't generate AI suggestions for group chats, so hide the AI card and
# rename "Copy & open iMessage" to just "Open iMessage" for that mode. Also
# guard copyAndOpenImessage() against non-numeric phone strings (group threads
# carry a synthetic "Group · N people" label, not a phone number, which would
# turn into an invalid sms: URL).
#
# Three narrow string-replacements; the marker GROUP_UI_FIX makes the patch
# idempotent on re-runs.

GROUP_UI_MARKER = "GROUP_UI_FIX (Reply or Die)"

# 3a — live AI card branch: insert an `isGroup ?` arm before the live card so
# group threads show a dashed "no AI for groups" placeholder instead.
GROUP_UI_AI_OLD = (
    "      ` : `\\n"
    "        <div class=\\\"ai-card\\\">\\n"
    "          <div class=\\\"ai-head\\\">\\n"
    "            <span>✦ ${isGroup?'Suggested reply to the group':'Suggested reply'} · editable<\\u002Fspan>"
)
GROUP_UI_AI_NEW = (
    "      ` : isGroup ? `\\n"
    "        <div class=\\\"ai-card\\\" style=\\\"opacity:.55;border-style:dashed\\\">\\n"
    "          <div class=\\\"ai-head\\\">\\n"
    "            <span style=\\\"opacity:.7\\\">\U0001F465 group chat — no AI draft<\\u002Fspan>\\n"
    "          <\\u002Fdiv>\\n"
    "          <div class=\\\"ai-body\\\" style=\\\"font-style:italic;color:var(--text-2)\\\">"
    "we don't draft replies for group chats. open Messages and jump in.<\\u002Fdiv>\\n"
    "        <\\u002Fdiv>\\n"
    "      ` : `\\n"
    "        <div class=\\\"ai-card\\\">\\n"
    "          <div class=\\\"ai-head\\\">\\n"
    "            <span>✦ Suggested reply · editable<\\u002Fspan>"
)

# 3b — live footer send-btn: branch the label and onclick on isGroup.
GROUP_UI_BTN_OLD = (
    "<button class=\\\"send-btn\\\" onclick=\\\"copyAndOpenImessage()\\\">"
    "Copy &amp; open iMessage →<\\u002Fbutton>"
)
GROUP_UI_BTN_NEW = (
    "<button class=\\\"send-btn\\\" onclick=\\\"${isGroup?'openImessage()':'copyAndOpenImessage()'}\\\">"
    "${isGroup?'Open iMessage':'Copy &amp; open iMessage'} →<\\u002Fbutton>"
)

# 3c — phone-URL guard + add openImessage(). Replace the sms:-builder so it
# only fires for numeric phones, and slot in openImessage() right after.
GROUP_UI_FN_OLD = (
    "  if (phone) {\\n"
    "    window.location.href = 'sms:' + phone;\\n"
    "  }\\n"
    "}\\n\\n"
    "function regenAi() {"
)
GROUP_UI_FN_NEW = (
    "  // GROUP_UI_FIX (Reply or Die): only follow sms: for numeric phones.\\n"
    "  if (phone && /^[+\\\\d]/.test(phone)) {\\n"
    "    window.location.href = 'sms:' + phone;\\n"
    "  }\\n"
    "}\\n\\n"
    "function openImessage() {\\n"
    "  // GROUP_UI_FIX: used for group chats (no phone to deep-link). Opens Messages.\\n"
    "  window.location.href = 'imessage:';\\n"
    "}\\n\\n"
    "function regenAi() {"
)


def _patch_groups(text: str) -> tuple[str, str]:
    """Returns (new_text, status_message). Raises ValueError if unpatchable."""
    if GROUPS_MARKER in text:
        return text, "GROUPS loader already patched"
    start = text.find(GROUPS_START_ANCHOR)
    end = text.find(GROUPS_END_ANCHOR)
    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            "GROUPS literal anchors not found. The design upload changed the "
            "surrounding code shape; re-derive the GROUPS_START_ANCHOR / "
            "GROUPS_END_ANCHOR in tools/patch_standalone.py."
        )
    # span: from `const GROUPS = [\n` through the closing `];\n` (inclusive),
    # leaving the next-section comment untouched.
    span_start = start
    span_end = end + len(GROUPS_END_ANCHOR)
    return text[:span_start] + GROUPS_REPLACEMENT + text[span_end:], "patched GROUPS loader"


def _patch_group_ui(text: str) -> tuple[str, str]:
    """Returns (new_text, status_message). Raises ValueError if unpatchable."""
    if GROUP_UI_MARKER in text:
        return text, "group-thread UI already patched"

    new_text = text
    for old, new, label in (
        (GROUP_UI_AI_OLD, GROUP_UI_AI_NEW, "live AI card head"),
        (GROUP_UI_BTN_OLD, GROUP_UI_BTN_NEW, "live send-btn"),
        (GROUP_UI_FN_OLD, GROUP_UI_FN_NEW, "copyAndOpenImessage / openImessage"),
    ):
        n = new_text.count(old)
        if n == 0:
            raise ValueError(
                f"group-thread UI: anchor for '{label}' not found. "
                "The design upload changed the surrounding code; re-derive "
                "the GROUP_UI_*_OLD/NEW constants in tools/patch_standalone.py."
            )
        if n > 1:
            raise ValueError(
                f"group-thread UI: anchor for '{label}' found {n} times; expected 1"
            )
        new_text = new_text.replace(old, new, 1)
    return new_text, "patched group-thread UI"


def main() -> int:
    if not TARGET.exists():
        print(f"error: {TARGET} not found", file=sys.stderr)
        return 2
    text = TARGET.read_text(encoding="utf-8")
    original_text = text

    try:
        text, msg1 = _patch_regen_ai(text)
        print(msg1)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        text, msg2 = _patch_groups(text)
        print(msg2)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        text, msg3 = _patch_group_ui(text)
        print(msg3)
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
