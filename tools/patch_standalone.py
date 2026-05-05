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
  3. Archive REPLIED list — the design tool ships placeholder names like
     Mom / Wesley / Bea, with only `lastText` per entry (which makes the
     thread-panel renderer synthesize a fake "(earlier in this thread...)"
     bubble). We repopulate from data/miranda_demo.json's i_replied_last
     conversations and emit full `msgs` arrays so the panel shows the real
     back-and-forth.
  4. Archive AUTO-FILTERED list — the design tool ships a generic
     templates dict + rotation IIFE. Replace with the 70 entries spelled
     out in docs/dummy-data-spec.md §4 (delivery / spam-with-fake-pols /
     2FA), each with explicit waitH.
  5. Compact archive UI for replied threads — the design tool renders a
     full dashed AI-card ("✓ you handled this one — no draft needed…")
     plus a left-hand "Mark unread" button. Replace the AI-card with a
     small "already replied" pill and drop the Mark-unread button (the
     existing right-hand "Open in iMessage →" button stays).

Whenever the standalone file is re-uploaded, run:

    python3 tools/patch_standalone.py

Idempotent: a no-op if the file is already patched. Exits non-zero if the
canned strings are present and the original block can't be located (which
means the design tool changed the surrounding code shape and the patch
needs to be revisited).
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "docs" / "standalone.html"
DEMO_DATA = ROOT / "data" / "miranda_demo.json"
DATA_SPEC = ROOT / "docs" / "dummy-data-spec.md"

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


# ---- Patch 3: Repopulate REPLIED with TV characters ----
# The design tool ships REPLIED entries with only `lastText`, which trips
# the thread-panel synthesizer that prepends a fake "(earlier in this
# thread...)" bubble. Build full entries (with `msgs` arrays) from the
# i_replied_last:true conversations in data/miranda_demo.json so the panel
# shows the real exchanges.

REPLIED_TV_MARKER = "REPLIED_TV (Reply or Die)"

REPLIED_LITERAL_START = "const REPLIED = [\\n"
REPLIED_LITERAL_END = "\\n];\\n\\n// ───── DISMISSED"


def _ago_label(then: datetime, now: datetime) -> str:
    """Compact relative-time label, matches CONTACTS msgs ago format ('6d', '14h', '40m')."""
    delta = now - then
    secs = max(0, int(delta.total_seconds()))
    mins = secs // 60
    hours = mins // 60
    days = hours // 24
    if days >= 1:
        return f"{days}d"
    if hours >= 1:
        return f"{hours}h"
    if mins >= 1:
        return f"{mins}m"
    return "just now"


def _when_label(then: datetime, now: datetime) -> str:
    """Right-side label on the archive list ('Replied 5h ago', 'Replied 2d ago')."""
    delta = now - then
    secs = max(0, int(delta.total_seconds()))
    mins = secs // 60
    hours = mins // 60
    days = hours // 24
    if days == 1:
        return "Replied yesterday"
    if days >= 2:
        return f"Replied {days}d ago"
    if hours >= 1:
        return f"Replied {hours}h ago"
    if mins >= 1:
        return f"Replied {mins}m ago"
    return "Replied just now"


def _build_replied_js() -> str:
    """Render the REPLIED literal as JS source (real newlines, JS-escaped strings).

    Source is data/miranda_demo.json filtered to non-group conversations with
    i_replied_last:true. `now` for relative-time labels is the file's
    exported_at — the demo is a fixed snapshot, not wall-clock.
    """
    payload = json.loads(DEMO_DATA.read_text(encoding="utf-8"))
    now = datetime.fromisoformat(payload["exported_at"])
    convos = [
        c for c in payload["conversations"]
        if c.get("i_replied_last") and not c.get("is_group")
    ]
    # Sort newest-first so the archive list reads top-down by recency.
    convos.sort(key=lambda c: c["last_message_at"], reverse=True)

    lines: list[str] = ["const REPLIED = ["]
    lines.append(
        "  /* REPLIED_TV (Reply or Die): generated from "
        "data/miranda_demo.json (i_replied_last:true) — re-run "
        "tools/patch_standalone.py after design uploads. */"
    )
    for i, c in enumerate(convos, start=1):
        last_at = datetime.fromisoformat(c["last_message_at"])
        when = _when_label(last_at, now)
        name = _js_str(c["contact_name"])
        phone = _js_str(c["phone"])
        last_text = _js_str(c["last_message_text"])
        lines.append(f"  {{ id:'r{i}', name:{name}, phone:{phone},")
        lines.append(f"    lastText:{last_text},")
        lines.append(f"    whenLabel:'{when}',")
        lines.append("    msgs:[")
        for m in c["messages"]:
            t_dt = datetime.fromisoformat(m["date"])
            ago = _ago_label(t_dt, now)
            me = "true " if m["from_me"] else "false"
            txt = _js_str(m["text"])
            lines.append(f"      {{ me:{me}, t:{txt}, ago:'{ago}' }},")
        lines.append("    ] },")
    lines.append("];")
    return "\n".join(lines)


