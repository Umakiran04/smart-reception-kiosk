import sqlite3

conn = sqlite3.connect("visitors.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS visitor_links (
    token TEXT PRIMARY KEY,
    created_by TEXT,
    expires_at TEXT,
    max_entries INTEGER,
    used_entries INTEGER DEFAULT 0
)
""")

conn.commit()
conn.close()

print("Visitor link table created successfully.")
