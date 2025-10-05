import pygame


class GameUI:
    def __init__(self, game, player_name, window=None):
        self.game = game
        self.player_name = player_name
        self.game_time = 0.0
        self.window = window  # Reference to main window for scaling

        # Fonts will be scaled dynamically
        self.font = None
        self.update_fonts()

    def update_fonts(self):
        """Update font sizes based on window scaling"""
        if self.window:
            font_size = self.window.get_scaled_size(24)
            self.font = pygame.font.Font(None, font_size)
        else:
            self.font = pygame.font.Font(None, 24)

    def update(self, delta_time):
        # Update game time
        self.game_time += delta_time

    def draw(self, screen, x_offset=None):
        # Calculate responsive x_offset if not provided
        if x_offset is None and self.window:
            x_offset = self.window.hud_x
        elif x_offset is None:
            x_offset = 650  # Fallback

        # Draw all UI elements
        self.draw_sidebar(screen, x_offset)

    def draw_sidebar(self, screen, x_offset):
        # Calculate responsive sidebar width
        sidebar_width = 150
        if self.window:
            sidebar_width = self.window.get_scaled_size(150)

        # Background of the sidebar
        sidebar_rect = pygame.Rect(
            x_offset, 0, sidebar_width, screen.get_height())
        pygame.draw.rect(screen, (64, 64, 64), sidebar_rect)  # DARK_GRAY

        # Calculate responsive spacing
        base_spacing = 30
        if self.window:
            base_spacing = self.window.get_scaled_size(30)

        # Player information
        y_pos = 50
        player_text = self.font.render(
            f"Player: {self.player_name}", True, (255, 255, 255))
        screen.blit(player_text, (x_offset + 10, y_pos))

        # Game time
        y_pos += base_spacing
        minutes = int(self.game_time // 60)
        seconds = int(self.game_time % 60)
        time_text = self.font.render(
            f"Time: {minutes:02d}:{seconds:02d}", True, (255, 255, 255))
        screen.blit(time_text, (x_offset + 10, y_pos))

        # Scoreboard
        y_pos += base_spacing + 20
        score_title = self.font.render(
            "SCORE", True, (255, 255, 0))  # YELLOW
        screen.blit(score_title, (x_offset + 10, y_pos))

        y_pos += 25
        score_text = self.font.render("Points: 0", True, (255, 255, 255))
        screen.blit(score_text, (x_offset + 10, y_pos))

        # Inventory
        y_pos += base_spacing + 20
        inventory_title = self.font.render("INVENTORY", True, (255, 255, 0))
        screen.blit(inventory_title, (x_offset + 10, y_pos))

        y_pos += 25
        inventory_text = self.font.render("Orders: 0", True, (255, 255, 255))
        screen.blit(inventory_text, (x_offset + 10, y_pos))