def _js_str(s: str) -> str:
    """Encode a Python string as a JS double-quoted string literal."""
    # json.dumps gives valid JS for plain strings (no `</`, no ` ` issues here).
    return json.dumps(s, ensure_ascii=False)


def _embed_in_template(js_source: str) -> str:
    """JSON-string-encode `js_source` for embedding in the bundler template.

    The whole HTML lives inside a JSON string in <script type="__bundler/template">,
    so we need real newlines as `\\n`, double quotes as `\\"`, backslashes as `\\\\`.
    Also rewrite `</` → `<\\u002F` so the embedded source doesn't terminate the
    surrounding <script> element prematurely (matches the design tool's output).
    """
    # json.dumps produces e.g. `"foo\\nbar"`; strip the wrapping quotes.
    encoded = json.dumps(js_source, ensure_ascii=False)[1:-1]
    return encoded.replace("</", "<\\u002F")


def _patch_replied_tv(text: str) -> tuple[str, str]:
    """Returns (new_text, status_message). Raises ValueError if unpatchable."""
    start = text.find(REPLIED_LITERAL_START)
    end = text.find(REPLIED_LITERAL_END)
    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            "REPLIED literal anchors not found. The design upload changed the "
            "surrounding code shape; re-derive REPLIED_LITERAL_START / "
            "REPLIED_LITERAL_END in tools/patch_standalone.py."
        )
    span_end = end + len(REPLIED_LITERAL_END)
    block = text[start:span_end]
    # Treat as up-to-date only if the marker is present AND the full-msgs
    # shape has been generated (older runs of this patch only emitted lastText).
    if REPLIED_TV_MARKER in block and "msgs:[" in block:
        return text, "REPLIED already TV-populated"
    js_source = _build_replied_js()
    embedded = _embed_in_template(js_source)
    replacement = embedded + "\\n\\n// ───── DISMISSED"
    new_text = text[:start] + replacement + text[span_end:]
    return new_text, "patched: REPLIED → TV characters (with msgs)"


# ---- Patch 4: Repopulate AUTO-FILTERED from docs/dummy-data-spec.md §4 ----
# The design tool ships AUTO_TEMPLATES + an IIFE that rotates 70 generic
# entries out of the templates. Replace the whole thing with a flat AUTO
# array sourced from the spec — explicit sender, kind, waitH, lastText.

AUTO_SPEC_MARKER = "AUTO_SPEC (Reply or Die)"

AUTO_LITERAL_START = "const AUTO_TEMPLATES = {\\n"
AUTO_LITERAL_END = "\\n})();\\n\\n// Stylized contact portraits"


