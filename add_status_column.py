import sqlite3

# Connect to the database file
conn = sqlite3.connect('database.db')

# Add a new column 'status' with default value 'Pending'
conn.execute("ALTER TABLE tasks ADD COLUMN status TEXT DEFAULT 'Pending'")

# Save and close
conn.commit()
conn.close()

print("✅ status column added.")
