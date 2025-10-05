import pygame


class GameUI:
    def __init__(self, game, player_name, window=None):
        self.game = game
        self.player_name = player_name
        self.game_time = 0.0
        self.window = window  # Reference to main window for scaling

        # Fonts will be scaled dynamically
        self.font = None
        self.update_fonts()

    def update_fonts(self):
        """Update font sizes based on window scaling"""
        if self.window:
            font_size = self.window.get_scaled_size(24)
            self.font = pygame.font.Font(None, font_size)
        else:
            self.font = pygame.font.Font(None, 24)

    def update(self, delta_time):
        # Update game time
        self.game_time += delta_time

    def draw(self, screen, x_offset=None):
        # Calculate responsive x_offset if not provided
        if x_offset is None and self.window:
            x_offset = self.window.hud_x
        elif x_offset is None:
            x_offset = 650  # Fallback

        # Draw all UI elements
        self.draw_sidebar(screen, x_offset)

    def draw_sidebar(self, screen, x_offset):
        # Calculate responsive sidebar width
        sidebar_width = 150
        if self.window:
            sidebar_width = self.window.get_scaled_size(150)

        # Background of the sidebar
        sidebar_rect = pygame.Rect(
            x_offset, 0, sidebar_width, screen.get_height())
        pygame.draw.rect(screen, (64, 64, 64), sidebar_rect)  # DARK_GRAY

        # Calculate responsive spacing
        base_spacing = 30
        if self.window:
            base_spacing = self.window.get_scaled_size(30)

        # Player information
        y_pos = 50
        player_text = self.font.render(
            f"Player: {self.player_name}", True, (255, 255, 255))
        screen.blit(player_text, (x_offset + 10, y_pos))

        # Game time
        y_pos += base_spacing
        minutes = int(self.game_time // 60)
        seconds = int(self.game_time % 60)
        time_text = self.font.render(
            f"Time: {minutes:02d}:{seconds:02d}", True, (255, 255, 255))
        screen.blit(time_text, (x_offset + 10, y_pos))

        # Undo information (if player exists in game)
        if hasattr(self.game, '_player') and self.game._player:
            y_pos += base_spacing
            undo_info = self.game._player.get_undo_info()
            undo_count = undo_info["undo_count"]
            max_undos = undo_info["max_undos"]

            # Color based on availability
            undo_color = (0, 255, 0) if undo_count > 0 else (128, 128, 128)
            undo_text = self.font.render(
                f"Undos: {undo_count}/{max_undos}", True, undo_color)
            screen.blit(undo_text, (x_offset + 10, y_pos))

            # Stamina information
            y_pos += base_spacing
            stamina_info = self.game._player.get_stamina_info()
            stamina = stamina_info["stamina"]
            resistance_state = stamina_info["resistance_state"]
            stamina_percentage = int(stamina)
            is_in_recovery_mode = stamina_info["is_in_recovery_mode"]
            recovery_threshold = stamina_info["recovery_threshold"]

            # Stamina label with percentage and state
            stamina_label = f"Stamina: {stamina_percentage}%"

            if is_in_recovery_mode:
                state_label = f"(RECOVERY MODE)"
                recovery_needed = max(0, recovery_threshold - stamina)
                if recovery_needed > 0:
                    state_label += f" Need +{recovery_needed:.0f}"
            else:
                state_label = f"({resistance_state.title()})"

            # Color based on stamina level and recovery mode
            if is_in_recovery_mode:
                stamina_color = (255, 100, 100)  # Bright red - recovery mode
                bar_color = (255, 0, 0)  # Red for recovery bar
            elif stamina > 30:
                stamina_color = (0, 255, 0)  # Green - normal
                bar_color = (0, 200, 0)  # Darker green for bar
            elif stamina <= 30 and stamina > 0:
                stamina_color = (255, 255, 0)  # Yellow - tired
                bar_color = (200, 200, 0)  # Darker yellow for bar
            else:
                stamina_color = (255, 50, 50)  # Red - exhausted
                bar_color = (200, 0, 0)  # Darker red for bar

            # Draw stamina percentage
            stamina_text = self.font.render(stamina_label, True, stamina_color)
            screen.blit(stamina_text, (x_offset + 10, y_pos))

            # Draw state on next line
            y_pos += int(base_spacing * 0.6)
            state_text = self.font.render(state_label, True, stamina_color)
            screen.blit(state_text, (x_offset + 10, y_pos))

            # Draw mini stamina bar
            y_pos += int(base_spacing * 0.6)
            bar_width = self.window.get_scaled_size(
                120) if self.window else 120
            bar_height = self.window.get_scaled_size(6) if self.window else 6

            # Background bar
            pygame.draw.rect(screen, (60, 60, 60),
                             (x_offset + 10, y_pos, bar_width, bar_height))

            # Progress bar
            stamina_progress = stamina / 100.0
            progress_width = int(bar_width * stamina_progress)
            if progress_width > 0:
                pygame.draw.rect(screen, bar_color,
                                 (x_offset + 10, y_pos, progress_width, bar_height))

            # Draw recovery threshold marker if in recovery mode
            if is_in_recovery_mode:
                threshold_progress = recovery_threshold / 100.0
                threshold_x = x_offset + 10 + \
                    int(bar_width * threshold_progress)
                # Draw vertical line at threshold
                pygame.draw.line(screen, (255, 255, 255),
                                 (threshold_x, y_pos),
                                 (threshold_x, y_pos + bar_height + 2), 2)

            # Show recovery status if applicable
            if stamina_info["is_recovering"]:
                y_pos += int(base_spacing * 0.8)
                if is_in_recovery_mode:
                    recovery_text = self.font.render(
                        "CANNOT MOVE", True, (255, 100, 100))
                else:
                    recovery_text = self.font.render(
                        "Recovering...", True, (100, 255, 100))
                screen.blit(recovery_text, (x_offset + 10, y_pos))

        # Scoreboard
        y_pos += base_spacing + 20
        score_title = self.font.render(
            "SCORE", True, (255, 255, 0))  # YELLOW
        screen.blit(score_title, (x_offset + 10, y_pos))

        y_pos += 25
        score_text = self.font.render("Points: 0", True, (255, 255, 255))
        screen.blit(score_text, (x_offset + 10, y_pos))

        # Inventory
        y_pos += base_spacing + 20
        inventory_title = self.font.render("INVENTORY", True, (255, 255, 0))
        screen.blit(inventory_title, (x_offset + 10, y_pos))

        y_pos += 25
        inventory_text = self.font.render("Orders: 0", True, (255, 255, 255))
        screen.blit(inventory_text, (x_offset + 10, y_pos))
