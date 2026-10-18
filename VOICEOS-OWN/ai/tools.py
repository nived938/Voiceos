import datetime
import urllib.parse
import requests
import psutil
import platform
import logging
from typing import Dict, Any

logger = logging.getLogger("VoiceOS.Tools")

def get_current_time(timezone: str = "local") -> str:
    """Returns the current date, time, and day of the week."""
    now = datetime.datetime.now()
    return now.strftime("%A, %B %d, %Y at %I:%M:%S %p")

def calculate(expression: str) -> str:
    """Safely evaluates a basic mathematical expression."""
    allowed = set("0123456789+-*/().,% eE")
    if not all(c in allowed for c in expression):
        return "Error: Expression contains unsupported characters."
    try:
        # Restricted eval for arithmetic
        result = eval(expression, {"__builtins__": None}, {})
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"

def weather_forecast(location: str) -> Dict[str, Any]:
    """
    Fetches live weather conditions and forecast for a given city or location using Open-Meteo.
    Mirrors VoiceOS's built-in weather tool.
    """
    try:
        # Step 1: Geocoding
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(location)}&count=1&language=en&format=json"
        geo_res = requests.get(geo_url, timeout=5)
        if not geo_res.ok:
            return {"error": f"Failed to find location: {location}"}
        geo_data = geo_res.json()
        if not geo_data.get("results"):
            return {"error": f"Location '{location}' not found."}

        place = geo_data["results"][0]
        lat = place["latitude"]
        lon = place["longitude"]
        name = place.get("name", location)
        country = place.get("country", "")

        # Step 2: Forecast
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=auto"
        )
        w_res = requests.get(weather_url, timeout=5)
        if not w_res.ok:
            return {"error": "Failed to fetch weather data."}

        w_data = w_res.json()
        current = w_data.get("current", {})
        daily = w_data.get("daily", {})

        return {
            "location": f"{name}, {country}".strip(", "),
            "temperature_c": current.get("temperature_2m"),
            "humidity_pct": current.get("relative_humidity_2m"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "forecast_high_c": daily.get("temperature_2m_max", [None])[0],
            "forecast_low_c": daily.get("temperature_2m_min", [None])[0],
            "rain_chance_pct": daily.get("precipitation_probability_max", [None])[0],
            "source": "Open-Meteo"
        }
    except Exception as e:
        logger.error(f"Weather lookup error: {e}")
        return {"error": f"Weather lookup failed: {str(e)}"}

def system_status() -> Dict[str, Any]:
    """Returns host CPU, memory, platform, and battery status."""
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        battery = psutil.sensors_battery()
        return {
            "os": f"{platform.system()} {platform.release()}",
            "cpu_usage_pct": cpu,
            "memory_used_gb": round(mem.used / (1024**3), 2),
            "memory_total_gb": round(mem.total / (1024**3), 2),
            "memory_percent": mem.percent,
            "battery_percent": battery.percent if battery else "AC Power"
        }
    except Exception as e:
        return {"error": str(e)}

VOICEOS_TOOLS = [
    get_current_time,
    calculate,
    weather_forecast,
    system_status
]
