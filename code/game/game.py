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

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Game, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Prevent re-initialization of singleton
        if hasattr(self, '_initialized') and self._initialized:
            return

        print("Game: Initializing singleton instance...")

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
        # 10 minutes in seconds (10 * 60)
        self._game_time_limit_s: float = 600.0
        # Start with full time (countdown)
        self._game_time_s: float = 600.0
        self._weather_timer: float = 0.0          # accumulator for bursts
        self._burst_period_s: float = 55.0        # ~45–60s
        self._transition_s: float = 3.0           # reserved for smooth transitions

        # Weather change tracking
        self._last_weather_change_time: float = 0.0  # Track when last change occurred
        self._next_scheduled_change: float = 0.0     # When next change should happen

        # --------- Inventories ---------
        # Align deadlines with plan's start_time (bursts) if exists
        start_iso = getattr(self._weather, "start_time", None)
        self._jobs: JobsInventory = JobsInventory(weather_start_iso=start_iso)
        self._player_inv: PlayerInventory = PlayerInventory(
            capacity_weight=8.0)

        # --------- Player / score ---------
        self._player_name: str = "Player1"
        self._scoreboard: Scoreboard = Scoreboard(self._player_name)
        self._player: Optional[Player] = None  # Initialize as None
        self._goal: int = getattr(self._city, "goal", 0) if self._city else 0

        # Local pygame clock (in case you need it for debugging)
        self._clock = pygame.time.Clock()

        # Mark as initialized
        self._initialized = True
        print("Game: Singleton initialization complete")

    def set_player_name(self, name):
        self._player_name = name

    def get_player_name(self):
        return self._player_name

    def get_city(self):
        return self._city

    def get_weather(self):
        return self._weather

    def get_weather_condition(self) -> dict:
        """
        Get comprehensive weather condition data including timing information.
        Returns dict with current condition, timing data, and burst information.
        """
        base_condition = {
            "condition": self._weather.get_current_condition(),
            "intensity": self._weather.get_current_intensity(),
            "speed_multiplier": self._weather.get_speed_multiplier(),
            "weather_timer": self._weather_timer,
            "burst_period_s": self._burst_period_s,
            "transition_s": self._transition_s,
            "time_until_next_burst": max(0.0, self._burst_period_s - self._weather_timer),
            "burst_progress": min(1.0, self._weather_timer / self._burst_period_s)
        }

        # Get active burst information if available
        active_burst = self._weather._get_active_burst()
        if active_burst:
            base_condition.update({
                "has_active_burst": True,
                "burst_condition": active_burst["condition"],
                "burst_intensity": active_burst["intensity"],
                "burst_remaining_sec": active_burst["remaining_sec"],
                "burst_duration_sec": active_burst["duration_sec"],
                "burst_from": active_burst["from"]
            })
        else:
            base_condition["has_active_burst"] = False

        return base_condition

    def get_weather_timing_info(self) -> dict:
        """
        Get specific timing information for weather system.
        Useful for UI display and debugging.
        """
        return {
            "weather_timer": self._weather_timer,
            "burst_period_s": self._burst_period_s,
            "transition_s": self._transition_s,
            "time_until_next_change": max(0.0, self._burst_period_s - self._weather_timer),
            "progress_to_next_change": min(1.0, self._weather_timer / self._burst_period_s),
            "is_in_transition": self._weather_timer >= (self._burst_period_s - self._transition_s)
        }

    def set_weather_timing(self, burst_period_s: float = None, transition_s: float = None):
        """
        Set weather timing parameters.
        burst_period_s: Time between weather changes (default ~55s)
        transition_s: Reserved time for smooth transitions (default 3s)
        """
        if burst_period_s is not None:
            self._burst_period_s = max(1.0, float(burst_period_s))
        if transition_s is not None:
            self._transition_s = max(0.0, float(transition_s))

        # Ensure transition time doesn't exceed burst period
        if self._transition_s >= self._burst_period_s:
            self._transition_s = self._burst_period_s * 0.1  # 10% of burst period

    def reset_weather_timer(self):
        """Reset the weather timer to 0. Useful for debugging or forced weather changes."""
        self._weather_timer = 0.0

    def force_weather_change(self):
        """Force immediate weather change and reset timer."""
        self._weather.next_weather()
        self._weather_timer = 0.0
        return self.get_weather_condition()

    def get_player_inventory(self) -> PlayerInventory:
        return self._player_inv

    def get_jobs(self) -> JobsInventory:
        return self._jobs

    def get_game_time(self) -> float:
        """Get remaining game time in seconds (countdown)"""
        return max(0.0, self._game_time_s)

    def get_game_time_remaining_minutes(self) -> int:
        """Get remaining minutes for display"""
        return int(self.get_game_time() // 60)

    def get_game_time_remaining_seconds(self) -> int:
        """Get remaining seconds for display"""
        return int(self.get_game_time() % 60)

    def is_game_time_up(self) -> bool:
        """Check if game time has reached 0"""
        return self._game_time_s <= 0.0

    def get_game_time_progress(self) -> float:
        """Get game progress as percentage (0.0 to 1.0)"""
        return 1.0 - (self._game_time_s / self._game_time_limit_s)

    def get_player(self) -> Optional[Player]:
        """Get the current player instance"""
        return getattr(self, '_player', None)

    def is_paused(self) -> bool:
        return getattr(self, '_paused', False)

    def pause_game(self):
        self._paused = True

    def resume_game(self):
        self._paused = False

    def toggle_pause(self):
        """Toggle pause state"""
        self._paused = not self._paused
        print(
            f"Game: Pause toggled - now {'paused' if self._paused else 'resumed'}")

    def start_new_game(self):
        print("Game: Starting new game...")
        self._is_playing = True
        self._paused = False
        # Reset to full time (10 minutes)
        self._game_time_s = self._game_time_limit_s
        self._weather_timer = 0.0
        self._last_weather_change_time = 0.0
        # First change after burst period
        self._next_scheduled_change = self._burst_period_s
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
        print(f"Game: Player created at position ({start_x}, {start_y})")

    def should_trigger_weather_change(self) -> bool:
        """
        Determine if weather should change based on burst timing and elapsed time.
        Returns True if weather change should be triggered.
        """
        elapsed_time = self._game_time_limit_s - \
            self._game_time_s  # Time since game start

        # Check if we have burst data to work with
        weather_data = self._weather.get_weather_data()

        if weather_data["has_active_burst"]:
            # If there's an active burst, check if it should end
            active_burst = weather_data["active_burst"]
            if active_burst["remaining_sec"] <= 0:
                print(f"Game: Active burst ending, triggering weather change")
                return True

        # Check if enough time has passed since last change (burst period)
        time_since_last_change = elapsed_time - self._last_weather_change_time
        if time_since_last_change >= self._burst_period_s:
            print(
                f"Game: Burst period ({self._burst_period_s}s) elapsed, triggering weather change")
            return True

        # Check for scheduled weather changes based on burst timing
        if elapsed_time >= self._next_scheduled_change:
            print(
                f"Game: Scheduled weather change time reached ({self._next_scheduled_change}s)")
            return True

        return False

    def calculate_next_weather_change_time(self) -> float:
        """
        Calculate when the next weather change should occur based on burst data.
        """
        elapsed_time = self._game_time_limit_s - self._game_time_s

        # Check if there are upcoming bursts
        burst_info = self._weather.get_burst_info()

        if burst_info["has_active_burst"]:
            # If there's an active burst, next change when it ends
            active_burst = burst_info["active_burst"]
            return elapsed_time + active_burst["remaining_sec"]
        else:
            # Otherwise, use the standard burst period
            return elapsed_time + self._burst_period_s

    def trigger_weather_change(self) -> dict:
        """
        Trigger a weather change and update tracking variables.
        Returns the weather change result.
        """
        elapsed_time = self._game_time_limit_s - self._game_time_s

        print(f"Game: Triggering weather change at {elapsed_time:.1f}s")

        # Trigger the weather change
        weather_result = self._weather.next_weather()

        # Update tracking variables
        self._last_weather_change_time = elapsed_time
        self._weather_timer = 0.0  # Reset weather timer
        self._next_scheduled_change = self.calculate_next_weather_change_time()

        # Log the change
        if weather_result:
            old_condition = weather_result.get("old_condition", "unknown")
            new_condition = weather_result.get("new_condition", "unknown")
            source = weather_result.get("source", "unknown")
            print(
                f"Game: Weather changed from {old_condition} to {new_condition} (source: {source})")

        return weather_result

    def update(self, delta_time: float) -> None:
        if not self._is_playing or self._paused:
            return
        # Advance clock
        try:
            dt = max(0.0, float(delta_time))
        except Exception:
            dt = 0.0

        # Countdown timer (subtract time instead of adding)
        self._game_time_s = max(0.0, self._game_time_s - dt)

        # Check if time is up
        if self.is_game_time_up():
            self._is_playing = False  # End game when time reaches 0
            print("Game Over - Time's up!")

        # Weather timing - increment timer
        self._weather_timer += dt

        # Check if weather should change based on burst timing
        if self.should_trigger_weather_change():
            self.trigger_weather_change()

        # Expire orders by time
        self._jobs.mark_expired(self._game_time_s)

    def get_weather_debug_info(self) -> dict:
        """
        Get detailed weather timing information for debugging.
        """
        elapsed_time = self._game_time_limit_s - self._game_time_s
        time_since_last_change = elapsed_time - self._last_weather_change_time
        time_until_next_change = self._next_scheduled_change - elapsed_time

        return {
            "elapsed_game_time": elapsed_time,
            "weather_timer": self._weather_timer,
            "last_change_time": self._last_weather_change_time,
            "time_since_last_change": time_since_last_change,
            "next_scheduled_change": self._next_scheduled_change,
            "time_until_next_change": max(0.0, time_until_next_change),
            "burst_period_s": self._burst_period_s,
            "should_change": self.should_trigger_weather_change()
        }

    def on_player_moved(self, new_px: int, new_py: int) -> Optional[str]:
        msg = self._player_inv.on_player_step(
            new_px, new_py, self._game_time_s)

        # If delivered, add payout to score (can extend with bonus/penalties)
        if msg and "delivered" in msg:
            try:
                # message format: "PED-001 delivered (+180)."
                add = float(msg.split("(+")[1].split(")")[0])
                self._scoreboard.add_score(int(add))
            except Exception:
                pass

        return msg