def _parse_auto_spec() -> list[dict]:
    """Parse §4 of docs/dummy-data-spec.md into [{n, kind, sender, waitH, text}].

    Bucket → kind mapping is driven by the section headers (### …),
    so reordering or relabeling the spec sections won't silently break.
    """
    if not DATA_SPEC.exists():
        raise ValueError(
            f"{DATA_SPEC} not found. Add the spec doc before running this patch."
        )
    text = DATA_SPEC.read_text(encoding="utf-8")
    # Find the start of section 4.
    sec4 = re.search(r"^## 4\.\s+Auto-filtered.*$", text, flags=re.MULTILINE)
    if not sec4:
        raise ValueError("Section '## 4. Auto-filtered' not found in data spec.")
    body = text[sec4.end():]
    # Stop at the next H2.
    next_h2 = re.search(r"^## ", body, flags=re.MULTILINE)
    if next_h2:
        body = body[:next_h2.start()]

    # Walk lines, tracking the current kind by H3 heading.
    kind = None
    entries: list[dict] = []
    row = re.compile(
        r"\|\s*F(\d+)\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*$"
    )
    for line in body.splitlines():
        if line.startswith("### "):
            head = line[4:].lower()
            if "delivery" in head or "order" in head:
                kind = "delivery"
            elif "spam" in head:
                kind = "spam"
            elif "verification" in head or "2fa" in head:
                kind = "2fa"
            else:
                kind = None
            continue
        m = row.match(line)
        if not m or kind is None:
            continue
        entries.append({
            "n": int(m.group(1)),
            "kind": kind,
            "sender": m.group(2).strip(),
            "waitH": int(m.group(3)),
            "text": m.group(4).strip(),
        })

    if len(entries) != 70:
        raise ValueError(
            f"Expected 70 auto-filtered entries in spec, got {len(entries)}."
        )
    return entries


def _build_auto_js() -> str:
    """Render AUTO_TEMPLATES + AUTO as JS source, sourced from the spec."""
    entries = _parse_auto_spec()
    lines: list[str] = []
    lines.append(
        "const AUTO_TEMPLATES = {}; "
        "/* AUTO_SPEC (Reply or Die): unused — AUTO is generated directly "
        "from docs/dummy-data-spec.md §4. See tools/patch_standalone.py. */"
    )
    lines.append("const AUTO = [")
    for e in entries:
        sender = json.dumps(e["sender"], ensure_ascii=False)
        body = json.dumps(e["text"], ensure_ascii=False)
        lines.append(
            f"  {{ id:'a{e['n']}', kind:'{e['kind']}', "
            f"name:{sender}, phone:'—', "
            f"lastText:{body}, waitH:{e['waitH']} }},"
        )
    lines.append("]")
    return "\n".join(lines)


def _patch_auto_spec(text: str) -> tuple[str, str]:
    """Returns (new_text, status_message). Raises ValueError if unpatchable."""
    start = text.find(AUTO_LITERAL_START)
    end = text.find(AUTO_LITERAL_END)
    if start == -1 or end == -1 or end <= start:
        # If the marker is already there but the END anchor isn't, it
        # means we've already replaced the IIFE block (so the anchor
        # naturally won't match). Treat that as up-to-date.
        if AUTO_SPEC_MARKER in text:
            return text, "AUTO already populated from spec"
        raise ValueError(
            "AUTO literal anchors not found. The design upload changed the "
            "surrounding code shape; re-derive AUTO_LITERAL_START / "
            "AUTO_LITERAL_END in tools/patch_standalone.py."
        )
    span_end = end + len(AUTO_LITERAL_END)
    block = text[start:span_end]
    if AUTO_SPEC_MARKER in block:
        return text, "AUTO already populated from spec"
    js_source = _build_auto_js()
    embedded = _embed_in_template(js_source)
    replacement = embedded + "\\n\\n// Stylized contact portraits"
    new_text = text[:start] + replacement + text[span_end:]
    return new_text, "patched: AUTO → spec (70 entries)"


# ---- Patch 5: Compact archive UI for replied threads ----
# 5a — replace the dashed AI-card with a small "already replied" pill.
# 5b — drop the left-hand "Mark unread" button (the right-hand
#       "Open in iMessage →" button stays).
# Together these strip extra chrome from threads we've already handled.

REPLIED_UI_MARKER = "REPLIED_UI (Reply or Die)"

