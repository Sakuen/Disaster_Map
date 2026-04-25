import sqlite3
import os
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
