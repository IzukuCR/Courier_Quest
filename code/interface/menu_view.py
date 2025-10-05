import pygame
from .base_view import BaseView


class MenuView(BaseView):
    def __init__(self):
        super().__init__()
        self.hovered_button = None

        # Fonts will be scaled in on_show()
        self.title_font = None
        self.button_font = None
        self.subtitle_font = None

    def on_show(self):
        """Initialize responsive layout when view is shown"""
        if self.window:
            # Scale fonts based on window size (was fixed sizes)
            title_size = self.window.get_scaled_size(48)
            button_size = self.window.get_scaled_size(24)
            subtitle_size = self.window.get_scaled_size(20)

            self.title_font = pygame.font.Font(None, title_size)
            self.button_font = pygame.font.Font(None, button_size)
            self.subtitle_font = pygame.font.Font(None, subtitle_size)

            # Calculate responsive button positions (was fixed center_x=700)
            center_x = self.window.width // 2
            center_y = self.window.height // 2

            button_width = self.window.get_scaled_size(200)
            button_height = self.window.get_scaled_size(50)
            button_spacing = self.window.get_scaled_size(70)

            # Create responsive button layout
            self.buttons = {
                "play": {
                    "rect": pygame.Rect(center_x - button_width//2,
                                        center_y - button_spacing,
                                        button_width, button_height),
                    "text": "Play"
                },
                "load": {
                    "rect": pygame.Rect(center_x - button_width//2,
                                        center_y,
                                        button_width, button_height),
                    "text": "Load Game"
                },
                "quit": {
                    "rect": pygame.Rect(center_x - button_width//2,
                                        center_y + button_spacing,
                                        button_width, button_height),
                    "text": "Quit"
                }
            }

        print("Menu view shown with responsive layout")

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

        # Responsive title positioning (was fixed at 700, 200)
        center_x = self.window.width // 2
        title_y = self.window.height // 4

        title_text = self.title_font.render(
            "COURIER QUEST", True, self.window.colors['WHITE'])
        title_rect = title_text.get_rect(center=(center_x, title_y))
        screen.blit(title_text, title_rect)

        # Responsive subtitle positioning
        subtitle_y = title_y + self.window.get_scaled_size(50)
        subtitle_text = self.subtitle_font.render(
            "Welcome to the game", True, self.window.colors['GRAY'])
        subtitle_rect = subtitle_text.get_rect(center=(center_x, subtitle_y))
        screen.blit(subtitle_text, subtitle_rect)

        # Buttons (positions now calculated in on_show())
        for button_key, button_data in self.buttons.items():
            self.draw_button(screen, button_key, button_data)

    def draw_button(self, screen, button_key, button_data):
        rect = button_data["rect"]
        text = button_data["text"]

        # Color based on hover state
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
