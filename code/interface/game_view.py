import pygame
from .base_view import BaseView
from ..game.game import Game


class GameView(BaseView):
    def __init__(self):
        super().__init__()
        self.game = Game()
        self.player_name = self.game.get_player_name() or "Player"

        # Map configuration
        self.city = self.game.get_city()
        self.matrix = self.city.tiles
        self.cell_size = 30  # Tiles size 30x30

        # Tile colors (fallback if images not loaded)
        self.tile_colors = {
            "C": (128, 128, 128),    # GRAY
            "P": (34, 139, 34),      # FOREST_GREEN
            "B": (139, 69, 19),      # BROWN
        }

        self.font = pygame.font.Font(None, 24)

        # Load tile images
        self.load_tile_images()

    def load_tile_images(self):

        self.tile_images = {}

        # List to load
        tile_files = {

            "B": "code/assets/tiles/buildIngBorderless1.PNG"
        }

        for tile_type, file_path in tile_files.items():
            try:
                image = pygame.image.load(file_path)
                # Change size if needed
                self.tile_images[tile_type] = pygame.transform.scale(
                    # Resize to 30x30 (cell_size)
                    image, (self.cell_size, self.cell_size)
                )
            except pygame.error as e:
                print(f"Game_View: Image can't be loaded {file_path}: {e}")

        if not self.tile_images:
            print("Game_View: Images not loaded, using colors instead.")
            self.tile_images = None

    def on_show(self):
        print(f"Starting game for: {self.player_name}")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from .menu_view import MenuView
                menu_view = MenuView()
                self.window.show_view(menu_view)

    def draw(self, screen):
        screen.fill(self.window.colors['BLACK'])

        # Draw map
        self.draw_map(screen)

        # Draw UI
        self.draw_ui(screen)

    def draw_map(self, screen):
        if not self.matrix:
            return

        map_offset_x = 30
        map_offset_y = 30

        for row_idx, row in enumerate(self.matrix):
            for col_idx, cell in enumerate(row):
                x = map_offset_x + col_idx * self.cell_size
                y = map_offset_y + row_idx * self.cell_size

                if self.tile_images and cell in self.tile_images:
                    # Usar imagen
                    screen.blit(self.tile_images[cell], (x, y))
                else:
                    # Fallback a colores
                    color = self.tile_colors.get(
                        cell, self.window.colors['WHITE'])
                    rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                    pygame.draw.rect(screen, color, rect)

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
