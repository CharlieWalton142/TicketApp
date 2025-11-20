import sqlite3

DB_PATH = "ticketapp.db"

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

# See current schema
cur.execute("PRAGMA table_info(tickets)")
cols = [c[1] for c in cur.fetchall()]
print("Current columns:", cols)

if "ticket_type" in cols:
    print("✅ ticket_type already exists, nothing to do.")
    con.close()
    raise SystemExit

print("⚙️  Migrating tickets table to add ticket_type...")

# 1) Create new table with ticket_type in schema
cur.execute("""
CREATE TABLE tickets_new (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_type TEXT NOT NULL DEFAULT 'Bug',
    subject TEXT NOT NULL,
    summary TEXT NOT NULL,
    prerequisites TEXT,
    steps_to_replicate TEXT,
    outcome TEXT,
    expected_outcome TEXT,
    status TEXT NOT NULL DEFAULT 'New',
    user_id INTEGER NULL,
    parent_id INTEGER NULL,
    created_by TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_id) REFERENCES tickets(ticket_id) ON DELETE SET NULL
)
""")

# 2) Copy data from old table into new one
#    Existing rows are treated as 'Bug' tickets by default.
cur.execute("""
INSERT INTO tickets_new (
    ticket_id,
    ticket_type,
    subject,
    summary,
    prerequisites,
    steps_to_replicate,
    outcome,
    expected_outcome,
    status,
    user_id,
    parent_id,
    created_by,
    created_at
)
SELECT
    ticket_id,
    'Bug' AS ticket_type,
    subject,
    summary,
    prerequisites,
    steps_to_replicate,
    outcome,
    expected_outcome,
    status,
    user_id,
    parent_id,
    created_by,
    created_at
FROM tickets
""")

# 3) Drop old table and rename new one
cur.execute("DROP TABLE tickets")
cur.execute("ALTER TABLE tickets_new RENAME TO tickets")
con.commit()
con.close()

print("✅ Migration complete. tickets table now has ticket_type.")