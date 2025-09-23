from core.city import City
from services.data_manager import DataManager


def main():
    try:
        data_manager = DataManager()
        data_manager.save_map_data()
        data_manager.save_jobs_data()
        data_manager.save_weather_data()

        print("City map loaded successfully from API!\n")
        city = City.from_data_manager()
        print("City map loaded successfully!\n")
        print(city)
    except Exception as e:
        print(f"Failed to load city: {e}")


if __name__ == "__main__":
    main()
