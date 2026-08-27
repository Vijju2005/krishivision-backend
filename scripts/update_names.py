import sqlite3
import os

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "krishivision.db"))
print("Target database:", db_path)

if not os.path.exists(db_path):
    print("Database not found!")
    exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Update names
updates = [
    ("Belagavi", "Belgaum"),
    ("Chikkamagaluru", "Chikmagalur"),
    ("Dakshina Kannada", "Dakshin Kannad"),
    ("Uttara Kannada", "Uttar Kannand")
]

for new_name, old_name in updates:
    c.execute("UPDATE districts SET name = ? WHERE name = ?", (new_name, old_name))
    print(f"Updated {c.rowcount} rows from '{old_name}' to '{new_name}'")

# Also let's check Udupi crops in the database
c.execute("SELECT d.name, cm.name, c.area_acres FROM crops c JOIN districts d ON c.district_id = d.id JOIN crop_masters cm ON c.crop_master_id = cm.id WHERE d.name = 'Udupi'")
print("Udupi crops in database:", c.fetchall())

conn.commit()
conn.close()
print("Done!")
