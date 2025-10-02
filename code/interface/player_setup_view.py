import pygame

from code.game import game
from .base_view import BaseView


class PlayerSetupView(BaseView):
    def __init__(self):
        super().__init__()
        self.player_name = ""
        self.font = pygame.font.Font(None, 32)
        self.title_font = pygame.font.Font(None, 36)
        self.cursor_timer = 0
        self.cursor_visible = True
        self.hovered_button = None

        self.buttons = {
            "continue": {"rect": pygame.Rect(700 + 50, 450, 100, 40), "text": "Continue"},
            "back": {"rect": pygame.Rect(700 - 150, 450, 100, 40), "text": "Back"},
        }

    def on_show(self):
        print("Player Setup View shown")

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

    def update(self):
        # Cursor blinking
        self.cursor_timer += 1
        if self.cursor_timer >= 30:  # 30 frames = 0.5 seconds at 60 FPS
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def draw(self, screen):
        screen.fill(self.window.colors['DARK_GRAY'])

        center_x = 700  # Center X for 1400 width

        # Title
        title_text = self.title_font.render(
            "Player Setup", True, self.window.colors['WHITE'])
        title_rect = title_text.get_rect(center=(center_x, 200))
        screen.blit(title_text, title_rect)

        # Instructions
        instruction_text = self.font.render(
            "Enter your name:", True, self.window.colors['WHITE'])
        instruction_rect = instruction_text.get_rect(center=(center_x, 300))
        screen.blit(instruction_text, instruction_rect)

        # Input field
        input_rect = pygame.Rect(center_x - 150, 350, 300, 40)
        pygame.draw.rect(screen, self.window.colors['WHITE'], input_rect)
        pygame.draw.rect(screen, self.window.colors['BLACK'], input_rect, 2)

        # Text entered
        display_text = self.player_name
        if self.cursor_visible:
            display_text += "_"

        text_surface = self.font.render(
            display_text, True, self.window.colors['BLACK'])
        screen.blit(text_surface, (input_rect.x + 10, input_rect.y + 10))

        # Buttons
        for button_key, button_data in self.buttons.items():
            self.draw_button(screen, button_key, button_data)

        # Instructions
        help_text = pygame.font.Font(None, 20).render(
            "Press Enter to continue or Escape to go back",
            True, self.window.colors['GRAY']
        )
        help_rect = help_text.get_rect(center=(center_x, 550))
        screen.blit(help_text, help_rect)

    def draw_button(self, screen, button_key, button_data):
        rect = button_data["rect"]
        text = button_data["text"]

        # Colors based on hover state (event)
        if self.hovered_button == button_key:
            if button_key == "continue":
                bg_color = self.window.colors['GREEN'] if self.window.colors.get(
                    'GREEN') else (0, 150, 0)
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

        from .game_view import GameView
        game_view = GameView()
        self.window.show_view(game_view)  # Switch to game view
