import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

queries = [
    "Chiang Mai University Library",
    "Ang Kaew Reservoir Chiang Mai University"
]

for q in queries:
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(q)}&format=jsonv2&polygon_geojson=1&countrycodes=th"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read().decode())
            print(f"Query: {q}")
            if data:
                print(f" Found: {data[0].get('display_name')}")
                print(f" Type: {data[0].get('geojson', {}).get('type')}")
            else:
                print(" Not found")
    except Exception as e:
        print(f" Error: {e}")
