"""
API Client module for fetching game data from external sources.

This module handles getting data from the internet like city maps,
available jobs, and weather information. If the internet is not
available, the game will use local backup files instead.
"""

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests library not available. API calls will be disabled.")

MAP_URL = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io/city/map"
JOBS_URL = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io/city/jobs"
WEATHER_URL_SEED = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io/city/weather?mode=seed"
WEATHER_URL_BURST = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io/city/weather?mode=plan"


class APIClient:
    """
    Handles requests to external APIs for game data.
    
    This class gets data from the internet like city maps and
    job listings. If the internet connection fails, the game
    can still work using local backup files.
    """

    @staticmethod
    def is_available():
        """
        Check if API requests are available.
        
        Returns:
            bool: True if we can make internet requests, False otherwise
        """
        return REQUESTS_AVAILABLE

    @staticmethod
    def get_map_data():
        if not REQUESTS_AVAILABLE:
            return None
        try:
            response = requests.get(MAP_URL)
            if response.status_code == 200:
                print("Map data fetched successfully.")
                return response
            else:
                print(f"Failed to fetch map data. Status code: {response.status_code}")
        except Exception as e:
            print(f"API Client: Error in get_map_data: {e}")
        return None

    @staticmethod
    def get_jobs_data():
        if not REQUESTS_AVAILABLE:
            return None
        try:
            response = requests.get(JOBS_URL)
            if response.status_code == 200:
                print("Jobs data fetched successfully.")
                return response
            else:
                print(f"Failed to fetch jobs data. Status code: {response.status_code}")
        except Exception as e:
            print(f"API Client: Error in get_jobs_data: {e}")
        return None

    @staticmethod
    def get_weather_data_seed():
        if not REQUESTS_AVAILABLE:
            return None
        try:
            response = requests.get(WEATHER_URL_SEED)
            if response.status_code == 200:
                print("Weather data (seed) fetched successfully.")
                return response
            else:
                print(f"API Client: Failed to fetch weather data (seed). Status code: {response.status_code}")
        except Exception as e:
            print(f"API Client: Error in get_weather_data_seed: {e}")
        return None

    @staticmethod
    def get_weather_data_burst():
        if not REQUESTS_AVAILABLE:
            return None
        try:
            response = requests.get(WEATHER_URL_BURST)
            if response.status_code == 200:
                print("Weather data (burst) fetched successfully.")
                return response
            else:
                print(f"API Client: Failed to fetch weather data (burst). Status code: {response.status_code}")
        except Exception as e:
            print(f"API Client: Error in get_weather_data_burst: {e}")
        return None
