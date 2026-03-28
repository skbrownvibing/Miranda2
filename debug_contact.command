#!/bin/bash
# Miranda2 – Contact Message Debugger
# Usage: double-click, or run from Terminal.
# Prompts for a contact name and prints per-message blob diagnostics.

echo ""
echo "  Miranda2 – Contact Message Debugger"
echo "  ===================================="
echo ""

if ! command -v python3 &>/dev/null; then
  echo "  ERROR: Python 3 not found."
  echo ""
  read -rp "  Press Enter to close..." _
  exit 1
fi

python3 <<'PYTHON_EOF'
import sqlite3, os, re, sys, plistlib
from datetime import datetime, timezone, timedelta

APPLE_EPOCH  = datetime(2001, 1, 1, tzinfo=timezone.utc)
SEARCH_NAME  = "Claire Rafson"   # ← change this to test a different contact

def apple_ts(ts):
    if not ts:
        return None
    try:
        secs = ts / 1e9 if abs(ts) > 1e10 else float(ts)
        return APPLE_EPOCH + timedelta(seconds=secs)
    except Exception:
        return None

def norm_phone(p):
    d = re.sub(r'\D', '', p or '')
    if len(d) == 11 and d[0] == '1':
        d = d[1:]
    return d

# ── Contacts: find phone numbers for the target name ─────────────────────────

import glob

def find_contact_phones(name_fragment):
    """Return list of normalised phones for contacts matching name_fragment."""
    patterns = [
        "~/Library/Application Support/AddressBook/Sources/*/AddressBook-v22.abcddb",
        "~/Library/Application Support/AddressBook/AddressBook-v22.abcddb",
    ]
    db_path = None
    for pat in patterns:
        found = glob.glob(os.path.expanduser(pat))
        if found:
            db_path = found[0]
            break
    if not db_path:
        print("  WARNING: AddressBook not found — searching by name in chat handles only")
        return []

    results = []
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur  = conn.cursor()
        cur.execute("""
            SELECT r.ZFIRSTNAME, r.ZLASTNAME, p.ZFULLNUMBER
            FROM ZABCDRECORD r
            JOIN ZABCDPHONENUMBER p ON p.ZOWNER = r.ROWID
            WHERE p.ZFULLNUMBER IS NOT NULL
        """)
        for first, last, phone in cur.fetchall():
            full = " ".join(x for x in [first, last] if x)
            if name_fragment.lower() in full.lower():
                results.append((full, norm_phone(phone), phone))
        conn.close()
    except Exception as e:
        print(f"  WARNING: AddressBook error – {e}")
    return results

# ── attributedBody parsing — verbose version ─────────────────────────────────

def _uid_int(obj):
    if isinstance(obj, plistlib.UID):
        return obj.data
    if isinstance(obj, dict):
        return obj.get('CF$UID')
    return None

try:
    from Foundation import NSData, NSUnarchiver
    _PYOBJC_OK = True
except ImportError:
    _PYOBJC_OK = False

