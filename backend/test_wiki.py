import requests

def search_wikipedia(title, year):
    # Try searching Wikipedia
    # We construct a query like "1906 San Francisco earthquake"
    query = f"{year} {title}"
    print(f"Querying Wikipedia for: {query}")
    
    search_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "utf8": 1,
        "srlimit": 1
    }
    
    r = requests.get(search_url, params=params)
    data = r.json()
    
    if data.get('query', {}).get('search'):
        first_result = data['query']['search'][0]
        page_id = first_result['pageid']
        page_title = first_result['title']
        
        # Get extract and image
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
        r2 = requests.get(search_url, params=details_params)
        page_data = r2.json()['query']['pages'][str(page_id)]
        
        print("Title:", page_title)
        print("Extract snippet:", page_data.get('extract', '')[:200] + "...")
        print("Image:", page_data.get('thumbnail', {}).get('source'))
        print("URL:", page_data.get('fullurl'))
    else:
        print("No Wiki results found.")

if __name__ == "__main__":
    search_wikipedia("San Francisco earthquake", 1906)
    search_wikipedia("Tsunami: INDIAN OCEAN", 2004)
