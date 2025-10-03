import pygame
from typing import Optional

from ..services.data_manager import DataManager
from ..weather.weather import Weather
from ..core.city import City
from .jobs_inventory import JobsInventory
from .player_inventory import PlayerInventory
from .scoreboard import Scoreboard
from .player import Player


class Game:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Game, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if Game._initialized:
            return

        # --------- Base data ---------
        self._dm = DataManager()
        try:
            self._city: City = City.from_data_manager()
        except Exception as e:
            print(f"Game Class: Error loading city: {e}")
            # Build an empty compatible City
            self._city = City({
                "name": "Unknown",
                "version": "0.0",
                "width": 0,
                "height": 0,
                "tiles": [],
                "legend": {},
                "goal": 0
            })

        try:
            self._weather: Weather = Weather()
            self._weather.load_weather()
        except Exception as e:
            print(f"Game Class: Error loading weather: {e}")
            self._weather = Weather()

        # --------- Game state / clock ---------
        self._is_playing: bool = False
        self._paused: bool = False
        self._game_time_s: float = 0.0            # game time (seconds)
        self._weather_timer: float = 0.0          # accumulator for bursts
        self._burst_period_s: float = 55.0        # ~45–60s
        self._transition_s: float = 3.0           # reserved for smooth transitions

        # --------- Inventories ---------
        # Align deadlines with plan's start_time (bursts) if exists
        start_iso = getattr(self._weather, "start_time", None)
        self._jobs: JobsInventory = JobsInventory(weather_start_iso=start_iso)
        self._player_inv: PlayerInventory = PlayerInventory(capacity_weight=8.0)

        # --------- Player / score ---------
        self._player_name: str = "Player1"
        self._scoreboard: Scoreboard = Scoreboard(self._player_name)
        self._player: Optional[Player] = None
        self._goal: int = getattr(self._city, "goal", 0) if self._city else 0

        # Local pygame clock (in case you need it for debugging)
        self._clock = pygame.time.Clock()

        Game._initialized = True

    def set_player_name(self, name):
        self._player_name = name

    def get_player_name(self):
        return self._player_name
    
    def get_city(self):
        return self._city

    def get_weather(self):
        return self._weather

    def get_player_inventory(self) -> PlayerInventory:
        return self._player_inv
    
    def get_jobs(self) -> JobsInventory:
        return self._jobs
    
    def get_game_time(self) -> float:
        return self._game_time_s

    def get_player(self) -> Optional[Player]:
        return self._player

    def is_paused(self) -> bool:
        return self._paused

    def pause_game(self):
        self._paused = True

    def resume_game(self):
        self._paused = False

    def start_new_game(self):
        self._is_playing = True
        self._paused = False
        self._game_time_s = 0.0
        self._weather_timer = 0.0
        self._scoreboard = Scoreboard(self._player_name)  # Reset scoreboard

        # Create player at a valid starting position
        start_x, start_y = 0, 0
        if self._city and getattr(self._city, "tiles", None):
            found = False
            for y in range(len(self._city.tiles)):
                for x in range(len(self._city.tiles[0])):
                    try:
                        if not self._city.is_blocked(x, y):
                            start_x, start_y = x, y
                            found = True
                            break
                    except Exception:
                        continue
                if found:
                    break

        self._player = Player(start_x, start_y)
        print(f"Player position on ({start_x}, {start_y})")

    def toggle_pause(self):
        self._paused = not self._paused

    def update(self, delta_time: float) -> None:
        if not self._is_playing or self._paused:
            return
        # Advance clock
        try:
            dt = max(0.0, float(delta_time))
        except Exception:
            dt = 0.0
        self._game_time_s += dt

        # Weather by bursts
        self._weather_timer += dt
        if self._weather_timer >= self._burst_period_s:
            self._weather_timer = 0.0
            # Change weather state (use plan+Markov if available)
            self._weather.next_weather()

        # Expire orders by time
        self._jobs.mark_expired(self._game_time_s)

    def on_player_moved(self, new_px: int, new_py: int) -> Optional[str]:
        msg = self._player_inv.on_player_step(new_px, new_py, self._game_time_s)

        # If delivered, add payout to score (can extend with bonus/penalties)
        if msg and "delivered" in msg:
            try:
                # message format: "PED-001 delivered (+180)."
                add = float(msg.split("(+")[1].split(")")[0])
                self._scoreboard.add_score(int(add))
            except Exception:
                pass

        return msg