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


# ---- Patch 4: Replace fake "Scanning your inbox" with real exporter step ----
# The design ships Step 3 as a fake animated scan and a "See my score" CTA.
# The actual app needs the user to download export.command, run it (which
# writes ~/Desktop/miranda2_messages.json), and pick that file. This patch
# replaces the entire step-3 panel body with a download-and-run flow whose
# Continue button (id="scanContinue") is then wired by app.js to open the
# file picker via connectExportFile().

import json as _json

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
    encoded = _json.dumps(html)
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


def main() -> int:
    if not TARGET.exists():
        print(f"error: {TARGET} not found", file=sys.stderr)
        return 2
    text = TARGET.read_text(encoding="utf-8")
    original_text = text

    for patcher in (
        _patch_regen_ai,
        _patch_cut_groups,
        _patch_fda_terminal,
        _patch_scan_to_export,
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
