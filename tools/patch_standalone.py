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
  4. FDA step framing — the design ships a Step 2 that asks the user to
     toggle "Reply or Die" in Full Disk Access and claims the app will
     auto-detect. The real flow needs Terminal (the app the export.command
     runs in) to have FDA, and there is no auto-detection — the user must
     confirm. Patch rewrites the instruction copy, the highlighted mock
     row, and the Continue button label.
  5. Step-3 exporter flow — the design ships a fake animated "Scanning
     your inbox" step. We replace it with real instructions to download
     export.command, run it (with macOS Gatekeeper bypass), and pick the
     resulting JSON; the existing scanContinue button is wired to the
     file picker by app.js.
  6. Archive AUTO-FILTERED list — the design tool ships a generic
     templates dict + rotation IIFE. Replace with the 70 entries spelled
     out in docs/dummy-data-spec.md §4 (delivery / spam-with-fake-pols /
     2FA), each with explicit waitH.
  7. Compact archive UI for replied threads — the design tool renders a
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

# ---- Patch 4: Repopulate DISMISSED from JSON ----
# The design tool ships two fake dismissed entries (Garrett / unknown-415).
# Replace them with the real D1–D6 set from data/miranda_demo.json (entries
# flagged dismissed:true). Mirrors the REPLIED patch.

DISMISSED_REAL_MARKER = "DISMISSED_REAL (Reply or Die)"

DISMISSED_LITERAL_START = "const DISMISSED = [\\n"
DISMISSED_LITERAL_END = "\\n];\\n\\n// ───── AUTO-FILTERED"


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
    return _prefixed_when_label(then, now, "Replied")


def _prefixed_when_label(then: datetime, now: datetime, prefix: str) -> str:
    delta = now - then
    secs = max(0, int(delta.total_seconds()))
    mins = secs // 60
    hours = mins // 60
    days = hours // 24
    if days == 1:
        return f"{prefix} yesterday"
    if days >= 2:
        return f"{prefix} {days}d ago"
    if hours >= 1:
        return f"{prefix} {hours}h ago"
    if mins >= 1:
        return f"{prefix} {mins}m ago"
    return f"{prefix} just now"


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


def _build_dismissed_js() -> str:
    """Render the DISMISSED literal as JS source.

    Source is data/miranda_demo.json filtered to non-group conversations with
    dismissed:true. `now` is the file's exported_at — fixed snapshot, not
    wall-clock — so the 'Dismissed Xd ago' label is stable across runs.
    """
    payload = json.loads(DEMO_DATA.read_text(encoding="utf-8"))
    now = datetime.fromisoformat(payload["exported_at"])
    convos = [
        c for c in payload["conversations"]
        if c.get("dismissed") and not c.get("is_group")
    ]
    convos.sort(key=lambda c: c["last_message_at"], reverse=True)

    lines: list[str] = ["const DISMISSED = ["]
    lines.append(
        "  /* DISMISSED_REAL (Reply or Die): generated from "
        "data/miranda_demo.json (dismissed:true) — re-run "
        "tools/patch_standalone.py after design uploads. */"
    )
    for i, c in enumerate(convos, start=1):
        last_at = datetime.fromisoformat(c["last_message_at"])
        when = _prefixed_when_label(last_at, now, "Dismissed")
        name = _js_str(c["contact_name"])
        phone = _js_str(c["phone"])
        last_text = _js_str(c["last_message_text"])
        lines.append(f"  {{ id:'d{i}', name:{name}, phone:{phone},")
        lines.append(f"    lastText:{last_text},")
        lines.append(f"    whenLabel:'{when}',")
        lines.append("    reason:'You marked: let it go',")
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


def _patch_dismissed_real(text: str) -> tuple[str, str]:
    """Returns (new_text, status_message). Raises ValueError if unpatchable.

    Idempotency is by content equality, not marker presence — so flipping
    `dismissed:true/false` flags in miranda_demo.json triggers a re-emit even
    though the marker is already in place from a previous run.
    """
    start = text.find(DISMISSED_LITERAL_START)
    end = text.find(DISMISSED_LITERAL_END)
    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            "DISMISSED literal anchors not found. The design upload changed the "
            "surrounding code shape; re-derive DISMISSED_LITERAL_START / "
            "DISMISSED_LITERAL_END in tools/patch_standalone.py."
        )
    span_end = end + len(DISMISSED_LITERAL_END)
    js_source = _build_dismissed_js()
    embedded = _embed_in_template(js_source)
    replacement = embedded + "\\n\\n// ───── AUTO-FILTERED"
    new_text = text[:start] + replacement + text[span_end:]
    if new_text == text:
        return text, "DISMISSED already matches JSON"
    return new_text, "patched: DISMISSED → real entries from JSON"


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


