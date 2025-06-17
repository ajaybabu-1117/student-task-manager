import sqlite3

# connect to database
conn = sqlite3.connect('database.db')
cur = conn.cursor()

# create users table
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)
""")

# create tasks table with status
cur.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task TEXT,
    user TEXT,
    status TEXT DEFAULT 'Pending'
)
""")

# save and close
conn.commit()
conn.close()

print("✅ Done! Database created with status column.")
