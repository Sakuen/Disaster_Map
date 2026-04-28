import sqlite3
import re
import os

def extract_country(title, disaster_type):
    if disaster_type == 'earthquake':
        parts = title.split(',')
        if len(parts) > 1:
            return parts[-1].strip()
        else:
            of_split = title.split(' of ')
            if len(of_split) > 1:
                return of_split[-1].strip()
            return title.strip()
    elif disaster_type == 'tsunami':
        t = title.replace("Tsunami:", "").strip()
        parts = t.split(',')
        if len(parts) > 1:
            return parts[-1].strip()
        return t
    elif disaster_type == 'volcano':
        t = re.sub(r'M\s*\d+\.\d+\s*Volcanic Eruption\s*-\s*', '', title, flags=re.IGNORECASE)
        parts = t.split(',')
        if len(parts) > 1:
            return parts[-1].strip()
        parts = t.split('-')
        if len(parts) > 1:
            return parts[-1].strip()
        return t.strip()
    return "Unknown"

if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), "disasters.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("PRAGMA table_info(disasters)")
    columns = [info[1] for info in c.fetchall()]

    if 'country' not in columns:
        c.execute("ALTER TABLE disasters ADD COLUMN country TEXT")

    c.execute("SELECT id, title, type FROM disasters")
    rows = c.fetchall()

    for row in rows:
        did, title, dtype = row
        country = extract_country(title, dtype)
        c.execute("UPDATE disasters SET country = ? WHERE id = ?", (country, did))

    conn.commit()
    conn.close()
    print("Updated countries successfully.")