# ---- Patch 4: Reframe FDA step around Terminal ----
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


# ---- Patch 5: Replace fake "Scanning your inbox" with real exporter step ----
# The design ships Step 3 as a fake animated scan and a "See my score" CTA.
# The actual app needs the user to download export.command, run it (which
# writes ~/Desktop/miranda2_messages.json), and pick that file. This patch
# replaces the entire step-3 panel body with a download-and-run flow whose
# Continue button (id="scanContinue") is then wired by app.js to open the
# file picker via connectExportFile().

SCAN_PANEL_DONE_MARKER = "Apple could not verify"

SCAN_PANEL_START_ANCHOR = (
    '<section class=\\"step-panel\\" data-panel=\\"3\\">'
)
# Try both forms of the closing tag — the design ships `/`, but
# json.dumps in this script writes a literal `/`, so the file may end
# up with either after a previous patch run.
SCAN_PANEL_END_ANCHORS = (
    '<\\u002Fsection>\\n\\n      <!-- STEP 4: DONE / FIRST SCORE -->',
    '<\\/section>\\n\\n      <!-- STEP 4: DONE / FIRST SCORE -->',
    '</section>\\n\\n      <!-- STEP 4: DONE / FIRST SCORE -->',
)


def _build_scan_panel_body() -> str:
    """Returns the JSON-encoded inner HTML for the new step-3 panel.

    The standalone HTML body lives inside a JSON-string bundler template,
    so we author the panel as plain HTML and then encode it the same way
    the surrounding template is encoded (json.dumps without the wrapping
    quotes).
    """
    html = (
        '<section class="step-panel" data-panel="3">\n'
        '        <div class="panel-head">\n'
        '          <div class="panel-num">Step 3 of 4</div>\n'
        '          <h2>Run the exporter.</h2>\n'
        '          <p class="panel-sub">Download the exporter, double-click it in Finder, then come back when it\'s done.</p>\n'
        '        </div>\n'
        '\n'
        '        <div class="fda-wrap">\n'
        '          <ol class="fda-steps">\n'
        '            <li>\n'
        '              <span class="fda-num">1</span>\n'
        '              <div>\n'
        '                <div class="fda-head">Download the exporter</div>\n'
        '                <div class="fda-sub">A small shell script that runs locally on your Mac.</div>\n'
        '                <a class="btn btn-primary" href="/export.command" download="export.command" style="margin-top:10px;display:inline-flex"><span>Download export.command</span><span class="arrow">↓</span></a>\n'
        '              </div>\n'
        '            </li>\n'
        '            <li>\n'
        '              <span class="fda-num">2</span>\n'
        '              <div>\n'
        '                <div class="fda-head">Double-click it in Finder</div>\n'
        '                <div class="fda-sub">Terminal opens and reads your Messages database. Takes a few seconds.</div>\n'
        '                <div class="fda-sub" style="margin-top:8px"><strong>If macOS blocks it</strong> with <em>"Apple could not verify export.command is free of malware"</em>:</div>\n'
        '                <ol style="margin:6px 0 0 22px;padding:0;font:13px/1.5 -apple-system,BlinkMacSystemFont,sans-serif;color:var(--ink-soft,#666)">\n'
        '                  <li>Click <strong>Done</strong> on the alert.</li>\n'
        '                  <li>Open <strong>System Settings → Privacy &amp; Security</strong>.</li>\n'
        '                  <li>Scroll to the bottom and click <strong>Open Anyway</strong> next to <em>export.command</em>.</li>\n'
        '                  <li>Click <strong>Open</strong> in the confirmation. Terminal will run it.</li>\n'
        '                </ol>\n'
        '              </div>\n'
        '            </li>\n'
        '            <li>\n'
        '              <span class="fda-num">3</span>\n'
        '              <div>\n'
        '                <div class="fda-head">Come back when it\'s done</div>\n'
        '                <div class="fda-sub">It writes <span class="chip">~/Desktop/replyordie_messages.json</span>. Click below and pick that file.</div>\n'
        '              </div>\n'
        '            </li>\n'
        '          </ol>\n'
        '        </div>\n'
        '\n'
        '        <div class="panel-actions">\n'
        '          <button class="btn btn-ghost" onclick="setupGo(2)"><span class="arrow">←</span><span>Back</span></button>\n'
        '          <button class="btn btn-primary" id="scanContinue" onclick="setupGo(4)"><span>I’ve run the exporter</span><span class="arrow">→</span></button>\n'
        '        </div>\n'
        '      </section>'
    )
    encoded = json.dumps(html)
    # Strip the surrounding double quotes that json.dumps adds.
    return encoded[1:-1]


