"""
Game UI module for displaying player information during gameplay.

This module handles the user interface that shows up while playing
the game, like the player's name, time, stamina bar, and score.
It draws everything on the right side of the screen.
"""

import pygame


class GameUI:
    """
    Manages the game's user interface display.
    
    This class draws all the UI elements like player info,
    stamina, score, and inventory on the screen. It updates
    in real-time as the player plays.
    """
    def __init__(self, game, player_name, window=None):
        """
        Create a new game UI.
        
        Args:
            game: The main game object
            player_name: Name of the current player
            window: Main window for responsive scaling
        """
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

    def _draw_gradient_rect(self, screen, rect, color1, color2):
        """Draw a vertical gradient rectangle."""
        for y in range(rect.height):
            # Calculate blend ratio
            ratio = y / rect.height
            # Interpolate colors
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            # Draw line
            pygame.draw.line(screen, (r, g, b), 
                           (rect.x, rect.y + y), (rect.x + rect.width, rect.y + y))

    def _draw_section_header(self, screen, text, x, y, width):
        """Draw a styled section header."""
        # Header background
        header_rect = pygame.Rect(x + 5, y - 5, width - 10, 25)
        pygame.draw.rect(screen, (70, 70, 80), header_rect)
        pygame.draw.rect(screen, (100, 100, 110), header_rect, 1)
        
        # Header text
        header_text = self.font.render(text, True, (255, 255, 255))
        text_rect = header_text.get_rect(center=(x + width // 2, y + 7))
        screen.blit(header_text, text_rect)
        
        return y + 35  # Return next Y position

    def draw(self, screen, x_offset=None):
        # Calculate responsive x_offset if not provided
        if x_offset is None and self.window:
            x_offset = self.window.hud_x
        elif x_offset is None:
            x_offset = 650  # Fallback

        # Draw all UI elements
        self.draw_sidebar(screen, x_offset)

    def draw_sidebar(self, screen, x_offset):
        """
        Draw a beautiful game sidebar with player stats and status.
        
        This creates a modern-looking sidebar with rounded corners,
        gradient backgrounds, and color-coded information sections.
        """
        # Calculate responsive sidebar width - make it wider for better layout
        sidebar_width = 200
        if self.window:
            sidebar_width = self.window.get_scaled_size(200)

        # Create sidebar with rounded corners and gradient
        sidebar_rect = pygame.Rect(x_offset, 10, sidebar_width - 10, screen.get_height() - 20)
        
        # Draw gradient background
        self._draw_gradient_rect(screen, sidebar_rect, (45, 45, 55), (25, 25, 35))
        
        # Draw border
        pygame.draw.rect(screen, (80, 80, 90), sidebar_rect, 2)

        # Start drawing organized sections
        current_y = 30
        
        # === PLAYER INFO SECTION ===
        current_y = self._draw_section_header(screen, "PLAYER INFO", x_offset, current_y, sidebar_width)
        
        # Player name with icon
        player_text = self.font.render(f"👤 {self.player_name}", True, (255, 255, 255))
        screen.blit(player_text, (x_offset + 15, current_y))
        current_y += 25
        
        # Game time with clock icon and better formatting
        minutes = int(self.game_time // 60)
        seconds = int(self.game_time % 60)
        time_color = (255, 255, 100) if minutes < 2 else (255, 255, 255)  # Yellow when time is low
        time_text = self.font.render(f"🕐 {minutes:02d}:{seconds:02d}", True, time_color)
        screen.blit(time_text, (x_offset + 15, current_y))
        current_y += 40

        # === STAMINA & STATUS SECTION ===
        if hasattr(self.game, '_player') and self.game._player:
            current_y = self._draw_section_header(screen, "STATUS", x_offset, current_y, sidebar_width)
            
            # Get player info
            stamina_info = self.game._player.get_stamina_info()
            undo_info = self.game._player.get_undo_info()
            stamina = stamina_info["stamina"]
            stamina_percentage = int(stamina)
            is_in_recovery_mode = stamina_info["is_in_recovery_mode"]
            
            # Stamina with modern progress bar
            stamina_text = self.font.render(f"💪 Stamina: {stamina_percentage}%", True, (255, 255, 255))
            screen.blit(stamina_text, (x_offset + 15, current_y))
            current_y += 20
            
            # Modern stamina progress bar
            bar_width = sidebar_width - 30
            bar_height = 8
            bar_x = x_offset + 15
            
            # Background bar with rounded edges
            pygame.draw.rect(screen, (40, 40, 40), (bar_x, current_y, bar_width, bar_height))
            
            # Progress bar with color based on stamina level
            if is_in_recovery_mode:
                bar_color = (255, 80, 80)  # Red for recovery
            elif stamina > 60:
                bar_color = (80, 255, 80)  # Green for good
            elif stamina > 30:
                bar_color = (255, 255, 80)  # Yellow for tired
            else:
                bar_color = (255, 120, 80)  # Orange for low
                
            progress_width = int(bar_width * (stamina / 100.0))
            if progress_width > 0:
                pygame.draw.rect(screen, bar_color, (bar_x, current_y, progress_width, bar_height))
            
            current_y += 25
            
            # Status message
            if is_in_recovery_mode:
                status_text = self.font.render("⚠️ RECOVERY MODE", True, (255, 100, 100))
            elif stamina <= 30:
                status_text = self.font.render("😴 Tired", True, (255, 255, 100))
            else:
                status_text = self.font.render("✅ Normal", True, (100, 255, 100))
            screen.blit(status_text, (x_offset + 15, current_y))
            current_y += 25
            
            # Undo information
            undo_count = undo_info["undo_count"] 
            max_undos = undo_info["max_undos"]
            undo_color = (100, 255, 100) if undo_count > 0 else (128, 128, 128)
            undo_text = self.font.render(f"↩️ Undos: {undo_count}/{max_undos}", True, undo_color)
            screen.blit(undo_text, (x_offset + 15, current_y))
            current_y += 40

        # === SCORE SECTION ===
        current_y = self._draw_section_header(screen, "SCORE & PROGRESS", x_offset, current_y, sidebar_width)
        
        # Get score information
        current_score = 0
        goal = 3000  # Default goal
        if hasattr(self.game, '_scoreboard') and self.game._scoreboard:
            current_score = self.game._scoreboard.get_score()
        if hasattr(self.game, '_goal'):
            goal = self.game._goal
            
        # Score with money icon
        score_text = self.font.render(f"💰 ${current_score}", True, (255, 215, 0))
        screen.blit(score_text, (x_offset + 15, current_y))
        current_y += 20
        
        # Goal progress bar
        goal_text = self.font.render(f"🎯 Goal: ${goal}", True, (200, 200, 200))
        screen.blit(goal_text, (x_offset + 15, current_y))
        current_y += 20
        
        # Progress bar for goal
        progress_ratio = min(1.0, current_score / goal) if goal > 0 else 0
        bar_width = sidebar_width - 30
        bar_height = 8
        bar_x = x_offset + 15
        
        # Background
        pygame.draw.rect(screen, (40, 40, 40), (bar_x, current_y, bar_width, bar_height))
        
        # Progress with color gradient based on completion
        if progress_ratio >= 1.0:
            progress_color = (0, 255, 0)  # Green when complete
        elif progress_ratio >= 0.75:
            progress_color = (255, 215, 0)  # Gold when close
        elif progress_ratio >= 0.5:
            progress_color = (255, 165, 0)  # Orange when halfway
        else:
            progress_color = (255, 100, 100)  # Red when far
            
        progress_width = int(bar_width * progress_ratio)
        if progress_width > 0:
            pygame.draw.rect(screen, progress_color, (bar_x, current_y, progress_width, bar_height))
        
        current_y += 25
        
        # Progress percentage
        progress_pct = int(progress_ratio * 100)
        progress_text = self.font.render(f"📊 {progress_pct}% Complete", True, (255, 255, 255))
        screen.blit(progress_text, (x_offset + 15, current_y))
        current_y += 40
        
        # === INVENTORY SECTION ===
        current_y = self._draw_section_header(screen, "INVENTORY", x_offset, current_y, sidebar_width)
        
        # Get inventory info
        if hasattr(self.game, '_player') and self.game._player and hasattr(self.game._player, 'inventory'):
            inventory = self.game._player.inventory
            order_count = len(inventory.accepted)
            weight = inventory.carried_weight()
            capacity = inventory.capacity_weight
            
            orders_text = self.font.render(f"📦 Orders: {order_count}", True, (255, 255, 255))
            screen.blit(orders_text, (x_offset + 15, current_y))
            current_y += 20
            
            weight_color = (255, 100, 100) if weight >= capacity * 0.9 else (255, 255, 255)
            weight_text = self.font.render(f"⚖️ Weight: {weight:.1f}/{capacity}", True, weight_color)
            screen.blit(weight_text, (x_offset + 15, current_y))
        else:
            orders_text = self.font.render("📦 Orders: 0", True, (255, 255, 255))
            screen.blit(orders_text, (x_offset + 15, current_y))
