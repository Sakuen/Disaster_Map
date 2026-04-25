import requests
import sqlite3
import os
import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "disasters.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    return conn

def fetch_tsunamis():
    print("Fetching NCEI Tsunami Data...")
    url = "https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/tsunamis/events"
    r = requests.get(url)
    data = r.json()
    items = data.get('items', [])
    print(f"Fetched {len(items)} Tsunamis.")
    return items

def populate_tsunamis(conn, items):
    cursor = conn.cursor()
    count = 0
    for item in items:
        # Require a valid year > 1900 and valid coordinates
        year = item.get('year')
        lat = item.get('latitude')
        lon = item.get('longitude')
        
        if year is None or year < 1900 or lat is None or lon is None:
            continue
            
        event_id = f"tsunami_{item.get('id')}"
        title = f"Tsunami: {item.get('locationName', 'Unknown')}, {item.get('country', '')}".strip(', ')
        # We can use max water height or intensity as magnitude
        mag = item.get('tsIntensity', item.get('maxWaterHeight', 5.0))
        # Ensure mag is somewhat within scale for deck.gl (5-10 range approximation)
        if mag > 10: mag = 10
        if mag < 5: mag = 5 + (mag / 5) # normalize tiny tsunamis up to 5 so they display
            
        # Create a basic timestamp for Jan 1 of that year to fit the timeline
        # If month/day are provided, we can use them
        month = item.get('month', 1)
        day = item.get('day', 1)
        if month is None: month = 1
        if day is None: day = 1
        
        try:
            dt = datetime.datetime(year, month, day, tzinfo=datetime.timezone.utc)
            time_ms = int(dt.timestamp() * 1000)
        except:
            time_ms = 0
            
        url = f"https://www.ngdc.noaa.gov/hazel/view/hazards/tsunami/event-more-info/{item.get('id')}"
            
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO disasters 
                (id, type, title, magnitude, time, year, latitude, longitude, depth, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (event_id, 'tsunami', title, mag, time_ms, year, lat, lon, 0, url))
            count += 1
        except Exception as e:
            print(f"Error inserting tsunami {event_id}: {e}")
            
    conn.commit()
    print(f"Inserted {count} tsunamis into DB.")

def fetch_volcanoes():
    print("Fetching NCEI Volcano Data...")
    url = "https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/volcanoes/locs"
    # Actually just hit the locs and eruption endpoints
    r = requests.get(url)
    if 'flashErrors' not in r.json():
        print(f"Fetched {len(r.json().get('items', []))} Volcanoes.")
    else:
        print("Failed to fetch volcanoes")

if __name__ == "__main__":
    conn = init_db()
    tsunamis = fetch_tsunamis()
    populate_tsunamis(conn, tsunamis)
    conn.close()
