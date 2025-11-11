import pygame
import os


class AIView:
    def __init__(self, ai_bot):
        self.ai_bot = ai_bot

        # Sprites - will be scaled dynamically
        self.base_sprite_size = 24
        self.current_sprite_size = 24
        self.sprites = {}
        self.original_sprites = {}

        # Animation state
        self.animation_frame = 0
        self.animation_timer = 0
        self.animation_speed = 10

        # Load sprites
        self.load_sprites()

    def load_sprites(self):
        """Load AI sprites for rendering"""
        self.original_sprites = {}
        self.sprites = {}

        sprite_files = {
            "UP": "code/assets/ai/ai_UP.PNG",
            "DOWN": "code/assets/ai/ai_DOWN.png",
            "LEFT": "code/assets/ai/ai_LEFT.PNG",
            "RIGHT": "code/assets/ai/ai_RIGHT.PNG"
        }

        for direction, file_path in sprite_files.items():
            try:
                if os.path.exists(file_path):
                    original_image = pygame.image.load(file_path)
                    self.original_sprites[direction] = original_image
                    scaled_image = pygame.transform.scale(
                        original_image, (self.base_sprite_size, self.base_sprite_size))
                    self.sprites[direction] = scaled_image
                else:
                    placeholder = self.create_placeholder_sprite(
                        direction, self.base_sprite_size)
                    self.original_sprites[direction] = placeholder
                    self.sprites[direction] = placeholder
            except Exception as e:
                print(f"AIView: Error loading sprite {file_path}: {e}")
                placeholder = self.create_placeholder_sprite(
                    direction, self.base_sprite_size)
                self.original_sprites[direction] = placeholder
                self.sprites[direction] = placeholder

        if not self.sprites:
            for direction in ["UP", "DOWN", "LEFT", "RIGHT"]:
                self.sprites[direction] = self.create_placeholder_sprite(
                    direction)

    def create_placeholder_sprite(self, direction, size=24):
        """Create placeholder sprite for AI bot"""
        surface = pygame.Surface((size, size), pygame.SRCALPHA)

        colors = {
            "UP": (0, 255, 0),
            "DOWN": (255, 0, 0),
            "LEFT": (0, 0, 255),
            "RIGHT": (255, 255, 0)
        }

        color = colors.get(direction, (255, 255, 255))
        center = size // 2

        pygame.draw.circle(surface, color, (center, center), center - 2)
        pygame.draw.circle(surface, (0, 0, 0), (center, center), center - 2, 2)

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

    def update_sprite_scale(self, cell_size):
        """Update sprite scaling based on current cell size"""
        new_size = max(16, int(cell_size * 0.8))

        if new_size != self.current_sprite_size:
            self.current_sprite_size = new_size

            for direction, original in self.original_sprites.items():
                if original:
                    self.sprites[direction] = pygame.transform.scale(
                        original, (new_size, new_size))

    def get_screen_position(self, cell_size, map_offset_x, map_offset_y):
        """Get AI bot screen position with smooth interpolation"""
        if self.ai_bot.is_moving:
            current_x = self.ai_bot.x + \
                (self.ai_bot.target_x - self.ai_bot.x) * self.ai_bot.move_progress
            current_y = self.ai_bot.y + \
                (self.ai_bot.target_y - self.ai_bot.y) * self.ai_bot.move_progress
        else:
            current_x = self.ai_bot.x
            current_y = self.ai_bot.y

        screen_x = map_offset_x + current_x * cell_size + (cell_size // 2)
        screen_y = map_offset_y + current_y * cell_size + (cell_size // 2)

        return int(screen_x), int(screen_y)

    def update(self, delta_time):
        """Update animation state"""
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_frame = (self.animation_frame + 1) % 4
            self.animation_timer = 0

    def draw(self, screen, cell_size, map_offset_x, map_offset_y):
        """Draw AI bot on screen"""
        if not self.ai_bot:
            return

        # Update sprite scale if needed
        self.update_sprite_scale(cell_size)

        # Get screen position
        screen_x, screen_y = self.get_screen_position(
            cell_size, map_offset_x, map_offset_y)

        # Get current direction from AI bot
        current_direction = self.ai_bot.current_direction

        # Draw sprite
        sprite = self.sprites.get(current_direction)
        if sprite:
            sprite_rect = sprite.get_rect()
            sprite_rect.center = (screen_x, screen_y)
            screen.blit(sprite, sprite_rect)
        else:
            # Fallback: circle
            radius = max(8, cell_size // 3)
            pygame.draw.circle(screen, (0, 255, 255),
                               (screen_x, screen_y), radius)
            pygame.draw.circle(screen, (0, 0, 0),
                               (screen_x, screen_y), radius, 2)
