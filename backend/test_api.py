import requests
import json

def test_gdacs():
    try:
        url = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/MAP?eventtypes=EQ,VO,TS"
        r = requests.get(url)
        data = r.json()
        print("GDACS keys:", data.keys())
        features = data.get('features', [])
        print("GDACS features count:", len(features))
        if features:
            print("Sample GDACS feature properties:", features[0]['properties'])
    except Exception as e:
        print("GDACS failed:", e)

def test_usgs():
    try:
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson"
        r = requests.get(url)
        data = r.json()
        features = data.get('features', [])
        print("USGS features count:", len(features))
        if features:
            print("Sample USGS feature properties:", features[0]['properties'])
    except Exception as e:
        print("USGS failed:", e)

if __name__ == "__main__":
    test_gdacs()
    test_usgs()
