import pickle
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from ..game.game import Game


class GameSaveManager:
    """Manages saving and loading game states using binary serialization."""

    def __init__(self):
        self.save_dir = Path("saves")
        # Add debugging for directory creation
        try:
            self.save_dir.mkdir(exist_ok=True)
            print(
                f"GameSaveManager: Save directory created/verified at: {self.save_dir.absolute()}")
        except Exception as e:
            print(f"GameSaveManager: Error creating save directory: {e}")

    def save_game(self, save_name: Optional[str] = None) -> bool:
        """
        Save the current game state to a binary file.

        Args:
            save_name: Optional name for the save file. If None, uses timestamp.

        Returns:
            bool: True if save was successful, False otherwise.
        """
        print(
            f"GameSaveManager: Starting save process... (save_name={save_name})")

        try:
            # Get game instance - don't create new one, use existing singleton
            print("GameSaveManager: Getting game instance...")
            if not hasattr(Game, '_instance') or Game._instance is None:
                print("GameSaveManager: ERROR - No game instance exists!")
                return False

            game = Game._instance
            print(f"GameSaveManager: Got game instance: {game}")
            print(
                f"GameSaveManager: Game state check - is_playing={getattr(game, '_is_playing', 'N/A')}, paused={getattr(game, '_paused', 'N/A')}")

            # Check if game is properly initialized
            if not hasattr(game, '_initialized') or not game._initialized:
                print("GameSaveManager: ERROR - Game instance not properly initialized!")
                return False

            # Generate save filename
            if not save_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_name = f"save_{timestamp}"

            save_file = self.save_dir / f"{save_name}.sav"
            print(f"GameSaveManager: Saving to: {save_file.absolute()}")

            # Collect all game state data
            print("GameSaveManager: Collecting game state...")
            game_state = self._collect_game_state(game)

            if not game_state:
                print("GameSaveManager: ERROR - Failed to collect game state!")
                return False

            print(
                f"GameSaveManager: Game state collected, keys: {list(game_state.keys())}")

            # Ensure save directory exists
            self.save_dir.mkdir(exist_ok=True)

            # Save to binary file
            print(f"GameSaveManager: Writing to file...")
            with open(save_file, 'wb') as f:
                pickle.dump(game_state, f, protocol=pickle.HIGHEST_PROTOCOL)

            # Verify file was created
            if save_file.exists():
                file_size = save_file.stat().st_size
                print(
                    f"GameSaveManager: Game saved successfully: {save_file} ({file_size} bytes)")
                return True
            else:
                print(f"GameSaveManager: ERROR - Save file was not created!")
                return False

        except Exception as e:
            print(f"GameSaveManager: Error saving game: {e}")
            import traceback
            traceback.print_exc()
            return False

    def load_game(self, save_name: str) -> bool:
        """
        Load a game state from a binary file.

        Args:
            save_name: Name of the save file (without extension).

        Returns:
            bool: True if load was successful, False otherwise.
        """
        print(f"GameSaveManager: Starting load process for: {save_name}")

        try:
            save_file = self.save_dir / f"{save_name}.sav"
            print(
                f"GameSaveManager: Looking for save file: {save_file.absolute()}")

            if not save_file.exists():
                print(
                    f"GameSaveManager: ERROR - Save file not found: {save_file}")
                return False

            file_size = save_file.stat().st_size
            print(f"GameSaveManager: Found save file ({file_size} bytes)")

            # Load from binary file
            print(f"GameSaveManager: Reading save file...")
            with open(save_file, 'rb') as f:
                game_state = pickle.load(f)

            print(
                f"GameSaveManager: Save file loaded, keys: {list(game_state.keys())}")

            # Restore game state
            print(f"GameSaveManager: Restoring game state...")
            success = self._restore_game_state(game_state)

            if success:
                print(
                    f"GameSaveManager: Game loaded successfully: {save_file}")
            else:
                print(f"GameSaveManager: ERROR - Failed to restore game state!")

            return success

        except Exception as e:
            print(f"GameSaveManager: Error loading game: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _collect_game_state(self, game: Game) -> Dict[str, Any]:
        """Collect all necessary game state data."""
        print("GameSaveManager: Starting game state collection...")

        try:
            # Check if game has required attributes
            required_attrs = ['_player_name', '_game_time_s',
                              '_game_time_limit_s', '_is_playing']
            for attr in required_attrs:
                if not hasattr(game, attr):
                    print(
                        f"GameSaveManager: ERROR - Game missing required attribute: {attr}")
                    return None

            # Get player state
            print("GameSaveManager: Collecting player state...")
            player = game.get_player()
            player_state = None
            if player:
                # Collect undo system state - fix attribute names
                undo_state = None
                if hasattr(player, 'undo_system') and player.undo_system:
                    undo_state = {
                        'position_history': getattr(player.undo_system, 'position_history', []),
                        'max_steps': getattr(player.undo_system, 'max_steps', 8),
                        # Fixed attribute name
                        'stamina_cost': getattr(player.undo_system, 'stamina_cost', 10.0)
                    }
                    print(
                        f"GameSaveManager: Undo system state collected - {len(undo_state['position_history'])} positions in history")

                # Collect reputation system state
                reputation_state = {
                    'successful_deliveries_streak': getattr(player, 'successful_deliveries_streak', 0),
                    'had_first_late_delivery_today': getattr(player, 'had_first_late_delivery_today', False),
                    'daily_delivery_stats': getattr(player, 'daily_delivery_stats', {
                        "on_time": 0, "early": 0, "late": 0, "canceled": 0, "lost": 0
                    })
                }

                player_state = {
                    'position': (player.x, player.y),
                    'target_position': (player.target_x, player.target_y),
                    'is_moving': player.is_moving,
                    'move_progress': player.move_progress,
                    'current_direction': player.current_direction,
                    'stamina': player.stamina,
                    'reputation': player.reputation,
                    'streak': player.streak,
                    'weight': player.weight,
                    'resistance_state': player.resistance_state,
                    'base_speed': player.base_speed,
                    'current_speed': player.current_speed,
                    'animation_frame': player.animation_frame,
                    'animation_timer': player.animation_timer,
                    # New stamina system data
                    'idle_time': getattr(player, 'idle_time', 0.0),
                    'stamina_recovery_rate': getattr(player, 'stamina_recovery_rate', 5.0),
                    'stamina_recovery_interval': getattr(player, 'stamina_recovery_interval', 1.0),
                    'recovery_threshold': getattr(player, 'recovery_threshold', 30.0),
                    'is_in_recovery_mode': getattr(player, 'is_in_recovery_mode', False),
                    'was_exhausted': getattr(player, 'was_exhausted', False),
                    # Undo system state
                    'undo_state': undo_state,
                    # Reputation system state
                    'reputation_state': reputation_state
                }
                print(
                    f"GameSaveManager: Player state collected at position ({player.x}, {player.y})")
            else:
                print("GameSaveManager: WARNING - No player instance found!")

            # Get jobs inventory state
            print("GameSaveManager: Collecting jobs state...")
            jobs = game.get_jobs()
            jobs_state = {
                'selected_index': jobs._selected_index,
                'scroll_offset': getattr(jobs, '_scroll_offset', 0),
                'visible_count': getattr(jobs, '_visible_count', 3),
                'orders': []
            }

            for order in jobs.all():
                order_data = {
                    'id': order.id,
                    'pickup': order.pickup,
                    'dropoff': order.dropoff,
                    'payout': order.payout,
                    'deadline_iso': order.deadline_iso,
                    'weight': order.weight,
                    'priority': order.priority,
                    'release_time': order.release_time,
                    'state': order.state,
                    'accepted_at': order.accepted_at,
                    'picked_at': order.picked_at,
                    'delivered_at': order.delivered_at,
                    'deadline_s': order.deadline_s,
                    # Save release tracking flags
                    '_was_released': getattr(order, '_was_released', False),
                    '_last_debug_time': getattr(order, '_last_debug_time', None)
                }
                jobs_state['orders'].append(order_data)

            print(
                f"GameSaveManager: Jobs state collected, {len(jobs_state['orders'])} orders")

            # Get player inventory state
            print("GameSaveManager: Collecting player inventory state...")
            player_inv = game.get_player_inventory()
            player_inv_state = {
                'capacity_weight': player_inv.capacity_weight,
                'accepted_orders': [order.id for order in player_inv.accepted],
                'active_order_id': player_inv.active.id if player_inv.active else None,
                '_debug_printed': getattr(player_inv, '_debug_printed', False)
            }

            # Get weather state with enhanced timing data
            print("GameSaveManager: Collecting weather state...")
            weather = game.get_weather()
            weather_state = {
                'current_condition': weather.current_condition,
                'current_intensity': weather.current_intensity,
                'city': weather.city,
                'start_time': weather.start_time,
                'conditions': weather.conditions,
                'transition_matrix': weather.transition_matrix,
                'bursts': weather.bursts,
                'meta': weather.meta
            }

            # Get scoreboard state
            print("GameSaveManager: Collecting scoreboard state...")
            scoreboard_state = {
                'score': game._scoreboard.score,
                'player_name': game._scoreboard.player_name
            }

            # Collect main game state with enhanced timing data
            print("GameSaveManager: Assembling final game state...")
            game_state = {
                'version': '2.0',  # Updated save format version
                'timestamp': datetime.now().isoformat(),
                'player_name': game.get_player_name(),
                'game_time_s': game._game_time_s,
                'game_time_limit_s': game._game_time_limit_s,
                'weather_timer': game._weather_timer,
                'burst_period_s': game._burst_period_s,
                'transition_s': game._transition_s,
                'last_weather_change_time': game._last_weather_change_time,
                'next_scheduled_change': game._next_scheduled_change,
                'is_playing': game._is_playing,
                'paused': game._paused,
                'goal': game._goal,
                # Enhanced game timing data
                '_last_update_time': getattr(game, '_last_update_time', None),
                '_last_debug_print_time': getattr(game, '_last_debug_print_time', None),
                # Component states
                'player_state': player_state,
                'jobs_state': jobs_state,
                'player_inventory_state': player_inv_state,
                'weather_state': weather_state,
                'scoreboard_state': scoreboard_state
            }

            print(f"GameSaveManager: Game state assembly complete")
            return game_state

        except Exception as e:
            print(f"GameSaveManager: Error collecting game state: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _restore_game_state(self, game_state: Dict[str, Any]) -> bool:
        """Restore game state from loaded data."""
        print("GameSaveManager: Starting game state restoration...")

        try:
            # Get existing game instance
            if not hasattr(Game, '_instance') or Game._instance is None:
                print("GameSaveManager: Creating new game instance for restore...")
                game = Game()
            else:
                game = Game._instance
                print("GameSaveManager: Using existing game instance for restore...")

            # Restore main game state
            print("GameSaveManager: Restoring main game state...")
            game._player_name = game_state['player_name']
            game._game_time_s = game_state['game_time_s']
            game._game_time_limit_s = game_state['game_time_limit_s']
            game._weather_timer = game_state['weather_timer']
            game._burst_period_s = game_state['burst_period_s']
            game._transition_s = game_state['transition_s']
            game._last_weather_change_time = game_state['last_weather_change_time']
            game._next_scheduled_change = game_state['next_scheduled_change']
            game._is_playing = game_state['is_playing']
            # Auto-resume game when loading - don't restore paused state
            game._paused = False  # Always resume when loading
            game._goal = game_state['goal']

            # Restore enhanced timing data if available
            if '_last_update_time' in game_state and game_state['_last_update_time']:
                game._last_update_time = game_state['_last_update_time']
            if '_last_debug_print_time' in game_state and game_state['_last_debug_print_time']:
                game._last_debug_print_time = game_state['_last_debug_print_time']

            # Restore player state with enhanced data
            print("GameSaveManager: Restoring player state...")
            if game_state['player_state']:
                from ..game.player import Player
                player_data = game_state['player_state']

                player = Player(
                    player_data['position'][0], player_data['position'][1])
                player.target_x = player_data['target_position'][0]
                player.target_y = player_data['target_position'][1]
                player.is_moving = player_data['is_moving']
                player.move_progress = player_data['move_progress']
                player.current_direction = player_data['current_direction']
                player.stamina = player_data['stamina']
                player.reputation = player_data['reputation']
                player.streak = player_data['streak']
                player.weight = player_data['weight']
                player.resistance_state = player_data['resistance_state']
                player.base_speed = player_data['base_speed']
                player.current_speed = player_data['current_speed']
                player.animation_frame = player_data['animation_frame']
                player.animation_timer = player_data['animation_timer']

                # Restore stamina system data
                player.idle_time = player_data.get('idle_time', 0.0)
                player.stamina_recovery_rate = player_data.get(
                    'stamina_recovery_rate', 5.0)
                player.stamina_recovery_interval = player_data.get(
                    'stamina_recovery_interval', 1.0)
                player.recovery_threshold = player_data.get(
                    'recovery_threshold', 30.0)
                player.is_in_recovery_mode = player_data.get(
                    'is_in_recovery_mode', False)
                player.was_exhausted = player_data.get('was_exhausted', False)

                # Restore undo system - fix attribute names and add null checks
                if 'undo_state' in player_data and player_data['undo_state'] and hasattr(player, 'undo_system'):
                    undo_data = player_data['undo_state']
                    if player.undo_system:
                        # Restore position history
                        if 'position_history' in undo_data:
                            player.undo_system.position_history = undo_data['position_history']

                        # Restore max steps
                        if 'max_steps' in undo_data:
                            player.undo_system.max_steps = undo_data['max_steps']

                        # Restore stamina cost (use correct attribute name)
                        if 'stamina_cost' in undo_data:
                            player.undo_system.stamina_cost = undo_data['stamina_cost']

                        print(
                            f"GameSaveManager: Undo system restored - {len(player.undo_system.position_history)} positions in history")
                    else:
                        print(
                            "GameSaveManager: WARNING - Player has no undo system to restore to")

                # Restore reputation system
                if 'reputation_state' in player_data and player_data['reputation_state']:
                    rep_data = player_data['reputation_state']
                    player.successful_deliveries_streak = rep_data.get(
                        'successful_deliveries_streak', 0)
                    player.had_first_late_delivery_today = rep_data.get(
                        'had_first_late_delivery_today', False)
                    player.daily_delivery_stats = rep_data.get('daily_delivery_stats', {
                        "on_time": 0, "early": 0, "late": 0, "canceled": 0, "lost": 0
                    })

                game._player = player
                print(
                    f"GameSaveManager: Player restored at position ({player.x}, {player.y})")

            # Restore weather state
            weather_data = game_state['weather_state']
            weather = game.get_weather()
            weather.current_condition = weather_data['current_condition']
            weather.current_intensity = weather_data['current_intensity']
            weather.city = weather_data['city']
            weather.start_time = weather_data['start_time']
            weather.conditions = weather_data['conditions']
            weather.transition_matrix = weather_data['transition_matrix']
            weather.bursts = weather_data['bursts']
            weather.meta = weather_data['meta']

            # Restore jobs inventory with enhanced data
            jobs_data = game_state['jobs_state']
            jobs = game.get_jobs()
            jobs._selected_index = jobs_data['selected_index']
            jobs._scroll_offset = jobs_data.get('scroll_offset', 0)
            jobs._visible_count = jobs_data.get('visible_count', 3)

            # Restore orders with correct constructor parameters - FIX THE ORDER RESTORATION
            print("GameSaveManager: Restoring orders...")
            from ..core.order import Order
            jobs._orders = []
            for order_data in jobs_data['orders']:
                try:
                    # Create Order with only the constructor parameters it accepts
                    order = Order(
                        id=order_data['id'],
                        pickup=order_data['pickup'],
                        dropoff=order_data['dropoff'],
                        payout=order_data['payout'],
                        deadline_iso=order_data['deadline_iso'],
                        weight=order_data['weight'],
                        priority=order_data['priority'],
                        release_time=order_data['release_time']
                        # Don't pass state, accepted_at, etc. to constructor
                    )

                    # Set state and timing attributes after creation
                    if 'state' in order_data:
                        order.state = order_data['state']
                    if 'accepted_at' in order_data:
                        order.accepted_at = order_data['accepted_at']
                    if 'picked_at' in order_data:
                        order.picked_at = order_data['picked_at']
                    if 'delivered_at' in order_data:
                        order.delivered_at = order_data['delivered_at']
                    if 'deadline_s' in order_data:
                        order.deadline_s = order_data['deadline_s']

                    # Restore tracking flags
                    if '_was_released' in order_data:
                        order._was_released = order_data['_was_released']
                    if '_last_debug_time' in order_data and order_data['_last_debug_time']:
                        order._last_debug_time = order_data['_last_debug_time']

                    jobs._orders.append(order)

                except Exception as e:
                    print(
                        f"GameSaveManager: Error restoring order {order_data.get('id', 'unknown')}: {e}")
                    continue  # Skip this order and continue with others

            print(f"GameSaveManager: Restored {len(jobs._orders)} orders")

            # Restore player inventory with debug state
            player_inv_data = game_state['player_inventory_state']
            player_inv = game.get_player_inventory()
            player_inv.capacity_weight = player_inv_data['capacity_weight']
            player_inv._debug_printed = player_inv_data.get(
                '_debug_printed', False)

            # Restore accepted orders
            player_inv.accepted = []
            accepted_order_ids = player_inv_data.get('accepted_orders', [])
            for order_id in accepted_order_ids:
                for order in jobs._orders:
                    if order.id == order_id:
                        player_inv.accepted.append(order)
                        print(
                            f"GameSaveManager: Restored accepted order: {order_id}")
                        break

            # Restore active order
            player_inv.active = None
            active_order_id = player_inv_data.get('active_order_id')
            if active_order_id:
                for order in jobs._orders:
                    if order.id == active_order_id:
                        player_inv.active = order
                        print(
                            f"GameSaveManager: Restored active order: {active_order_id}")
                        break

            # Restore scoreboard
            scoreboard_data = game_state['scoreboard_state']
            from ..game.scoreboard import Scoreboard
            game._scoreboard = Scoreboard(scoreboard_data['player_name'])
            game._scoreboard.score = scoreboard_data['score']

            print("GameSaveManager: Game state restoration complete")
            print("GameSaveManager: Game automatically resumed after loading")
            return True

        except Exception as e:
            print(f"GameSaveManager: Error restoring game state: {e}")
            import traceback
            traceback.print_exc()
            return False

    def list_saves(self) -> list:
        """List all available save files."""
        saves = []
        for save_file in self.save_dir.glob("*.sav"):
            try:
                # Get basic info about the save
                stat = save_file.stat()
                name = save_file.stem
                timestamp = datetime.fromtimestamp(stat.st_mtime)

                saves.append({
                    'name': name,
                    'file': save_file,
                    'timestamp': timestamp,
                    'size': stat.st_size
                })
            except Exception:
                continue

        # Sort by modification time (newest first)
        saves.sort(key=lambda x: x['timestamp'], reverse=True)
        return saves

    def delete_save(self, save_name: str) -> bool:
        """Delete a save file."""
        try:
            save_file = self.save_dir / f"{save_name}.sav"
            if save_file.exists():
                save_file.unlink()
                return True
        except Exception as e:
            print(f"Error deleting save: {e}")
        return False
