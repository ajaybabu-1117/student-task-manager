import sqlite3

# Replace these with your desired test credentials
username = "ajaybabupadamatiaj@gmail.com"
password = "1234"

conn = sqlite3.connect('database.db')
cur = conn.cursor()
cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
conn.commit()
conn.close()

print(f"✅ User '{username}' added!")
