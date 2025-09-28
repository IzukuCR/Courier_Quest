import pygame
from .base_view import BaseView


class MenuView(BaseView):
    def __init__(self):
        super().__init__()

        # Menu buttons
        center_x = 700  # Position X centered for 1200 width
        self.buttons = {
            "play": {"rect": pygame.Rect(center_x - 100, 350, 200, 50), "text": "Play"},
            "load": {"rect": pygame.Rect(center_x - 100, 420, 200, 50), "text": "Load Game"},
            "quit": {"rect": pygame.Rect(center_x - 100, 490, 200, 50), "text": "Quit"}
        }

        self.hovered_button = None

        # Fonts (Can change sizes and types as needed)
        self.title_font = pygame.font.Font(None, 48)
        self.button_font = pygame.font.Font(None, 24)
        self.subtitle_font = pygame.font.Font(None, 20)

    def on_show(self):
        print("Showing Menu View")

    def handle_event(self, event):  # Handle events for the menu
        if event.type == pygame.MOUSEMOTION:
            self.hovered_button = None
            for button_key, button_data in self.buttons.items():
                if button_data["rect"].collidepoint(event.pos):
                    self.hovered_button = button_key
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                for button_key, button_data in self.buttons.items():
                    if button_data["rect"].collidepoint(event.pos):
                        self.handle_button_click(button_key)
                        break

    def handle_button_click(self, button_key):
        if button_key == "play":
            print("Starting new game...")
            from .player_setup_view import PlayerSetupView
            player_setup_view = PlayerSetupView()
            self.window.show_view(player_setup_view)

        elif button_key == "load":
            print("Loading game... (Not implemented)")  # Not yet implemented

        elif button_key == "quit":
            print("Closing game...")
            self.window.running = False

    def draw(self, screen):
        # Background
        screen.fill(self.window.colors['DARK_GRAY'])

        # Title
        title_text = self.title_font.render(
            "COURIER QUEST", True, self.window.colors['WHITE'])
        title_rect = title_text.get_rect(
            center=(700, 200))  # Centered for 1200 width
        screen.blit(title_text, title_rect)

        # Subtitle
        subtitle_text = self.subtitle_font.render(
            "Welcome to the game", True, self.window.colors['GRAY'])
        subtitle_rect = subtitle_text.get_rect(
            center=(700, 250))  # Centered for 1200 width
        screen.blit(subtitle_text, subtitle_rect)

        # Buttons
        for button_key, button_data in self.buttons.items():
            self.draw_button(screen, button_key, button_data)

    def draw_button(self, screen, button_key, button_data):
        rect = button_data["rect"]
        text = button_data["text"]

        # color based on hover state
        if self.hovered_button == button_key:
            bg_color = self.window.colors['BLUE']
            border_color = self.window.colors['WHITE']
        else:
            bg_color = self.window.colors['GRAY']
            border_color = self.window.colors['WHITE']

        # Draw button rectangle
        pygame.draw.rect(screen, bg_color, rect)
        pygame.draw.rect(screen, border_color, rect, 2)

        # Button text
        text_surface = self.button_font.render(
            text, True, self.window.colors['WHITE'])
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)
