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
        scenes = json.loads(response.read().decode("utf-8"))
        print(f"Total scenes: {len(scenes)}")
        for idx, scene in enumerate(scenes):
            dt = scene.get("dt")
            s_type = scene.get("type")
            cl = scene.get("cl")
            
            stats_url = f"https://api.agromonitoring.com/agro/1.0/stats/ndvi?polyid={polygon_id}&dt={dt}&appid={api_key}"
            try:
                with urllib.request.urlopen(stats_url, timeout=8.0) as resp2:
                    stats = json.loads(resp2.read().decode("utf-8"))
                    print(f"  Scene {idx} (dt={dt}, type={s_type}, cl={cl}): NDVI Stats found: {stats.get('mean')}")
            except Exception as e:
                print(f"  Scene {idx} (dt={dt}, type={s_type}, cl={cl}): Stats failed: {e}")
except Exception as e:
    print(e)
