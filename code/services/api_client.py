import requests

map_url = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io/city/map"
jobs_url = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io/city/jobs"
weather_url = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io/city/weather?city=TigerCity&mode=seed"


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
            print(f"Error in get_map_data: {e}")
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
            print(f"Error in get_jobs_data: {e}")
        return None

    @staticmethod
    def get_weather_data():
        try:
            response = requests.get(weather_url)
            if response.status_code == 200:
                print("Weather data fetched successfully.")
                return response
            else:
                print(
                    f"Failed to fetch weather data. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error in get_weather_data: {e}")
        return None
