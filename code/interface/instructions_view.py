import pygame
from .base_view import BaseView

# These will be scaled dynamically now
BASE_PADDING = 32
BASE_CONTENT_W = 720
BASE_LINE_SPACING = 6

INSTRUCTIONS_TEXT = [
    "Objective",
    "• Complete deliveries to earn points and reach the money goal before time runs out.",
    "• Maintain your reputation above 20% to stay in business.",
    "",
    "Controls",
    "• Arrow keys or WASD to move through the city tile by tile.",
    "• TAB to cycle between available orders.",
    "• SPACE to accept/pick up/deliver the selected order.",
    "• Z to undo last movement (costs stamina).",
    "• X to discard/cancel active order (affects reputation).",
    "• Q/E to switch between accepted orders.",
    "• ESC to pause game or return to menu.",
    "",
    "Game Systems",
    "• Stamina: Rest by not moving to recover stamina.",
    "• Reputation: Deliver on time to increase, late deliveries decrease it.",
    "• Weight: Heavy packages slow you down.",
    "",
    "Orders",
    "• Priority levels affect deadline time and payout.",
    "• Early delivery: +5 reputation.",
    "• On-time delivery: +3 reputation.",
    "• Late delivery: -2 to -10 reputation.",
    "• 3 consecutive on-time deliveries: +2 reputation bonus.",
    "",
    "Tips",
    "• Check order deadlines and priorities carefully.",
    "• Rest when stamina is low to avoid exhaustion.",
    "• Excellence bonus at 90+ reputation: +5% earnings.",
    "• First late delivery penalty is halved at 85+ reputation.",
    "",
    "Weather",
    "• Weather affects movement speed.",
    "• Watch for weather changes and plan accordingly.",
    "",
    "Ready!",
    "Press ACCEPT to start delivering!",
]


class InstructionsView(BaseView):
    def __init__(self):
        super().__init__()
        self.hovered_button = None

        # Fonts will be scaled in on_show()
        self.title_font = None
        self.text_font = None
        self.button_font = None

        # These will be calculated in on_show()
        self.buttons = {}
        self._wrapped_lines = []

    def on_show(self):
        """Initialize responsive layout when view is shown"""
        if self.window:
            # Scale fonts based on window size
            title_size = self.window.get_scaled_size(48)
            text_size = self.window.get_scaled_size(26)
            button_size = self.window.get_scaled_size(28)

            self.title_font = pygame.font.Font(None, title_size)
            self.text_font = pygame.font.Font(None, text_size)
            self.button_font = pygame.font.Font(None, button_size)

            # Calculate responsive dimensions
            center_x = self.window.width // 2
            center_y = self.window.height // 2

            # Scale content dimensions
            content_w = self.window.get_scaled_size(BASE_CONTENT_W)
            button_width = self.window.get_scaled_size(180)
            button_height = self.window.get_scaled_size(50)
            button_spacing = self.window.get_scaled_size(
                300)  # Space between buttons

            # Position buttons responsively
            buttons_y = self.window.height - \
                self.window.get_scaled_size(120)  # 120px from bottom

            self.buttons = {
                "accept": {
                    "rect": pygame.Rect(center_x + button_spacing//4, buttons_y,
                                        button_width, button_height),
                    "text": "ACCEPT"
                },
                "back": {
                    "rect": pygame.Rect(center_x - button_spacing//4 - button_width, buttons_y,
                                        button_width, button_height),
                    "text": "BACK"
                },
            }

            # Pre-render wrapped lines with responsive content width
            self._wrapped_lines = self._wrap_paragraphs(
                INSTRUCTIONS_TEXT, content_w, self.text_font)

        print("Instructions View shown with responsive layout")

    # --- text wrapping utility ---
    def _wrap_line(self, text, max_w, font):
        if not text:
            return [""]
        words = text.split(" ")
        lines = []
        current = ""
        for w in words:
            test = w if current == "" else current + " " + w
            if font.size(test)[0] <= max_w:
                current = test
            else:
                if current:
                    lines.append(current)
                current = w
        if current:
            lines.append(current)
        return lines

    def _wrap_paragraphs(self, lines, max_w, font):
        out = []
        for line in lines:
            wrapped = self._wrap_line(line, max_w, font)
            out.extend(wrapped)
        return out

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._go_accept()
            elif event.key == pygame.K_ESCAPE:
                self._go_back()

        elif event.type == pygame.MOUSEMOTION:
            self.hovered_button = None
            for k, b in self.buttons.items():
                if b["rect"].collidepoint(event.pos):
                    self.hovered_button = k
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for k, b in self.buttons.items():
                if b["rect"].collidepoint(event.pos):
                    if k == "accept":
                        self._go_accept()
                    elif k == "back":
                        self._go_back()
                    break

    def _go_back(self):
        from .player_setup_view import PlayerSetupView
        self.window.show_view(PlayerSetupView())

    def _go_accept(self):
        # Start the game and jump to GameView
        from ..game.game import Game
        game = Game()
        game.start_new_game()

        from .game_view import GameView
        self.window.show_view(GameView())

    def draw(self, screen):
        # Background
        screen.fill(self.window.colors['DARK_GRAY'])

        # Calculate responsive dimensions
        padding = self.window.get_scaled_size(BASE_PADDING)
        content_w = self.window.get_scaled_size(BASE_CONTENT_W)
        panel_height = self.window.get_scaled_size(760)

        center_x = self.window.width // 2
        center_y = self.window.height // 2

        # Central panel - responsive sizing and positioning
        panel_rect = pygame.Rect(0, 0, content_w + 2 * padding, panel_height)
        # Offset up slightly
        panel_rect.center = (center_x, center_y -
                             self.window.get_scaled_size(50))
        pygame.draw.rect(
            screen, self.window.colors['WHITE'], panel_rect, border_radius=12)

        # Title - responsive positioning
        title_y = panel_rect.top - self.window.get_scaled_size(80)
        title = self.title_font.render(
            "How to Play?", True, self.window.colors['WHITE'])
        title_rect = title.get_rect(center=(center_x, title_y))
        screen.blit(title, title_rect)

        # Text with responsive spacing
        line_spacing = self.window.get_scaled_size(BASE_LINE_SPACING)
        x0 = panel_rect.left + padding
        y0 = panel_rect.top + padding

        for line in self._wrapped_lines:
            surf = self.text_font.render(
                line, True, self.window.colors['BLACK'])
            screen.blit(surf, (x0, y0))
            y0 += surf.get_height() + line_spacing
            if y0 > panel_rect.bottom - padding:
                break

        # Buttons (now responsive)
        for key, btn in self.buttons.items():
            self._draw_button(screen, key, btn)

    def _draw_button(self, screen, key, btn):
        rect = btn["rect"]
        hovered = (self.hovered_button == key)
        bg = (self.window.colors['GREEN'] if (key == "accept" and hovered) else
              self.window.colors['BLUE'] if hovered else self.window.colors['GRAY'])
        pygame.draw.rect(screen, bg, rect, border_radius=10)
        pygame.draw.rect(
            screen, self.window.colors['WHITE'], rect, 2, border_radius=10)

        text = self.button_font.render(
            btn["text"], True, self.window.colors['WHITE'])
        screen.blit(text, text.get_rect(center=rect.center))
