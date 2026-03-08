import urllib.request
import json
import time

queries = [
    "Chiang Mai University Library",
    "Faculty of Engineering Chiang Mai University",
    "Ang Kaew Reservoir Chiang Mai University",
    "library Chiang Mai University"
]

for q in queries:
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(q)}&format=jsonv2&polygon_geojson=1&countrycodes=th"
    req = urllib.request.Request(url, headers={'User-Agent': 'BookTrack/1.0 (test@example.com)'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"Query: {q}")
            if data:
                print(f" Found: {data[0].get('display_name')}")
                print(f" Type: {data[0].get('geojson', {}).get('type')}")
            else:
                print(" Not found")
    except Exception as e:
        print(f" Error: {e}")
    time.sleep(1)