# 5a — original archive AI-card branch (JS source, plain form). Embedding
# rewrites `</` → `</` and JSON-escapes everything to match the file.
_AICARD_5A_OLD_JS = (
    "${archive ? `\n"
    "        <div class=\"ai-card\" style=\"opacity:.55;border-style:dashed\">\n"
    "          <div class=\"ai-head\">\n"
    "            <span style=\"opacity:.7\">"
    "${isReplied?'✓ you handled this one'"
    ":isDismissed?'✕ you let this one go'"
    ":'∅ filtered automatically'}</span>\n"
    "          </div>\n"
    "          <div class=\"ai-body\" "
    "style=\"font-style:italic;color:var(--text-2)\">${\n"
    "            isReplied ? 'no draft needed — you already replied. nice.'\n"
    "            : isDismissed ? 'no reply expected. won\\'t affect your score.'\n"
    "            : 'no human attention required. you\\'re welcome.'\n"
    "          }</div>\n"
    "        </div>\n"
    "      `"
)

_AICARD_5A_NEW_JS = (
    "${archive ? (isReplied ? `\n"
    "        <!-- REPLIED_UI (Reply or Die): compact pill in place of the "
    "ai-card for replied threads -->\n"
    "        <div class=\"archive-pill\" "
    "style=\"opacity:.5;font-style:italic;color:var(--text-2);"
    "font-size:12px;text-align:center;padding:8px 0;letter-spacing:.04em\">"
    "already replied</div>\n"
    "      ` : `\n"
    "        <div class=\"ai-card\" style=\"opacity:.55;border-style:dashed\">\n"
    "          <div class=\"ai-head\">\n"
    "            <span style=\"opacity:.7\">"
    "${isDismissed?'✕ you let this one go':'∅ filtered automatically'}"
    "</span>\n"
    "          </div>\n"
    "          <div class=\"ai-body\" "
    "style=\"font-style:italic;color:var(--text-2)\">${\n"
    "            isDismissed ? 'no reply expected. won\\'t affect your score.'\n"
    "            : 'no human attention required. you\\'re welcome.'\n"
    "          }</div>\n"
    "        </div>\n"
    "      `)"
)

# 5b — the "Mark unread" button. Drop it entirely for isReplied; keep the
# original handler/text for the dismissed and auto cases.
_DISMISSBTN_5B_OLD_JS = (
    "<button class=\"dismiss-btn\" onclick=\"restoreThread()\">"
    "${isReplied?'Mark unread'"
    ":isDismissed?'Restore to inbox'"
    ":'Mark as not spam'}</button>"
)

_DISMISSBTN_5B_NEW_JS = (
    "${isReplied ? '' : `"
    "<button class=\"dismiss-btn\" onclick=\"restoreThread()\">"
    "${isDismissed?'Restore to inbox':'Mark as not spam'}</button>"
    "`}"
)


def _patch_replied_ui(text: str) -> tuple[str, str]:
    """Returns (new_text, status_message). Raises ValueError if unpatchable."""
    if REPLIED_UI_MARKER in text:
        return text, "replied-thread UI already compact"
    aicard_old = _embed_in_template(_AICARD_5A_OLD_JS)
    aicard_new = _embed_in_template(_AICARD_5A_NEW_JS)
    btn_old = _embed_in_template(_DISMISSBTN_5B_OLD_JS)
    btn_new = _embed_in_template(_DISMISSBTN_5B_NEW_JS)

    if text.count(aicard_old) != 1:
        raise ValueError(
            "archive AI-card block not found exactly once. The design upload "
            "changed its shape; re-derive _AICARD_5A_OLD_JS in "
            "tools/patch_standalone.py."
        )
    if text.count(btn_old) != 1:
        raise ValueError(
            "Mark-unread button not found exactly once. The design upload "
            "changed its shape; re-derive _DISMISSBTN_5B_OLD_JS in "
            "tools/patch_standalone.py."
        )
    text = text.replace(aicard_old, aicard_new, 1)
    text = text.replace(btn_old, btn_new, 1)
    return text, "patched: replied-thread UI compacted"


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


def main() -> int:
    if not TARGET.exists():
        print(f"error: {TARGET} not found", file=sys.stderr)
        return 2
    text = TARGET.read_text(encoding="utf-8")
    original_text = text

    for patcher in (
        _patch_regen_ai,
        _patch_cut_groups,
        _patch_replied_tv,
        _patch_auto_spec,
        _patch_replied_ui,
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
