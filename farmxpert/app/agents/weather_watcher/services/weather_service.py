import requests
from datetime import datetime
import logging
from ..models.weather_models import WeatherSnapshot
from typing import Optional
import os
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Use app configuration instead of manual .env loading
from farmxpert.app.config import settings

# Load project-level .env for backward compatibility
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(_PROJECT_ROOT / ".env")

# Use settings for API keys
OPENWEATHER_API_KEY = settings.openweather_api_key or os.getenv("OPENWEATHER_API_KEY")
WEATHERAPI_KEY = settings.weatherapi_key or os.getenv("WEATHERAPI_KEY")


class WeatherService:

    @staticmethod
    def get_weather(latitude: float, longitude: float) -> Optional[WeatherSnapshot]:
        """
        Try OpenWeather first, fallback to WeatherAPI
        """
        weather = WeatherService._fetch_openweather(latitude, longitude)

        if weather:
            return weather

        logger.warning("OpenWeather failed, switching to fallback WeatherAPI")
        return WeatherService._fetch_weatherapi(latitude, longitude)

    # ---------------- PRIMARY ---------------- #

    @staticmethod
    def _fetch_openweather(lat: float, lon: float) -> Optional[WeatherSnapshot]:
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            return WeatherSnapshot(
                temperature=data["main"]["temp"],
                min_temperature=data["main"]["temp_min"],
                max_temperature=data["main"]["temp_max"],
                humidity=data["main"]["humidity"],
                wind_speed=data["wind"]["speed"] * 3.6,  # m/s → km/h
                rainfall_mm=data.get("rain", {}).get("1h", 0.0),
                weather_condition=data["weather"][0]["main"].lower(),
                source="OpenWeather",
                observed_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"OpenWeather API error: {e}")
            return None

    # ---------------- FALLBACK ---------------- #

    # @staticmethod
    # def _fetch_weatherapi(lat: float, lon: float) -> Optional[WeatherSnapshot]:
    #     try:
    #         #url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={WEATHERAPI_KEY}"
    #         params = {
    #             "key": WEATHERAPI_KEY,
    #             "q": f"{lat},{lon}"
    #         }

    #         response = requests.get(url, params=params, timeout=10)
    #         response.raise_for_status()

    #         data = response.json()["current"]

    #         return WeatherSnapshot(
    #             temperature=data["temp_c"],
    #             min_temperature=data["temp_c"],
    #             max_temperature=data["temp_c"],
    #             humidity=data["humidity"],
    #             wind_speed=data["wind_kph"],
    #             rainfall_mm=data.get("precip_mm", 0.0),
    #             weather_condition=data["condition"]["text"].lower(),
    #             source="WeatherAPI",
    #             observed_at=datetime.utcnow()
    #         )

    #     except Exception as e:
    #         logger.critical(f"❌ WeatherAPI fallback failed: {e}")
    #         return None

    @staticmethod
    def _fetch_weatherapi(lat: float, lon: float) -> Optional[WeatherSnapshot]:
        try:
            url = "https://api.weatherapi.com/v1/current.json"
            params = {
                "key": WEATHERAPI_KEY,
                "q": f"{lat},{lon}"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()["current"]

            return WeatherSnapshot(
                temperature=data["temp_c"],
                min_temperature=data["temp_c"],
                max_temperature=data["temp_c"],
                humidity=data["humidity"],
                wind_speed=data["wind_kph"],
                rainfall_mm=data.get("precip_mm", 0.0),
                weather_condition=data["condition"]["text"].lower(),
                source="WeatherAPI",
                observed_at=datetime.utcnow()
            )

        except Exception as e:
            logger.critical(f"WeatherAPI fallback failed: {e}")
            return None

    @staticmethod
    async def analyze_weather(location: dict, crop_info: dict = None):
        """Analyze weather for a location"""
        try:
            # For now, return basic weather info
            # In a full implementation, this would call the actual weather APIs
            return {
                "data": {
                    "location": location,
                    "weather_condition": "partly_cloudy",
                    "temperature": 28,
                    "humidity": 65,
                    "wind_speed": 12,
                    "rainfall_mm": 0,
                    "recommendations": ["Good conditions for field work"]
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Weather analysis failed: {e}")
            return {"error": str(e)}

# Create service instance for FastAPI import
weather_watcher_service = WeatherService()
