import requests

def test_usgs_volcano():
    print("Testing USGS Earthquake API for Volcanic Eruptions...")
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=1900-01-01&eventtype=volcanic%20eruption"
    try:
        r = requests.get(url)
        data = r.json()
        print(f"Found {len(data['features'])} volcanic eruptions in USGS database.")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_usgs_volcano()
