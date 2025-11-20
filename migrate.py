import sqlite3

DB_PATH = "ticketapp.db"

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

# Check if the old table uses 'id' instead of 'ticket_id'
cur.execute("PRAGMA table_info(tickets)")
cols = [c[1] for c in cur.fetchall()]

if "id" in cols and "ticket_id" not in cols:
    print("🔧 Migrating old 'tickets' table to new schema...")

    # Rename old table
    cur.execute("ALTER TABLE tickets RENAME TO tickets_old")

    # Create new schema with ticket_id + foreign keys
    cur.execute("""
        CREATE TABLE tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            summary TEXT NOT NULL,
            prerequisites TEXT,
            steps_to_replicate TEXT,
            outcome TEXT,
            expected_outcome TEXT,
            status TEXT NOT NULL DEFAULT 'Open'
                CHECK(status IN ('Open','In Progress','Closed')),
            user_id INTEGER NULL,
            parent_id INTEGER NULL,
            created_by TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (parent_id) REFERENCES tickets(ticket_id) ON DELETE SET NULL
        )
    """)

    # Copy old data (filling subject from summary if needed)
    cur.execute("""
        INSERT INTO tickets (subject, summary, prerequisites, steps_to_replicate,
                             outcome, expected_outcome, status, user_id, parent_id, created_by, created_at)
        SELECT
            COALESCE(summary, 'Untitled') AS subject,
            summary, prerequisites, steps_to_replicate,
            outcome, expected_outcome, status, NULL, NULL, created_by, created_at
        FROM tickets_old
    """)

    # Drop the old table
    cur.execute("DROP TABLE tickets_old")
    con.commit()
    print("✅ Migration complete.")
else:
    print("✅ No migration needed — schema already up to date.")

con.close()