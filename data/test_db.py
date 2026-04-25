import sqlite3
import requests

conn = sqlite3.connect('backend/disasters.db')
c = conn.cursor()

# Get a few examples of each type
examples = c.execute("SELECT year, type, title FROM disasters WHERE type='earthquake' LIMIT 5").fetchall()
examples += c.execute("SELECT year, type, title FROM disasters WHERE type='tsunami' LIMIT 5").fetchall()
examples += c.execute("SELECT year, type, title FROM disasters WHERE type='volcano' LIMIT 5").fetchall()

def build_query(year, type_, title):
    # Base heuristic logic
    if type_ == "earthquake":
        # Usually titles are "30 km W of Illapel, Chile" or "Southern California"
        # Let's take the last part after comma if exists
        parts = title.split(',')
        location = parts[-1].strip() if len(parts) > 1 else title.strip()
        # Remove things like "region", "off the coast of", "near"
        for w in ["region", "off the coast of", "near the coast of", "near", "northern", "southern", "eastern", "western"]:
            location = location.lower().replace(w, "").strip()
        return f"{year} {location} earthquake"
        
    elif type_ == "tsunami":
        # Tsunami titles are "Tsunami: INDIAN OCEAN, INDONESIA"
        clean_title = title.replace("Tsunami:", "").strip()
        parts = clean_title.split(',')
        location = parts[-1].strip() if len(parts) > 1 else clean_title
        return f"{year} {location} tsunami"
        
    elif type_ == "volcano":
        # Volcano titles are "Volcano: Mount St. Helens"
        clean_title = title.replace("Volcano:", "").strip()
        return f"{year} {clean_title} eruption"
        
    return f"{year} {title}"

search_url = "https://en.wikipedia.org/w/api.php"
headers = {"User-Agent": "DisasterMap/1.0"}

for y, t, title in examples:
    query = build_query(y, t, title)
    
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
    
    res = data.get('query', {}).get('search', [])
    if res:
        print(f"[{t}] | Original: '{title}' | Query: '{query}' => FOUND: {res[0]['title']}")
    else:
        # Fallback query if zero hits?
        fallback = f"{y} {t}"
        print(f"[{t}] | Original: '{title}' | Query: '{query}' => NO RESULTS")
