import arcade

from ..services.data_manager import DataManager
from ..weather.weather import Weather
from ..core.city import City
from .inventory import Inventory


class Game:
    def __init__(self):
        self.city = City.from_data_manager()
        self.weather = self.load_weather()
        self.inventory = Inventory().load_orders()

    def load_city(self):
        data_manager = DataManager()
        map_data = data_manager.load_map()
        if map_data:
            return City(map_data)
        return None

    def load_weather(self):
        data_manager = DataManager()
        weather_data = data_manager.load_weather()
        if weather_data:
            return Weather(weather_data)
        return None

    def get_city(self):
        return self.city

    def get_weather(self):
        return self.weather

    def get_inventory(self):
        return self.inventory
