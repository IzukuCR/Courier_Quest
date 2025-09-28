from ..services.data_manager import DataManager
from ..weather.weather import Weather
from ..core.city import City
from .inventory import Inventory
from .scoreboard import Scoreboard


class Game:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Game, cls).__new__(cls)
        return cls._instance

    def __init__(self):

        if not Game._initialized:
            self._data_manager = DataManager()
            try:
                self._city = City.from_data_manager()
                self._weather = self._data_manager.load_weather()
                self._inventory = Inventory().load_orders()
            except Exception as e:
                print(f"Game Class: Error loading game data: {e}")
                self._city = City([])
                self._weather = Weather({})
                self._inventory = Inventory()

            self._scoreboard = Scoreboard()
            self._player_name = None
            self._game_time = 0.0
            # self._is_playing = False (not used yet)

            Game._initialized = True  # Prevent re-initialization

    def set_player_name(self, name):
        self._player_name = name

    def get_player_name(self):
        return self._player_name

    def get_game_time(self):
        return self._game_time

    def update_game_time(self, delta_time):
        if self._is_playing:
            self._game_time += delta_time

    def get_city(self):
        return self._city

    def get_weather(self):
        return self._weather

    def get_inventory(self):
        return self._inventory

    def pause_game(self):
        self._is_playing = False

    def resume_game(self):
        self._is_playing = True
