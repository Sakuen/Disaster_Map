import sqlite3
import os
import requests
import time
import datetime
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Global Disaster Map API")
DB_PATH = os.path.join(os.path.dirname(__file__), "disasters.db")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Disaster Map API is running"}

# Simple in-memory cache for live data
LIVE_CACHE = {
    "data": None,
    "timestamp": 0
}

@app.get("/api/live")
def get_live_events():
    global LIVE_CACHE
    current_time = time.time()
    
    # Return cached data if less than 60 seconds old
    if LIVE_CACHE["data"] and (current_time - LIVE_CACHE["timestamp"]) < 60:
        return LIVE_CACHE["data"]
        
    events = []
    
    # 1. Fetch GDACS Live Events (Tsunamis, Earthquakes, Volcanoes, Floods, Tropical Cyclones)
    try:
        r = requests.get("https://www.gdacs.org/gdacsapi/api/events/geteventlist/MAP?eventtypes=EQ,VO,TC,FL", timeout=5)
        if r.status_code == 200:
            features = r.json().get('features', [])
            for f in features:
                props = f.get('properties', {})
                geom = f.get('geometry', {})
                coords = geom.get('coordinates', [0, 0])
                
                # Map GDACS type to our types
                ev_type = props.get('eventtype', '')
                type_map = {'EQ': 'earthquake', 'VO': 'volcano', 'TC': 'cyclone', 'FL': 'flood', 'TS': 'tsunami'}
                mapped_type = type_map.get(ev_type, 'other')
                
                # Extract time
                from_date = props.get('fromdate', '')
                try:
                    # GDACS fromdate is like '2026-04-26T04:23:24'
                    dt = datetime.datetime.fromisoformat(from_date)
                    time_ms = int(dt.replace(tzinfo=datetime.timezone.utc).timestamp() * 1000)
                except Exception:
                    time_ms = int(current_time * 1000)
                
                events.append({
                    "id": f"gdacs_{props.get('eventid')}_{props.get('episodeid')}",
                    "title": props.get('name', props.get('description', 'Unknown Event')),
                    "type": mapped_type,
                    "alert_level": props.get('alertlevel', 'Green').lower(),
                    "magnitude": props.get('severitydata', {}).get('severity', 5.0),
                    "latitude": coords[1] if len(coords) > 1 else 0,
                    "longitude": coords[0] if len(coords) > 0 else 0,
                    "time": time_ms,
                    "url": props.get('url', {}).get('report', ''),
                    "source": "GDACS"
                })
    except Exception as e:
        print(f"GDACS Fetch Error: {e}")

    # 2. Fetch USGS Significant Earthquakes (Past 30 days)
    try:
        r = requests.get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson", timeout=5)
        if r.status_code == 200:
            features = r.json().get('features', [])
            for f in features:
                props = f.get('properties', {})
                geom = f.get('geometry', {})
                coords = geom.get('coordinates', [0, 0, 0])
                
                # Avoid duplicates if GDACS already has it (simple check by ID or distance could be done, but we'll just append for now)
                events.append({
                    "id": f"usgs_{f.get('id')}",
                    "title": props.get('title', 'Unknown Earthquake'),
                    "type": "earthquake",
                    "alert_level": props.get('alert', 'green') or 'green',
                    "magnitude": props.get('mag', 5.0),
                    "latitude": coords[1] if len(coords) > 1 else 0,
                    "longitude": coords[0] if len(coords) > 0 else 0,
                    "time": props.get('time', int(current_time * 1000)),
                    "url": props.get('url', ''),
                    "source": "USGS"
                })
    except Exception as e:
        print(f"USGS Fetch Error: {e}")
        
    # Sort live events by time descending (newest first)
    events.sort(key=lambda x: x.get('time', 0), reverse=True)
        
    LIVE_CACHE["data"] = events
    LIVE_CACHE["timestamp"] = current_time
    
    return events

