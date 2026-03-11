import sqlite3

conn = sqlite3.connect("nrsc.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS staff (
    staff_id TEXT PRIMARY KEY,
    name TEXT,
    password TEXT,
    role TEXT
)
""")

cur.execute("""
INSERT OR IGNORE INTO staff VALUES
('NRSC101', 'Dr. Sharma', 'admin123', 'Scientist'),
('NRSC102', 'Ms. Rao', 'staff123', 'Reception')
""")

conn.commit()
conn.close()

print("Staff table created and sample data inserted.")
