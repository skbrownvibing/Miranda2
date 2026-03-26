#!/bin/bash
# Miranda2 – Message Inbox Exporter
# Double-click to run. Requires Full Disk Access for Terminal.

echo ""
echo "  Miranda2 – Message Inbox Export"
echo "  ================================"
echo ""

if ! command -v python3 &>/dev/null; then
  echo "  ERROR: Python 3 not found."
  echo "  Install it from python.org or via Homebrew."
  echo ""
  read -rp "  Press Enter to close..." _
  exit 1
fi

python3 <<'PYTHON_EOF'
import sqlite3, json, os, re, glob, sys
from datetime import datetime, timezone, timedelta

APPLE_EPOCH      = datetime(2001, 1, 1, tzinfo=timezone.utc)
LOOKBACK_DAYS    = 90
PERSONAL_DAYS    = 90
PERSONAL_THRESH  = 3   # messages exchanged in PERSONAL_DAYS to count as personal (fallback)

# ── Helpers ──────────────────────────────────────────────────────────────────

def apple_ts(ts):
    """Apple Core Data timestamp → datetime (handles both ns and s variants)."""
    if not ts:
        return None
    try:
        secs = ts / 1e9 if abs(ts) > 1e10 else float(ts)
        return APPLE_EPOCH + timedelta(seconds=secs)
    except Exception:
        return None

def fmt(dt):
    return dt.isoformat() if dt else None

def norm_phone(p):
    """Strip formatting; remove leading 1 from 11-digit US numbers."""
    d = re.sub(r'\D', '', p or '')
    if len(d) == 11 and d[0] == '1':
        d = d[1:]
    return d

# ── Contacts ──────────────────────────────────────────────────────────────────

def load_contacts():
    contacts = {}   # normalised phone/email → display name
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
        return contacts
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur  = conn.cursor()

        cur.execute("""
            SELECT r.ZFIRSTNAME, r.ZLASTNAME, r.ZORGANIZATION, p.ZFULLNUMBER
            FROM ZABCDRECORD r
            JOIN ZABCDPHONENUMBER p ON p.ZOWNER = r.ROWID
            WHERE p.ZFULLNUMBER IS NOT NULL
        """)
        for first, last, org, phone in cur.fetchall():
            name = " ".join(x for x in [first, last] if x) or org or ""
            if name:
                contacts[norm_phone(phone)] = name

        cur.execute("""
            SELECT r.ZFIRSTNAME, r.ZLASTNAME, r.ZORGANIZATION, e.ZADDRESS
            FROM ZABCDRECORD r
            JOIN ZABCDEMAILADDRESS e ON e.ZOWNER = r.ROWID
            WHERE e.ZADDRESS IS NOT NULL
        """)
        for first, last, org, email in cur.fetchall():
            name = " ".join(x for x in [first, last] if x) or org or ""
            if name and email:
                contacts[email.strip().lower()] = name

        conn.close()
    except Exception as e:
        print(f"  Warning: could not load contacts – {e}")
    return contacts

# ── Categorisation ────────────────────────────────────────────────────────────

DELIVERY_SENDERS = {
    'doordash', 'ubereats', 'grubhub', 'instacart', 'postmates', 'shipt',
    'amazon', 'fedex', 'ups', 'usps', 'dhl', 'ontrac', 'lasership',
    'uber', 'lyft', 'gopuff', 'getir', 'walmart', 'target',
}

DELIVERY_WORDS = [
    'your order', 'your delivery', 'your package', 'your shipment',
    'out for delivery', 'has been delivered', 'pick up your order',
    'ready for pickup', 'estimated delivery', 'tracking number',
    'doordash', 'ubereats', 'grubhub', 'instacart', 'fedex', 'ups', 'usps',
    'amazon.com', 'uber eats', 'postmates', 'shipt', 'dhl',
]

SPAM_WORDS = [
    'reply stop', 'text stop', 'opt-out', 'to unsubscribe',
    'verification code', 'verify your', 'one-time password', 'one time password',
    'do not share this code', 'do not share',
    'otp:', ' otp ', 'passcode', 'expires in', 'will expire',
    'you have won', 'claim your', 'free gift', "you've been selected",
    'click here', 'limited time offer', 'act now',
    'fraud alert', 'suspicious activity', 'unusual activity',
    'account suspended', 'account on hold', 'verify your account',
]

