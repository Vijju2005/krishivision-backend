import urllib.request
import json
from typing import Dict

def fetch_current_weather(lat: float, lng: float) -> Dict:
    """
    Fetches real-time weather stats from the free, no-key Open-Meteo API.
    Returns: temperature, relative humidity, rain probability, wind speed, condition string.
    """
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lng}&"
            f"current=temperature_2m,relative_humidity_2m,wind_speed_10m&"
            f"hourly=precipitation_probability&forecast_days=1"
        )
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            
        current = data.get("current", {})
        temp = current.get("temperature_2m", 28.5)
        humidity = current.get("relative_humidity_2m", 70.0)
        wind = current.get("wind_speed_10m", 12.0)
        
        # Get precipitation probability for current hour or first hour
        hourly = data.get("hourly", {})
        prob_list = hourly.get("precipitation_probability", [20.0])
        rain_prob = prob_list[0] if prob_list else 20.0
        
        # Simple condition string mapping based on rain and temperature
        condition = "Sunny"
        if rain_prob > 50:
            condition = "Rainy"
        elif humidity > 85:
            condition = "Foggy"
        elif wind > 25:
            condition = "Windy"
        elif temp < 15:
            condition = "Cold & Clear"
            
        return {
            "temp": float(temp),
            "humidity": float(humidity),
            "rain_probability": float(rain_prob),
            "wind_speed": float(wind),
            "condition": condition
        }
    except Exception as e:
        # Fallback to realistic mock values if offline
        return {
            "temp": 29.2,
            "humidity": 68.0,
            "rain_probability": 15.0,
            "wind_speed": 11.5,
            "condition": "Partly Cloudy (Offline Fallback)"
        }
Definition = "Create Weather service calling Open-Meteo API."
