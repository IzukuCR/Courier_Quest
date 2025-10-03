import pygame
import os


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

        # Update speed based on initial stats
        self.update_move_speed()

    def load_sprites(self):

        sprite_files = {
            "UP": "code/assets/player/bike_UP.PNG",
            "DOWN": "code/assets/player/bike_DOWN.png",
            "LEFT": "code/assets/player/bike_LEFT.PNG",
            "RIGHT": "code/assets/player/bike_RIGHT.PNG"
        }

        for direction, file_path in sprite_files.items():
            try:
                if os.path.exists(file_path):  # Check if file exists
                    image = pygame.image.load(file_path)  # Load image

                    scaled_image = pygame.transform.scale(
                        image, (24, 24))  # Change size of sprite
                    # Store in dictionary
                    self.sprites[direction] = scaled_image

                else:
                    self.sprites[direction] = self.create_placeholder_sprite(
                        direction)  # Create placeholder if file not found

            except Exception as e:
                print(f"Player: Error loading player sprite {file_path}: {e}")
                self.sprites[direction] = self.create_placeholder_sprite(
                    direction)

        # If don't have any sprites, create placeholders
        if not self.sprites:

            for direction in ["UP", "DOWN", "LEFT", "RIGHT"]:
                self.sprites[direction] = self.create_placeholder_sprite(
                    direction)

    def create_placeholder_sprite(self, direction):
        # Create a colored circle if sprite not found
        size = 24
        surface = pygame.Surface(
            (size, size), pygame.SRCALPHA)  # Transparent surface

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

        # Small arrow to indicate direction
        if direction == "UP":
            pygame.draw.polygon(surface, (0, 0, 0), [
                                (center, 6), (center-4, 14), (center+4, 14)])  # Arrow
        elif direction == "DOWN":
            pygame.draw.polygon(surface, (0, 0, 0), [
                                # Arrow
                                (center, size-6), (center-4, size-14), (center+4, size-14)])
        elif direction == "LEFT":
            pygame.draw.polygon(surface, (0, 0, 0), [
                                (6, center), (14, center-4), (14, center+4)])  # Arrow
        elif direction == "RIGHT":
            pygame.draw.polygon(surface, (0, 0, 0), [
                                # Arrow
                                (size-6, center), (size-14, center-4), (size-14, center+4)])

        return surface

    def move_to(self, new_x, new_y, city, weather=None):

        if not self.is_moving:  # Solo si no se está moviendo

            # Calcular velocidad actual
            self.current_speed = self.calculate_speed(
                weather, city, self.x, self.y)

            # Si velocidad es 0 (exhausto), no puede moverse
            if self.current_speed <= 0:
                print("Player is exhausted - cannot move!")
                return False

            # ✅ NUEVO: Calcular cuántas casillas puede moverse basado en velocidad
            max_distance = self.calculate_movement_distance()

            # Calcular dirección del movimiento
            direction_x = 1 if new_x > self.x else (
                -1 if new_x < self.x else 0)
            direction_y = 1 if new_y > self.y else (
                -1 if new_y < self.y else 0)

            # ✅ NUEVO: Encontrar la posición final válida dentro del rango
            final_x, final_y = self.find_final_position(
                self.x, self.y, direction_x, direction_y, max_distance, city
            )

            # Solo moverse si hay cambio de posición
            if final_x != self.x or final_y != self.y:

                distance_moved = max(abs(final_x - self.x),
                                     abs(final_y - self.y))

                self.target_x = final_x
                self.target_y = final_y
                self.is_moving = True
                self.move_progress = 0.0

                # Actualizar move_speed basado en distancia
                self.update_move_speed_for_distance()

                # Update stamina after move
                self.update_stamina_after_move(distance_moved, weather, city)

                # Determinar dirección para animación
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
            # Time corresponding to distance and speed
            # High speed + long distance = same time as normal speed + short distance
            base_time = distance / self.current_speed  # Time in seconds
            # Convert to progress per frame
            self.move_speed = min(1.0, 1.0 / (base_time * 60))
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

    def draw(self, screen, cell_size, map_offset_x, map_offset_y):
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
            # Fallback: simple circle
            pygame.draw.circle(screen, (255, 0, 0), (screen_x, screen_y), 12)

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
        """Actualizar move_speed interno basado en current_speed"""
        # Convertir celdas/seg a move_progress por frame
        # move_speed controla qué tan rápido se completa el movimiento (0.0-1.0 por frame)
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
        self.stamina = max(0, min(100, self.stamina + stamina_loss))

        # Update resistance state based on new stamina
        if self.stamina >= 70:
            self.set_resistance_state("normal")
        elif self.stamina >= 30:
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

        # update resistance state
        if self.stamina >= 70:
            self.set_resistance_state("normal")
        elif self.stamina >= 30:
            self.set_resistance_state("tired")
        else:
            self.set_resistance_state("exhausted")

        # Debug info
        actual_increase = self.stamina - old_stamina
        print(
            f"Stamina increased by {actual_increase:.1f} → {self.stamina:.1f} - State: {self.resistance_state}")

        return actual_increase
