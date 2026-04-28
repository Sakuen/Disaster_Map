import os
import sqlite3
import requests
import datetime
import re

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "disasters.db")

class CountryExtractor:
    @staticmethod
    def extract(title, disaster_type):
        country = CountryExtractor._extract_raw(title, disaster_type)
        if country and country != 'Unknown':
            return ' '.join(word.capitalize() for word in country.split())
        return country

    @staticmethod
    def _extract_raw(title, disaster_type):
        if not title:
            return "Unknown"
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

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()
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
                economic_loss REAL,
                country TEXT
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_year ON disasters(year)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_type ON disasters(type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lat ON disasters(latitude)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lon ON disasters(longitude)')
        self.conn.commit()

    def clear_all(self):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM disasters')
        self.conn.commit()

    def upsert_disaster(self, data):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO disasters 
            (id, type, title, magnitude, time, year, latitude, longitude, depth, url, fatalities, economic_loss, country)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['id'], data['type'], data['title'], data['magnitude'], 
            data['time'], data['year'], data['latitude'], data['longitude'], 
            data.get('depth', 0), data.get('url', ''), 
            data.get('fatalities'), data.get('economic_loss'), data['country']
        ))
        
    def find_matching_earthquake(self, year, lat, lon):
        cursor = self.conn.cursor()
        # Find earthquake in the same year, within 2 degrees lat/lon
        cursor.execute('''
            SELECT id FROM disasters 
            WHERE type='earthquake' AND year=? 
            AND latitude BETWEEN ? AND ? 
            AND longitude BETWEEN ? AND ?
        ''', (year, lat-2, lat+2, lon-2, lon+2))
        row = cursor.fetchone()
        return row[0] if row else None

    def update_impact(self, event_id, fatalities, economic_loss):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE disasters 
            SET fatalities = COALESCE(fatalities, ?), 
                economic_loss = COALESCE(economic_loss, ?)
            WHERE id = ?
        ''', (fatalities, economic_loss, event_id))

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

class USGSFetcher:
    def __init__(self, db):
        self.db = db
        
    def fetch_and_populate(self):
        print("Fetching USGS Earthquake Data (Mag >= 6.0, since 1900)...")
        url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
        params = {
            "format": "geojson",
            "starttime": "1900-01-01",
            "minmagnitude": "6.0"
        }
        r = requests.get(url, params=params)
        r.raise_for_status()
        features = r.json().get('features', [])
        
        count = 0
        for f in features:
            props = f['properties']
            geom = f['geometry']
            time_ms = props.get('time')
            if not time_ms:
                continue
            
            dt = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(milliseconds=time_ms)
            title = props.get('title', 'Unknown')
            lon, lat, depth = geom['coordinates']
            
            data = {
                'id': f.get('id'),
                'type': 'earthquake',
                'title': title,
                'magnitude': props.get('mag', 6.0),
                'time': time_ms,
                'year': dt.year,
                'latitude': lat,
                'longitude': lon,
                'depth': depth,
                'url': props.get('url', ''),
                'fatalities': None,
                'economic_loss': None,
                'country': CountryExtractor.extract(title, 'earthquake')
            }
            self.db.upsert_disaster(data)
            count += 1
            
        self.db.commit()
        print(f"Inserted {count} USGS earthquakes.")

    def fetch_volcanoes(self):
        print("Fetching USGS Volcano Data...")
        url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
        params = {
            "format": "geojson",
            "starttime": "1900-01-01",
            "eventtype": "volcanic eruption"
        }
        r = requests.get(url, params=params)
        r.raise_for_status()
        features = r.json().get('features', [])
        
        count = 0
        for f in features:
            props = f['properties']
            geom = f['geometry']
            time_ms = props.get('time')
            if not time_ms:
                continue
            
            dt = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(milliseconds=time_ms)
            title = props.get('title', 'Unknown Volcanic Eruption')
            mag = props.get('mag')
            if mag is None or mag < 5.0: mag = 5.5 # baseline visibility
            
            lon, lat, depth = geom['coordinates']
            
            data = {
                'id': f"usgs_volc_{f.get('id')}",
                'type': 'volcano',
                'title': title,
                'magnitude': mag,
                'time': time_ms,
                'year': dt.year,
                'latitude': lat,
                'longitude': lon,
                'depth': depth,
                'url': props.get('url', ''),
                'fatalities': None,
                'economic_loss': None,
                'country': CountryExtractor.extract(title, 'volcano')
            }
            self.db.upsert_disaster(data)
            count += 1
            
        self.db.commit()
        print(f"Inserted {count} USGS volcanoes.")

class NOAAFetcher:
    def __init__(self, db):
        self.db = db
        self.base_url = "https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1"

    def fetch_tsunamis(self):
        print("Fetching NCEI Tsunami Data...")
        count = 0
        for year_start in range(1900, 2030, 10):
            url = f"{self.base_url}/tsunamis/events?minYear={year_start}&maxYear={year_start+9}"
            try:
                items = requests.get(url).json().get('items', [])
                for item in items:
                    year = item.get('year')
                    lat = item.get('latitude')
                    lon = item.get('longitude')
                    if not year or not lat or not lon:
                        continue
                        
                    title = f"Tsunami: {item.get('locationName', 'Unknown')}, {item.get('country', '')}".strip(', ')
                    mag = item.get('tsIntensity', item.get('maxWaterHeight', 5.0))
                    if mag is None: mag = 5.0
                    mag = min(max(mag, 5.0), 10.0) # Clamp magnitude
                    
                    try:
                        dt = datetime.datetime(year, item.get('month', 1) or 1, item.get('day', 1) or 1, tzinfo=datetime.timezone.utc)
                        time_ms = int(dt.timestamp() * 1000)
                    except:
                        time_ms = 0
                        
                    data = {
                        'id': f"tsunami_{item.get('id')}",
                        'type': 'tsunami',
                        'title': title,
                        'magnitude': mag,
                        'time': time_ms,
                        'year': year,
                        'latitude': lat,
                        'longitude': lon,
                        'depth': 0,
                        'url': f"https://www.ngdc.noaa.gov/hazel/view/hazards/tsunami/event-more-info/{item.get('id')}",
                        'fatalities': item.get('deathsTotal'),
                        'economic_loss': item.get('damageMillionsDollars'),
                        'country': CountryExtractor.extract(title, 'tsunami')
                    }
                    self.db.upsert_disaster(data)
                    count += 1
            except Exception as e:
                pass
        self.db.commit()
        print(f"Inserted {count} NCEI tsunamis.")

    def fetch_significant_earthquakes(self):
        print("Fetching NCEI Significant Earthquakes to merge casualties/damages...")
        count_updated = 0
        count_inserted = 0
        for year_start in range(1900, 2030, 10):
            url = f"{self.base_url}/earthquakes/events?minYear={year_start}&maxYear={year_start+9}"
            try:
                items = requests.get(url).json().get('items', [])
                for item in items:
                    year = item.get('year')
                    lat = item.get('latitude')
                    lon = item.get('longitude')
                    fatalities = item.get('deathsTotal')
                    economic_loss = item.get('damageMillionsDollars')
                    
                    if not year or not lat or not lon:
                        continue
                    if not fatalities and not economic_loss:
                        continue # No impact data to merge
                        
                    # Try to find a matching USGS earthquake
                    match_id = self.db.find_matching_earthquake(year, lat, lon)
                    if match_id:
                        self.db.update_impact(match_id, fatalities, economic_loss)
                        count_updated += 1
                    else:
                        # Insert as a new earthquake if no match
                        title = f"Earthquake: {item.get('locationName', 'Unknown')}, {item.get('country', '')}".strip(', ')
                        mag = item.get('eqMagnitude', 6.0)
                        try:
                            dt = datetime.datetime(year, item.get('month', 1) or 1, item.get('day', 1) or 1, tzinfo=datetime.timezone.utc)
                            time_ms = int(dt.timestamp() * 1000)
                        except:
                            time_ms = 0
                            
                        data = {
                            'id': f"noaa_eq_{item.get('id')}",
                            'type': 'earthquake',
                            'title': title,
                            'magnitude': mag,
                            'time': time_ms,
                            'year': year,
                            'latitude': lat,
                            'longitude': lon,
                            'depth': item.get('eqDepth', 0),
                            'url': f"https://www.ngdc.noaa.gov/hazel/view/hazards/earthquake/event-more-info/{item.get('id')}",
                            'fatalities': fatalities,
                            'economic_loss': economic_loss,
                            'country': CountryExtractor.extract(title, 'earthquake')
                        }
                        self.db.upsert_disaster(data)
                        count_inserted += 1
            except Exception as e:
                pass
        self.db.commit()
        print(f"Updated {count_updated} and Inserted {count_inserted} NCEI Earthquakes.")

if __name__ == "__main__":
    db = DatabaseManager()
    db.clear_all() # Rebuild from scratch
    
    usgs = USGSFetcher(db)
    usgs.fetch_and_populate()
    usgs.fetch_volcanoes()
    
    noaa = NOAAFetcher(db)
    noaa.fetch_tsunamis()
    noaa.fetch_significant_earthquakes()
    
    db.close()
    print("Database pipeline complete.")
