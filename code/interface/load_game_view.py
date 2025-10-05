import pygame
from .base_view import BaseView
from datetime import datetime


class LoadGameView(BaseView):
    def __init__(self):
        super().__init__()
        self.saves = []
        self.selected_save = 0
        self.hovered_button = None
        self.scroll_offset = 0
        self.max_visible_saves = 8  # Maximum saves visible at once

        # Click tracking for double-click detection
        self.last_click_time = 0
        self.last_clicked_save = -1
        self.double_click_delay = 500  # milliseconds

        # Fonts will be scaled in on_show()
        self.title_font = None
        self.font = None
        self.small_font = None

        # Buttons will be calculated in on_show()
        self.buttons = {}

    def on_show(self):
        """Initialize responsive layout when view is shown"""
        if self.window:
            # Scale fonts
            title_size = self.window.get_scaled_size(48)
            font_size = self.window.get_scaled_size(24)
            small_size = self.window.get_scaled_size(18)

            self.title_font = pygame.font.Font(None, title_size)
            self.font = pygame.font.Font(None, font_size)
            self.small_font = pygame.font.Font(None, small_size)

            # Load available saves
            from ..game.game import Game
            game = Game()
            self.saves = game.list_saves()

            # Calculate button positions - moved significantly higher up
            center_x = self.window.width // 2
            # Changed from -60 to -120 to give more space
            bottom_y = self.window.height - self.window.get_scaled_size(120)

            button_width = self.window.get_scaled_size(
                140)  # Made buttons slightly wider
            button_height = self.window.get_scaled_size(
                45)  # Made buttons slightly taller
            button_spacing = self.window.get_scaled_size(25)

            # Arrange buttons horizontally with better spacing
            total_button_width = button_width * 3 + button_spacing * 2
            start_x = center_x - total_button_width // 2

            self.buttons = {
                "load": {
                    "rect": pygame.Rect(start_x,
                                        bottom_y, button_width, button_height),
                    "text": "Load Game"
                },
                "delete": {
                    "rect": pygame.Rect(start_x + button_width + button_spacing,
                                        bottom_y, button_width, button_height),
                    "text": "Delete Save"
                },
                "back": {
                    "rect": pygame.Rect(start_x + (button_width + button_spacing) * 2,
                                        bottom_y, button_width, button_height),
                    "text": "Back"
                }
            }

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.go_back()
            elif event.key == pygame.K_UP and self.saves:
                self.selected_save = (self.selected_save - 1) % len(self.saves)
                self._ensure_selected_visible()
            elif event.key == pygame.K_DOWN and self.saves:
                self.selected_save = (self.selected_save + 1) % len(self.saves)
                self._ensure_selected_visible()
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.saves:
                self.load_selected_game()

        elif event.type == pygame.MOUSEWHEEL:
            # Handle scrolling
            if self.saves:
                old_offset = self.scroll_offset
                self.scroll_offset = max(0, min(
                    max(0, len(self.saves) - self.max_visible_saves),
                    self.scroll_offset - event.y
                ))

        elif event.type == pygame.MOUSEMOTION:
            self.hovered_button = None
            for button_key, button_data in self.buttons.items():
                if button_data["rect"].collidepoint(event.pos):
                    self.hovered_button = button_key
                    break

            # Check if hovering over save entries
            self._update_hovered_save(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Handle button clicks first
            button_clicked = False
            for button_key, button_data in self.buttons.items():
                if button_data["rect"].collidepoint(event.pos):
                    if button_key == "load" and self.saves:
                        self.load_selected_game()
                    elif button_key == "delete" and self.saves:
                        self.delete_selected_save()
                    elif button_key == "back":
                        self.go_back()
                    button_clicked = True
                    break

            # Handle save list clicks if no button was clicked
            if not button_clicked and self.saves:
                clicked_save = self._get_clicked_save(event.pos)
                if clicked_save >= 0:
                    current_time = pygame.time.get_ticks()

                    # Check for double-click
                    if (clicked_save == self.last_clicked_save and
                            current_time - self.last_click_time < self.double_click_delay):
                        # Double click - load game
                        self.selected_save = clicked_save
                        self.load_selected_game()
                    else:
                        # Single click - just select
                        self.selected_save = clicked_save

                    self.last_clicked_save = clicked_save
                    self.last_click_time = current_time

    def load_selected_game(self):
        if not self.saves or self.selected_save >= len(self.saves):
            print("LoadGameView: No saves available or invalid selection")
            return

        save_name = self.saves[self.selected_save]['name']
        print(f"LoadGameView: Attempting to load save: {save_name}")

        from ..game.game import Game
        game = Game()

        print(f"LoadGameView: Got game instance: {game}")

        if game.load_game(save_name):
            print(
                f"LoadGameView: Successfully loaded {save_name}, transitioning to game view")
            # Successfully loaded, go to game view
            from .game_view import GameView
            game_view = GameView()
            self.window.show_view(game_view)
        else:
            print(f"LoadGameView: Failed to load save: {save_name}")

    def delete_selected_save(self):
        if not self.saves or self.selected_save >= len(self.saves):
            print("LoadGameView: No saves available or invalid selection for delete")
            return

        save_name = self.saves[self.selected_save]['name']
        print(f"LoadGameView: Attempting to delete save: {save_name}")

        from ..game.game import Game
        game = Game()

        if game.delete_save(save_name):
            print(f"LoadGameView: Successfully deleted save: {save_name}")
            # Refresh save list
            self.saves = game.list_saves()
            if self.selected_save >= len(self.saves) and self.saves:
                self.selected_save = len(self.saves) - 1
            elif not self.saves:
                self.selected_save = 0
        else:
            print(f"LoadGameView: Failed to delete save: {save_name}")

    def go_back(self):
        from .menu_view import MenuView
        menu_view = MenuView()
        self.window.show_view(menu_view)

    def _update_hovered_save(self, mouse_pos):
        """Update which save is being hovered over"""
        if not self.saves:
            return

        save_y_start = self.window.get_scaled_size(
            140)  # Updated to match draw method
        save_height = self.window.get_scaled_size(40)

        visible_saves = self.saves[self.scroll_offset:
                                   self.scroll_offset + self.max_visible_saves]

        for i, save in enumerate(visible_saves):
            actual_index = self.scroll_offset + i
            save_rect = pygame.Rect(self.window.width // 2 - 200,
                                    save_y_start + i * (save_height + 5),
                                    400, save_height)
            if save_rect.collidepoint(mouse_pos):
                # Could add hover effect here if desired
                pass

    def _get_clicked_save(self, mouse_pos):
        """Get the index of the clicked save, or -1 if none"""
        if not self.saves:
            return -1

        save_y_start = self.window.get_scaled_size(
            140)  # Updated to match draw method
        save_height = self.window.get_scaled_size(40)

        visible_saves = self.saves[self.scroll_offset:
                                   self.scroll_offset + self.max_visible_saves]

        for i, save in enumerate(visible_saves):
            actual_index = self.scroll_offset + i
            save_rect = pygame.Rect(self.window.width // 2 - 200,
                                    save_y_start + i * (save_height + 5),
                                    400, save_height)
            if save_rect.collidepoint(mouse_pos):
                return actual_index
        return -1

    def _ensure_selected_visible(self):
        """Ensure the selected save is visible in the scroll area"""
        if self.selected_save < self.scroll_offset:
            self.scroll_offset = self.selected_save
        elif self.selected_save >= self.scroll_offset + self.max_visible_saves:
            self.scroll_offset = self.selected_save - self.max_visible_saves + 1

        self.scroll_offset = max(0, min(
            max(0, len(self.saves) - self.max_visible_saves),
            self.scroll_offset
        ))

    def draw(self, screen):
        screen.fill(self.window.colors['DARK_GRAY'])

        center_x = self.window.width // 2

        # Title
        title_text = self.title_font.render(
            "Load Game", True, self.window.colors['WHITE'])
        title_rect = title_text.get_rect(
            center=(center_x, self.window.get_scaled_size(80)))
        screen.blit(title_text, title_rect)

        if not self.saves:
            # No saves available
            no_saves_text = self.font.render(
                "No saved games found", True, self.window.colors['GRAY'])
            no_saves_rect = no_saves_text.get_rect(
                center=(center_x, self.window.height // 2))
            screen.blit(no_saves_text, no_saves_rect)
        else:
            # Draw save list with scroll support - adjusted area
            save_y_start = self.window.get_scaled_size(140)  # Start higher up
            save_height = self.window.get_scaled_size(40)

            # Calculate available space for saves (leave room for buttons and instructions)
            available_height = self.window.height - \
                save_y_start - self.window.get_scaled_size(180)
            max_saves_that_fit = available_height // (save_height + 5)
            self.max_visible_saves = max(
                4, min(8, max_saves_that_fit))  # Between 4-8 saves

            # Get visible saves based on scroll
            visible_saves = self.saves[self.scroll_offset:
                                       self.scroll_offset + self.max_visible_saves]

            for i, save in enumerate(visible_saves):
                actual_index = self.scroll_offset + i
                y_pos = save_y_start + i * (save_height + 5)

                # Background for save entry
                save_rect = pygame.Rect(
                    center_x - 200, y_pos, 400, save_height)

                if actual_index == self.selected_save:
                    pygame.draw.rect(
                        screen, self.window.colors['BLUE'], save_rect)
                else:
                    pygame.draw.rect(screen, (60, 60, 60), save_rect)

                pygame.draw.rect(
                    screen, self.window.colors['WHITE'], save_rect, 2)

                # Save name
                name_text = self.font.render(
                    save['name'], True, self.window.colors['WHITE'])
                screen.blit(name_text, (save_rect.x + 10, save_rect.y + 5))

                # Timestamp
                time_str = save['timestamp'].strftime("%Y-%m-%d %H:%M")
                time_color = self.window.colors.get(
                    'LIGHT_GRAY', self.window.colors.get('GRAY', (128, 128, 128)))
                time_text = self.small_font.render(time_str, True, time_color)
                screen.blit(time_text, (save_rect.x + 10, save_rect.y + 22))

                # File size
                size_kb = save['size'] / 1024
                size_text = self.small_font.render(
                    f"{size_kb:.1f} KB", True, time_color)
                size_rect = size_text.get_rect(
                    right=save_rect.right - 10, centery=save_rect.centery)
                screen.blit(size_text, size_rect)

            # Draw scroll indicator if needed
            if len(self.saves) > self.max_visible_saves:
                self._draw_scroll_indicator(screen, save_y_start, save_height)

        # Draw buttons
        for button_key, button_data in self.buttons.items():
            self._draw_button(screen, button_key, button_data)

        # Instructions with better positioning and contrast
        if self.saves:
            instruction_y = self.window.height - \
                self.window.get_scaled_size(70)  # Above buttons

            # Draw background for better text visibility
            instruction_text = "Double-click to load • Single-click to select • Mouse wheel to scroll"
            text_surface = self.small_font.render(
                instruction_text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(center_x, instruction_y))

            # Draw semi-transparent background
            bg_rect = text_rect.copy()
            bg_rect.inflate(20, 8)
            # Semi-transparent black
            pygame.draw.rect(screen, (0, 0, 0, 128), bg_rect)
            pygame.draw.rect(screen, (80, 80, 80), bg_rect, 1)  # Border

            screen.blit(text_surface, text_rect)

    def _draw_scroll_indicator(self, screen, save_y_start, save_height):
        """Draw scroll bar indicator"""
        if len(self.saves) <= self.max_visible_saves:
            return

        # Scroll bar area - adjusted position
        scroll_x = self.window.width // 2 + 210
        scroll_y = save_y_start
        scroll_width = 12  # Made slightly wider
        scroll_height = self.max_visible_saves * (save_height + 5) - 5

        # Background with border
        pygame.draw.rect(screen, (30, 30, 30),
                         (scroll_x, scroll_y, scroll_width, scroll_height))
        pygame.draw.rect(screen, (80, 80, 80),
                         (scroll_x, scroll_y, scroll_width, scroll_height), 1)

        # Thumb
        thumb_height = max(20, scroll_height *
                           self.max_visible_saves // len(self.saves))
        thumb_y = scroll_y + (scroll_height - thumb_height) * \
            self.scroll_offset // max(1, len(self.saves) -
                                      self.max_visible_saves)

        # Thumb with gradient effect
        pygame.draw.rect(screen, (120, 120, 120),
                         (scroll_x + 1, thumb_y, scroll_width - 2, thumb_height))
        pygame.draw.rect(screen, (150, 150, 150),
                         (scroll_x + 1, thumb_y, scroll_width - 2, thumb_height), 1)

    def _draw_button(self, screen, button_key, button_data):
        rect = button_data["rect"]
        text = button_data["text"]

        # Determine if button should be enabled
        enabled = True
        if button_key in ("load", "delete") and not self.saves:
            enabled = False

        # Enhanced button styling
        if not enabled:
            bg_color = (40, 40, 40)
            text_color = (100, 100, 100)
            border_color = (60, 60, 60)
        elif self.hovered_button == button_key:
            bg_color = self.window.colors['BLUE']
            text_color = self.window.colors['WHITE']
            border_color = (255, 255, 255)
        else:
            # Darker than original GRAY for better contrast
            bg_color = (80, 80, 80)
            text_color = self.window.colors['WHITE']
            border_color = (120, 120, 120)

        # Draw button with shadow effect
        shadow_rect = rect.copy()
        shadow_rect.move_ip(2, 2)
        pygame.draw.rect(screen, (20, 20, 20), shadow_rect)  # Shadow

        pygame.draw.rect(screen, bg_color, rect)
        pygame.draw.rect(screen, border_color, rect, 2)

        # Button text
        text_surface = self.font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)
