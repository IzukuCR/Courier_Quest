import pygame
from .base_view import BaseView
from ..game.game import Game


class GameView(BaseView):
    def __init__(self):
        super().__init__()
        self.game = Game()
        self.player_name = self.game.get_player_name()

        # Map configuration
        self.city = self.game.get_city()
        if hasattr(self.city, 'tiles'):
            self.matrix = self.city.tiles
        else:
            self.matrix = []

        self.cell_size = 30
        self.map_offset_x = 20
        self.map_offset_y = 20  # Tiles size 30x30

        # Tile colors (fallback if images not loaded)
        self.tile_colors = {
            "C": (128, 128, 128),    # GRAY
            "P": (34, 139, 34),      # FOREST_GREEN
            "B": (139, 69, 19),      # BROWN
        }

        self.font = pygame.font.Font(None, 24)

        # Load tile images
        self.load_tile_images()

        # Player
        self.player = self.game.get_player()  # Get player from game

    def load_tile_images(self):

        self.tile_images = {}

        tile_files = {
            "B": "code/assets/tiles/buildIngBorderless1.PNG"
        }

        for tile_type, file_path in tile_files.items():  # Load only specified tiles
            try:
                image = pygame.image.load(file_path)
                original_size = image.get_size()
                print(
                    f"DEBUG TILES - Original '{tile_type}' size: {original_size}")

                # VERIFICAR: ¿Se está escalando correctamente?
                scaled_image = pygame.transform.scale(
                    image, (self.cell_size, self.cell_size))
                final_size = scaled_image.get_size()
                print(f"DEBUG TILES - Scaled '{tile_type}' size: {final_size}")

                self.tile_images[tile_type] = scaled_image

            except pygame.error as e:
                print(f"Error loading {file_path}: {e}")

        if not self.tile_images:
            print("Game view: No tile images loaded, using colors")
            self.tile_images = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:  # Key pressed
            if event.key == pygame.K_ESCAPE:  # Escape to go back to menu
                from .menu_view import MenuView
                menu_view = MenuView()
                self.window.show_view(menu_view)
                # PLAYER CONTROLS
            elif self.player:
                new_x, new_y = self.player.x, self.player.y  # Current position

                if event.key == pygame.K_UP or event.key == pygame.K_w:  # W or Up
                    new_y -= 1
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:  # S or Down
                    new_y += 1
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:  # A or Left
                    new_x -= 1
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:  # D or Right
                    new_x += 1

                # Intentar mover el jugador
                if (new_x, new_y) != (self.player.x, self.player.y):
                    success = self.player.move_to(
                        new_x, new_y, self.city, self.game.get_weather())
                    if success:
                        print(
                            f"{self.player.get_speed_info(self.game.get_weather(), self.city)}")
                        self.game.get_weather().next_weather()
                        print(f"Player moved to ({new_x}, {new_y})")
                    else:
                        print(f"Cannot move to ({new_x}, {new_y})")

    def draw(self, screen):
        screen.fill(self.window.colors['BLACK'])

        # Draw map
        self.draw_map(screen)

        # Draw UI
        self.draw_ui(screen)

        # Draw player
        if self.player:
            self.player.draw(screen, self.cell_size,
                             self.map_offset_x, self.map_offset_y)

    def draw_map(self, screen):
        if not self.matrix:
            return

        for row_idx, row in enumerate(self.matrix):
            for col_idx, cell in enumerate(row):
                x = self.map_offset_x + col_idx * self.cell_size
                y = self.map_offset_y + row_idx * self.cell_size

                # Draw tile image if available, else color
                if self.tile_images and cell in self.tile_images:
                    tile_image = self.tile_images[cell]
                    screen.blit(tile_image, (x, y))

                    rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                    border_color = (80, 80, 80)  # Medium gray

                    # Only draw bottom and right borders to avoid double lines
                    pygame.draw.line(screen, border_color,
                                     (x + self.cell_size - 1, y),
                                     (x + self.cell_size - 1, y + self.cell_size - 1))
                    pygame.draw.line(screen, border_color,
                                     (x, y + self.cell_size - 1),
                                     (x + self.cell_size - 1, y + self.cell_size - 1))

                else:
                    # Default to color if no image
                    color = self.tile_colors.get(
                        cell, self.window.colors['WHITE'])
                    rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                    pygame.draw.rect(screen, color, rect)
                    pygame.draw.rect(screen, (0, 0, 0), rect, 1)

    def draw_ui(self, screen):
        # Game UI elements
        ui_x = 950  # Start UI at x=950
        player_text = self.font.render(
            f"Player: {self.player_name}", True, self.window.colors['WHITE'])
        screen.blit(player_text, (ui_x, 50))

        # Instructions
        help_text = self.font.render(
            "Press ESC to return to menu", True, self.window.colors['GRAY'])
        screen.blit(help_text, (ui_x, 700))

    def update(self):
        # Update game time
        self.game.update_game_time(1/60)

        # Update player
        if self.player:
            self.player.update(1/60)

    def on_show(self):
        print("Game view shown")
