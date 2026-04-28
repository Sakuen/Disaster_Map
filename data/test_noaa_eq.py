import requests

url = "https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/earthquakes/events?minYear=2011&maxYear=2011"
r = requests.get(url)
items = r.json().get('items', [])
if items:
    # Print keys of the first item to see what's available for deaths/damage
    print(list(items[0].keys()))
    print("Sample:", items[0])
else:
    print("No items")
