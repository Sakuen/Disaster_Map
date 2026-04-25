import sqlite3
import os
import requests
from fastapi import FastAPI
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
def get_disasters(start_year: int = 1900, end_year: int = 2026, min_mag: float = 6.0):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, type, title, magnitude, time, year, latitude, longitude, depth, url 
        FROM disasters 
        WHERE year >= ? AND year <= ? AND magnitude >= ?
    ''', (start_year, end_year, min_mag))
    
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
                "url": row[9]
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
