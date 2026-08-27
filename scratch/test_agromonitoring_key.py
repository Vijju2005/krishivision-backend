import urllib.request
import json

api_key = "35c3682795c14edee7dd512a190128e5"
url = f"https://api.agromonitoring.com/agro/1.0/polygons?appid={api_key}"

try:
    with urllib.request.urlopen(url, timeout=8.0) as response:
        data = json.loads(response.read().decode("utf-8"))
        print(f"Status: {response.getcode()}")
        print(f"Polygons count: {len(data)}")
        for p in data:
            print(f"  ID: {p.get('id')}, Name: {p.get('name')}, Center: {p.get('center')}")
except Exception as e:
    print("Error querying AgroMonitoring API:", e)
