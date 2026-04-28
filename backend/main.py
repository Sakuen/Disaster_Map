import sqlite3
import os
import requests
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