@app.get("/api/predict")
def get_predictions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Query all major earthquakes (Mag >= 6.5) with known country
    cursor.execute('''
        SELECT country, year, latitude, longitude
        FROM disasters 
        WHERE type='earthquake' AND magnitude >= 6.5 AND country IS NOT NULL AND country != 'Unknown'
        ORDER BY country, year ASC
    ''')
    
    country_data = {}
    for row in cursor.fetchall():
        country, year, lat, lon = row
        if country not in country_data:
            country_data[country] = []
        country_data[country].append({"year": year, "lat": lat, "lon": lon})
        
    conn.close()
    
    predictions = []
    current_year = datetime.datetime.now().year
    
    for country, events in country_data.items():
        # Filter out invalid "countries" like "M 6.5 - Mid-indian Ridge"
        if any(char.isdigit() for char in country):
            continue
            
        if len(events) < 5:
            continue # Need at least 5 major events to establish a reliable frequency
            
        years = sorted(list(set(e["year"] for e in events)))
        if len(years) < 2: 
            continue
            
        # Calculate Average Frequency based on the full 126 year dataset (1900 to 2026)
        # This prevents clustered historical events from skewing the gap
        avg_gap = 126.0 / len(events)
        
        last_event = max(years)
        years_since_last = current_year - last_event
        
        # Calculate Seismic Gap Risk Ratio
        risk_ratio = years_since_last / avg_gap if avg_gap > 0 else 0
        
        # Calculate rough centroid for map marker
        avg_lat = sum(e["lat"] for e in events) / len(events)
        avg_lon = sum(e["lon"] for e in events) / len(events)
        
        predictions.append({
            "country": country,
            "events_count": len(events),
            "avg_gap_years": round(avg_gap, 1),
            "last_event_year": last_event,
            "years_since_last": years_since_last,
            "risk_ratio": round(risk_ratio, 2),
            "latitude": round(avg_lat, 2),
            "longitude": round(avg_lon, 2)
        })
        
    # Sort by risk_ratio descending
    predictions.sort(key=lambda x: x["risk_ratio"], reverse=True)
    
    return predictions

