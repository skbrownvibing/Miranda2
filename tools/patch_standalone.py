#!/usr/bin/env python3
"""Re-apply the Reply or Die standalone patches after a fresh design upload.

The Inbox iframe loads docs/standalone.html. That file is exported from a
design tool and ships with hardcoded behavior that we patch:

1. regenAi() picks at random from a 3-element alts array. We patch it to
   call window.parent.miranda2RegenAi() instead.

2. The Dismiss button in the thread footer ships with no onclick. We add
   onclick="dismissThread()".

3. dismissThread() is injected. It bridges to the host
   (window.parent.miranda2DismissThread), tracks dismissed contacts in
   window.DISMISSED_CONTACTS, removes the contact from CONTACTS, and updates
   the in-iframe DOM (score widget, hanging count, waiting-on-you chip,
   Archive Dismissed chip) so the user can see the effect.

4. The Archive 'Dismissed' chip is given data-filter="dismissed" so the
   existing chip click handler routes through it. filteredContacts() is
   extended with a 'dismissed' branch that returns DISMISSED_CONTACTS.
   openContact() is extended to also resolve dismissed contacts so clicking
   one in the Dismissed view still opens its thread.

Whenever the standalone file is re-uploaded, run:

    python3 tools/patch_standalone.py

Idempotent: a no-op for parts already patched. Exits non-zero if a section
that should be patched can't be located (which means the design tool changed
the surrounding code shape and the patch needs to be revisited).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "docs" / "standalone.html"

# In the standalone source, what looks like a newline in JavaScript is the
# literal two-char sequence \n inside a JSON-encoded template tag. We compose
# patch strings the same way.
NL = "\\n"

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
# Patch 2: Dismiss button onclick.
# ---------------------------------------------------------------------------
DISMISS_BTN_ORIGINAL = '<button class=\\"dismiss-btn\\">Dismiss<\\u002Fbutton>'
DISMISS_BTN_PATCHED = (
    '<button class=\\"dismiss-btn\\" onclick=\\"dismissThread()\\">'
    'Dismiss<\\u002Fbutton>'
)

# ---------------------------------------------------------------------------
# Patch 3: inject dismissThread() and helper between copyAndOpenImessage
# and regenAi. Versioned via "PATCHED v2" marker so older v1 injections can
# be safely upgraded.
# ---------------------------------------------------------------------------
DISMISS_FN_ANCHOR_PRE = (
    "window.location.href = 'sms:' + phone;" + NL + "  }" + NL + "}" + NL + NL
)
DISMISS_FN_ANCHOR_POST = "function regenAi() {"

DISMISS_FN_INSERT = NL.join([
    "function dismissThread() {",
    "  // PATCHED v2 (Reply or Die): wires the design's Dismiss button to the host app,",
    "  // tracks dismissed contacts locally, and updates score + chip counts in the",
    "  // standalone iframe so dismissals visibly raise the score and populate the",
    "  // Archive > Dismissed bucket. Re-apply via tools/patch_standalone.py.",
    "  const sc = (typeof selectedContact !== 'undefined') ? selectedContact : null;",
    "  if (!sc) return;",
    "  try {",
    "    const fn = window.parent && window.parent.miranda2DismissThread;",
    "    if (typeof fn === 'function') fn(sc);",
    "  } catch (e) {}",
    "  let scoreBoost = 0;",
    "  try {",
    "    const allBefore = (typeof CONTACTS !== 'undefined' && Array.isArray(CONTACTS)) ? CONTACTS.slice() : [];",
    "    const dBefore = Array.isArray(window.DISMISSED_CONTACTS) ? window.DISMISSED_CONTACTS.slice() : [];",
    "    const allAfter = allBefore.filter(c => !c || c.id !== sc.id);",
    "    const dAfter = dBefore.concat([sc]);",
    "    scoreBoost = Math.max(0, _rodScoreFor(allAfter, dAfter) - _rodScoreFor(allBefore, dBefore));",
    "  } catch (e) {}",
    "  if (!Array.isArray(window.DISMISSED_CONTACTS)) window.DISMISSED_CONTACTS = [];",
    "  if (!window.DISMISSED_CONTACTS.some(c => c && c.id === sc.id)) window.DISMISSED_CONTACTS.push(sc);",
    "  if (typeof CONTACTS !== 'undefined' && Array.isArray(CONTACTS)) {",
    "    const idx = CONTACTS.findIndex(c => c && c.id === sc.id);",
    "    if (idx >= 0) CONTACTS.splice(idx, 1);",
    "  }",
    "  selectedContact = (typeof CONTACTS !== 'undefined' && CONTACTS.length) ? CONTACTS[0] : null;",
    "  try { renderMsgList(); } catch (e) {}",
    "  try { renderThread(); } catch (e) {}",
    "  try {",
    "    const sbrNum = document.querySelector('.sbr-num');",
    "    if (sbrNum && scoreBoost > 0) {",
    "      const cur = parseInt(sbrNum.textContent, 10) || 0;",
    "      sbrNum.textContent = String(Math.max(0, Math.min(100, cur + scoreBoost)));",
    "    }",
    "    const stats = document.querySelectorAll('.sb-stats .sb-stat .v');",
    "    if (stats[2]) {",
    "      const curH = parseInt(stats[2].textContent, 10) || 0;",
    "      stats[2].textContent = String(Math.max(0, curH - 1));",
    "    }",
    "    const ctAll = document.getElementById('ct-all');",
    "    if (ctAll) {",
    "      const cn = parseInt(ctAll.textContent, 10) || 0;",
    "      ctAll.textContent = String(Math.max(0, cn - 1));",
    "    }",
    "    document.querySelectorAll('.rail-chip').forEach(function(b) {",
    "      const label = b.querySelector('span:not(.ct)');",
    "      if (label && label.textContent.trim() === 'Dismissed') {",
    "        const cspan = b.querySelector('.ct');",
    "        if (cspan) {",
    "          const n = parseInt(cspan.textContent, 10) || 0;",
    "          cspan.textContent = String(n + 1);",
    "        }",
    "      }",
    "    });",
    "    const sub = document.getElementById('inbox-sub');",
    "    if (sub) sub.textContent = sub.textContent.replace(/^\\d+/, function(m) { return String(Math.max(0, parseInt(m, 10) - 1)); });",
    "  } catch (e) {}",
    "}",
    "",
    "function _rodScoreFor(active, dismissed) {",
    "  const total = active.length + dismissed.length;",
    "  if (!total) return 100;",
    "  const rate = Math.round((dismissed.length / total) * 100);",
    "  let avgWait = 0;",
    "  if (active.length) avgWait = active.reduce(function(s, c) { return s + (Number(c && c.waitH) || 0); }, 0) / active.length;",
    "  let speedScore = 100;",
    "  if (avgWait > 1) speedScore = Math.max(0, Math.round(100 - (avgWait / 72) * 100));",
    "  let hp = 0;",
    "  active.forEach(function(c) {",
    "    const h = Number(c && c.waitH) || 0;",
    "    if (h < 1) hp += 1; else if (h < 24) hp += 3; else if (h < 72) hp += 6; else hp += 10;",
    "  });",
    "  const hangingScore = Math.max(0, 100 - hp);",
    "  return Math.max(0, Math.min(100, Math.round(rate * 0.45 + speedScore * 0.25 + hangingScore * 0.30)));",
    "}",
])

# Pattern that matches any prior version of dismissThread + helper that sits
# between the copyAndOpen close and regenAi. Uses .*? non-greedy across the
# block so v1 (without _rodScoreFor) and any future variant get cleanly
# replaced.
_DISMISS_FN_RANGE_RE = re.compile(
    re.escape(DISMISS_FN_ANCHOR_PRE)
    + r"function dismissThread\(\) \{.*?\}"
    + r"(?:" + re.escape(NL + NL) + r"function _rodScoreFor\(.*?\}" + r")?"
    + re.escape(NL + NL + DISMISS_FN_ANCHOR_POST),
    re.DOTALL,
)

V2_MARKER = "PATCHED v2 (Reply or Die)"

# ---------------------------------------------------------------------------
# Patch 4: Archive Dismissed chip data-filter; filteredContacts branch;
# openContact dismissed lookup.
# ---------------------------------------------------------------------------
CHIP_OLD = '<button class=\\"rail-chip\\"><span>Dismissed<\\u002Fspan>'
CHIP_NEW = '<button class=\\"rail-chip\\" data-filter=\\"dismissed\\"><span>Dismissed<\\u002Fspan>'

FILTERED_OLD = NL.join([
    "function filteredContacts() {",
    "  if (currentFilter === 'urgent') return CONTACTS.filter(c => c.waitH >= 72);",
    "  if (currentFilter === 'today') return CONTACTS.filter(c => c.waitH < 24);",
    "  if (currentFilter === 'group') return [];",
    "  return CONTACTS;",
    "}",
])
FILTERED_NEW = NL.join([
    "function filteredContacts() {",
    "  if (currentFilter === 'urgent') return CONTACTS.filter(c => c.waitH >= 72);",
    "  if (currentFilter === 'today') return CONTACTS.filter(c => c.waitH < 24);",
    "  if (currentFilter === 'group') return [];",
    "  if (currentFilter === 'dismissed') return Array.isArray(window.DISMISSED_CONTACTS) ? window.DISMISSED_CONTACTS : [];",
    "  return CONTACTS;",
    "}",
])

OPEN_OLD = NL.join([
    "function openContact(id) {",
    "  selectedContact = CONTACTS.find(c => c.id === id);",
    "  renderMsgList();",
    "  renderThread();",
    "}",
])
OPEN_NEW = NL.join([
    "function openContact(id) {",
    "  selectedContact = CONTACTS.find(c => c.id === id);",
    "  if (!selectedContact && Array.isArray(window.DISMISSED_CONTACTS)) {",
    "    selectedContact = window.DISMISSED_CONTACTS.find(c => c.id === id);",
    "  }",
    "  renderMsgList();",
    "  renderThread();",
    "}",
])


def _apply_simple(text: str, name: str, old: str, new: str, *, allow_missing_original: bool = False) -> tuple[str, str]:
    if new in text:
        return text, "noop"
    n = text.count(old)
    if n == 0:
        if allow_missing_original:
            return text, "noop"
        return text, f"error: '{name}' original not found"
    if n > 1:
        return text, f"error: '{name}' original found {n} times; expected 1"
    return text.replace(old, new, 1), "patched"


def patch_regenai(text: str) -> tuple[str, str]:
    if REGEN_PATCHED in text and not any(m in text for m in CANNED_MARKERS):
        return text, "noop"
    matches = text.count(REGEN_ORIGINAL)
    if matches == 0:
        canned = [m for m in CANNED_MARKERS if m in text]
        if canned:
            return text, (
                "error: canned alts present but original regenAi() block not found. "
                f"Canned strings: {canned}"
            )
        return text, "error: nothing to patch (no original regenAi(), no canned alts)"
    if matches > 1:
        return text, f"error: original regenAi() found {matches} times; expected 1"
    return text.replace(REGEN_ORIGINAL, REGEN_PATCHED, 1), "patched"


def patch_dismiss(text: str) -> tuple[str, str]:
    """Patches the dismiss button + injects/upgrades the dismissThread block."""
    statuses = []

    text, s = _apply_simple(text, "dismiss-btn onclick", DISMISS_BTN_ORIGINAL, DISMISS_BTN_PATCHED)
    if s.startswith("error"):
        return text, s
    statuses.append(("btn", s))

    # If v2 marker already present, leave the block alone.
    if V2_MARKER in text:
        statuses.append(("fn", "noop"))
    else:
        m = _DISMISS_FN_RANGE_RE.search(text)
        if m:
            text = (
                text[: m.start()]
                + DISMISS_FN_ANCHOR_PRE
                + DISMISS_FN_INSERT
                + NL + NL + DISMISS_FN_ANCHOR_POST
                + text[m.end():]
            )
            statuses.append(("fn", "upgraded"))
        else:
            anchor = DISMISS_FN_ANCHOR_PRE + DISMISS_FN_ANCHOR_POST
            n = text.count(anchor)
            if n == 0:
                return text, "error: dismissThread injection anchor not found"
            if n > 1:
                return text, f"error: dismissThread anchor found {n} times; expected 1"
            text = text.replace(
                anchor,
                DISMISS_FN_ANCHOR_PRE + DISMISS_FN_INSERT + NL + NL + DISMISS_FN_ANCHOR_POST,
                1,
            )
            statuses.append(("fn", "patched"))

    text, s = _apply_simple(text, "Dismissed chip data-filter", CHIP_OLD, CHIP_NEW)
    if s.startswith("error"):
        return text, s
    statuses.append(("chip", s))

    text, s = _apply_simple(text, "filteredContacts dismissed branch", FILTERED_OLD, FILTERED_NEW)
    if s.startswith("error"):
        return text, s
    statuses.append(("filter", s))

    text, s = _apply_simple(text, "openContact dismissed lookup", OPEN_OLD, OPEN_NEW)
    if s.startswith("error"):
        return text, s
    statuses.append(("open", s))

    summary = ", ".join(f"{k}={v}" for k, v in statuses)
    return text, summary


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
