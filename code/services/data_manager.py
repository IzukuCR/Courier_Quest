import json
from pathlib import Path
from .api_client import APIClient


class DataManager:
    DATA_DIR = Path(__file__).parent.parent / "data"
    MAP_JSON = DATA_DIR / "cities.json"
    JOBS_JSON = DATA_DIR / "jobs.json"
    WEATHER_JSON = DATA_DIR / "weather.json"

    def __init__(self):
        self.api_client = APIClient()

    def load_map(self):
        try:  # Try to get map data from API
            response = self.api_client.get_map_data()
            if response is not None:
                data = response.json()
                if "data" in data:
                    return data["data"]
                return data
        except Exception as e:
            print(f"Error fetching map data from API: {e}")

        # Fallback: load from local JSON
        if self.MAP_JSON.exists():
            try:
                with open(self.MAP_JSON, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "data" in data:
                        return data["data"]
                return data
            except Exception as e:
                print(f"Error reading local map file: {e}")
                return None

        else:
            print(f"Local map file not found: {self.MAP_JSON}")
            return None

    def load_jobs(self):
        try:  # Try to get jobs data from API
            response = self.api_client.get_jobs_data()
            if response is not None:
                data = response.json()
                if "data" in data:
                    return data["data"]
                return data
        except Exception as e:
            print(f"Error fetching jobs data from API: {e}")

        # Fallback: load from local JSON
        if self.JOBS_JSON.exists():
            with open(self.JOBS_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "data" in data:
                    return data["data"]
                return data
        else:
            print(f"Local jobs file not found: {self.JOBS_JSON}")
            return None

    def load_weather(self):
        try:  # Try to get weather data from API
            response = self.api_client.get_weather_data()
            if response is not None:
                data = response.json()
                if "data" in data:
                    return data["data"]
                return data
        except Exception as e:
            print(f"Error fetching weather data from API: {e}")

        # Fallback: load from local JSON
        if self.WEATHER_JSON.exists():
            with open(self.WEATHER_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "data" in data:
                    return data["data"]
                return data
        else:
            print(f"Local weather file not found: {self.WEATHER_JSON}")
            return None
