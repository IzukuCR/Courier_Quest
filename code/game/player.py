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

    def move_to(self, new_x, new_y, city):

        # Check if the new position is valid and not blocked
        if city.is_valid_position(new_x, new_y) and not city.is_blocked(new_x, new_y):
            if not self.is_moving:  # Only if not already moving
                self.target_x = new_x
                self.target_y = new_y
                self.is_moving = True
                self.move_progress = 0.0  # Reset movement progress

                # Determine direction for animation
                if new_x > self.x:
                    self.current_direction = "RIGHT"
                elif new_x < self.x:
                    self.current_direction = "LEFT"
                elif new_y > self.y:
                    self.current_direction = "DOWN"
                elif new_y < self.y:
                    self.current_direction = "UP"

                return True
        return False

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
