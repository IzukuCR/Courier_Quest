import requests

map_url = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io/city/map"
jobs_url = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io/city/jobs"
weather_url_seed = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io/city/weather?mode=seed"
weather_url_burst = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io/city/weather?mode=plan"


class APIClient:

    @staticmethod
    def get_map_data():
        try:
            response = requests.get(map_url)
            if response.status_code == 200:
                print("Map data fetched successfully.")
                return response
            else:
                print(
                    f"Failed to fetch map data. Status code: {response.status_code}")
        except Exception as e:
            print(f"Api Client: Error in get_map_data: {e}")
        return None

    @staticmethod
    def get_jobs_data():
        try:
            response = requests.get(jobs_url)
            if response.status_code == 200:
                print("Jobs data fetched successfully.")
                return response
            else:
                print(
                    f"Failed to fetch jobs data. Status code: {response.status_code}")
        except Exception as e:
            print(f"Api Client: Error in get_jobs_data: {e}")
        return None

    @staticmethod
    def get_weather_data_seed():
        try:
            response = requests.get(weather_url_seed)
            if response.status_code == 200:
                print("Weather data (seed) fetched successfully.")
                return response
            else:
                print(
                    f"Api Client: Failed to fetch weather data (seed). Status code: {response.status_code}")
        except Exception as e:
            print(f"Api Client: Error in get_weather_data_seed: {e}")
        return None

    @staticmethod
    def get_weather_data_burst():
        try:
            response = requests.get(weather_url_burst)
            if response.status_code == 200:
                print("Weather data (burst) fetched successfully.")
                return response
            else:
                print(
                    f"Api Client: Failed to fetch weather data (burst). Status code: {response.status_code}")
        except Exception as e:
            print(f"Api Client: Error in get_weather_data_burst: {e}")
        return None
