import requests
import json
import sqlite3
import os
import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "disasters.db")

def fetch_usgs_earthquakes():
    print("Fetching USGS Earthquake Data (Mag >= 6.0, since 1900)...")
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": "1900-01-01",
        "minmagnitude": "6.0"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    print(f"Fetched {len(data['features'])} earthquakes.")
    return data['features']

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disasters (
            id TEXT PRIMARY KEY,
            type TEXT,
            title TEXT,
            magnitude REAL,
            time INTEGER,
            year INTEGER,
            latitude REAL,
            longitude REAL,
            depth REAL,
            url TEXT,
            fatalities INTEGER,
            economic_loss REAL
        )
    ''')
    # Create indices for quick filtering by year and location box
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_year ON disasters(year)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_type ON disasters(type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_lat ON disasters(latitude)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_lon ON disasters(longitude)')
    conn.commit()
    return conn

def populate_db(conn, features):
    cursor = conn.cursor()
    count = 0
    for f in features:
        props = f['properties']
        geom = f['geometry']
        
        time_ms = props.get('time')
        if not time_ms:
            continue
            
        dt = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(milliseconds=time_ms)
        event_id = f.get('id')
        title = props.get('title')
        mag = props.get('mag')
        url = props.get('url')
        lon, lat, depth = geom['coordinates']
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO disasters 
                (id, type, title, magnitude, time, year, latitude, longitude, depth, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (event_id, 'earthquake', title, mag, time_ms, dt.year, lat, lon, depth, url))
            count += 1
        except Exception as e:
            print(f"Error inserting {event_id}: {e}")
            
    conn.commit()
    print(f"Inserted {count} records in database.")

if __name__ == "__main__":
    features = fetch_usgs_earthquakes()
    conn = init_db()
    populate_db(conn, features)
    conn.close()