def parse_blob_verbose(blob):
    """Try to extract text; return (text_or_None, method, notes)."""
    if not blob:
        return None, 'none', 'blob is null'
    raw = bytes(blob)

    # ── streamtyped path ──────────────────────────────────────────────────────
    if raw.startswith(b'\x04\x0bstreamtyped'):
        if _PYOBJC_OK:
            try:
                from Foundation import NSData, NSUnarchiver
                ns_data = NSData.dataWithBytes_length_(raw, len(raw))
                obj = NSUnarchiver.unarchiveObjectWithData_(ns_data)
                if obj is not None:
                    s = str(obj.string()).strip() if hasattr(obj, 'string') else str(obj).strip()
                    if s:
                        return s, 'pyobjc', f'len={len(raw)}'
                    return None, 'pyobjc', f'obj present but empty string, type={type(obj)}'
            except Exception as e:
                pass  # fall through to byte scan

        # byte scan
        _meta = {
            'streamtyped', 'NSString', 'NSMutableString', 'NSAttributedString',
            'NSMutableAttributedString', 'NSObject', 'NSArray', 'NSMutableArray',
            'NSDictionary', 'NSMutableDictionary', 'NSColor', 'NSFont',
            'NSParagraphStyle', 'NSValue', 'NSNumber', 'NSData', 'NSShadow',
            'NSOriginalFont',
        }
        _cls_prefixes = ('NS', 'UI', 'CK', 'IM', '__', '$')
        candidates = []
        i = 0
        while i < len(raw):
            b = raw[i]
            if 0x20 <= b <= 0x7e or b >= 0xc2:
                j = i + 1
                while j < len(raw):
                    bj = raw[j]
                    if 0x20 <= bj <= 0x7e or 0x80 <= bj <= 0xbf or bj >= 0xc2:
                        j += 1
                    else:
                        break
                try:
                    s = raw[i:j].decode('utf-8').strip().lstrip('+')
                    if len(s) >= 4 and s not in _meta:
                        if ' ' in s or not any(s.startswith(p) for p in _cls_prefixes):
                            return s, 'streamtyped_scan', f'len={len(raw)}'
                        else:
                            candidates.append(s)
                except UnicodeDecodeError:
                    pass
                i = j
            else:
                i += 1
        return None, 'streamtyped_scan_fail', f'blob_len={len(raw)}, skipped_candidates={candidates[:5]}'

    # ── NSKeyedArchiver plist path ────────────────────────────────────────────
    try:
        plist   = plistlib.loads(raw)
        objects = plist.get('$objects', [])

        try:
            top_idx = _uid_int(plist.get('$top', {}).get('root'))
            if top_idx is not None:
                top_obj = objects[top_idx]
                if isinstance(top_obj, dict):
                    ns_idx = _uid_int(top_obj.get('NSString'))
                    if ns_idx is not None:
                        s = objects[ns_idx]
                        if isinstance(s, str) and s.strip():
                            return s.strip(), 'plist_structured', f'len={len(raw)}'
                        if isinstance(s, dict):
                            v = str(s.get('NS.string', '')).strip()
                            if v:
                                return v, 'plist_structured_nsstring', f'len={len(raw)}'
        except Exception as e:
            pass

        _meta_set = {
            '$null', 'NSString', 'NSMutableString', 'NSAttributedString',
            'NSMutableAttributedString', 'NSColor', 'NSFont', 'NSParagraphStyle',
            'NSValue', 'NSNumber', 'NSObject', 'NSData', 'NSArray',
            'NSMutableArray', 'NSDictionary', 'NSMutableDictionary',
            '__kIMMessagePartAttributeName', '__kIMDataDetectedAttributeName',
            '__kIMTapbackAttributeName', 'NSOriginalFont', 'NSShadow',
        }
        for obj in objects:
            if isinstance(obj, str):
                s = obj.strip()
                if s and s not in _meta_set and not s.startswith(('NS', 'UI', '__', '$')):
                    return s, 'plist_scan', f'len={len(raw)}'

        # both plist paths failed — show what objects look like
        top_val = plist.get('$top')
        return None, 'plist_no_text', (
            f'$top={top_val}  '
            f'first_8_objects={[type(o).__name__ + (":" + repr(o)[:40] if isinstance(o, str) else "") for o in objects[:8]]}'
        )

    except Exception as e:
        return None, 'plist_load_fail', f'error={e}  hex={raw[:24].hex()}'

# ── Main ─────────────────────────────────────────────────────────────────────

db_path = os.path.expanduser("~/Library/Messages/chat.db")
if not os.path.exists(db_path):
    print("  ERROR: iMessage database not found.")
    sys.exit(1)

try:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.execute("SELECT 1 FROM chat LIMIT 1")
except sqlite3.OperationalError as e:
    print(f"  ERROR: Cannot read iMessage database: {e}")
    sys.exit(1)

