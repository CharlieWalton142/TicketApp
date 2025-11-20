import sqlite3
import bcrypt

DB_PATH = "ticketapp.db"

def get_user(username: str):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    con.close()
    return dict(row) if row else None

def verify_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return None
    if bcrypt.checkpw(password.encode("utf-8"), user["password_hash"]):
        return {"id": user["id"], "username": user["username"], "role": user["role"]}
    return None

def create_user(username: str, password: str, role: str = "user"):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, datetime('now'))",
            (username, pw_hash, role),
        )
        con.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        con.close()