def _patch_scan_to_export(text: str) -> tuple[str, str]:
    """Returns (new_text, status_message). Raises ValueError if unpatchable."""
    if SCAN_PANEL_DONE_MARKER in text:
        return text, "scan-to-export already patched"
    start = text.find(SCAN_PANEL_START_ANCHOR)
    if start == -1:
        raise ValueError("scan-to-export: step-3 section anchor not found")
    end = -1
    end_len = 0
    for anchor in SCAN_PANEL_END_ANCHORS:
        # Pull just the closing-tag portion before `\n\n      <!-- STEP 4:`.
        idx = text.find(anchor, start)
        if idx != -1:
            end = idx
            end_len = anchor.index('\\n')  # length of just the </section> part
            break
    if end == -1:
        raise ValueError("scan-to-export: end-of-step-3 anchor not found")
    # Replace from `<section data-panel="3">` through `</section>` (inclusive).
    section_end = end + end_len
    replacement = _build_scan_panel_body()
    new_text = text[:start] + replacement + text[section_end:]
    return new_text, "patched scan step into download-the-exporter"


# ---- Patch 6: Repopulate AUTO-FILTERED from docs/dummy-data-spec.md §4 ----
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
    sec4 = re.search(r"^## 4\.\s+Auto-filtered.*$", text, flags=re.MULTILINE)
    if not sec4:
        raise ValueError("Section '## 4. Auto-filtered' not found in data spec.")
    body = text[sec4.end():]
    next_h2 = re.search(r"^## ", body, flags=re.MULTILINE)
    if next_h2:
        body = body[:next_h2.start()]

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


# ---- Patch 7: Compact archive UI for replied threads ----
# 7a — replace the dashed AI-card with a small "already replied" pill.
# 7b — drop the left-hand "Mark unread" button (the right-hand
#       "Open in iMessage →" button stays).

REPLIED_UI_MARKER = "REPLIED_UI (Reply or Die)"

