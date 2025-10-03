from ..weather.weather import Weather
from ..core.city import City
from .inventory import Inventory
from .scoreboard import Scoreboard
from .player import Player
import pygame


class Game:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Game, cls).__new__(cls)
        return cls._instance

    def __init__(self):

        if not Game._initialized:
            from ..services.data_manager import DataManager
            self._data_manager = DataManager()  # Init data manager
            try:
                self._city = City.from_data_manager()  # Load city from data manager
                self._weather = Weather()  # Load weather from data manager
                weather_loaded = self._weather.load_weather()
                self._inventory = Inventory().load_orders()  # Load inventory from data manager
            except Exception as e:
                self._city = City([])
                self._weather = Weather({})
                self._inventory = Inventory()
                print(f"Game Class: Error loading game data: {e}")

            self._scoreboard = Scoreboard()
            self._player_name = "Player1"
            self._game_time = 0.0
            self._player = None
            self._is_playing = False
            self._goal = self._city.goal if self._city else 0

            Game._initialized = True  # Prevent re-initialization

            self.clock_ = pygame.time.Clock()

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

    def start_new_game(self):
        self._is_playing = True
        self._game_time = 0.0
        self._scoreboard = Scoreboard(self._player_name)  # Reset scoreboard

        # Create player at a valid starting position
        if self._city and hasattr(self._city, 'tiles'):
            # Start near the center or first non-blocked tile
            start_x, start_y = 15, 15  # Assuming a 30x30 map center
            found_start = False
            if not self._city.is_blocked(start_x, start_y):
                found_start = True
            if not found_start:
                for y in range(len(self._city.tiles)):
                    for x in range(len(self._city.tiles[0])):
                        if not self._city.is_blocked(x, y):
                            start_x, start_y = x, y
                            found_start = True
                            break
                    if found_start:
                        break

            self._player = Player(start_x, start_y)
            print(f"Player position on ({start_x}, {start_y})")
        else:
            self._player = Player(0, 0)
            print("Player created at (0,0) - no valid city")

    def get_player(self):
        return self._player
