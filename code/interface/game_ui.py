import pygame


class GameUI:
    def __init__(self, game, player_name):
        self.game = game
        self.player_name = player_name
        self.font = pygame.font.Font(None, 24)
        self.game_time = 0.0

    def update(self, delta_time):
        # Update game time
        self.game_time += delta_time

    def draw(self, screen, x_offset=650):
        # Draw all UI elements
        self.draw_sidebar(screen, x_offset)

    def draw_sidebar(self, screen, x_offset):
        # Draw sidebar with information
        # Background of the sidebar
        sidebar_rect = pygame.Rect(x_offset, 0, 150, screen.get_height())
        pygame.draw.rect(screen, (64, 64, 64), sidebar_rect)  # DARK_GRAY

        # Player information
        y_pos = 50
        player_text = self.font.render(
            f"Player: {self.player_name}", True, (255, 255, 255))
        screen.blit(player_text, (x_offset + 10, y_pos))

        # Game time
        y_pos += 30
        minutes = int(self.game_time // 60)
        seconds = int(self.game_time % 60)
        time_text = self.font.render(
            f"Time: {minutes:02d}:{seconds:02d}", True, (255, 255, 255))
        screen.blit(time_text, (x_offset + 10, y_pos))

        # Scoreboard
        y_pos += 50
        score_title = self.font.render(
            "SCORE", True, (255, 255, 0))  # YELLOW
        screen.blit(score_title, (x_offset + 10, y_pos))

        y_pos += 25
        score_text = self.font.render("Points: 0", True, (255, 255, 255))
        screen.blit(score_text, (x_offset + 10, y_pos))

        # Inventory
        y_pos += 50
        inventory_title = self.font.render("INVENTORY", True, (255, 255, 0))
        screen.blit(inventory_title, (x_offset + 10, y_pos))

        y_pos += 25
        inventory_text = self.font.render("Orders: 0", True, (255, 255, 255))
        screen.blit(inventory_text, (x_offset + 10, y_pos))