print(f"  Searching for contact: {SEARCH_NAME!r}")
matches = find_contact_phones(SEARCH_NAME)
if matches:
    for full, norm, raw_phone in matches:
        print(f"    Found: {full!r}  raw={raw_phone!r}  norm={norm!r}")
else:
    print("  (no AddressBook match — will search chat handles by name)")

print()

cur = conn.cursor()

# Find chats where this contact appears
cur.execute("""
    SELECT c.ROWID, c.guid, c.chat_identifier, c.display_name, c.style
    FROM chat c
    JOIN chat_handle_join chj ON chj.chat_id = c.ROWID
    JOIN handle h ON h.ROWID = chj.handle_id
    ORDER BY c.ROWID
""")
all_chats = cur.fetchall()

target_phones = {norm for _, norm, _ in matches}

matching_chats = []
for chat_id, guid, chat_identifier, display_name, style in all_chats:
    norm = norm_phone(chat_identifier or '')
    if norm in target_phones or (display_name and SEARCH_NAME.lower() in display_name.lower()):
        matching_chats.append((chat_id, guid, chat_identifier, display_name, style))

# deduplicate by chat_id
seen = set()
unique_chats = []
for row in matching_chats:
    if row[0] not in seen:
        seen.add(row[0])
        unique_chats.append(row)

if not unique_chats:
    print(f"  No chats found for {SEARCH_NAME!r}.")
    print("  Check the SEARCH_NAME value at the top of this script.")
    sys.exit(0)

for chat_id, guid, chat_identifier, display_name, style in unique_chats:
    print(f"  Chat: {chat_identifier!r}  display={display_name!r}  guid={guid}")
    print()

    cur.execute("""
        SELECT
            m.ROWID,
            m.text,
            m.is_from_me,
            m.date,
            m.attributedBody,
            m.associated_message_type,
            m.item_type,
            EXISTS(
                SELECT 1 FROM message_attachment_join maj
                JOIN attachment a ON a.ROWID = maj.attachment_id
                WHERE maj.message_id = m.ROWID
            ) AS has_attachment
        FROM message m
        JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
        WHERE cmj.chat_id = ?
        ORDER BY m.date DESC
        LIMIT 40
    """, (chat_id,))
    rows = cur.fetchall()

    print(f"  {'ROWID':<8} {'DIR':<5} {'ASSOC':<6} {'ITEM':<5} {'ATT':<4}  {'RESULT':<12}  DETAIL")
    print(f"  {'-'*8} {'-'*5} {'-'*6} {'-'*5} {'-'*4}  {'-'*12}  ------")

    for rowid, text, is_from_me, date, att_body, assoc_type, item_type, has_att in rows:
        direction = 'ME' if is_from_me else 'THEM'
        t = (text or '').strip()

        if t:
            result  = 'text'
            detail  = repr(t[:60])
            method  = '—'
        elif att_body:
            parsed, method, notes = parse_blob_verbose(att_body)
            if parsed:
                result = 'parsed'
                detail = repr(parsed[:60])
            else:
                result = '💬 FAIL'
                detail = notes
        elif has_att:
            result, method, detail = '📎 att', '—', ''
        elif assoc_type != 0:
            result, method, detail = 'tapback', '—', f'assoc={assoc_type}'
        elif item_type != 0:
            result, method, detail = 'sys_event', '—', f'item={item_type}'
        else:
            result, method, detail = 'empty', '—', ''

        ts = apple_ts(date)
        ts_str = ts.strftime('%m/%d %H:%M') if ts else '?'
        print(f"  {rowid:<8} {direction:<5} {assoc_type:<6} {item_type:<5} {has_att:<4}  {result:<12}  [{ts_str}] {method}  {detail}")

    print()

conn.close()
PYTHON_EOF

STATUS=$?
echo ""
read -rp "  Press Enter to close..." _