_AICARD_7A_OLD_JS = (
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

_AICARD_7A_NEW_JS = (
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

_DISMISSBTN_7B_OLD_JS = (
    "<button class=\"dismiss-btn\" onclick=\"restoreThread()\">"
    "${isReplied?'Mark unread'"
    ":isDismissed?'Restore to inbox'"
    ":'Mark as not spam'}</button>"
)

_DISMISSBTN_7B_NEW_JS = (
    "${isReplied ? '' : `"
    "<button class=\"dismiss-btn\" onclick=\"restoreThread()\">"
    "${isDismissed?'Restore to inbox':'Mark as not spam'}</button>"
    "`}"
)


def _patch_replied_ui(text: str) -> tuple[str, str]:
    """Returns (new_text, status_message). Raises ValueError if unpatchable."""
    if REPLIED_UI_MARKER in text:
        return text, "replied-thread UI already compact"
    aicard_old = _embed_in_template(_AICARD_7A_OLD_JS)
    aicard_new = _embed_in_template(_AICARD_7A_NEW_JS)
    btn_old = _embed_in_template(_DISMISSBTN_7B_OLD_JS)
    btn_new = _embed_in_template(_DISMISSBTN_7B_NEW_JS)

    if text.count(aicard_old) != 1:
        raise ValueError(
            "archive AI-card block not found exactly once. The design upload "
            "changed its shape; re-derive _AICARD_7A_OLD_JS in "
            "tools/patch_standalone.py."
        )
    if text.count(btn_old) != 1:
        raise ValueError(
            "Mark-unread button not found exactly once. The design upload "
            "changed its shape; re-derive _DISMISSBTN_7B_OLD_JS in "
            "tools/patch_standalone.py."
        )
    text = text.replace(aicard_old, aicard_new, 1)
    text = text.replace(btn_old, btn_new, 1)
    return text, "patched: replied-thread UI compacted"


# ---- Patch 8: Readable Step-2 troubleshooting list ----
# Two issues with the design tool's "If macOS blocks it" sub-list:
#   8a — `.fda-steps li { display: grid; ... }` is a descendant selector,
#        so it also applies to the nested <li>s in the troubleshooting
#        <ol>. Each text node and <strong>/<em> becomes its own grid
#        cell, so words like "Click" wrap inside a 36px column. Scope
#        the rule to direct children only and add normal flow for the
#        nested list.
#   8b — the inline font on that <ol> is `13px/1.5`, which is too small
#        and too cramped. Bump to `15px/1.6` for readability.

READABLE_TROUBLESHOOT_MARKER = ".fda-steps > li {"

_READABLE_OLD_CSS = (
    ".fda-steps li {\n"
    "    display: grid;\n"
    "    grid-template-columns: 36px 1fr;\n"
    "    gap: 14px;\n"
    "    align-items: start;\n"
    "  }"
)

_READABLE_NEW_CSS = (
    ".fda-steps > li {\n"
    "    display: grid;\n"
    "    grid-template-columns: 36px 1fr;\n"
    "    gap: 14px;\n"
    "    align-items: start;\n"
    "  }\n"
    "  .fda-steps ol {\n"
    "    margin: 8px 0 0 22px;\n"
    "    padding: 0;\n"
    "    font: 15px/1.6 -apple-system,BlinkMacSystemFont,sans-serif;\n"
    "    color: var(--ink-soft,#666);\n"
    "  }\n"
    "  .fda-steps ol li {\n"
    "    display: list-item;\n"
    "    margin-bottom: 6px;\n"
    "  }"
)

_READABLE_OLD_INLINE = (
    "<ol style=\"margin:6px 0 0 22px;padding:0;"
    "font:13px/1.5 -apple-system,BlinkMacSystemFont,sans-serif;"
    "color:var(--ink-soft,#666)\">"
)

_READABLE_NEW_INLINE = (
    "<ol style=\"margin:8px 0 0 22px;padding:0;"
    "font:15px/1.6 -apple-system,BlinkMacSystemFont,sans-serif;"
    "color:var(--ink-soft,#666)\">"
)


def _patch_readable_troubleshoot(text: str) -> tuple[str, str]:
    """Returns (new_text, status_message). Raises ValueError if unpatchable."""
    if READABLE_TROUBLESHOOT_MARKER in text:
        return text, "Step-2 troubleshooting list already readable"
    css_old = _embed_in_template(_READABLE_OLD_CSS)
    css_new = _embed_in_template(_READABLE_NEW_CSS)
    inline_old = _embed_in_template(_READABLE_OLD_INLINE)
    inline_new = _embed_in_template(_READABLE_NEW_INLINE)

    if text.count(css_old) != 1:
        raise ValueError(
            ".fda-steps li grid rule not found exactly once. The design "
            "upload changed its shape; re-derive _READABLE_OLD_CSS in "
            "tools/patch_standalone.py."
        )
    if text.count(inline_old) != 1:
        raise ValueError(
            "Step-2 troubleshooting <ol> inline style not found exactly "
            "once. The design upload changed its shape; re-derive "
            "_READABLE_OLD_INLINE in tools/patch_standalone.py."
        )
    text = text.replace(css_old, css_new, 1)
    text = text.replace(inline_old, inline_new, 1)
    return text, "patched: Step-2 troubleshooting list readable"


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
        _patch_dismissed_real,
        _patch_fda_terminal,
        _patch_scan_to_export,
        _patch_auto_spec,
        _patch_replied_ui,
        _patch_readable_troubleshoot,
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