def categorize(handle, contact_name, in_contacts, messages, msg_count_lookback):
    digits = re.sub(r'\D', '', handle or '')

    # Short codes (5–6 digits) → spam
    if len(digits) in (5, 6):
        return 'spam'

    name_lower   = (contact_name or '').lower()
    handle_lower = (handle or '').lower()

    # Known delivery service sender names
    for svc in DELIVERY_SENDERS:
        if svc in name_lower or svc in handle_lower:
            return 'delivery'

    sample = ' '.join((m.get('text') or '') for m in messages[:15]).lower()

    for kw in DELIVERY_WORDS:
        if kw in sample:
            return 'delivery'

    for kw in SPAM_WORDS:
        if kw in sample:
            return 'spam'

    # Saved in contacts → personal (strongest signal for real people)
    if in_contacts:
        return 'personal'

    # Enough recent back-and-forth → personal
    if msg_count_lookback >= PERSONAL_THRESH:
        return 'personal'

    return 'uncategorized'

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    db_path = os.path.expanduser("~/Library/Messages/chat.db")

    if not os.path.exists(db_path):
        print("  ERROR: iMessage database not found.")
        print(f"  Expected: {db_path}")
        print("  Make sure iMessage is enabled on this Mac.")
        return False

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.execute("SELECT 1 FROM chat LIMIT 1")
    except sqlite3.OperationalError as e:
        print("  ERROR: Cannot read iMessage database.")
        print("")
        msg = str(e).lower()
        if "unable to open" in msg or "permission" in msg or "denied" in msg or "authorization" in msg:
            print("  Terminal needs Full Disk Access:")
            print("  1. Open System Settings")
            print("  2. Privacy & Security → Full Disk Access")
            print("  3. Enable Terminal (or your terminal app)")
            print("  4. Re-run this script")
        else:
            print(f"  Details: {e}")
        return False

    print("  Loading contacts…")
    contacts = load_contacts()
    print(f"  {len(contacts)} contacts found")
    print("  Reading messages…")

    cur = conn.cursor()
    now       = datetime.now(timezone.utc)
    cut_90d   = int(((now - timedelta(days=LOOKBACK_DAYS)) - APPLE_EPOCH).total_seconds() * 1e9)
    cut_30d   = int(((now - timedelta(days=PERSONAL_DAYS)) - APPLE_EPOCH).total_seconds() * 1e9)

    cur.execute("""
        SELECT c.ROWID, c.guid, c.chat_identifier, c.display_name, c.style
        FROM chat c
        ORDER BY c.ROWID
    """)
    chats = cur.fetchall()

    conversations = []

    for chat_id, guid, chat_identifier, display_name, style in chats:
        cur.execute("""
            SELECT h.id FROM handle h
            JOIN chat_handle_join chj ON h.ROWID = chj.handle_id
            WHERE chj.chat_id = ?
        """, (chat_id,))
        handles = [r[0] for r in cur.fetchall()]

        is_group     = bool(style == 43 or len(handles) > 1)
        primary      = handles[0] if handles else (chat_identifier or '')
        phone_norm   = norm_phone(primary)

        in_contacts  = bool(contacts.get(phone_norm) or contacts.get(primary.lower()))
        contact_name = (
            contacts.get(phone_norm) or
            contacts.get(primary.lower()) or
            (display_name if is_group else None)
        )

        # Messages in lookback window
        cur.execute("""
            SELECT m.text, m.is_from_me, m.date
            FROM message m
            JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
            WHERE cmj.chat_id = ? AND m.date > ? AND m.text IS NOT NULL
            ORDER BY m.date DESC
            LIMIT 100
        """, (chat_id, cut_90d))
        rows = cur.fetchall()

        # Fall back to most recent messages if nothing in window
        if not rows:
            cur.execute("""
                SELECT m.text, m.is_from_me, m.date
                FROM message m
                JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
                WHERE cmj.chat_id = ? AND m.text IS NOT NULL
                ORDER BY m.date DESC
                LIMIT 10
            """, (chat_id,))
            rows = cur.fetchall()

        if not rows:
            continue

        msg_list = [
            {'text': t, 'from_me': bool(fm), 'date': fmt(apple_ts(d))}
            for t, fm, d in rows
        ]

        msg_count_lookback = sum(1 for _, _, d in rows if d > cut_90d)
        last = msg_list[0]

        conversations.append({
            'id':                guid,
            'contact_name':      contact_name,
            'phone':             primary,
            'is_group':          is_group,
            'group_name':        display_name if is_group else None,
            'category':          categorize(primary, contact_name, in_contacts, msg_list, msg_count_lookback),
            'last_message_at':   last['date'],
            'last_message_text': last['text'],
            'i_replied_last':    last['from_me'],
            'message_count_30d': msg_count_lookback,
            'messages':          list(reversed(msg_list[:5])),   # chronological, last 5
        })

    conn.close()

    conversations.sort(key=lambda c: c.get('last_message_at') or '', reverse=True)

    # ── Stats ──
    cats = {}
    unreplied_personal = 0
    for c in conversations:
        cats[c['category']] = cats.get(c['category'], 0) + 1
        if c['category'] == 'personal' and not c['i_replied_last']:
            unreplied_personal += 1

    output = {
        'app':         'Miranda2',
        'version':     '1.0',
        'exported_at': now.isoformat(),
        'conversations': conversations,
    }

    out_path = os.path.join(os.path.expanduser("~/Desktop"), "miranda2_messages.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    p = cats.get('personal', 0)
    d = cats.get('delivery', 0)
    s = cats.get('spam', 0)
    u = cats.get('uncategorized', 0)

    print(f"")
    print(f"  Done!")
    print(f"")
    print(f"  Conversations exported: {len(conversations)}")
    print(f"    Personal:       {p}  ({unreplied_personal} unreplied)")
    print(f"    Delivery:       {d}")
    print(f"    Spam:           {s}")
    print(f"    Uncategorized:  {u}")
    print(f"")
    print(f"  File: {out_path}")
    print(f"")
    print(f"  Open index.html and drag the JSON file onto the page.")
    return True

ok = main()
sys.exit(0 if ok else 1)
PYTHON_EOF

STATUS=$?
echo ""
if [ $STATUS -eq 0 ]; then
  echo "  Export complete. You can close this window."
else
  echo "  Export failed. See errors above."
fi
echo ""
read -rp "  Press Enter to close..." _
