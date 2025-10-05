import pygame
import os
from .undo_sistem import UndoSystem


class Player:
    def __init__(self, start_x=0, start_y=0):
        self.x = start_x
        self.y = start_y
        self.target_x = start_x
        self.target_y = start_y

        # Animación
        self.is_moving = False
        self.move_progress = 0.0
        self.move_speed = 0.7  # Speed of movement (0.0 to 1.0)

        # Sprites - will be scaled dynamically
        self.base_sprite_size = 24  # Base size for scaling
        self.current_sprite_size = 24

        self.sprites = {}  # Sprites
        self.current_direction = "DOWN"  # Default direction
        self.animation_frame = 0
        self.animation_timer = 0
        self.animation_speed = 10  # Fraemes per animation step

        # Load sprites
        self.load_sprites()

        self.stamina = 100  # Player stamina
        self.reputation = 70  # Player reputation
        self.streak = 0  # Player streak
        self.weight = 8  # Current weight carried
        self.base_speed = 3.0  # v0 = 3 tiles/seg
        self.current_speed = 3.0  # Current speed (modified by conditions)
        self.resistance_state = "tired"  # "normal", "tired", "exhausted"

        # Stamina recovery system
        self.idle_time = 0.0  # Time spent not moving (in seconds)
        self.stamina_recovery_rate = 5.0  # Stamina recovered per second when idle
        self.stamina_recovery_interval = 1.0  # Recovery every 1 second

        # Recovery threshold system
        # Must recover to this amount to move again after exhaustion
        self.recovery_threshold = 30.0
        self.is_in_recovery_mode = False  # Track if player is in recovery mode
        self.was_exhausted = False  # Track if player was previously exhausted

        # Update speed based on initial stats
        self.update_move_speed()

        # Add undo system
        self.undo_system = UndoSystem(
            max_undo_steps=8, stamina_cost_per_undo=10.0)
        print(
            f"Player: Undo system initialized with {self.undo_system.max_steps} max steps")

    def load_sprites(self):
        # Store original sprites for scaling
        self.original_sprites = {}
        self.sprites = {}

        sprite_files = {
            "UP": "code/assets/player/bike_UP.PNG",
            "DOWN": "code/assets/player/bike_DOWN.png",
            "LEFT": "code/assets/player/bike_LEFT.PNG",
            "RIGHT": "code/assets/player/bike_RIGHT.PNG"
        }

        for direction, file_path in sprite_files.items():
            try:
                if os.path.exists(file_path):  # Check if file exists
                    # Load original image without scaling
                    original_image = pygame.image.load(file_path)
                    self.original_sprites[direction] = original_image

                    # Create initial scaled version
                    scaled_image = pygame.transform.scale(
                        original_image, (self.base_sprite_size, self.base_sprite_size))
                    self.sprites[direction] = scaled_image
                else:
                    # Create placeholder and store as original
                    placeholder = self.create_placeholder_sprite(
                        direction, self.base_sprite_size)
                    self.original_sprites[direction] = placeholder
                    self.sprites[direction] = placeholder

            except Exception as e:
                print(f"Player: Error loading player sprite {file_path}: {e}")
                placeholder = self.create_placeholder_sprite(
                    direction, self.base_sprite_size)
                self.original_sprites[direction] = placeholder
                self.sprites[direction] = placeholder

        # If don't have any sprites, create placeholders
        if not self.sprites:

            for direction in ["UP", "DOWN", "LEFT", "RIGHT"]:
                self.sprites[direction] = self.create_placeholder_sprite(
                    direction)

    def create_placeholder_sprite(self, direction, size=24):
        # Create scalable placeholder (was fixed size)
        surface = pygame.Surface(
            (size, size), pygame.SRCALPHA)

        # Colors for directions
        colors = {
            "UP": (0, 255, 0),      # Green
            "DOWN": (255, 0, 0),    # Red
            "LEFT": (0, 0, 255),    # Blue
            "RIGHT": (255, 255, 0)  # Yellow
        }

        color = colors.get(direction, (255, 255, 255))  # Default white
        center = size // 2

        pygame.draw.circle(surface, color, (center, center),
                           center - 2)  # Circle
        pygame.draw.circle(surface, (0, 0, 0),
                           (center, center), center - 2, 2)  # Border

        # Scale arrow proportionally
        arrow_size = max(4, size // 6)
        if direction == "UP":
            pygame.draw.polygon(surface, (0, 0, 0), [
                                (center, arrow_size),
                                (center-arrow_size, arrow_size*2),
                                (center+arrow_size, arrow_size*2)])
        elif direction == "DOWN":
            pygame.draw.polygon(surface, (0, 0, 0), [
                                (center, size-arrow_size),
                                (center-arrow_size, size-arrow_size*2),
                                (center+arrow_size, size-arrow_size*2)])
        elif direction == "LEFT":
            pygame.draw.polygon(surface, (0, 0, 0), [
                                (arrow_size, center),
                                (arrow_size*2, center-arrow_size),
                                (arrow_size*2, center+arrow_size)])
        elif direction == "RIGHT":
            pygame.draw.polygon(surface, (0, 0, 0), [
                                (size-arrow_size, center),
                                (size-arrow_size*2, center-arrow_size),
                                (size-arrow_size*2, center+arrow_size)])

        return surface

    def move_to(self, new_x, new_y, city, weather) -> bool:
        # Save current position before attempting move
        self.undo_system.save_position(self.x, self.y)

        if not self.is_moving:  # Only if not already moving

            # Check if player is in recovery mode (cannot move until threshold is met)
            if self.is_in_recovery_mode:
                if self.stamina < self.recovery_threshold:
                    print(
                        f"Player is in recovery mode - need {self.recovery_threshold} stamina to move (current: {self.stamina:.1f})")
                    return False
                else:
                    # Player has recovered enough, exit recovery mode
                    self.is_in_recovery_mode = False
                    self.was_exhausted = False
                    print(
                        f"Player recovered! Can move again (stamina: {self.stamina:.1f})")

            # Calculate current speed
            self.current_speed = self.calculate_speed(
                weather, city, self.x, self.y)

            # If speed is 0 (exhausted), cannot move
            if self.current_speed <= 0:
                print("Player is exhausted - cannot move!")
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
                f"Player: Speed={self.current_speed:.1f}, Distance={distance}, AnimTime={actual_animation_time:.3f}, AnimSpeed={self.move_speed:.3f}")
        else:
            self.move_speed = 0.0

    def update(self, delta_time=1/60):
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
            # Player is not moving - accumulate idle time
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
                            f"Player: Recovered {recovered:.1f} stamina from resting (idle for {recovery_cycles}s)")

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

    def can_move_to(self, new_x, new_y, city):
        # Check if the player can move to a position
        return (city.is_valid_position(new_x, new_y) and
                not city.is_blocked(new_x, new_y) and
                not self.is_moving)

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

    def update_move_speed(self):
        # Update move_speed based on current_speed
        if self.current_speed > 0:
            # A 60 FPS, 1 celda/seg = 1/60 de progreso por frame
            self.move_speed = min(
                1.0, self.current_speed / 60.0 * 10)  # Ajustar factor
        else:
            self.move_speed = 0.0

    def set_weight(self, new_weight):
        self.weight = new_weight  # Set weight directly

    def increase_weight(self, amount):
        self.weight += amount  # Increase weight by amount

    def decrease_weight(self, amount):
        self.weight = max(0, self.weight - amount)  # Dont go below 0

    def set_resistance_state(self, state):
        if state in ["normal", "tired", "exhausted"]:  # Valid states
            self.resistance_state = state  # Set state

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
                f"Player exhausted! Entering recovery mode - must recover to {self.recovery_threshold} stamina to move again")

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
                f"Recovery threshold reached! Player can move again (stamina: {self.stamina:.1f})")

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
                print(f"Player exhausted during recovery! Re-entering recovery mode")

        # Debug info
        actual_increase = self.stamina - old_stamina
        print(
            f"Stamina increased by {actual_increase:.1f} → {self.stamina:.1f} - State: {self.resistance_state} - Recovery Mode: {self.is_in_recovery_mode}")

        return actual_increase

    def undo_last_move(self) -> bool:
        """Undo the last move if possible"""
        if not self.undo_system.can_undo():
            print("Player: No moves to undo")
            return False

        # Check if player has enough stamina (if stamina system exists)
        stamina_cost = self.undo_system.get_stamina_cost()
        if hasattr(self, 'stamina') and self.stamina < stamina_cost:
            print(
                f"Player: Not enough stamina for undo (need {stamina_cost}, have {self.stamina})")
            return False

        success, prev_x, prev_y = self.undo_system.undo_last_move()

        if success:
            # Move player to previous position
            self.x = prev_x
            self.y = prev_y
            self.target_x = prev_x
            self.target_y = prev_y
            self.is_moving = False

            # Reset idle time when undoing (player just "moved")
            self.idle_time = 0.0

            # Consume stamina if system exists
            if hasattr(self, 'stamina'):
                self.stamina -= stamina_cost

            print(f"Player: Undid move to position ({prev_x}, {prev_y})")
            return True

        return False

    def get_stamina_info(self) -> dict:
        """Get stamina system information for UI display"""
        return {
            "stamina": self.stamina,
            "max_stamina": 100,
            "resistance_state": self.resistance_state,
            "idle_time": self.idle_time,
            "recovery_rate": self.stamina_recovery_rate,
            "time_to_next_recovery": max(0.0, self.stamina_recovery_interval - self.idle_time),
            "is_recovering": not self.is_moving and self.stamina < 100,
            "is_in_recovery_mode": self.is_in_recovery_mode,
            "recovery_threshold": self.recovery_threshold,
            "recovery_progress": self.stamina / self.recovery_threshold if self.is_in_recovery_mode else 1.0,
            "can_move": not self.is_in_recovery_mode or self.stamina >= self.recovery_threshold
        }

    def clear_undo_on_delivery(self):
        """Clear undo history when making a delivery"""
        self.undo_system.clear_history_on_delivery()

    def get_undo_info(self) -> dict:
        """Get undo system information for UI display"""
        return self.undo_system.get_info()
