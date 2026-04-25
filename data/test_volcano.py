import requests

def debug_chunking():
    print("Testing Volcanoes events chunking...")
    for y in range(1900, 2030, 10):
        url = f"https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/volcanoes/events?minYear={y}&maxYear={y+9}"
        r = requests.get(url)
        data = r.json()
        if 'items' in data:
            print(f"  Volcanoes events {y}-{y+9}: {len(data['items'])} items")
        else:
            print(f"  Volcanoes events {y}-{y+9}: FAILED {list(data.keys())}")
            
    print("Testing Volcanoes eruptions chunking...")
    for y in range(1900, 2030, 10):
        url = f"https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/volcanoes/eruptions?minYear={y}&maxYear={y+9}"
        r = requests.get(url)
        data = r.json()
        if 'items' in data:
            print(f"  Volcanoes eruptions {y}-{y+9}: {len(data['items'])} items")
        else:
            print(f"  Volcanoes eruptions {y}-{y+9}: FAILED {list(data.keys())}")

if __name__ == "__main__":
    debug_chunking()
