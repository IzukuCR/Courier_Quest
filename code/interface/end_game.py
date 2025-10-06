import pygame
import math  # Add standard math module
from .base_view import BaseView


class EndGameView(BaseView):
    def __init__(self, victory=False, player_stats=None):
        super().__init__()

        # Game result
        self.victory = victory
        self.player_stats = player_stats or {}

        # UI elements
        self.buttons = {}
        self.hovered_button = None

        # Animation variables
        self.animation_timer = 0.0
        self.fade_in_duration = 1.0
        self.text_reveal_delay = 0.5
        self.section_reveal_times = {
            "title": 0.2,
            "result": 0.5,
            "statistics": 1.0,
            "score": 1.5,
            "buttons": 2.0  # Adjusted timing since we removed performance section
        }

        # Fonts (will be initialized in on_show)
        self.title_font = None
        self.header_font = None
        self.text_font = None
        self.small_font = None

        # Colors
        self.victory_color = (50, 200, 50)
        self.defeat_color = (200, 50, 50)
        self.gold_color = (255, 215, 0)
        self.silver_color = (192, 192, 192)
        self.bronze_color = (205, 127, 50)

        # Sections visibility tracking
        self.sections_visible = {
            "title": False,
            "result": False,
            "statistics": False,
            "score": False,
            "buttons": False
        }

        # Add flag to track if score has been saved
        self.score_saved = False
        self.high_scores = []
        self.load_high_scores()

    def on_show(self):
        """Initialize responsive layout when view is shown"""
        if not self.window:
            return

        # Initialize fonts based on window size - Make title bigger
        # Was 72, increased for better readability
        title_size = self.window.get_scaled_size(96)
        header_size = self.window.get_scaled_size(48)
        text_size = self.window.get_scaled_size(28)
        small_size = self.window.get_scaled_size(20)

        self.title_font = pygame.font.Font(None, title_size)
        self.header_font = pygame.font.Font(None, header_size)
        self.text_font = pygame.font.Font(None, text_size)
        self.small_font = pygame.font.Font(None, small_size)

        # Setup buttons
        self.setup_buttons()

        # Reset animation
        self.animation_timer = 0.0
        self.sections_visible = {key: False for key in self.sections_visible}

        print(
            f"EndGameView: Showing {'victory' if self.victory else 'defeat'} screen with responsive layout")

    def setup_buttons(self):
        """Setup responsive button layout"""
        button_width = self.window.get_scaled_size(200)
        button_height = self.window.get_scaled_size(50)
        button_spacing = self.window.get_scaled_size(20)

        center_x = self.window.width // 2
        bottom_area_y = self.window.height - self.window.get_scaled_size(100)

        # Calculate button positions
        total_buttons = 3
        total_width = (total_buttons * button_width) + \
            ((total_buttons - 1) * button_spacing)
        start_x = center_x - (total_width // 2)

        self.buttons = {
            "new_game": {
                "rect": pygame.Rect(start_x, bottom_area_y, button_width, button_height),
                "text": "New Game"
            },
            "main_menu": {
                "rect": pygame.Rect(start_x + button_width + button_spacing, bottom_area_y,
                                    button_width, button_height),
                "text": "Main Menu"
            },
            "quit": {
                "rect": pygame.Rect(start_x + 2 * (button_width + button_spacing), bottom_area_y,
                                    button_width, button_height),
                "text": "Quit Game"
            }
        }

    def handle_event(self, event):
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

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.handle_button_click("main_menu")
            elif event.key == pygame.K_RETURN:
                self.handle_button_click("new_game")

    def handle_button_click(self, button_key):
        """Handle button clicks"""
        print(f"EndGameView: Button clicked: {button_key}")

        if button_key == "new_game":
            # Start a new game
            from .player_setup_view import PlayerSetupView
            player_setup_view = PlayerSetupView()
            self.window.show_view(player_setup_view)

        elif button_key == "main_menu":
            # Return to main menu
            from .menu_view import MenuView
            menu_view = MenuView()
            self.window.show_view(menu_view)

        elif button_key == "quit":
            # Quit the game
            self.window.running = False

    def update(self, delta_time: float):
        """Update animations"""
        self.animation_timer += delta_time

        # Update section visibility based on reveal times
        for section, reveal_time in self.section_reveal_times.items():
            if self.animation_timer >= reveal_time:
                self.sections_visible[section] = True

    def draw(self, screen):
        """Draw the end game screen"""
        # Initialize panel dimensions and positions first
        center_x = self.window.width // 2
        main_panel_width = self.window.get_scaled_size(600)
        main_panel_height = self.window.get_scaled_size(600)

        # Calculate centered positions for both panels
        total_width = main_panel_width + \
            self.window.get_scaled_size(50) + self.window.get_scaled_size(400)
        start_x = (self.window.width - total_width) // 2
        main_panel_x = start_x
        main_panel_y = self.window.height // 2 - main_panel_height // 2

        # Draw background
        if self.victory:
            self.draw_gradient_background(screen, (20, 40, 20), (30, 60, 30))
        else:
            self.draw_gradient_background(screen, (40, 20, 20), (60, 30, 30))

        # Draw main container panel
        if self.sections_visible["statistics"]:
            # Main stats panel
            stats_panel_rect = pygame.Rect(
                main_panel_x,
                main_panel_y,
                main_panel_width,
                main_panel_height
            )
            self.draw_translucent_panel(
                screen, stats_panel_rect, (30, 30, 30, 180))

            # High scores panel
            scores_panel_width = self.window.get_scaled_size(400)
            scores_panel_x = main_panel_x + main_panel_width + \
                self.window.get_scaled_size(50)
            scores_panel_rect = pygame.Rect(
                scores_panel_x,
                main_panel_y,
                scores_panel_width,
                main_panel_height
            )
            self.draw_translucent_panel(
                screen, scores_panel_rect, (30, 30, 30, 180))

            # Draw high scores table in the right panel only
            self.draw_high_scores_table(screen, scores_panel_x + self.window.get_scaled_size(20),
                                        main_panel_y + self.window.get_scaled_size(20))

        # Adjust center_x for the main content to be centered in left panel
        center_x = main_panel_x + (main_panel_width // 2)

        # Draw sections
        current_y = self.window.get_scaled_size(80)

        # Title Section
        if self.sections_visible["title"]:
            self.draw_title_section(screen, center_x, current_y)
            current_y += self.window.get_scaled_size(80)

        # Result Message Section
        if self.sections_visible["result"]:
            self.draw_result_section(screen, center_x, current_y)
            current_y += self.window.get_scaled_size(80)

        # Statistics Section
        if self.sections_visible["statistics"]:
            stats_y = self.window.height // 2 - \
                self.window.get_scaled_size(160)
            self.draw_statistics_section(screen, center_x, stats_y)

        # Score Calculation Section
        if self.sections_visible["score"]:
            score_y = self.window.height // 2 + self.window.get_scaled_size(60)
            self.draw_score_calculation(screen, center_x, score_y)

        # Buttons Section
        if self.sections_visible["buttons"]:
            self.draw_buttons(screen)

    def draw_gradient_background(self, screen, color1, color2):
        """Draw a smooth gradient background"""
        height = screen.get_height()
        for y in range(height):
            # Calculate color interpolation
            ratio = y / height
            r = color1[0] + (color2[0] - color1[0]) * ratio
            g = color1[1] + (color2[1] - color1[1]) * ratio
            b = color1[2] + (color2[2] - color1[2]) * ratio

            # Draw horizontal line with calculated color
            pygame.draw.line(screen, (r, g, b), (0, y),
                             (screen.get_width(), y))

    def draw_translucent_panel(self, screen, rect, color):
        """Draw a translucent panel with rounded corners"""
        # Create a surface with alpha channel
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)

        # Fill with semi-transparent color
        pygame.draw.rect(panel, color, panel.get_rect(), border_radius=10)

        # Draw border
        pygame.draw.rect(panel, (200, 200, 200, 100),
                         panel.get_rect(), width=2, border_radius=10)

        # Draw to screen
        screen.blit(panel, rect.topleft)

    def draw_title_section(self, screen, center_x, y):
        """Draw the title section with enhanced visibility"""
        # Title with stronger glow effect
        if self.victory:
            title_text = "VICTORY!"
            title_color = self.victory_color
            glow_color = (100, 255, 100)  # Green glow
            glow_amount = 5  # Stronger glow for victory
        else:
            title_text = "GAME OVER"
            title_color = (255, 50, 50)  # Brighter red for game over
            glow_color = (255, 100, 100)  # Red glow
            glow_amount = 6  # Extra strong glow for game over

        # Draw extra glow layer for more visibility
        for offset in range(glow_amount + 2, 0, -1):
            alpha = min(255, int((255 - (offset * 40)) * 1.2))  # Brighter glow
            if alpha > 0:
                glow_surface = self.title_font.render(
                    title_text, True, glow_color)
                glow_surface.set_alpha(alpha)
                for dx, dy in [(-offset, -offset), (offset, -offset), (-offset, offset), (offset, offset)]:
                    glow_rect = glow_surface.get_rect(
                        center=(center_x + dx, y + dy))
                    screen.blit(glow_surface, glow_rect)

        # Draw main text with pulsating effect
        pulse_amount = 0
        if self.animation_timer > 1.0:
            pulse_amount = 3 * (1 + math.sin(self.animation_timer * 3)) / 2

        # Main text with enhanced contrast
        text_surface = self.title_font.render(title_text, True, title_color)
        text_rect = text_surface.get_rect(center=(center_x, y))
        screen.blit(text_surface, text_rect)

    def draw_result_section(self, screen, center_x, y):
        """Draw the game result message"""
        if self.victory:
            message = "Congratulations! You reached your income goal!"
            subtitle = f"Goal achieved with {self.get_time_remaining()} remaining"
            message_color = self.gold_color
        else:
            reason = self.get_defeat_reason()
            if reason == "time_up":
                message = "Time's up! You didn't reach your income goal."
                subtitle = f"You earned ${self.player_stats.get('total_earnings', 0)} of ${self.player_stats.get('goal', 3000)}"
            elif reason == "reputation":
                message = "Game Over! Your reputation fell too low."
                subtitle = f"Final reputation: {self.player_stats.get('reputation', 0)}/100"
            elif reason == "no_jobs":
                message = "No more jobs available! Goal not reached."
                subtitle = f"You earned ${self.player_stats.get('total_earnings', 0)} of ${self.player_stats.get('goal', 3000)}"
            else:
                message = "Game Over!"
                subtitle = "Better luck next time!"
            message_color = (200, 200, 200)

        # Draw with smooth fade-in
        alpha = min(
            255, int((self.animation_timer - self.section_reveal_times["result"]) * 510))

        # Main message
        message_surface = self.header_font.render(message, True, message_color)
        message_rect = message_surface.get_rect(center=(center_x, y))
        screen.blit(message_surface, message_rect)

        # Subtitle - Fix color reference here
        subtitle_surface = self.text_font.render(
            # Changed from 'LIGHT_GRAY' to 'GRAY'
            subtitle, True, self.window.colors['GRAY'])
        subtitle_rect = subtitle_surface.get_rect(
            center=(center_x, y + self.window.get_scaled_size(40)))
        screen.blit(subtitle_surface, subtitle_rect)

    def draw_statistics_section(self, screen, center_x, y):
        """Draw player statistics in a nicely formatted table"""
        # Section title with decoration
        stats_title = "Game Statistics"
        stats_title_surface = self.header_font.render(
            stats_title, True, self.gold_color)
        stats_rect = stats_title_surface.get_rect(center=(center_x, y))
        screen.blit(stats_title_surface, stats_rect)

        # Decorative line under the title
        line_y = y + stats_rect.height // 2 + 10
        line_width = self.window.get_scaled_size(600)
        pygame.draw.line(
            screen,
            self.gold_color,
            (center_x - line_width//2, line_y),
            (center_x + line_width//2, line_y),
            2
        )

        # Calculate column positions
        col_spacing = self.window.get_scaled_size(350)
        left_col_x = center_x - col_spacing // 2
        right_col_x = center_x + col_spacing // 2

        # Stats table positioning
        stats_y = y + self.window.get_scaled_size(50)
        row_height = self.window.get_scaled_size(30)

        # Left column stats
        left_stats = [
            ("Total Earnings:",
             f"${self.player_stats.get('total_earnings', 0)}"),
            ("Orders Completed:", str(self.player_stats.get('orders_completed', 0))),
            ("Orders Canceled:", str(self.player_stats.get('orders_canceled', 0))),
            ("On-Time Deliveries:", str(self.player_stats.get('on_time_deliveries', 0)))
        ]

        # Right column stats
        right_stats = [
            ("Final Reputation:",
             f"{self.player_stats.get('reputation', 70)}/100"),
            ("Late Deliveries:", str(self.player_stats.get('late_deliveries', 0))),
            ("Distance Traveled:",
             f"{self.player_stats.get('distance_traveled', 0)} tiles"),
            ("Times Exhausted:", str(self.player_stats.get('times_exhausted', False)))
        ]

        # Draw stats with animated reveal
        animation_offset = self.animation_timer - \
            self.section_reveal_times["statistics"]

        # Draw left column stats
        for i, (label, value) in enumerate(left_stats):
            # Only show rows that have been revealed by the animation
            if i * 0.15 <= animation_offset:
                row_y = stats_y + i * row_height
                alpha = min(255, int((animation_offset - i * 0.15) * 510))

                # Draw stat label
                label_surface = self.text_font.render(
                    label, True, self.window.colors['WHITE'])
                label_rect = label_surface.get_rect(right=left_col_x)
                label_rect.centery = row_y
                screen.blit(label_surface, label_rect)

                # Draw stat value
                value_color = self.get_stat_color(label, value)
                value_surface = self.text_font.render(value, True, value_color)
                screen.blit(value_surface, (left_col_x + 20,
                            row_y - value_surface.get_height() // 2))

        # Draw right column stats
        for i, (label, value) in enumerate(right_stats):
            # Only show rows that have been revealed by the animation
            if i * 0.15 <= animation_offset:
                row_y = stats_y + i * row_height
                alpha = min(255, int((animation_offset - i * 0.15) * 510))

                # Draw stat label
                label_surface = self.text_font.render(
                    label, True, self.window.colors['WHITE'])
                label_rect = label_surface.get_rect(right=right_col_x)
                label_rect.centery = row_y
                screen.blit(label_surface, label_rect)

                # Draw stat value with appropriate color
                value_color = self.get_stat_color(label, value)
                value_surface = self.text_font.render(value, True, value_color)
                screen.blit(value_surface, (right_col_x + 20,
                            row_y - value_surface.get_height() // 2))

    def save_current_score(self):
        """Save current game score"""
        if self.score_saved:
            return

        from ..game.scoreboard import Scoreboard
        # Get the actual player name from game instance
        from ..game.game import Game
        game = Game()
        # Use actual player name instead of default
        player_name = game.get_player_name()

        scoreboard = Scoreboard(player_name)  # Use correct player name

        # Calculate final score components
        base_score = self.player_stats.get('total_earnings', 0)
        reputation_bonus = self.calculate_reputation_bonus()
        time_bonus = self.calculate_time_bonus()
        penalties = self.calculate_penalties()
        final_score = base_score + reputation_bonus + time_bonus - penalties

        # Set score and stats
        scoreboard.score = final_score
        scoreboard.stats = self.player_stats

        # Save score
        if scoreboard.save_score():
            self.score_saved = True
            self.load_high_scores()  # Reload high scores after saving

    def load_high_scores(self):
        """Load high scores from data manager"""
        from ..game.scoreboard import Scoreboard
        self.high_scores = Scoreboard.get_high_scores(limit=5)  # Get top 5

    def draw_score_calculation(self, screen, center_x, y):
        """Draw final score calculation with high scores table"""
        # Save score when this section is drawn
        self.save_current_score()

        # Section title
        score_title = "Final Score Calculation"
        score_title_surface = self.header_font.render(
            score_title, True, self.gold_color)
        title_rect = score_title_surface.get_rect(center=(center_x, y))
        screen.blit(score_title_surface, title_rect)

        # Decorative line
        line_y = y + title_rect.height // 2 + 10
        line_width = self.window.get_scaled_size(500)
        pygame.draw.line(
            screen,
            self.gold_color,
            (center_x - line_width//2, line_y),
            (center_x + line_width//2, line_y),
            2
        )

        # Score components table
        score_y = y + self.window.get_scaled_size(40)
        row_height = self.window.get_scaled_size(30)
        label_x = center_x - self.window.get_scaled_size(180)
        value_x = center_x + self.window.get_scaled_size(150)

        # Calculate score components
        base_score = self.player_stats.get('total_earnings', 0)
        reputation_bonus = self.calculate_reputation_bonus()
        time_bonus = self.calculate_time_bonus()
        penalties = self.calculate_penalties()
        final_score = base_score + reputation_bonus + time_bonus - penalties

        # Define score components with labels, values and colors
        score_components = [
            ("Base Score (Earnings):",
             f"+${base_score}", self.window.colors['WHITE']),
            ("Reputation Bonus:", f"+${reputation_bonus}",
             self.victory_color if reputation_bonus > 0 else self.window.colors['GRAY']),
            ("Time Bonus:", f"+${time_bonus}", self.victory_color if time_bonus >
             0 else self.window.colors['GRAY']),
            ("Penalties:", f"-${penalties}", self.defeat_color if penalties >
             0 else self.window.colors['GRAY']),
        ]

        # Draw score components with animated reveal
        animation_offset = self.animation_timer - \
            self.section_reveal_times["score"]

        # Draw each score component
        for i, (label, value, color) in enumerate(score_components):
            # Only show components that have been revealed by the animation
            if i * 0.2 <= animation_offset:
                row_y = score_y + i * row_height

                # Draw score label (right-aligned)
                label_surface = self.text_font.render(
                    label, True, self.window.colors['WHITE'])
                label_rect = label_surface.get_rect(right=center_x - 20)
                label_rect.centery = row_y
                screen.blit(label_surface, label_rect)

                # Draw score value (left-aligned)
                value_surface = self.text_font.render(value, True, color)
                value_rect = value_surface.get_rect(left=center_x + 20)
                value_rect.centery = row_y
                screen.blit(value_surface, value_rect)

        # Draw separator line
        separator_y = score_y + len(score_components) * row_height + 5
        pygame.draw.line(
            screen,
            self.window.colors['GRAY'],  # Changed from 'LIGHT_GRAY' to 'GRAY'
            (center_x - self.window.get_scaled_size(150), separator_y),
            (center_x + self.window.get_scaled_size(150), separator_y),
            2
        )

        # Draw final score with larger font and more prominence
        if len(score_components) * 0.2 <= animation_offset:
            final_y = separator_y + self.window.get_scaled_size(40)

            # Draw thicker gold separator lines for emphasis
            line_y = final_y - self.window.get_scaled_size(10)
            pygame.draw.line(
                screen,
                self.gold_color,
                (center_x - self.window.get_scaled_size(250), line_y),
                (center_x + self.window.get_scaled_size(250), line_y),
                4  # Thicker line
            )

            # More space before final score
            final_y += self.window.get_scaled_size(40)

            # Draw final score with larger font and animation
            if self.animation_timer > self.section_reveal_times["score"] + 1.0:
                # Reduce pulse effect for better readability
                # Reduced from 0.15
                pulse = 1.0 + 0.08 * math.sin(self.animation_timer * 4)
                # Increased base size for better readability
                pulse_size = int(
                    self.window.get_scaled_size(72) * pulse)  # Was 60
                final_font = pygame.font.Font(None, pulse_size)

                # Simplified text format
                final_text = f"${final_score}"  # Removed "FINAL SCORE:" prefix

                # Draw black outline for better contrast
                self.draw_text_with_outline(
                    screen,
                    final_text,
                    final_font,
                    self.gold_color,
                    center_x,
                    final_y,
                    outline_color=(20, 20, 20)
                )

                # Draw "FINAL SCORE" text above with normal size
                label_y = final_y - self.window.get_scaled_size(40)
                label_surface = self.header_font.render(
                    "FINAL SCORE", True, self.gold_color)
                label_rect = label_surface.get_rect(center=(center_x, label_y))
                screen.blit(label_surface, label_rect)

            else:
                # Static display before animation
                final_text = f"${final_score}"
                final_surface = self.header_font.render(
                    final_text, True, self.gold_color)
                final_rect = final_surface.get_rect(center=(center_x, final_y))
                screen.blit(final_surface, final_rect)

    def draw_buttons(self, screen):
        """Draw the action buttons with smooth fade-in"""
        animation_progress = self.animation_timer - \
            self.section_reveal_times["buttons"]
        if animation_progress <= 0:
            return

        alpha = min(255, int(animation_progress * 510))

        for i, (button_key, button_data) in enumerate(self.buttons.items()):
            # Staggered button appearance
            button_delay = i * 0.15
            if animation_progress <= button_delay:
                continue

            button_alpha = min(
                255, int((animation_progress - button_delay) * 510))

            rect = button_data["rect"]
            text = button_data["text"]

            # Button color based on hover state
            if self.hovered_button == button_key:
                if button_key == "quit":
                    bg_color = self.defeat_color
                elif button_key == "new_game":
                    bg_color = self.victory_color
                else:
                    bg_color = self.window.colors['BLUE']
                border_color = self.window.colors['WHITE']
                text_color = self.window.colors['WHITE']
            else:
                bg_color = (60, 60, 60)
                border_color = (150, 150, 150)
                text_color = (200, 200, 200)

            # Create a surface with per-pixel alpha
            button_surface = pygame.Surface(rect.size, pygame.SRCALPHA)

            # Draw button background
            pygame.draw.rect(button_surface, (*bg_color, button_alpha),
                             button_surface.get_rect(), border_radius=8)
            pygame.draw.rect(button_surface, (*border_color, button_alpha),
                             button_surface.get_rect(), width=2, border_radius=8)

            # Draw button text
            text_surface = self.text_font.render(text, True, text_color)
            text_rect = text_surface.get_rect(
                center=button_surface.get_rect().center)
            button_surface.blit(text_surface, text_rect)

            # Draw button to screen
            screen.blit(button_surface, rect.topleft)

    def draw_text_with_glow(self, screen, text, font, color, x, y, glow_amount=3):
        """Draw text with a glowing effect"""
        # Draw glow
        for offset in range(glow_amount, 0, -1):
            alpha = 255 - (offset * 50)
            if alpha < 0:
                alpha = 0

            glow_color = (color[0], color[1], color[2], alpha)
            glow_surface = font.render(text, True, glow_color)

            # Draw offset versions for the glow
            for dx, dy in [(-offset, -offset), (offset, -offset), (-offset, offset), (offset, offset)]:
                glow_rect = glow_surface.get_rect(center=(x+dx, y+dy))
                screen.blit(glow_surface, glow_rect)

        # Draw main text
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(x, y))
        screen.blit(text_surface, text_rect)

    def draw_text_with_outline(self, screen, text, font, color, x, y, outline_color=(0, 0, 0)):
        """Draw text with outline for better visibility"""
        # Draw outline
        for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
            outline_surface = font.render(text, True, outline_color)
            outline_rect = outline_surface.get_rect(center=(x + dx, y + dy))
            screen.blit(outline_surface, outline_rect)

        # Draw main text
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(x, y))
        screen.blit(text_surface, text_rect)

    def get_stat_color(self, label, value):
        """Get appropriate color for a stat based on its value and label"""
        if "Earnings" in label or "Total" in label:
            return self.gold_color
        elif "Reputation" in label:
            rep_value = 0
            try:
                rep_value = int(value.split('/')[0])
            except:
                pass

            if rep_value >= 90:
                return self.victory_color
            elif rep_value >= 70:
                return self.gold_color
            elif rep_value >= 40:
                return (255, 255, 0)  # Hardcoded yellow color
            else:
                return self.defeat_color
        elif "Late" in label:
            if value == "0":
                return self.victory_color
            else:
                return (255, 255, 0)  # Hardcoded yellow color
        elif "Canceled" in label:
            if value == "0":
                return self.victory_color
            else:
                return self.defeat_color
        elif "On-Time" in label:
            if int(value) > 0:
                return self.victory_color
            else:
                return (255, 255, 0)  # Hardcoded yellow color
        elif "Exhausted" in label:
            if value.lower() == "false":
                return self.victory_color
            else:
                return self.defeat_color

        return self.window.colors['WHITE']

    def draw_high_scores_table(self, screen, x, y):
        """Draw high scores table in a nicely formatted way"""
        # Title - Centered in the panel
        title = "HIGH SCORES TABLE"
        title_surface = self.header_font.render(title, True, self.gold_color)
        title_rect = title_surface.get_rect(
            center=(x + self.window.get_scaled_size(180), y))
        screen.blit(title_surface, title_rect)

        # Center all content within the panel
        panel_width = self.window.get_scaled_size(360)
        start_x = x + ((panel_width - self.window.get_scaled_size(320)) // 2)

        # Draw decorative line
        line_y = y + title_rect.height + 10
        pygame.draw.line(
            screen,
            self.gold_color,
            (start_x, line_y),
            (start_x + self.window.get_scaled_size(320), line_y),
            2
        )

        # Table headers
        header_y = line_y + 30
        headers = ["Rank", "Player", "Score", "Date"]
        # Adjusted positions for centering
        header_x_positions = [0, 60, 180, 260]

        for header, x_offset in zip(headers, header_x_positions):
            header_surface = self.text_font.render(
                header, True, self.window.colors['WHITE'])
            screen.blit(header_surface, (start_x + x_offset, header_y))

        # Draw scores
        row_height = self.window.get_scaled_size(30)
        start_y = header_y + row_height

        for i, score_data in enumerate(self.high_scores[:10]):
            row_y = start_y + (i * row_height)

            # Rank with medal colors for top 3
            rank_text = f"#{i+1}"
            if i == 0:
                rank_color = self.gold_color
            elif i == 1:
                rank_color = self.silver_color
            elif i == 2:
                rank_color = self.bronze_color
            else:
                rank_color = self.window.colors['GRAY']

            # Draw rank
            rank_surface = self.text_font.render(rank_text, True, rank_color)
            screen.blit(rank_surface, (start_x, row_y))

            # Draw player name (truncated if too long)
            name = score_data.get('player_name', 'Unknown')[:12]
            name_surface = self.text_font.render(name, True, rank_color)
            screen.blit(name_surface, (start_x + 60, row_y))

            # Draw score
            score = f"${score_data.get('score', 0)}"
            score_surface = self.text_font.render(score, True, rank_color)
            screen.blit(score_surface, (start_x + 180, row_y))

            # Draw date
            date = score_data.get('date', '').split('T')[0]
            date_surface = self.small_font.render(date, True, rank_color)
            screen.blit(date_surface, (start_x + 260, row_y))

    def get_defeat_reason(self):
        """Get the reason for defeat"""
        return self.player_stats.get('defeat_reason', 'unknown')

    def get_time_remaining(self):
        """Get formatted time remaining when victory was achieved"""
        remaining_seconds = self.player_stats.get('time_remaining', 0)
        minutes = int(remaining_seconds // 60)
        seconds = int(remaining_seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def calculate_reputation_bonus(self):
        """Calculate bonus based on reputation"""
        reputation = self.player_stats.get('reputation', 70)
        if reputation >= 90:
            # 10% bonus
            return int(self.player_stats.get('total_earnings', 0) * 0.1)
        elif reputation >= 80:
            # 5% bonus
            return int(self.player_stats.get('total_earnings', 0) * 0.05)
        return 0

    def calculate_time_bonus(self):
        """Calculate bonus for finishing early"""
        time_remaining = self.player_stats.get('time_remaining', 0)
        if time_remaining <= 0:
            return 0
        elif time_remaining <= 60:
            # Up to 1 minute early
            return int(100 * (time_remaining / 60))
        else:
            # More than 1 minute early
            return 100

    def calculate_penalties(self):
        """Calculate penalties for late deliveries or other issues"""
        penalties = 0
        if self.player_stats.get('late_deliveries', 0) > 0:
            penalties -= 50 * self.player_stats['late_deliveries']
        if self.player_stats.get('times_exhausted', 0) > 0:
            penalties -= 100 * self.player_stats['times_exhausted']
        return penalties

    def get_defeat_reason(self):
        """Get the reason for defeat"""
        return self.player_stats.get('defeat_reason', 'unknown')

    def get_time_remaining(self):
        """Get formatted time remaining when victory was achieved"""
        remaining_seconds = self.player_stats.get('time_remaining', 0)
        minutes = int(remaining_seconds // 60)
        seconds = int(remaining_seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def calculate_reputation_bonus(self):
        """Calculate bonus based on reputation"""
        reputation = self.player_stats.get('reputation', 70)
        if reputation >= 90:
            # 10% bonus
            return int(self.player_stats.get('total_earnings', 0) * 0.1)
        elif reputation >= 80:
            # 5% bonus
            return int(self.player_stats.get('total_earnings', 0) * 0.05)
        return 0

    def calculate_time_bonus(self):
        """Calculate bonus for finishing early"""
        time_remaining = self.player_stats.get('time_remaining', 0)
        if time_remaining <= 0:
            return 0
        elif time_remaining <= 60:
            # Up to 1 minute early
            return int(100 * (time_remaining / 60))
        else:
            # More than 1 minute early
            return 100

    def calculate_penalties(self):
        """Calculate penalties for late deliveries or other issues"""
        penalties = 0
        if self.player_stats.get('late_deliveries', 0) > 0:
            penalties -= 50 * self.player_stats['late_deliveries']
        if self.player_stats.get('times_exhausted', 0) > 0:
            penalties -= 100 * self.player_stats['times_exhausted']
        return penalties
