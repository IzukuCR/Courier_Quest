import pygame
from .base_view import BaseView


class PlayerSetupView(BaseView):
    def __init__(self):
        super().__init__()
        self.player_name = ""
        self.cursor_timer = 0
        self.cursor_visible = True
        self.hovered_button = None

        # Fonts will be scaled in on_show()
        self.font = None
        self.title_font = None
        self.help_font = None

        # Buttons will be calculated in on_show()
        self.buttons = {}

    def on_show(self):
        """Initialize responsive layout when view is shown"""
        if self.window:
            # Scale fonts based on window size
            font_size = self.window.get_scaled_size(32)
            title_size = self.window.get_scaled_size(36)
            help_size = self.window.get_scaled_size(20)

            self.font = pygame.font.Font(None, font_size)
            self.title_font = pygame.font.Font(None, title_size)
            self.help_font = pygame.font.Font(None, help_size)

            # Calculate responsive positions
            center_x = self.window.width // 2
            center_y = self.window.height // 2

            # Button dimensions
            button_width = self.window.get_scaled_size(100)
            button_height = self.window.get_scaled_size(40)
            button_spacing = self.window.get_scaled_size(
                200)  # Space between buttons
            buttons_y = center_y + self.window.get_scaled_size(100)

            self.buttons = {
                "continue": {
                    "rect": pygame.Rect(center_x + self.window.get_scaled_size(50),
                                        buttons_y, button_width, button_height),
                    "text": "Continue"
                },
                "back": {
                    "rect": pygame.Rect(center_x - self.window.get_scaled_size(150),
                                        buttons_y, button_width, button_height),
                    "text": "Back"
                },
            }

        print("Player Setup View shown with responsive layout")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.player_name.strip():
                    self.continue_to_game()
            elif event.key == pygame.K_ESCAPE:
                self.go_back()
            elif event.key == pygame.K_BACKSPACE:
                self.player_name = self.player_name[:-1]
            else:
                if len(self.player_name) < 20:
                    self.player_name += event.unicode

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

    def update(self, delta_time: float):
        # Cursor blinking
        self.cursor_timer += 1
        if self.cursor_timer >= 30:  # 30 frames = 0.5 seconds at 60 FPS
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def draw(self, screen):
        screen.fill(self.window.colors['DARK_GRAY'])

        # Calculate responsive positions
        center_x = self.window.width // 2
        center_y = self.window.height // 2

        # Title - responsive positioning
        title_y = center_y - self.window.get_scaled_size(150)
        title_text = self.title_font.render(
            "Player Setup", True, self.window.colors['WHITE'])
        title_rect = title_text.get_rect(center=(center_x, title_y))
        screen.blit(title_text, title_rect)

        # Instructions - responsive positioning
        instruction_y = center_y - self.window.get_scaled_size(50)
        instruction_text = self.font.render(
            "Enter your name:", True, self.window.colors['WHITE'])
        instruction_rect = instruction_text.get_rect(
            center=(center_x, instruction_y))
        screen.blit(instruction_text, instruction_rect)

        # Input field - responsive sizing and positioning
        input_width = self.window.get_scaled_size(300)
        input_height = self.window.get_scaled_size(40)
        input_y = center_y

        input_rect = pygame.Rect(
            center_x - input_width//2, input_y, input_width, input_height)
        pygame.draw.rect(screen, self.window.colors['WHITE'], input_rect)
        pygame.draw.rect(screen, self.window.colors['BLACK'], input_rect, 2)

        # Text entered
        display_text = self.player_name
        if self.cursor_visible:
            display_text += "_"

        text_surface = self.font.render(
            display_text, True, self.window.colors['BLACK'])
        screen.blit(text_surface, (input_rect.x + 10, input_rect.y + 10))

        # Buttons (now responsive)
        for button_key, button_data in self.buttons.items():
            self.draw_button(screen, button_key, button_data)

        # Help instructions - responsive positioning
        help_y = center_y + self.window.get_scaled_size(200)
        help_text = self.help_font.render(
            "Press Enter to continue or Escape to go back",
            True, self.window.colors['GRAY']
        )
        help_rect = help_text.get_rect(center=(center_x, help_y))
        screen.blit(help_text, help_rect)

    def draw_button(self, screen, button_key, button_data):
        rect = button_data["rect"]
        text = button_data["text"]

        # Colors based on hover state
        if self.hovered_button == button_key:
            if button_key == "continue":
                bg_color = (self.window.colors.get('GREEN', (0, 150, 0)))
            else:
                bg_color = self.window.colors['BLUE']
            border_color = self.window.colors['WHITE']
        else:
            bg_color = self.window.colors['GRAY']
            border_color = self.window.colors['WHITE']

        # Draw button
        pygame.draw.rect(screen, bg_color, rect)
        pygame.draw.rect(screen, border_color, rect, 2)

        # Button text
        text_surface = self.font.render(
            text, True, self.window.colors['WHITE'])
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)

    def handle_button_click(self, button_key):
        if button_key == "continue":
            if self.player_name.strip():  # If name is not empty
                self.continue_to_game()
            else:
                print("Player Setup: No name entered!")

        elif button_key == "back":
            self.go_back()

    def go_back(self):
        from .menu_view import MenuView
        menu_view = MenuView()
        self.window.show_view(menu_view)  # Switch to menu view

    def continue_to_game(self):
        from ..game.game import Game
        game = Game()
        game.set_player_name(self.player_name)  # Set player name

        game.start_new_game()  # Reset game state for new game

        from .instructions_view import InstructionsView
        # Switch to instructions view
        self.window.show_view(InstructionsView())
