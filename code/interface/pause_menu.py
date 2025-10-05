import pygame


class PauseMenu:
    def __init__(self, window):
        self.window = window
        self.visible = False
        self.hovered_button = None

        # Menu dimensions (responsive)
        self.menu_width = self.window.get_scaled_size(300)
        self.menu_height = self.window.get_scaled_size(250)

        # Calculate menu position (centered)
        self.menu_x = (self.window.width - self.menu_width) // 2
        self.menu_y = (self.window.height - self.menu_height) // 2

        # Fonts
        self.title_font = pygame.font.Font(
            None, self.window.get_scaled_size(32))
        self.button_font = pygame.font.Font(
            None, self.window.get_scaled_size(24))

        # Button configuration
        button_width = self.window.get_scaled_size(200)
        button_height = self.window.get_scaled_size(40)
        button_spacing = self.window.get_scaled_size(15)

        # Center buttons within menu
        button_x = self.menu_x + (self.menu_width - button_width) // 2
        start_y = self.menu_y + self.window.get_scaled_size(80)

        self.buttons = {
            "continue": {
                "rect": pygame.Rect(button_x, start_y, button_width, button_height),
                "text": "Continue Game",
                "action": "continue"
            },
            "save": {
                "rect": pygame.Rect(button_x, start_y + button_height + button_spacing,
                                    button_width, button_height),
                "text": "Save Game",
                "action": "save"
            },
            "exit": {
                "rect": pygame.Rect(button_x, start_y + 2 * (button_height + button_spacing),
                                    button_width, button_height),
                "text": "Exit to Menu",
                "action": "exit"
            }
        }

    def show(self):
        """Show the pause menu"""
        self.visible = True

    def hide(self):
        """Hide the pause menu"""
        self.visible = False
        self.hovered_button = None

    def handle_event(self, event):
        """Handle mouse events for the pause menu"""
        if not self.visible:
            return None

        if event.type == pygame.MOUSEMOTION:
            # Check which button is being hovered
            self.hovered_button = None
            for button_key, button_data in self.buttons.items():
                if button_data["rect"].collidepoint(event.pos):
                    self.hovered_button = button_key
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check which button was clicked
                for button_key, button_data in self.buttons.items():
                    if button_data["rect"].collidepoint(event.pos):
                        # Return the action to perform
                        return button_data["action"]

        elif event.type == pygame.KEYDOWN:
            # Allow ESC to continue game
            if event.key == pygame.K_ESCAPE:
                return "continue"

        return None

    def draw(self, screen):
        """Draw the pause menu"""
        if not self.visible:
            return

        # Semi-transparent overlay over entire screen
        overlay = pygame.Surface(
            (self.window.width, self.window.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))  # Dark semi-transparent
        screen.blit(overlay, (0, 0))

        # Menu background (darker with border)
        menu_rect = pygame.Rect(self.menu_x, self.menu_y,
                                self.menu_width, self.menu_height)
        # Dark gray background
        pygame.draw.rect(screen, (40, 40, 40), menu_rect)
        pygame.draw.rect(screen, (200, 200, 200), menu_rect, 3)  # Light border

        # Menu title
        title_text = self.title_font.render(
            "GAME PAUSED", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.menu_x + self.menu_width // 2,
                                                 self.menu_y + self.window.get_scaled_size(40)))
        screen.blit(title_text, title_rect)

        # Draw buttons
        for button_key, button_data in self.buttons.items():
            self._draw_button(screen, button_key, button_data)

    def _draw_button(self, screen, button_key, button_data):
        """Draw individual button with hover effects"""
        rect = button_data["rect"]
        text = button_data["text"]

        # Button colors based on hover state
        if self.hovered_button == button_key:
            if button_key == "exit":
                bg_color = (180, 50, 50)  # Red for exit
                border_color = (255, 100, 100)
            else:
                bg_color = (70, 100, 180)  # Blue for other buttons
                border_color = (100, 150, 255)
            text_color = (255, 255, 255)
        else:
            bg_color = (80, 80, 80)  # Dark gray
            border_color = (150, 150, 150)  # Light gray border
            if button_key == "exit":
                text_color = (255, 150, 150)  # Light red text for exit
            else:
                text_color = (200, 200, 200)  # Light gray text

        # Draw button background and border
        pygame.draw.rect(screen, bg_color, rect)
        pygame.draw.rect(screen, border_color, rect, 2)

        # Draw button text
        text_surface = self.button_font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)
