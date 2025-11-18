import pygame
import time
import threading
from .abstract_AI import EasyAI, HardAI, MediumAI
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
            # VERIFY city loaded correctly
            if not self._city or not hasattr(self._city, 'tiles') or not self._city.tiles:
                print("Game: ERROR - City failed to load properly, attempting reload...")
                self._city = City.from_data_manager()

            # Final check
            if self._city and hasattr(self._city, 'tiles') and len(self._city.tiles) > 0:
                print(
                    f"Game: City loaded successfully - {self._city.name} ({len(self._city.tiles)}x{len(self._city.tiles[0])} tiles)")
            else:
                print("Game: CRITICAL ERROR - City has no tile data!")
                raise Exception("City failed to load tile data")

        except Exception as e:
            print(f"Game Class: Error loading city: {e}")
            # DON'T create empty city - re-raise the error
            raise Exception(
                f"Failed to initialize game - city load error: {e}")

        # --------- Initialize Weather BEFORE using it ---------
        try:
            self._weather: Weather = Weather.from_data_manager()
            print(f"Game: Weather initialized successfully")
        except Exception as e:
            print(f"Game: Error loading weather: {e}")
            raise Exception(
                f"Failed to initialize game - weather load error: {e}")

        # --------- Game state / clock ---------
        self._is_playing: bool = False
        self._paused: bool = False
        self._game_time_limit_s: float = 600.0
        self._game_time_s: float = 600.0
        self._weather_timer: float = 0.0
        self._burst_period_s: float = 55.0
        self._transition_s: float = 3.0

        # Weather change tracking
        self._last_weather_change_time: float = 0.0
        self._next_scheduled_change: float = 0.0

        # --------- Inventories (NOW weather is available) ---------
        start_iso = getattr(self._weather, "start_time", None)
        self._jobs: JobsInventory = JobsInventory(weather_start_iso=start_iso)
        self._player_inv: PlayerInventory = PlayerInventory(
            capacity_weight=8.0)

        # --------- Player / score ---------
        self._player_name: str = "Player1"
        self._scoreboard: Scoreboard = Scoreboard(self._player_name)
        self._player: Optional[Player] = None
        self._goal: int = getattr(self._city, "goal", 0) if self._city else 0

        # Local pygame clock
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

        # AI Bots
        self.difficulty = "Normal"
        self.ai_bot = None
        self.bot_thread = None
        self.bot_running = False

        self._ai_inventory: PlayerInventory = PlayerInventory(
            capacity_weight=8.0)
        self._ai_jobs: JobsInventory = JobsInventory(
            weather_start_iso=start_iso)

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
        self._ai_jobs.mark_expired(self._game_time_s)

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
        """
        Check all game over conditions and return if game should end
        Returns: (is_game_over, reason)
        where reason can be: "victory", "time_up", "reputation", "no_jobs"
        """
        # Always check victory condition FIRST - this is the most important
        current_score = self._scoreboard.get_score() if hasattr(self, '_scoreboard') else 0
        if current_score >= self._goal:
            return True, "victory"

        # Check if time is up
        if self._game_time_s <= 0:
            return True, "time_up"

        # Check reputation too low
        if self._player and self._player.is_game_over_by_reputation():
            return True, "reputation"

        # Only check no more jobs if goal hasn't been reached
        no_more_jobs = self._check_no_more_jobs_available()
        if no_more_jobs:
            return True, "no_jobs"

        # No game over condition met
        return False, ""

    def _check_no_more_jobs_available(self) -> bool:
        """
        Check if there are no more jobs available and no pending orders.
        Returns True when the player has nothing left to do.
        """
        # Get current elapsed game time
        elapsed_game_time = self._game_time_limit_s - self._game_time_s

        # Check if there are any upcoming jobs to be released
        unreleased_jobs = [o for o in self._jobs.all()
                           if o.state == "available"
                           and getattr(o, 'release_time', 0) > elapsed_game_time]
        has_future_jobs = len(unreleased_jobs) > 0

        # Check if there are any selectable jobs now
        available_jobs = len(self._jobs.selectable(self._game_time_s))

        # Check if there are any active or pending orders in player inventory
        pending_orders = 0
        if hasattr(self._player_inv, 'accepted'):
            pending_orders += len(self._player_inv.accepted)
        if self._player_inv.active is not None:
            pending_orders += 1

        # Only end game if:
        # 1. No jobs are currently available AND
        # 2. No jobs will be released in the future AND
        # 3. No orders are pending in player's inventory
        no_current_jobs = available_jobs == 0
        no_pending_orders = pending_orders == 0

        if no_current_jobs and no_pending_orders and not has_future_jobs:
            print("Game: No more jobs available, no pending orders, and no future jobs!")
            return True

        # Otherwise, keep playing
        return False

    def set_difficulty(self, difficulty: str):
        """Create the corresponding AI based on the selected difficulty."""
        self.difficulty = difficulty.capitalize()

        if self.difficulty == "None":
            # No AI - solo jugador humano
            self.ai_bot = None
            print(f"[Game] No AI - Playing solo")
        elif self.difficulty == "Easy":
            self.ai_bot = EasyAI(start_x=12, start_y=12)
            self.ai_bot.jobs = self._ai_jobs
            self.ai_bot.inventory = self._ai_inventory
            print(f"[Game] AI created: {self.ai_bot.get_name()}")
        elif self.difficulty == "Medium":
            self.ai_bot = MediumAI(start_x=12, start_y=12)
            self.ai_bot.jobs = self._ai_jobs
            self.ai_bot.inventory = self._ai_inventory
            print(f"[Game] AI created: {self.ai_bot.get_name()}")
        elif self.difficulty == "Hard":
            self.ai_bot = HardAI(start_x=12, start_y=12)
            self.ai_bot.jobs = self._ai_jobs
            self.ai_bot.inventory = self._ai_inventory
            print(f"[Game] AI created: {self.ai_bot.get_name()}")
        else:
            self.ai_bot = None
            print(f"[Game] Unknown difficulty '{difficulty}' - No AI")

    def start_bot(self):
        """Inicia el hilo del bot de IA en paralelo al juego."""
        if not self.ai_bot:
            print("[Game] No AI assigned. Initialization aborted.")
            return

        # CRITICAL: If bot is already running, stop it first
        if self.bot_running:
            print("[Game] Bot already running - stopping previous instance...")
            self.stop_bot()

        if not self._city or not hasattr(self._city, 'tiles') or not self._city.tiles:
            print(f"[Game] ERROR: Cannot start AI - city data is invalid!")
            return

        # Assign references FIRST
        self.ai_bot.city = self._city
        self.ai_bot.weather = self._weather
        self.ai_bot.jobs = self._ai_jobs
        self.ai_bot.inventory = self._ai_inventory

        # THEN reset AI state
        if hasattr(self.ai_bot, 'reset_for_new_game'):
            self.ai_bot.reset_for_new_game()

        # Verification
        print(f"[Game] Starting AI: {self.ai_bot.get_name()}")
        print(f"  Position: ({self.ai_bot.x}, {self.ai_bot.y})")
        print(f"  City: {self.ai_bot.city.name}")
        print(
            f"  Tiles: {len(self.ai_bot.city.tiles)}x{len(self.ai_bot.city.tiles[0])}")
        print(f"  Weather: {self.ai_bot.weather is not None}")
        print(f"  Jobs: {len(self.ai_bot.jobs.all())} orders")

        # Start the thread
        self.bot_running = True
        self.bot_thread = threading.Thread(
            target=self._run_bot_loop, daemon=True)
        self.bot_thread.start()
        print(f"[Game] AI thread started successfully")

    def _run_bot_loop(self):
        """Bucle de ejecución del bot (hilo separado)."""
        clock = pygame.time.Clock()
        while self.bot_running:
            delta_time = clock.tick(30) / 1000.0  # 30 ticks/seg
            try:
                # La IA ejecuta su lógica interna
                self.ai_bot.run_bot_logic(self, delta_time)
            except Exception as e:
                print(f"[AI ERROR] {e}")
                self.bot_running = False
                break

            # Condición de salida (por ejemplo: reputación o tiempo)
            if self.ai_bot.is_game_over_by_reputation():
                print("[AI] Game over por reputación baja.")
                self.bot_running = False

    def stop_bot(self):
        """Stop the AI bot thread safely."""
        if self.bot_running:
            print("[Game] Stopping AI bot...")
            self.bot_running = False

            # Wait for thread to finish (with timeout)
            if self.bot_thread and self.bot_thread.is_alive():
                self.bot_thread.join(timeout=2.0)

                # Force terminate if still alive (shouldn't happen, but safety)
                if self.bot_thread.is_alive():
                    print("[Game] WARNING: Bot thread did not terminate cleanly")

            self.bot_thread = None
            print("[Game] AI bot stopped")

    def cleanup_for_menu(self):
        """Clean up game state when returning to menu."""
        print("[Game] Cleaning up for menu return...")

        # CRITICAL: Stop AI bot FIRST before clearing references
        self.stop_bot()

        # Set game as not playing
        self._is_playing = False
        self._paused = False

        # Clear player reference
        self._player = None

        # IMPORTANT: Don't set ai_bot to None - keep the difficulty selection
        # but ensure the bot is fully stopped
        if self.ai_bot:
            # Clear AI state manually
            self.ai_bot.is_moving = False
            self.ai_bot.move_progress = 0.0
            print(f"[Game] AI bot state cleared: {self.ai_bot.get_name()}")

        print("[Game] Cleanup complete")

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

        # Reset jobs inventory
        self._jobs.reset_for_new_game()

        # CRITICAL: Reset AI jobs inventory too
        self._ai_jobs.reset_for_new_game()

        # Reset player inventory
        self._player_inv.reset_for_new_game()

        # CRITICAL: Reset AI inventory too
        self._ai_inventory.reset_for_new_game()

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

        # Create new player instance
        self._player = Player(start_x, start_y)
        print(f"Game: Setting initial player reputation to 70")
        self._player.reputation = 70.0
        self._player.reset_daily_reputation_tracking()

        print(
            f"Game: New game started - Player at ({start_x}, {start_y}), Reputation: {self._player.reputation}")

        # CRITICAL: If AI exists, reset its position too
        if self.ai_bot:
            # Reset AI to its starting position (12, 12 by default)
            self.ai_bot.x = 12
            self.ai_bot.y = 12
            self.ai_bot.target_x = 12
            self.ai_bot.target_y = 12
            print(f"[Game] AI position reset to (12, 12)")
