import pygame
from .base_view import BaseView


class ScoresManagerView(BaseView):
    def __init__(self):
        super().__init__()
        self.high_scores = []
        self.selected_score = 0
        self.hovered_button = None
        self.scroll_offset = 0
        self.max_visible_scores = 10

        # Fonts will be initialized in on_show()
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

            # Load high scores
            from ..game.scoreboard import Scoreboard
            self.high_scores = Scoreboard.get_all_scores()

            # Calculate button positions
            center_x = self.window.width // 2
            bottom_y = self.window.height - self.window.get_scaled_size(80)

            button_width = self.window.get_scaled_size(160)
            button_height = self.window.get_scaled_size(45)
            button_spacing = self.window.get_scaled_size(20)

            # Create two buttons side by side
            total_width = (button_width * 2) + button_spacing
            start_x = center_x - (total_width // 2)

            self.buttons = {
                "delete": {
                    "rect": pygame.Rect(start_x, bottom_y, button_width, button_height),
                    "text": "Delete Score"
                },
                "back": {
                    "rect": pygame.Rect(start_x + button_width + button_spacing,
                                        bottom_y, button_width, button_height),
                    "text": "Back"
                }
            }

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.go_back()
            elif event.key == pygame.K_UP and self.high_scores:
                self.selected_score = (
                    self.selected_score - 1) % len(self.high_scores)
                self._ensure_selected_visible()
            elif event.key == pygame.K_DOWN and self.high_scores:
                self.selected_score = (
                    self.selected_score + 1) % len(self.high_scores)
                self._ensure_selected_visible()

        elif event.type == pygame.MOUSEWHEEL:
            if self.high_scores:
                self.scroll_offset = max(0, min(
                    len(self.high_scores) - self.max_visible_scores,
                    self.scroll_offset - event.y
                ))

        elif event.type == pygame.MOUSEMOTION:
            self.hovered_button = None
            for button_key, button_data in self.buttons.items():
                if button_data["rect"].collidepoint(event.pos):
                    self.hovered_button = button_key
                    break

            # Check if hovering over scores
            clicked_score = self._get_score_at_position(event.pos)
            if clicked_score >= 0:
                self.selected_score = clicked_score

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Handle button clicks
            for button_key, button_data in self.buttons.items():
                if button_data["rect"].collidepoint(event.pos):
                    if button_key == "delete":
                        self.delete_selected_score()
                    elif button_key == "back":
                        self.go_back()
                    break

    def delete_selected_score(self):
        """Delete the currently selected score"""
        if not self.high_scores or self.selected_score >= len(self.high_scores):
            return

        # Get the selected score data
        score_data = self.high_scores[self.selected_score]
        player_name = score_data.get('player_name')
        score = score_data.get('score')
        date = score_data.get('date')

        # Delete score from storage using DataManager
        from ..services.data_manager import DataManager
        data_manager = DataManager.get_instance()
        if data_manager.delete_score(player_name, score, date):
            # Remove from local list
            self.high_scores.pop(self.selected_score)

            # Adjust selected score if needed
            if self.selected_score >= len(self.high_scores):
                self.selected_score = max(0, len(self.high_scores) - 1)

            # Adjust scroll offset if needed
            max_scroll = max(0, len(self.high_scores) -
                             self.max_visible_scores)
            self.scroll_offset = min(self.scroll_offset, max_scroll)

    def go_back(self):
        from .menu_view import MenuView
        menu_view = MenuView()
        self.window.show_view(menu_view)

    def _ensure_selected_visible(self):
        """Ensure the selected score is visible in the scroll area"""
        if self.selected_score < self.scroll_offset:
            self.scroll_offset = self.selected_score
        elif self.selected_score >= self.scroll_offset + self.max_visible_scores:
            self.scroll_offset = self.selected_score - self.max_visible_scores + 1

    def _get_score_at_position(self, pos):
        """Get the score index at the given position"""
        if not self.high_scores:
            return -1

        x, y = pos
        score_y = self.window.get_scaled_size(120)
        score_height = self.window.get_scaled_size(40)
        score_area_rect = pygame.Rect(
            self.window.width // 2 - 300,
            score_y,
            600,
            score_height * self.max_visible_scores
        )

        if not score_area_rect.collidepoint(x, y):
            return -1

        idx = (y - score_y) // score_height + self.scroll_offset
        if 0 <= idx < len(self.high_scores):
            return idx
        return -1

    def draw(self, screen):
        screen.fill(self.window.colors['DARK_GRAY'])

        # Draw title
        title = "HIGH SCORES"
        title_surface = self.title_font.render(
            title, True, self.window.colors['WHITE'])
        title_rect = title_surface.get_rect(
            center=(self.window.width // 2, self.window.get_scaled_size(60)))
        screen.blit(title_surface, title_rect)

        if not self.high_scores:
            # Show message when no scores exist
            no_scores_text = self.font.render(
                "No high scores yet!", True, self.window.colors['GRAY'])
            no_scores_rect = no_scores_text.get_rect(
                center=(self.window.width // 2, self.window.height // 2))
            screen.blit(no_scores_text, no_scores_rect)
        else:
            # Draw scores table
            self._draw_scores_table(screen)

        # Draw buttons
        for button_key, button_data in self.buttons.items():
            self._draw_button(screen, button_key, button_data)

        # Draw instructions
        if self.high_scores:
            instructions = "Use mouse wheel to scroll • Click to select • Press DELETE to remove"
            inst_surface = self.small_font.render(
                instructions, True, self.window.colors['GRAY'])
            inst_rect = inst_surface.get_rect(center=(
                self.window.width // 2, self.window.height - self.window.get_scaled_size(120)))
            screen.blit(inst_surface, inst_rect)

    def _draw_scores_table(self, screen):
        """Draw the high scores table"""
        start_y = self.window.get_scaled_size(120)
        row_height = self.window.get_scaled_size(40)
        visible_scores = self.high_scores[self.scroll_offset:
                                          self.scroll_offset + self.max_visible_scores]

        # Draw table headers
        headers = ["Rank", "Player", "Score", "Date"]
        header_positions = [0, 100, 300, 400]
        header_y = start_y - self.window.get_scaled_size(30)

        for header, x_offset in zip(headers, header_positions):
            header_surface = self.font.render(header, True, self.gold_color)
            screen.blit(header_surface, (self.window.width //
                        2 - 250 + x_offset, header_y))

        # Draw scores
        for i, score in enumerate(visible_scores):
            actual_index = i + self.scroll_offset
            y = start_y + (i * row_height)

            # Row background
            row_rect = pygame.Rect(self.window.width //
                                   2 - 300, y, 600, row_height - 2)
            if actual_index == self.selected_score:
                pygame.draw.rect(screen, self.window.colors['BLUE'], row_rect)
            elif i % 2 == 0:
                pygame.draw.rect(screen, (40, 40, 40), row_rect)
            else:
                pygame.draw.rect(screen, (50, 50, 50), row_rect)

            # Rank
            rank_text = f"#{actual_index + 1}"
            rank_color = self.get_rank_color(actual_index)
            rank_surface = self.font.render(rank_text, True, rank_color)
            screen.blit(rank_surface, (self.window.width // 2 - 250, y + 5))

            # Player name
            name = score.get('player_name', 'Unknown')[:15]
            name_surface = self.font.render(name, True, rank_color)
            screen.blit(name_surface, (self.window.width // 2 - 150, y + 5))

            # Score
            score_value = f"${score.get('score', 0)}"
            score_surface = self.font.render(score_value, True, rank_color)
            screen.blit(score_surface, (self.window.width // 2 + 50, y + 5))

            # Date
            date = score.get('date', '').split('T')[0]
            date_surface = self.small_font.render(
                date, True, self.window.colors['GRAY'])
            screen.blit(date_surface, (self.window.width // 2 + 150, y + 10))

    def _draw_button(self, screen, button_key, button_data):
        """Draw a button with hover effect"""
        rect = button_data["rect"]
        text = button_data["text"]

        if self.hovered_button == button_key:
            bg_color = self.window.colors['BLUE']
            text_color = self.window.colors['WHITE']
        else:
            bg_color = (60, 60, 60)
            text_color = self.window.colors['GRAY']

        pygame.draw.rect(screen, bg_color, rect, border_radius=5)
        pygame.draw.rect(
            screen, self.window.colors['WHITE'], rect, 2, border_radius=5)

        text_surface = self.font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)

    def get_rank_color(self, rank):
        """Get color based on ranking"""
        if rank == 0:
            return self.gold_color
        elif rank == 1:
            return self.silver_color
        elif rank == 2:
            return self.bronze_color
        return self.window.colors['WHITE']

    @property
    def gold_color(self):
        return (255, 215, 0)

    @property
    def silver_color(self):
        return (192, 192, 192)

    @property
    def bronze_color(self):
        return (205, 127, 50)
