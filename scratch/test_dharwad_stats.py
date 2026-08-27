import urllib.request
import json
import time

api_key = "35c3682795c14edee7dd512a190128e5"
polygon_id = "6a8542dd646c6569d79fe060"
now_ts = int(time.time()) - 300
thirty_days_ago_ts = now_ts - (30 * 24 * 60 * 60)

search_url = f"https://api.agromonitoring.com/agro/1.0/image/search?start={thirty_days_ago_ts}&end={now_ts}&polyid={polygon_id}&appid={api_key}"

try:
    with urllib.request.urlopen(search_url, timeout=8.0) as response:
        scenes = json.loads(response.read().decode("utf-8"))
        print(f"Scenes count for Dharwad: {len(scenes)}")
        if scenes:
            latest_scene = scenes[-1]
            dt = latest_scene.get("dt")
            print(f"Latest scene: dt={dt}, type={latest_scene.get('type')}")
            
            stats_url = f"https://api.agromonitoring.com/agro/1.0/stats/ndvi?polyid={polygon_id}&dt={dt}&appid={api_key}"
            try:
                with urllib.request.urlopen(stats_url, timeout=8.0) as resp2:
                    stats = json.loads(resp2.read().decode("utf-8"))
                    print("Stats:", stats)
            except Exception as e:
                print("Error querying stats for Dharwad:", e)
except Exception as e:
    print("Error querying scenes for Dharwad:", e)
