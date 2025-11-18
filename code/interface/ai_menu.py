import pygame
from .base_view import BaseView


class AIMenuView(BaseView):
    """Seleccionar dificultad de IA: Solo / Easy / Medium / Hard. Back / Next para navegar."""

    def __init__(self):
        super().__init__()
        self.hovered = None
        self.selected = None  # "None" (Solo), "Easy", "Medium", "Hard"
        self.title_font = None
        self.button_font = None
        self.small_font = None
        self.buttons = {}

    def on_show(self):
        if not self.window:
            return

        # Fonts
        self.title_font = pygame.font.Font(
            None, self.window.get_scaled_size(48))
        self.button_font = pygame.font.Font(
            None, self.window.get_scaled_size(28))
        self.small_font = pygame.font.Font(
            None, self.window.get_scaled_size(18))

        # Layout
        center_x = self.window.width // 2
        center_y = self.window.height // 2

        btn_w = self.window.get_scaled_size(220)
        btn_h = self.window.get_scaled_size(56)
        spacing = self.window.get_scaled_size(18)

        # Four difficulty buttons stacked (including Solo)
        start_y = center_y - (2 * btn_h + spacing)
        self.buttons = {
            "solo": {"rect": pygame.Rect(center_x - btn_w//2, start_y, btn_w, btn_h), "text": "Solo", "value": "None"},
            "easy": {"rect": pygame.Rect(center_x - btn_w//2, start_y + (btn_h + spacing), btn_w, btn_h), "text": "Easy", "value": "Easy"},
            "medium": {"rect": pygame.Rect(center_x - btn_w//2, start_y + 2*(btn_h + spacing), btn_w, btn_h), "text": "Medium", "value": "Medium"},
            "hard": {"rect": pygame.Rect(center_x - btn_w//2, start_y + 3*(btn_h + spacing), btn_w, btn_h), "text": "Hard", "value": "Hard"},
        }

        # Back / Next below
        bottom_y = start_y + 4*(btn_h + spacing) + \
            self.window.get_scaled_size(18)
        side_w = (btn_w - spacing) // 2
        self.buttons.update({
            "back": {"rect": pygame.Rect(center_x - btn_w//2, bottom_y, side_w, btn_h), "text": "Back"},
            "next": {"rect": pygame.Rect(center_x - btn_w//2 + side_w + spacing, bottom_y, side_w, btn_h), "text": "Next"},
        })

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = None
            for k, v in self.buttons.items():
                if v["rect"].collidepoint(event.pos):
                    self.hovered = k
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for k, v in self.buttons.items():
                if v["rect"].collidepoint(event.pos):
                    self._on_button(k)
                    break

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_button("back")
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._on_button("next")

    def _on_button(self, key):
        if key in ("solo", "easy", "medium", "hard"):
            # Get the value from button data
            self.selected = self.buttons[key].get("value", self.buttons[key]["text"])
            # persist selection on window for other views
            if self.window:
                self.window.selected_ai = self.selected
        elif key == "back":
            from .menu_view import MenuView
            self.window.show_view(MenuView())
        elif key == "next":
            # ensure selection stored; allow proceeding even if None
            if self.window:
                self.window.selected_ai = getattr(
                    self.window, "selected_ai", self.selected)
            # go to player setup (same as Play)
            from .player_setup_view import PlayerSetupView
            self.window.show_view(PlayerSetupView())

    def draw(self, screen):
        screen.fill(self.window.colors['DARK_GRAY'])

        # Title
        title_surf = self.title_font.render(
            "AI Difficulty", True, self.window.colors['WHITE'])
        title_rect = title_surf.get_rect(
            center=(self.window.width//2, self.window.get_scaled_size(100)))
        screen.blit(title_surf, title_rect)

        # Draw buttons
        for key, data in self.buttons.items():
            rect = data["rect"]
            is_hover = (self.hovered == key)
            # highlight selected difficulties
            button_value = data.get("value", data["text"])
            if key in ("solo", "easy", "medium", "hard") and self.selected == button_value:
                bg = (40, 90, 40)  # selected greenish
                # Usar get con valor por defecto para evitar KeyError si 'GOLD' no está definido
                border = getattr(self.window, "colors", {}).get(
                    "GOLD", (255, 215, 0))
                text_color = self.window.colors['WHITE']
            else:
                bg = self.window.colors['GRAY'] if not is_hover else self.window.colors['BLUE']
                border = self.window.colors['WHITE']
                text_color = self.window.colors['WHITE']

            pygame.draw.rect(screen, bg, rect, border_radius=6)
            pygame.draw.rect(screen, border, rect, 2, border_radius=6)

            txt = self.button_font.render(data["text"], True, text_color)
            txt_rect = txt.get_rect(center=rect.center)
            screen.blit(txt, txt_rect)

        # Small hint
        hint = "Select difficulty (or Solo) then press Next"
        hint_surf = self.small_font.render(
            hint, True, self.window.colors['GRAY'])
        hint_rect = hint_surf.get_rect(
            center=(self.window.width//2, self.window.get_scaled_size(180)))
        screen.blit(hint_surf, hint_rect)
