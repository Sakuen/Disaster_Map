import sqlite3

def normalize(conn):
    c = conn.cursor()
    c.execute("SELECT id, country FROM disasters WHERE country IS NOT NULL")
    updates = []
    for row in c.fetchall():
        d_id, country = row
        # Title case the country (e.g., 'INDONESIA' -> 'Indonesia', 'PAPUA NEW GUINEA' -> 'Papua New Guinea')
        # We can handle words separated by space or hyphen
        normalized = ' '.join(word.capitalize() for word in country.split())
        if normalized != country:
            updates.append((normalized, d_id))
            
    if updates:
        c.executemany("UPDATE disasters SET country = ? WHERE id = ?", updates)
        conn.commit()
        print(f"Normalized {len(updates)} country records.")
    else:
        print("No normalization needed.")

if __name__ == "__main__":
    conn = sqlite3.connect('../backend/disasters.db')
    normalize(conn)
    conn.close()
