import sqlite3
con = sqlite3.connect("ticketapp.db")
cur = con.cursor()
for row in cur.execute("SELECT id, username, role FROM users"):
    print(row)
con.close()