#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
TMP_DIR="$(mktemp -d)"
DB_PATH="$TMP_DIR/chat_fixture.db"
OUT_PATH="$TMP_DIR/replyordie_messages.json"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

python3 - "$DB_PATH" <<'PY'
import sqlite3
import sys
from datetime import datetime, timezone

db_path = sys.argv[1]
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.executescript('''
CREATE TABLE chat (
  ROWID INTEGER PRIMARY KEY,
  guid TEXT,
  chat_identifier TEXT,
  display_name TEXT,
  style INTEGER
);
CREATE TABLE handle (
  ROWID INTEGER PRIMARY KEY,
  id TEXT
);
CREATE TABLE chat_handle_join (
  chat_id INTEGER,
  handle_id INTEGER
);
CREATE TABLE message (
  ROWID INTEGER PRIMARY KEY,
  text TEXT,
  is_from_me INTEGER,
  date INTEGER,
  attributedBody BLOB,
  associated_message_type INTEGER,
  item_type INTEGER
);
CREATE TABLE chat_message_join (
  chat_id INTEGER,
  message_id INTEGER
);
CREATE TABLE attachment (
  ROWID INTEGER PRIMARY KEY
);
CREATE TABLE message_attachment_join (
  message_id INTEGER,
  attachment_id INTEGER
);
''')

apple_epoch = datetime(2001, 1, 1, tzinfo=timezone.utc)
now = datetime.now(timezone.utc)
ns = int((now - apple_epoch).total_seconds() * 1e9)

cur.execute("INSERT INTO chat (ROWID, guid, chat_identifier, display_name, style) VALUES (1, 'chat-guid-1', '+12125550111', NULL, 0)")
cur.execute("INSERT INTO handle (ROWID, id) VALUES (1, '+12125550111')")
cur.execute("INSERT INTO chat_handle_join (chat_id, handle_id) VALUES (1, 1)")
cur.execute("INSERT INTO message (ROWID, text, is_from_me, date, attributedBody, associated_message_type, item_type) VALUES (1, 'hey are we still on for tonight?', 0, ?, NULL, 0, 0)", (ns,))
cur.execute("INSERT INTO chat_message_join (chat_id, message_id) VALUES (1, 1)")

conn.commit()
conn.close()
PY

REPLYORDIE_CHAT_DB_PATH="$DB_PATH" REPLYORDIE_OUTPUT_PATH="$OUT_PATH" bash "$ROOT_DIR/export.command" >/dev/null

python3 - "$OUT_PATH" <<'PY'
import json
import sys

path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as f:
    payload = json.load(f)

assert payload.get('app') == 'Reply or Die', 'Missing app key'
assert isinstance(payload.get('conversations'), list), 'conversations must be a list'
assert payload['conversations'], 'expected at least one conversation in fixture export'
print('ok')
PY
