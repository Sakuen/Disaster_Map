import requests

def debug_chunking():
    ok = True
    print("Testing Tsunamis...")
    for y in range(1900, 2030, 25):
        url = f"https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/tsunamis/events?minYear={y}&maxYear={y+24}"
        r = requests.get(url)
        items = r.json().get('items', [])
        print(f"  Tsunamis {y}-{y+24}: {len(items)} items")
        
    print("Testing Volcanoes locs...")
    url = "https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/volcanoes/locs"
    r = requests.get(url)
    data = r.json()
    if 'items' in data:
        print(f"  Volcano locs: {len(data['items'])} items")
        print(f"  First keys: {list(data['items'][0].keys())}")
        print(f"  First item: {data['items'][0]}")
    else:
        print(f"  Volcano locs: FAILED {list(data.keys())}")

if __name__ == "__main__":
    debug_chunking()
