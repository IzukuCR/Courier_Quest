from abc import ABC, abstractmethod
import pygame
import os


class AbstractAI(ABC):
    """
    Base abstract class for difficulty AI.
    Defines behavior modifiers for stamina, reputation, and player performance.
    """

    def __init__(self, start_x=0, start_y=0):

        self.x = start_x
        self.y = start_y
        self.target_x = start_x
        self.target_y = start_y

        # Animation
        self.is_moving = False
        self.move_progress = 0.0
        self.move_speed = 0.7  # Speed of movement (0.0 to 1.0)
        self.current_direction = "DOWN"

        # Core player-like attributes
        self.stamina = 100
        self.reputation = 70
        self.streak = 0
        self.base_speed = 3.0
        self.current_speed = 3.0
        self.weight = 0  # Start with 0 weight, not 8 (8 is the maximum capacity)
        self.resistance_state = "normal"

        # Stamina system
        self.idle_time = 0.0
        self.stamina_recovery_rate = 5.0
        self.stamina_recovery_interval = 1.0
        self.recovery_threshold = 30.0
        self.is_in_recovery_mode = False
        self.was_exhausted = False

        # Reputation system
        self.successful_deliveries_streak = 0
        self.had_first_late_delivery_today = False
        self.daily_delivery_stats = {
            "on_time": 0,
            "early": 0,
            "late": 0,
            "canceled": 0,
            "lost": 0
        }

        # Animation attributes
        self.animation_frame = 0
        self.animation_timer = 0
        self.animation_speed = 10

        # Sprite attributes
        self.base_sprite_size = 24
        self.current_sprite_size = 24
        self.sprites = {}
        self.original_sprites = {}

        # Update speed based on initial stats
        self.update_move_speed()

    def move_to(self, new_x, new_y, city, weather) -> bool:

        if not self.is_moving:  # Only if not already moving

            # Check if player is in recovery mode (cannot move until threshold is met)
            if self.is_in_recovery_mode:
                if self.stamina < self.recovery_threshold:
                    print(
                        f"AI is in recovery mode - need {self.recovery_threshold} stamina to move (current: {self.stamina:.1f})")
                    return False
                else:
                    # Player has recovered enough, exit recovery mode
                    self.is_in_recovery_mode = False
                    self.was_exhausted = False
                    print(
                        f"AI recovered! Can move again (stamina: {self.stamina:.1f})")

            # Calculate current speed
            self.current_speed = self.calculate_speed(
                weather, city, self.x, self.y)

            # If speed is 0 (exhausted), cannot move
            if self.current_speed <= 0:
                print("AI is exhausted - cannot move!")
                return False

            # Movement distance based on speed
            max_distance = self.calculate_movement_distance()

            # Calculate movement direction
            direction_x = 1 if new_x > self.x else (
                -1 if new_x < self.x else 0)
            direction_y = 1 if new_y > self.y else (
                -1 if new_y < self.y else 0)

            # Find final position considering obstacles
            final_x, final_y = self.find_final_position(
                self.x, self.y, direction_x, direction_y, max_distance, city
            )

            # Only move if there is a change in position
            if final_x != self.x or final_y != self.y:

                distance_moved = max(abs(final_x - self.x),
                                     abs(final_y - self.y))

                self.target_x = final_x
                self.target_y = final_y
                self.is_moving = True
                self.move_progress = 0.0

                # Reset idle time when starting to move
                self.idle_time = 0.0

                # Update move_speed based on distance
                self.update_move_speed_for_distance()

                # Update stamina after move
                self.update_stamina_after_move(distance_moved, weather, city)

                # Determine direction for animation
                if final_x > self.x:
                    self.current_direction = "RIGHT"
                elif final_x < self.x:
                    self.current_direction = "LEFT"
                elif final_y > self.y:
                    self.current_direction = "DOWN"
                elif final_y < self.y:
                    self.current_direction = "UP"

                return True

        return False

    def can_move_to(self, new_x, new_y, city):
        # Check if the player can move to a position
        return (city.is_valid_position(new_x, new_y) and
                not city.is_blocked(new_x, new_y) and
                not self.is_moving)

    def calculate_movement_distance(self):
        # High speed = more tiles per movement

        if self.current_speed < 1.0:
            return 0
        elif self.current_speed >= 1.0 and self.current_speed < 2.0:
            return 1  # Normal speed = 1 tile
        elif self.current_speed >= 2.0 and self.current_speed < 3.0:
            return 2  # High speed = 2 tiles
        elif self.current_speed >= 3.0 and self.current_speed < 4.0:
            return 3  # Very high speed = 3 tiles
        elif self.current_speed >= 4.0 and self.current_speed < 5.0:
            return 4  # Extreme speed = 4 tiles
        else:
            # Max 5 tiles per movement
            return min(5, int(self.current_speed // 3))

    def find_final_position(self, start_x, start_y, dir_x, dir_y, max_distance, city):

        current_x, current_y = start_x, start_y

        for step in range(1, max_distance + 1):  # From 1 to max_distance
            next_x = start_x + (dir_x * step)
            next_y = start_y + (dir_y * step)

            # Check if next position is valid and not blocked
            if (city.is_valid_position(next_x, next_y) and
                    not city.is_blocked(next_x, next_y)):
                current_x, current_y = next_x, next_y
            else:
                # If blocked, stop at previous position
                break

        return current_x, current_y

    def calculate_speed(self, weather, city, current_tile_x=None, current_tile_y=None):

        # v0 = base speed = 3.0
        v0 = self.base_speed

        # Mclima = weather speed multiplier
        mclima = weather.get_speed_multiplier() if weather else 1.0

        # Mpeso = max(0.8, 1 - 0.03 * weight)
        mpeso = max(0.8, 1.0 - 0.03 * self.weight)

        # Mrep = 1.03 if reputation ≥ 90, else 1.0
        mrep = 1.03 if self.reputation >= 90 else 1.0

        # Mresistencia based on resistance state
        resistance_multipliers = {
            "normal": 1.0,
            "tired": 0.8,
            "exhausted": 0.0
        }
        mresistencia = resistance_multipliers.get(self.resistance_state, 1.0)

        # Surface_weight of current tile
        surface_weight = 1.0  # Default
        if city and current_tile_x is not None and current_tile_y is not None:
            surface_weight = city.get_surface_weight(
                current_tile_x, current_tile_y)

        # Final speed calculation
        final_speed = v0 * mclima * mpeso * mrep * mresistencia * surface_weight

        return max(0.0, final_speed)  # Dont allow negative speed

    def get_speed_info(self, weather=None, city=None):
        """Obtener información detallada de velocidad para debug"""
        speed = self.calculate_speed(weather, city, self.x, self.y)

        mclima = weather.get_speed_multiplier() if weather else 1.0
        mpeso = max(0.8, 1.0 - 0.03 * self.weight)
        mrep = 1.03 if self.reputation >= 90 else 1.0
        mresistencia = {"normal": 1.0, "tired": 0.8,
                        "exhausted": 0.0}.get(self.resistance_state, 1.0)
        surface_weight = city.get_surface_weight(
            self.x, self.y) if city else 2.0

        distance = self.calculate_movement_distance()

        return {
            "final_speed": speed,
            "movement_distance": distance,
            "base_speed": self.base_speed,
            "weather_multiplier": mclima,
            "weight_multiplier": mpeso,
            "reputation_multiplier": mrep,
            "resistance_multiplier": mresistencia,
            "surface_multiplier": surface_weight,
            "current_weight": self.weight,
            "reputation": self.reputation,
            "resistance_state": self.resistance_state
        }

    def update_move_speed(self):
        # Update move_speed based on current_speed
        if self.current_speed > 0:
            # A 60 FPS, 1 celda/seg = 1/60 de progreso por frame
            self.move_speed = min(
                1.0, self.current_speed / 60.0 * 10)  # Ajustar factor
        else:
            self.move_speed = 0.0

    def update_move_speed_for_distance(self):
        # Calculate movement distance
        distance = max(abs(self.target_x - self.x),
                       abs(self.target_y - self.y))

        if distance > 0 and self.current_speed > 0:
            # Base animation time - reduced values to make movements faster overall
            # The current 2-tile speed becomes the new 1-tile speed
            if distance == 1:
                # Faster for single tile (was 0.4, now uses old 2-tile speed)
                base_animation_time = 0.25
            elif distance == 2:
                # Even faster for 2-tile movements (was 0.5)
                base_animation_time = 0.35
            elif distance >= 3:
                # Fastest for longer movements (was 0.6)
                base_animation_time = 0.45
            else:
                base_animation_time = 0.2   # Fallback - very fast

            # Scale animation time based on speed - higher speed = faster animation
            # But keep the distance-based difference
            speed_multiplier = self.current_speed / 3.0  # Normalize to base speed of 3.0
            actual_animation_time = base_animation_time / \
                max(0.5, speed_multiplier)

            # Convert to progress per frame (60 FPS)
            self.move_speed = min(1.0, 1.0 / (actual_animation_time * 60))

            # Debug info to see the animation speed difference
            print(
                f"AI: Speed={self.current_speed:.1f}, Distance={distance}, AnimTime={actual_animation_time:.3f}, AnimSpeed={self.move_speed:.3f}")
        else:
            self.move_speed = 0.0

    def calculate_stamina_loss(self, distance_moved=1, weather=None, city=None):
        # Base stamina loss per cell moved
        base_stamina_loss = -0.5 * distance_moved

        # If weight > 3, additional penalty per cell (-0.2 per extra weight unit)
        weight_penalty = 0.0
        if self.weight > 3:
            weight_penalty = -0.2 * (self.weight - 3) * distance_moved

        # Weather impact on stamina
        weather_penalty = 0.0
        if weather and hasattr(weather, 'current_condition'):
            weather_impacts = {
                "rain": -0.1 * distance_moved,
                "rain_light": -0.1 * distance_moved,
                "wind": -0.1 * distance_moved,
                "storm": -0.3 * distance_moved,
                "heat": -0.2 * distance_moved,
                "cold": -0.1 * distance_moved,
            }
            weather_penalty = weather_impacts.get(
                weather.current_condition, 0.0)

        # Total stamina loss
        total_stamina_loss = base_stamina_loss + weight_penalty + weather_penalty

        return total_stamina_loss

    def update_stamina_after_move(self, distance_moved=1, weather=None, city=None):
        # Calculate stamina loss based on distance moved and conditions
        stamina_loss = self.calculate_stamina_loss(
            distance_moved, weather, city)  # get stamina loss

        # stamina_loss is negative
        old_stamina = self.stamina
        self.stamina = max(0, min(100, self.stamina + stamina_loss))

        # Check if player just became exhausted (stamina reached 0)
        if old_stamina > 0 and self.stamina <= 0:
            self.is_in_recovery_mode = True
            self.was_exhausted = True
            print(
                f"AI exhausted! Entering recovery mode - must recover to {self.recovery_threshold} stamina to move again")

        # Update resistance state based on new stamina
        if self.stamina > 30:
            self.set_resistance_state("normal")
        elif self.stamina <= 30 and self.stamina > 0:
            self.set_resistance_state("tired")
        else:
            self.set_resistance_state("exhausted")

        # Debug info
        print(
            f"Stamina: {self.stamina:.1f} (lost {abs(stamina_loss):.1f}) - State: {self.resistance_state}")

    def recover_stamina(self, amount=5):
        old_stamina = self.stamina

        # Increase stamina by amount, capped at 100
        self.stamina = max(0, min(100, self.stamina + amount))

        # Check if player exits recovery mode and update resistance state immediately
        if self.is_in_recovery_mode and self.stamina >= self.recovery_threshold:
            self.is_in_recovery_mode = False
            self.was_exhausted = False
            print(
                f"Recovery threshold reached! AI can move again (stamina: {self.stamina:.1f})")

        # Update resistance state based on new stamina - do this after checking recovery mode
        if self.stamina > 30:
            self.set_resistance_state("normal")
        elif self.stamina <= 30 and self.stamina > 0:
            self.set_resistance_state("tired")
        else:
            self.set_resistance_state("exhausted")
            # If stamina drops to 0, enter recovery mode
            if not self.is_in_recovery_mode and old_stamina > 0:
                self.is_in_recovery_mode = True
                self.was_exhausted = True
                print(f"AI exhausted during recovery! Re-entering recovery mode")

        # Debug info
        actual_increase = self.stamina - old_stamina
        print(
            f"Stamina increased by {actual_increase:.1f} → {self.stamina:.1f} - State: {self.resistance_state} - Recovery Mode: {self.is_in_recovery_mode}")

        return actual_increase

    def update(self, delta_time=1/60):
        # Check if game is paused - don't update stamina recovery if paused
        from .game import Game
        game = Game()
        is_paused = game.is_paused() if hasattr(game, 'is_paused') else False

        # update movement and animation
        if self.is_moving:
            # Update movement progress
            self.move_progress += self.move_speed * delta_time * 60  # Normalize FPS

            if self.move_progress >= 1.0:
                # Movement complete
                self.x = self.target_x
                self.y = self.target_y
                self.is_moving = False
                self.move_progress = 0.0
        else:
            # Player is not moving - accumulate idle time ONLY if game is not paused
            if not is_paused:
                self.idle_time += delta_time

                # Check if enough idle time has passed for stamina recovery
                if self.idle_time >= self.stamina_recovery_interval:
                    # Calculate how many recovery intervals have passed
                    recovery_cycles = int(
                        self.idle_time // self.stamina_recovery_interval)

                    if recovery_cycles > 0:
                        # Recover stamina
                        stamina_to_recover = self.stamina_recovery_rate * recovery_cycles
                        old_stamina = self.stamina
                        recovered = self.recover_stamina(stamina_to_recover)

                        # Reset idle time, keeping any fractional remainder
                        self.idle_time = self.idle_time % self.stamina_recovery_interval

                        if recovered > 0:
                            print(
                                f"AI: Recovered {recovered:.1f} stamina from resting (idle for {recovery_cycles}s)")

        # Update animation (always, even if not moving)
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            # 4 frames of animation
            self.animation_frame = (self.animation_frame + 1) % 4
            self.animation_timer = 0

    def get_screen_position(self, cell_size, map_offset_x, map_offset_y):
        # Get screen position with smooth interpolation
        if self.is_moving:
            # Smooth interpolation during movement
            current_x = self.x + (self.target_x - self.x) * self.move_progress
            current_y = self.y + (self.target_y - self.y) * self.move_progress
        else:
            current_x = self.x
            current_y = self.y

        screen_x = map_offset_x + current_x * cell_size + (cell_size // 2)
        screen_y = map_offset_y + current_y * cell_size + (cell_size // 2)

        return int(screen_x), int(screen_y)

    def update_sprite_scale(self, cell_size):
        """Update sprite scaling based on current cell size"""
        # Calculate appropriate sprite size (80% of cell size)
        new_size = max(16, int(cell_size * 0.8))

        if new_size != self.current_sprite_size:
            self.current_sprite_size = new_size

            # Rescale all sprites from originals
            for direction, original in self.original_sprites.items():
                if original:
                    self.sprites[direction] = pygame.transform.scale(
                        original, (new_size, new_size))

    def draw(self, screen, cell_size, map_offset_x, map_offset_y):
        # Update sprite scale if needed
        self.update_sprite_scale(cell_size)

        # Draw player
        screen_x, screen_y = self.get_screen_position(
            cell_size, map_offset_x, map_offset_y)

        # Draw sprite
        sprite = self.sprites.get(self.current_direction)
        if sprite:
            sprite_rect = sprite.get_rect()
            sprite_rect.center = (screen_x, screen_y)
            screen.blit(sprite, sprite_rect)
        else:
            # Fallback: scaled circle
            radius = max(8, cell_size // 3)
            pygame.draw.circle(screen, (255, 0, 0),
                               (screen_x, screen_y), radius)

    def set_weight(self, new_weight):
        self.weight = new_weight  # Set weight directly

    def increase_weight(self, amount):
        self.weight += amount  # Increase weight by amount

    def decrease_weight(self, amount):
        self.weight = max(0, self.weight - amount)  # Dont go below 0

    def set_resistance_state(self, state):
        if state in ["normal", "tired", "exhausted"]:  # Valid states
            self.resistance_state = state  # Set state

    def update_reputation_delivery(self, delivery_time, deadline, is_canceled=False, is_lost=False, overtime_seconds=0):
        """
        Update reputation based on delivery outcome

        Args:
            delivery_time: Time when delivery was completed (elapsed game time)
            deadline: Deadline for the delivery (elapsed game time)
            is_canceled: Whether the order was canceled
            is_lost: Whether the package was lost/expired
            overtime_seconds: How many seconds late the delivery was (if applicable)

        Returns:
            dict: Information about reputation change
        """
        old_reputation = self.reputation
        reputation_change = 0
        message = ""

        if is_canceled:
            # Canceling an accepted order
            reputation_change = -4
            message = "Order canceled: -4 reputation"
            self.successful_deliveries_streak = 0
            self.daily_delivery_stats["canceled"] += 1

        elif is_lost:
            # Losing/expiring a package - use overtime calculation for penalty
            # but track as "lost" in statistics
            self.daily_delivery_stats["lost"] += 1
            self.successful_deliveries_streak = 0

            # Apply half penalty for first late delivery if reputation ≥ 85
            apply_half_penalty = (
                self.reputation >= 85 and not self.had_first_late_delivery_today)

            # Use explicit overtime for penalties (just like late deliveries)
            if overtime_seconds <= 30:
                base_penalty = -2
                penalty = base_penalty / 2 if apply_half_penalty else base_penalty
                reputation_change = penalty
                message = f"Expired package (overtime {overtime_seconds:.1f}s): {penalty} reputation"
            elif overtime_seconds <= 120:
                base_penalty = -5
                penalty = base_penalty / 2 if apply_half_penalty else base_penalty
                reputation_change = penalty
                message = f"Expired package (overtime {overtime_seconds:.1f}s): {penalty} reputation"
            else:
                base_penalty = -10
                penalty = base_penalty / 2 if apply_half_penalty else base_penalty
                reputation_change = penalty
                message = f"Expired package (overtime {overtime_seconds:.1f}s): {penalty} reputation"

            # Mark first late delivery used
            if apply_half_penalty:
                self.had_first_late_delivery_today = True

        else:
            # Normal delivery - check timing
            # Calculate time remaining (could be negative if late)
            time_remaining = deadline - delivery_time
            # 20% of the total deadline time
            early_threshold = (
                deadline - (delivery_time - overtime_seconds)) * 0.2
            is_late = overtime_seconds > 0

            print(
                f"DEBUG REPUTATION: time_remaining={time_remaining:.1f}, early_threshold={early_threshold:.1f}, overtime={overtime_seconds:.1f}s")

            if not is_late and time_remaining >= early_threshold:
                # Early delivery (≥20% before deadline)
                reputation_change = 5
                message = "Early delivery: +5 reputation"
                self.successful_deliveries_streak += 1
                self.daily_delivery_stats["early"] += 1

            elif not is_late:
                # On-time delivery
                reputation_change = 3
                message = "On-time delivery: +3 reputation"
                self.successful_deliveries_streak += 1
                self.daily_delivery_stats["on_time"] += 1

            else:
                # Late delivery - use explicit overtime calculation
                self.daily_delivery_stats["late"] += 1

                # Apply half penalty for first late delivery if reputation ≥ 85
                apply_half_penalty = (
                    self.reputation >= 85 and not self.had_first_late_delivery_today)

                # Use exact overtime for penalties
                if overtime_seconds <= 30:
                    base_penalty = -2
                    penalty = base_penalty / 2 if apply_half_penalty else base_penalty
                    reputation_change = penalty
                    message = f"Slightly late delivery ({overtime_seconds:.1f}s): {penalty} reputation"
                elif overtime_seconds <= 120:
                    base_penalty = -5
                    penalty = base_penalty / 2 if apply_half_penalty else base_penalty
                    reputation_change = penalty
                    message = f"Late delivery ({overtime_seconds:.1f}s): {penalty} reputation"
                else:
                    base_penalty = -10
                    penalty = base_penalty / 2 if apply_half_penalty else base_penalty
                    reputation_change = penalty
                    message = f"Very late delivery ({overtime_seconds:.1f}s): {penalty} reputation"

                # Mark first late delivery used
                if apply_half_penalty:
                    self.had_first_late_delivery_today = True

                # Reset streak on late delivery
                self.successful_deliveries_streak = 0

        # Check for streak bonus (3 successful deliveries without penalties)
        streak_bonus = 0
        if self.successful_deliveries_streak == 3:
            streak_bonus = 2
            message += " + Streak bonus: +2 reputation"
            # Don't reset streak, allow it to keep counting for visibility

        # Apply reputation change with minimum safety
        total_change = reputation_change + streak_bonus

        # IMPORTANT FIX: Ensure we never lose more than 20% reputation in one go
        if total_change < 0:
            # Ensure there's always at least a small reputation loss for negative events
            # But no more than 20% of current reputation
            min_loss = -1.0  # At minimum, always lose 1 point
            max_loss = min(abs(total_change), max(1.0, old_reputation * 0.20))

            # If reputation is already at or near 0, use minimal loss
            if old_reputation <= 5.0:
                actual_loss = min_loss
            else:
                actual_loss = max_loss

            # Never reduce below 20 (game over threshold) from a single event
            if old_reputation - actual_loss < 20.0 and old_reputation >= 20.0:
                actual_loss = old_reputation - 20.0
                print(
                    f"DEBUG REPUTATION: Limiting loss to prevent dropping below game over threshold")

            print(
                f"DEBUG REPUTATION: Processing loss: raw={total_change}, adjusted to -{actual_loss:.1f}")
            total_change = -actual_loss

        print(
            f"DEBUG REPUTATION: old={old_reputation:.1f}, change={total_change:.1f}")
        self.add_reputation(total_change)

        new_reputation = self.reputation
        print(
            f"DEBUG REPUTATION: new={new_reputation:.1f}, absolute loss={old_reputation - new_reputation:.1f}")

        # Check game over condition
        game_over = self.reputation < 20

        return {
            "old_reputation": old_reputation,
            "new_reputation": self.reputation,
            "change": total_change,
            "streak": self.successful_deliveries_streak,
            "message": message,
            "game_over": game_over
        }

    def get_reputation(self) -> float:
        """Get current reputation value"""
        return self.reputation

    def set_reputation(self, value: float):
        """Set reputation value (0-100)"""
        self.reputation = max(0.0, min(100.0, value))

    def add_reputation(self, amount: float):
        """Add to reputation value with improved safeguards"""
        old_rep = self.reputation

        # Calculate new reputation with min/max bounds
        new_rep = max(0.0, min(100.0, self.reputation + amount))

        # Special case: if reputation was already at or near zero, and we're trying to decrease it further
        if amount < 0 and old_rep < 5.0:
            # Keep at the current value or ensure it's at least 1
            new_rep = max(1.0, old_rep)
            print(
                f"DEBUG REPUTATION: Already at minimal reputation, keeping at {new_rep}")

        # Final assignment
        self.reputation = new_rep

        # Debug information
        if amount != 0:
            print(
                f"DEBUG REPUTATION: Final adjustment: {old_rep:.1f} → {self.reputation:.1f} (change: {self.reputation - old_rep:.1f})")

    def reset_daily_reputation_tracking(self):
        """Reset daily tracking variables and ensure reputation is not 0 (call at start of new game day)"""
        self.had_first_late_delivery_today = False
        self.daily_delivery_stats = {
            "on_time": 0,
            "early": 0,
            "late": 0,
            "canceled": 0,
            "lost": 0
        }

        # Ensure reputation is not 0 at game start - should always start at 70
        if self.reputation < 20.0:
            self.reputation = 70.0
            print(
                f"DEBUG REPUTATION: Reset reputation to {self.reputation} for new game")

    def get_payment_multiplier(self):
        """Calculate payment multiplier based on reputation"""
        # 5% bonus for reputation ≥ 90
        if self.reputation >= 90:
            return 1.05
        return 1.0

    def is_game_over_by_reputation(self):
        """Check if reputation has dropped below game-over threshold"""
        return self.reputation < 20

    def get_reputation_stats(self):
        """Get comprehensive stats about reputation and delivery performance"""
        return {
            "reputation": self.reputation,
            "streak": self.successful_deliveries_streak,
            "payment_multiplier": self.get_payment_multiplier(),
            "had_first_late_delivery_today": self.had_first_late_delivery_today,
            "daily_stats": self.daily_delivery_stats,
            "excellence_bonus": self.reputation >= 90,
            "first_late_discount": self.reputation >= 85 and not self.had_first_late_delivery_today,
            "game_over": self.reputation < 20
        }

    def is_game_over_by_reputation(self):
        """Check if reputation has dropped below game-over threshold"""
        if self.reputation < 20:
            return True
        return False

    @abstractmethod
    def run_bot_logic(self, game, delta_time):
        """Run AI logic for movement and actions"""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return difficulty name"""
        pass


class EasyAI(AbstractAI):
    """
    Easy difficulty AI using random decision making.
    
    This AI uses simple probabilistic logic and queue-based movement.
    It randomly selects jobs and moves in random directions, avoiding
    only obvious obstacles.
    
    Complexity Analysis:
    - Job selection: O(n) where n is number of available jobs
    - Movement: O(1) per direction choice
    - Queue operations: O(1) for enqueue/dequeue
    
    Data Structures Used:
    - List: For storing available jobs and directions
    - Queue (FIFO): For managing movement direction sequence
    """
    
    def __init__(self, start_x=0, start_y=0):
        """
        Initialize Easy AI with random movement capabilities.
        
        Args:
            start_x (int): Starting x position on the map
            start_y (int): Starting y position on the map
        """
        super().__init__(start_x, start_y)
        
        # AI-specific inventory system
        from collections import deque
        self.accepted_orders = []  # List to store accepted orders
        self.active_order = None   # Currently active order
        self.direction_queue = deque(maxlen=5)  # FIFO queue for movement directions
        
        # Decision making timers
        self.decision_timer = 0.0
        self.decision_interval = 2.0  # Make decision every 2 seconds
        self.movement_timer = 0.0
        self.movement_interval = 0.8  # Move every 0.8 seconds (slower for better visibility)
        
        # Random behavior configuration
        self.direction_change_probability = 0.15  # 15% chance for random move (reduced from 30%)
        self.job_selection_timer = 0.0
        self.job_selection_interval = 3.0  # Check for jobs every 3 seconds (reduced from 5)
        
        # Current target (if any)
        self.target_position = None
        self.target_type = None  # "pickup" or "dropoff"
        
    def get_name(self):
        """Return AI difficulty name."""
        return "Easy"
    
    def _select_random_job(self, game):
        """
        Randomly select an available job from the jobs inventory.
        
        Uses random selection from a list of available jobs.
        
        Complexity: O(n) where n is number of available jobs
        
        Args:
            game: The game instance to access job inventory
            
        Returns:
            Order or None: Randomly selected order if available
        """
        import random
        
        jobs_inventory = game.get_jobs()
        game_time = game.get_game_time()
        
        # Get all selectable jobs
        available_jobs = jobs_inventory.selectable(game_time)
        
        if not available_jobs:
            return None
        
        # Random selection from available jobs - O(1) operation on list
        selected_job = random.choice(available_jobs)
        
        return selected_job
    
    def _accept_job(self, game, order):
        """
        Accept a job and add it to AI's inventory.
        
        Args:
            game: The game instance
            order: The order to accept
            
        Returns:
            bool: True if job was accepted successfully
        """
        if not order:
            return False
        
        # Get current elapsed game time
        game_time_remaining = game.get_game_time()
        elapsed_game_time = game._game_time_limit_s - game_time_remaining
        
        # Mark as accepted
        order.state = "accepted"
        order.accepted_at = elapsed_game_time
        
        # Set deadline based on priority
        if order.priority == 0:
            base_time = 120
        elif order.priority == 1:
            base_time = 90
        else:
            base_time = 60
        
        order.deadline_s = elapsed_game_time + base_time
        
        # Add to accepted orders list
        if order not in self.accepted_orders:
            self.accepted_orders.append(order)
        
        # Set as active if no active order
        if self.active_order is None:
            self.active_order = order
            self.target_position = order.pickup
            self.target_type = "pickup"
            distance = abs(self.x - order.pickup[0]) + abs(self.y - order.pickup[1])
            print(f"[EasyAI] Accepted job {order.id} (Priority {order.priority}) - heading to pickup at {order.pickup} (distance: {distance} tiles)")
        else:
            print(f"[EasyAI] Accepted additional job {order.id} (Priority {order.priority}) - will handle after current job")
        
        return True
    
    def _get_random_direction(self, game):
        """
        Get a random valid movement direction.
        
        Uses queue to maintain recent directions and avoid immediate backtracking.
        
        Complexity: O(1) per direction check
        
        Args:
            game: The game instance to access city map
            
        Returns:
            tuple: (dx, dy) direction vector or None
        """
        import random
        
        city = game.get_city()
        
        # All possible directions: up, down, left, right
        all_directions = [
            (0, -1),   # UP
            (0, 1),    # DOWN
            (-1, 0),   # LEFT
            (1, 0),    # RIGHT
        ]
        
        # Shuffle to randomize
        random.shuffle(all_directions)
        
        # Try each direction until we find a valid one
        for dx, dy in all_directions:
            new_x = self.x + dx
            new_y = self.y + dy
            
            # Check if position is valid and not blocked
            if city.is_valid_position(new_x, new_y) and not city.is_blocked(new_x, new_y):
                return (dx, dy)
        
        # No valid direction found
        return None
    
    def _move_towards_target(self, game, target_pos):
        """
        Make a movement that generally moves towards target.
        
        Uses probabilistic approach: 85% chance to move towards target,
        15% chance to move randomly (to avoid getting stuck).
        
        Complexity: O(1)
        
        Args:
            game: The game instance
            target_pos: (x, y) tuple of target position
            
        Returns:
            bool: True if movement was attempted
        """
        import random
        
        if not target_pos:
            return False
        
        target_x, target_y = target_pos
        city = game.get_city()
        weather = game.get_weather()
        
        # Calculate general direction to target
        dx = 0 if target_x == self.x else (1 if target_x > self.x else -1)
        dy = 0 if target_y == self.y else (1 if target_y > self.y else -1)
        
        # 85% chance to move towards target, 15% chance to move randomly (to avoid getting stuck)
        if random.random() < 0.85 and (dx != 0 or dy != 0):
            # Try to move towards target
            # Prioritize the direction with larger distance
            distance_x = abs(target_x - self.x)
            distance_y = abs(target_y - self.y)
            
            if dx != 0 and dy != 0:
                # Need to move in both directions - choose the one with larger distance
                if distance_x > distance_y:
                    move_dx, move_dy = dx, 0
                elif distance_y > distance_x:
                    move_dx, move_dy = 0, dy
                else:
                    # Equal distance - randomly choose one
                    if random.random() < 0.5:
                        move_dx, move_dy = dx, 0
                    else:
                        move_dx, move_dy = 0, dy
            else:
                move_dx, move_dy = dx, dy
            
            new_x = self.x + move_dx
            new_y = self.y + move_dy
            
            # Check if valid
            if city.is_valid_position(new_x, new_y) and not city.is_blocked(new_x, new_y):
                return self.move_to(new_x, new_y, city, weather)
            else:
                # Target direction is blocked, try the other direction
                if move_dx != 0 and dy != 0:
                    # Was trying to move in x, try y
                    alt_x = self.x
                    alt_y = self.y + dy
                    if city.is_valid_position(alt_x, alt_y) and not city.is_blocked(alt_x, alt_y):
                        return self.move_to(alt_x, alt_y, city, weather)
                elif move_dy != 0 and dx != 0:
                    # Was trying to move in y, try x
                    alt_x = self.x + dx
                    alt_y = self.y
                    if city.is_valid_position(alt_x, alt_y) and not city.is_blocked(alt_x, alt_y):
                        return self.move_to(alt_x, alt_y, city, weather)
        
        # Random movement fallback (when probability fails or blocked)
        direction = self._get_random_direction(game)
        if direction:
            dx, dy = direction
            new_x = self.x + dx
            new_y = self.y + dy
            return self.move_to(new_x, new_y, city, weather)
        
        return False
    
    def _check_pickup_delivery(self, game):
        """
        Check if AI is at pickup or delivery location and handle it.
        
        Complexity: O(1)
        
        Args:
            game: The game instance
            
        Returns:
            str or None: Status message if action was taken
        """
        if not self.active_order:
            return None
        
        game_time_remaining = game.get_game_time()
        elapsed_game_time = game._game_time_limit_s - game_time_remaining
        
        # Check pickup
        if self.active_order.state == "accepted":
            pickup_x, pickup_y = self.active_order.pickup
            distance = max(abs(self.x - pickup_x), abs(self.y - pickup_y))
            
            if distance <= 1:  # Adjacent or at location
                # Pick up the package
                if self.weight + self.active_order.weight <= 8.0:
                    self.active_order.state = "carrying"
                    self.active_order.picked_at = elapsed_game_time
                    self.weight += self.active_order.weight
                    
                    # Update target to dropoff
                    self.target_position = self.active_order.dropoff
                    self.target_type = "dropoff"
                    
                    new_distance = abs(self.x - self.active_order.dropoff[0]) + abs(self.y - self.active_order.dropoff[1])
                    print(f"[EasyAI] ✓ Picked up {self.active_order.id} - Now heading to dropoff at {self.active_order.dropoff} (distance: {new_distance} tiles)")
                    return f"Package {self.active_order.id} picked up"
                else:
                    print(f"[EasyAI] ✗ Cannot pick up {self.active_order.id} - overweight (current: {self.weight:.1f}, package: {self.active_order.weight:.1f})")
        
        # Check delivery
        elif self.active_order.state == "carrying":
            dropoff_x, dropoff_y = self.active_order.dropoff
            distance = max(abs(self.x - dropoff_x), abs(self.y - dropoff_y))
            
            if distance <= 1:  # Adjacent or at location
                # Deliver the package
                deadline = getattr(self.active_order, 'deadline_s', 0)
                overtime_seconds = max(0, elapsed_game_time - deadline)
                
                # Update reputation based on delivery time
                rep_result = self.update_reputation_delivery(
                    elapsed_game_time, 
                    deadline,
                    overtime_seconds=overtime_seconds
                )
                
                # Calculate payout with multiplier
                payment_multiplier = self.get_payment_multiplier()
                payout = self.active_order.payout * payment_multiplier
                
                # Reduce weight
                self.weight = max(0, self.weight - self.active_order.weight)
                
                # Remove from accepted orders
                if self.active_order in self.accepted_orders:
                    self.accepted_orders.remove(self.active_order)
                
                delivered_id = self.active_order.id
                timing_msg = "on time" if overtime_seconds == 0 else f"{overtime_seconds:.0f}s late"
                print(f"[EasyAI] ✓ Delivered {delivered_id} ({timing_msg}) - Earned ${payout:.0f} - Reputation: {self.reputation:.1f}")
                
                # Clear active order and target
                self.active_order = None
                self.target_position = None
                self.target_type = None
                
                # Select next order if available
                if self.accepted_orders:
                    self.active_order = self.accepted_orders[0]
                    self.target_position = self.active_order.pickup if self.active_order.state == "accepted" else self.active_order.dropoff
                    self.target_type = "pickup" if self.active_order.state == "accepted" else "dropoff"
                    print(f"[EasyAI] → Next job: {self.active_order.id} - heading to {self.target_type}")
                else:
                    print(f"[EasyAI] → All jobs completed, looking for new jobs...")
                
                return f"Delivered {delivered_id}"
        
        return None

    def run_bot_logic(self, game, delta_time):
        """
        Main AI logic loop for Easy difficulty.
        
        This method implements random decision-making with basic queue-based
        movement. The AI:
        1. Randomly selects available jobs
        2. Moves towards targets with some randomness
        3. Uses FIFO queue for direction management
        
        Time Complexity: O(n) where n is number of available jobs
        Space Complexity: O(k) where k is queue size (constant at 5)
        
        Args:
            game: The game instance containing all game state
            delta_time (float): Time elapsed since last update in seconds
        """
        # Update AI state (stamina recovery, animation, etc.)
        self.update(delta_time)
        
        # Don't make decisions or move if game is paused
        if game.is_paused():
            return
        
        # Update timers
        self.decision_timer += delta_time
        self.movement_timer += delta_time
        self.job_selection_timer += delta_time
        
        # Check for pickup/delivery at current position
        self._check_pickup_delivery(game)
        
        # Job selection logic - try to get a job if we don't have one
        # Try immediately if no active order, otherwise wait for interval
        should_select_job = False
        if self.active_order is None:
            should_select_job = True  # Always try to get a job if we have none
        elif self.job_selection_timer >= self.job_selection_interval:
            should_select_job = True
            self.job_selection_timer = 0.0
        
        if should_select_job:
            # Only accept new jobs if we have capacity
            if len(self.accepted_orders) < 3 and self.weight < 8.0:
                job = self._select_random_job(game)
                if job:
                    self._accept_job(game, job)
        
        # Movement logic - only move if not currently animating movement
        if self.movement_timer >= self.movement_interval and not self.is_moving:
            self.movement_timer = 0.0
            
            # If we have a target, move towards it
            if self.target_position:
                # Check if we're already at or very close to target
                distance_to_target = max(
                    abs(self.x - self.target_position[0]),
                    abs(self.y - self.target_position[1])
                )
                
                if distance_to_target <= 1:
                    # We're at the target - pickup/delivery should handle next step
                    # Just stay here, don't move randomly
                    pass
                else:
                    # Move towards the target
                    self._move_towards_target(game, self.target_position)
            else:
                # No target - wander randomly
                direction = self._get_random_direction(game)
                if direction:
                    city = game.get_city()
                    weather = game.get_weather()
                    dx, dy = direction
                    new_x = self.x + dx
                    new_y = self.y + dy
                    self.move_to(new_x, new_y, city, weather)


class MediumAI(AbstractAI):
    def get_name(self): return "Medium"

    def run_bot_logic(self, game, delta_time):
       # Simple AI logic for Medium difficulty
        pass


class HardAI(AbstractAI):
    def get_name(self): return "Hard"

    def run_bot_logic(self, game, delta_time):
       # Simple AI logic for Hard difficulty
        pass