@app.get("/api/disasters")
def get_disasters(
    start_year: int = 1900, 
    end_year: int = 2026, 
    min_mag: float = 0.0,
    max_mag: float = 10.0,
    min_depth: float = -100.0,
    max_depth: float = 1000.0
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, type, title, magnitude, time, year, latitude, longitude, depth, url, country, fatalities, economic_loss 
        FROM disasters 
        WHERE year >= ? AND year <= ? 
          AND magnitude >= ? AND magnitude <= ?
          AND (depth IS NULL OR (depth >= ? AND depth <= ?))
    ''', (start_year, end_year, min_mag, max_mag, min_depth, max_depth))
    
    features = []
    for row in cursor.fetchall():
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row[7], row[6]] # lon, lat
            },
            "properties": {
                "id": row[0],
                "type": row[1],
                "title": row[2],
                "magnitude": row[3],
                "time": row[4],
                "year": row[5],
                "depth": row[8],
                "url": row[9],
                "country": row[10],
                "fatalities": row[11],
                "economic_loss": row[12]
            }
        })
        
    conn.close()
    return {"type": "FeatureCollection", "features": features}

import re

@app.get("/api/details")
def get_event_details(year: int, title: str, type: str = 'earthquake'):
    query = f"{year} {title}"
    
    # Robust string cleaning for Wikipedia searches
    t = title
    if type == 'volcano':
        import re
        t = re.sub(r'M\s*\d+\.\d+\s*Volcanic Eruption\s*-\s*', '', t, flags=re.IGNORECASE)
        parts = t.split('-')
        t = parts[-1].strip()
        query = f"{year} {t} eruption"
    elif type == 'tsunami':
        t = t.replace("Tsunami:", "").strip()
        parts = t.split(',')
        if len(parts) > 1:
            t = parts[-1].strip() # focus on region/country
        query = f"{year} {t} tsunami"
    else:
        import re
        t = re.sub(r'M\s*\d+\.\d+\s*-\s*', '', t, flags=re.IGNORECASE)
        parts = t.split(',')
        loc = parts[-1].strip() if len(parts) > 1 else t
        for w in ["region", "off the coast of", "near the coast of", "near", "northern", "southern", "eastern", "western"]:
            loc = re.sub(rf'\b{w}\b', '', loc, flags=re.IGNORECASE).strip()
        query = f"{year} {loc} earthquake"

    search_url = "https://en.wikipedia.org/w/api.php"
    headers = {"User-Agent": "DisasterMap/1.0"}
            
    # Search for page
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "utf8": 1,
        "srlimit": 1
    }
    
    r = requests.get(search_url, params=params, headers=headers)
    data = r.json()
    
    if data.get('query', {}).get('search'):
        first_result = data['query']['search'][0]
        page_id = first_result['pageid']
        page_title = first_result['title']
        
        # Get extract, thumbnail, and url
        details_params = {
            "action": "query",
            "format": "json",
            "prop": "extracts|pageimages|info",
            "pageids": page_id,
            "exintro": 1,
            "explaintext": 1,
            "pithumbsize": 500,
            "inprop": "url"
        }
        r2 = requests.get(search_url, params=details_params, headers=headers)
        page_data = r2.json()['query']['pages'][str(page_id)]
        
        return {
            "found": True,
            "title": page_title,
            "extract": page_data.get('extract', 'No detailed description available.'),
            "image": page_data.get('thumbnail', {}).get('source'),
            "url": page_data.get('fullurl')
        }
        
    return {"found": False, "message": "No specific Wikipedia article found for this exact event."}

@app.get("/api/analytics")
def get_analytics(
    country: Optional[str] = Query(None, description="Filter by country"),
    type: Optional[str] = Query(None, description="Filter by disaster type"),
    year: Optional[int] = Query(None, description="Filter by year")
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Build dynamic WHERE clause
    conditions = []
    params = []
    
    if country:
        conditions.append("country = ?")
        params.append(country)
    if type:
        conditions.append("type = ?")
        params.append(type)
    if year:
        conditions.append("year = ?")
        params.append(year)
        
    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)
        
    def build_query(base_select, base_where="", group_by="", order_by="", limit=""):
        full_where = where_clause
        if base_where:
            if full_where:
                full_where += " AND " + base_where
            else:
                full_where = "WHERE " + base_where
        return f"{base_select} {full_where} {group_by} {order_by} {limit}"

    # By Country
    cursor.execute(build_query(
        base_select="SELECT country, COUNT(*) as count FROM disasters",
        base_where="country IS NOT NULL AND country != 'Unknown'",
        group_by="GROUP BY country",
        order_by="ORDER BY count DESC",
        limit="LIMIT 15"
    ), params)
    by_country = [{"country": row[0], "count": row[1]} for row in cursor.fetchall()]
    
    # By Year and Type
    cursor.execute(build_query(
        base_select="SELECT year, type, COUNT(*) as count FROM disasters",
        group_by="GROUP BY year, type",
        order_by="ORDER BY year ASC"
    ), params)
    
    year_map = {}
    for row in cursor.fetchall():
        y, t, c = row
        if y not in year_map:
            year_map[y] = {"year": y, "earthquake": 0, "tsunami": 0, "volcano": 0}
        year_map[y][t] = c
        
    by_year = list(year_map.values())
    
    # By Type
    cursor.execute(build_query(
        base_select="SELECT type, COUNT(*) as count FROM disasters",
        group_by="GROUP BY type"
    ), params)
    by_type = [{"name": row[0], "value": row[1]} for row in cursor.fetchall()]

    # By Fatalities (Top 10 deadliest)
    cursor.execute(build_query(
        base_select="SELECT title, year, fatalities, type FROM disasters",
        base_where="fatalities IS NOT NULL AND fatalities > 0",
        order_by="ORDER BY fatalities DESC",
        limit="LIMIT 10"
    ), params)
    by_fatalities = [{"title": row[0], "year": row[1], "fatalities": row[2], "type": row[3]} for row in cursor.fetchall()]

    # By Damage (Top 10 costliest)
    cursor.execute(build_query(
        base_select="SELECT title, year, economic_loss, type FROM disasters",
        base_where="economic_loss IS NOT NULL AND economic_loss > 0",
        order_by="ORDER BY economic_loss DESC",
        limit="LIMIT 10"
    ), params)
    by_damage = [{"title": row[0], "year": row[1], "damage_millions": row[2], "type": row[3]} for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "by_country": by_country,
        "by_year": by_year,
        "by_type": by_type,
        "by_fatalities": by_fatalities,
        "by_damage": by_damage
    }
