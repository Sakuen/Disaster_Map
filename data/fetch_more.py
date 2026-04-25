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
    all_items = []
    # NCEI API limits to 200 items, chunk by 10 years to ensure we get all records
    for year_start in range(1900, 2030, 10):
        url = f"https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/tsunamis/events?minYear={year_start}&maxYear={year_start+9}"
        try:
            r = requests.get(url)
            items = r.json().get('items', [])
            all_items.extend(items)
            print(f"  {year_start}-{year_start+9}: {len(items)} Tsunamis")
        except:
            pass
    print(f"Fetched {len(all_items)} Tsunamis total.")
    return all_items

def populate_tsunamis(conn, items):
    cursor = conn.cursor()
    count = 0
    for item in items:
        year = item.get('year')
        lat = item.get('latitude')
        lon = item.get('longitude')
        
        if year is None or year < 1900 or lat is None or lon is None:
            continue
            
        event_id = f"tsunami_{item.get('id')}"
        title = f"Tsunami: {item.get('locationName', 'Unknown')}, {item.get('country', '')}".strip(', ')
        mag = item.get('tsIntensity', item.get('maxWaterHeight', 5.0))
        if mag is None: mag = 5.0
        if mag > 10: mag = 10
        if mag < 5: mag = 5 + (mag / 5)
            
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
                INSERT OR REPLACE INTO disasters 
                (id, type, title, magnitude, time, year, latitude, longitude, depth, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (event_id, 'tsunami', title, mag, time_ms, year, lat, lon, 0, url))
            count += 1
        except Exception as e:
            pass
            
    conn.commit()
    print(f"Inserted {count} tsunamis into DB.")

def fetch_volcanoes():
    print("Fetching USGS Volcano Data...")
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=1900-01-01&eventtype=volcanic%20eruption"
    r = requests.get(url)
    features = r.json().get('features', [])
    print(f"Fetched {len(features)} Volcano Eruptions.")
    return features

def populate_volcanoes(conn, features):
    cursor = conn.cursor()
    count = 0
    for f in features:
        props = f['properties']
        geom = f['geometry']
        
        time_ms = props.get('time')
        if not time_ms:
            continue
            
        dt = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(milliseconds=time_ms)
        event_id = f"volcano_{f.get('id')}"
        title = props.get('title', 'Unknown Volcanic Eruption')
        mag = props.get('mag')
        if mag is None or mag < 5.0: mag = 5.5 # Ensure baseline visibility
        
        url = props.get('url', '')
        lon, lat, depth = geom['coordinates']
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO disasters 
                (id, type, title, magnitude, time, year, latitude, longitude, depth, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (event_id, 'volcano', title, mag, time_ms, dt.year, lat, lon, depth, url))
            count += 1
        except Exception as e:
            print(f"Error inserting {event_id}: {e}")
            
    conn.commit()
    print(f"Inserted {count} volcano eruptions into DB.")

if __name__ == "__main__":
    conn = init_db()
    tsunamis = fetch_tsunamis()
    populate_tsunamis(conn, tsunamis)
    
    volcanoes = fetch_volcanoes()
    populate_volcanoes(conn, volcanoes)
    
    conn.close()
