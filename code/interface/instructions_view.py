import pygame
from .base_view import BaseView

PADDING = 32
CONTENT_W = 720
LINE_SPACING = 6

INSTRUCTIONS_TEXT = [
    "Objective",
    "• Complete deliveries to earn points. Reach destinations before the time limit.",
    "",
    "Controls",
    "• Arrow keys or WASD to move through the city tile by tile.",
    "• ESC to return to menu (from game) or go back (on this screen).",
    "",
    "Terrain and Blocks",
    "• Streets (C) are passable.",
    "• Parks/buildings (P / B) may be blocked; the player cannot traverse them.",
    "",
    "Orders",
    "• Each order has: pickup point, delivery, payment,",
    "  deadline, weight and priority.",
    "• Manage the order of deliveries to maximize score and meet deadlines.",
    "",
    "Weather",
    "• Weather affects your speed (wind, rain, heat, etc.).",
    "• Weather conditions can change during the game.",
    "",
    "Tips",
    "• Plan routes through connected streets.",
    "• Prioritize nearby orders or those with closer deadlines.",
    "• Avoid blocks; look for alternative paths.",
    "",
    "Ready!",
    "Press ACCEPT to start the game.",
]


class InstructionsView(BaseView):
    def __init__(self):
        super().__init__()
        self.title_font = pygame.font.Font(None, 48)
        self.text_font = pygame.font.Font(None, 26)
        self.button_font = pygame.font.Font(None, 28)
        self.hovered_button = None

        center_x = 700  # same convention as other views (1400x1000 screen)
        self.btns = {
            "accept": {"rect": pygame.Rect(center_x + 60, 820, 180, 50), "text": "ACCEPT"},
            "back": {"rect": pygame.Rect(center_x - 240, 820, 180, 50), "text": "BACK"},
        }

        # Pre-render wrapped lines
        self._wrapped_lines = self._wrap_paragraphs(INSTRUCTIONS_TEXT, CONTENT_W, self.text_font)

    def on_show(self):
        print("Instructions View shown")

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
            for k, b in self.btns.items():
                if b["rect"].collidepoint(event.pos):
                    self.hovered_button = k
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for k, b in self.btns.items():
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

        # Central panel
        panel_rect = pygame.Rect(0, 0, CONTENT_W + 2 * PADDING, 760)
        panel_rect.center = (700, 430)
        pygame.draw.rect(screen, self.window.colors['WHITE'], panel_rect, border_radius=12)

        # Title
        title = self.title_font.render("How to Play?", True, self.window.colors['WHITE'])
        title_rect = title.get_rect(center=(700, 120))
        screen.blit(title, title_rect)

        # Text
        x0 = panel_rect.left + PADDING
        y0 = panel_rect.top + PADDING
        for line in self._wrapped_lines:
            surf = self.text_font.render(line, True, self.window.colors['BLACK'])
            screen.blit(surf, (x0, y0))
            y0 += surf.get_height() + LINE_SPACING
            if y0 > panel_rect.bottom - PADDING:
                break  # if you ever want scroll, this would be the place

        # Buttons
        for key, btn in self.btns.items():
            self._draw_button(screen, key, btn)

    def _draw_button(self, screen, key, btn):
        rect = btn["rect"]
        hovered = (self.hovered_button == key)
        bg = (self.window.colors['GREEN'] if (key == "accept" and hovered) else
              self.window.colors['BLUE'] if hovered else self.window.colors['GRAY'])
        pygame.draw.rect(screen, bg, rect, border_radius=10)
        pygame.draw.rect(screen, self.window.colors['WHITE'], rect, 2, border_radius=10)

        text = self.button_font.render(btn["text"], True, self.window.colors['WHITE'])
        screen.blit(text, text.get_rect(center=rect.center))
