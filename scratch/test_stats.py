import urllib.request
import json

api_key = "35c3682795c14edee7dd512a190128e5"
polygon_id = "6a8542d10ece801e53e03a99"
dt = 1787011200

url = f"https://api.agromonitoring.com/agro/1.0/stats/ndvi?polyid={polygon_id}&dt={dt}&appid={api_key}"

try:
    with urllib.request.urlopen(url, timeout=8.0) as response:
        data = json.loads(response.read().decode("utf-8"))
        print(f"Status: {response.getcode()}")
        print("Data:", data)
except Exception as e:
    print("Error querying stats:", e)
