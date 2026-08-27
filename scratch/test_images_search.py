import urllib.request
import json
import time

api_key = "35c3682795c14edee7dd512a190128e5"
polygon_id = "6a8542d10ece801e53e03a99"
now_ts = int(time.time()) - 300
thirty_days_ago_ts = now_ts - (30 * 24 * 60 * 60)

url = f"https://api.agromonitoring.com/agro/1.0/image/search?start={thirty_days_ago_ts}&end={now_ts}&polyid={polygon_id}&appid={api_key}"

try:
    with urllib.request.urlopen(url, timeout=8.0) as response:
        data = json.loads(response.read().decode("utf-8"))
        print(f"Status: {response.getcode()}")
        print(f"Scenes count: {len(data)}")
        for idx, scene in enumerate(data):
            print(f"Scene {idx}: dt={scene.get('dt')}, type={scene.get('type')}, cl={scene.get('cl')}")
except Exception as e:
    print("Error querying scenes:", e)
