import sqlite3
import bcrypt
import datetime
from contextlib import closing

# =========================================================
# CONFIGURATION
# =========================================================
DB_PATH = "ticketapp.db"


def _connect():
    """Connect to the SQLite database with FK support enabled."""
    con = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


# =========================================================
# USER MANAGEMENT
# =========================================================
def init_user_db():
    """Create the users table if it doesn't exist."""
    with _connect() as con, closing(con.cursor()) as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash BLOB NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'admin')),
                created_at TEXT NOT NULL
            )
        """
        )
        con.commit()


def create_user(username: str, password: str, role: str = "user") -> bool:
    """Create a new user with a hashed password. Returns True on success, False if username exists."""
    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    with _connect() as con, closing(con.cursor()) as cur:
        try:
            cur.execute(
                """
                INSERT INTO users (username, password_hash, role, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (username, pw_hash, role, datetime.datetime().isoformat()),
            )
            con.commit()
            print(f"✅ Created user: {username} ({role})")
            return True
        except sqlite3.IntegrityError:
            print(f"⚠️ Username '{username}' already exists.")
            return False


def authenticate_user(username: str, password: str):
    """Return user record if credentials are valid, else None."""
    with _connect() as con, closing(con.cursor()) as cur:
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        if user and bcrypt.checkpw(password.encode("utf-8"), user["password_hash"]):
            return user
        return None


def list_users():
    """Return a list of all users (id + username)."""
    with _connect() as con, closing(con.cursor()) as cur:
        cur.execute("SELECT id, username FROM users ORDER BY username ASC")
        return cur.fetchall()


# =========================================================
# TICKET MANAGEMENT
# =========================================================
def init_ticket_db():
    """Create the tickets table (if it doesn't exist)."""
    with _connect() as con, closing(con.cursor()) as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
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
        """
        )
        con.commit()


def create_ticket(
    ticket_type: str,
    subject: str,
    summary: str,
    prerequisites: str,
    steps_to_replicate: str,
    outcome: str,
    expected_outcome: str,
    created_by: str,
    user_id: int | None = None,
    parent_id: int | None = None,
    status: str = "New",
) -> int:
    """
    Insert a new ticket and return its ID.

    ticket_type examples: 'Bug', 'Test Case', 'Change Request', ...
    """
    with _connect() as con, closing(con.cursor()) as cur:
        cur.execute(
            """
            INSERT INTO tickets
            (ticket_type, subject, summary, prerequisites, steps_to_replicate,
             outcome, expected_outcome, created_by, user_id, parent_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                ticket_type,
                subject,
                summary,
                prerequisites,
                steps_to_replicate,
                outcome,
                expected_outcome,
                created_by,
                user_id,
                parent_id,
                status,
            ),
        )
        con.commit()
        return cur.lastrowid


def list_tickets(statuses=None, search: str = ""):
    """
    Return ticket rows, optionally filtered by statuses and search term.

    Each row has: ticket_id, ticket_type, subject, summary, status,
    created_by, created_at, assigned_to.
    """
    q = """
        SELECT t.ticket_id,
               t.ticket_type,
               t.subject,
               t.summary,
               t.status,
               t.created_by,
               t.created_at,
               COALESCE(u.username, '') AS assigned_to
        FROM tickets t
        LEFT JOIN users u ON t.user_id = u.id
        WHERE 1=1
    """
    params: list = []

    if statuses:
        q += f" AND t.status IN ({','.join('?' * len(statuses))})"
        params += list(statuses)

    if search:
        s = f"%{search}%"
        q += """
        AND (
            t.subject LIKE ? OR
            t.summary LIKE ? OR
            t.expected_outcome LIKE ?
        )
        """
        params += [s, s, s]

    q += " ORDER BY t.created_at DESC"

    with _connect() as con, closing(con.cursor()) as cur:
        cur.execute(q, params)
        return cur.fetchall()


def get_ticket(ticket_id: int):
    """Return full ticket details by ID."""
    with _connect() as con, closing(con.cursor()) as cur:
        cur.execute(
            """
            SELECT t.*, u.username AS assigned_to
            FROM tickets t
            LEFT JOIN users u ON t.user_id = u.id
            WHERE ticket_id = ?
        """,
            (ticket_id,),
        )
        return cur.fetchone()


def update_ticket_status(ticket_id: int, new_status: str):
    """Update only the status of a given ticket."""
    with _connect() as con, closing(con.cursor()) as cur:
        cur.execute(
            "UPDATE tickets SET status = ? WHERE ticket_id = ?",
            (new_status, ticket_id),
        )
        con.commit()


def update_ticket(
    ticket_id: int,
    ticket_type: str,
    subject: str,
    summary: str,
    prerequisites: str,
    steps_to_replicate: str,
    outcome: str,
    expected_outcome: str,
    status: str,
    user_id: int | None,
    parent_id: int | None,
):
    """Update all editable fields of a ticket."""
    with _connect() as con, closing(con.cursor()) as cur:
        cur.execute(
            """
            UPDATE tickets
            SET ticket_type = ?,
                subject = ?,
                summary = ?,
                prerequisites = ?,
                steps_to_replicate = ?,
                outcome = ?,
                expected_outcome = ?,
                status = ?,
                user_id = ?,
                parent_id = ?
            WHERE ticket_id = ?
        """,
            (
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
                ticket_id,
            ),
        )
        con.commit()

def delete_ticket(ticket_id: int):
    """
    Permanently delete a ticket by ID.
    """
    with _connect() as con, closing(con.cursor()) as cur:
        cur.execute("DELETE FROM tickets WHERE ticket_id = ?", (ticket_id,))
        con.commit()


# =========================================================
# INITIALISATION
# =========================================================
def init_db():
    """Initialise all database tables (safe to call multiple times)."""
    init_user_db()
    init_ticket_db()
    print("✅ Database initialised successfully.")