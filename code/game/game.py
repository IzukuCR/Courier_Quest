import pygame
import time
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

        # Initialize save manager
        print("Game: Initializing save manager...")
        try:
            from ..services.game_save_manager import GameSaveManager
            self._save_manager = GameSaveManager()
            print("Game: Save manager initialized successfully")
        except Exception as e:
            print(f"Game: Error initializing save manager: {e}")
            self._save_manager = None

    def set_player_name(self, name):
        self._player_name = name

    def get_player_name(self):
        return self._player_name

    def get_city(self):
        return self._city

    def get_weather(self):
        return self._weather

    def save_game(self, save_name: Optional[str] = None) -> bool:
        """Save the current game state."""
        print(f"Game: save_game called with save_name={save_name}")

        if not self._save_manager:
            print("Game: ERROR - Save manager not initialized!")
            return False

        print(
            f"Game: Current game state - playing={self._is_playing}, player_name={self._player_name}")
        print(
            f"Game: Game time={self._game_time_s}, has_player={self._player is not None}")

        result = self._save_manager.save_game(save_name)
        print(f"Game: save_game result={result}")
        return result

    def load_game(self, save_name: str) -> bool:
        """Load a game state."""
        print(f"Game: load_game called with save_name={save_name}")

        if not self._save_manager:
            print("Game: ERROR - Save manager not initialized!")
            return False

        result = self._save_manager.load_game(save_name)
        print(f"Game: load_game result={result}")
        return result

    def list_saves(self) -> list:
        """List available saves."""
        return self._save_manager.list_saves()

    def delete_save(self, save_name: str) -> bool:
        """Delete a save file."""
        return self._save_manager.delete_save(save_name)

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
        self._next_scheduled_change = self._burst_period_s

        # Reset scoreboard
        self._scoreboard = Scoreboard(self._player_name)

        # Reset jobs inventory - THIS IS CRUCIAL
        self._jobs.reset_for_new_game()

        # Reset player inventory
        self._player_inv.reset_for_new_game()

        # Create new player at a valid starting position
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

        # Create new player instance with fresh stats
        self._player = Player(start_x, start_y)

        # Ensure player reputation is reset to initial value
        print(f"Game: Setting initial player reputation to 70")
        self._player.reputation = 70.0  # Always start with this value
        self._player.reset_daily_reputation_tracking()

        print(
            f"Game: New game started - Player at ({start_x}, {start_y}), Reputation: {self._player.reputation}")

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

        # Advance clock - ensure proper time scaling
        try:
            # Make sure delta_time is in the expected range
            dt = max(0.0, min(0.1, float(delta_time)))

            # Debug time information - only print once every 10 seconds
            if hasattr(self, '_last_update_time') and hasattr(self, '_last_debug_print_time'):
                real_delta = time.time() - self._last_update_time
                current_time = time.time()

                # Only print debug info once every 10 seconds to avoid spam
                if current_time - self._last_debug_print_time > 10:
                    time_ratio = dt / real_delta if real_delta > 0 else 0
                    if abs(1.0 - time_ratio) > 0.2:  # If more than 20% off
                        print(
                            f"Time debug: dt={dt:.4f}s, real={real_delta:.4f}s, ratio={time_ratio:.2f}")
                    self._last_debug_print_time = current_time
            else:
                self._last_debug_print_time = time.time()

            self._last_update_time = time.time()

            # Apply a time correction factor to fix the slow game time
            time_correction_factor = 2.0  # Adjust this value based on testing
            dt *= time_correction_factor

        except Exception as e:
            print(f"Error processing delta time: {e}")
            dt = 0.0

        # Countdown timer (subtract time instead of adding)
        self._game_time_s = max(0.0, self._game_time_s - dt)

        # Check if time is up
        if self.is_game_time_up():
            self._is_playing = False  # End game when time reaches 0
            print("Game Over - Time's up!")

        # Check for game over due to reputation
        if self._player and self._player.is_game_over_by_reputation():
            self._is_playing = False  # End game when reputation < 20
            print("Game Over - Reputation too low!")

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

    def check_game_over_conditions(self) -> tuple[bool, str]:
        """Check all game over conditions and return if game should end"""
        if self._game_time_s <= 0:
            return True, "Time's up!"

        if self._player and self._player.is_game_over_by_reputation():
            return True, "Reputation too low (<20)!"

        # Add other game over conditions here

        return False, ""
        if self._player and self._player.is_game_over_by_reputation():
            return True, "Reputation too low (<20)!"

        # Add other game over conditions here

        return False, ""
