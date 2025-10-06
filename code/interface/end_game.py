import pygame
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

    def on_show(self):
        """Initialize responsive layout when view is shown"""
        
        # Initialize fonts based on window size
        base_font_size = max(16, self.window.height // 40)
        self.title_font = pygame.font.Font(None, base_font_size * 3)
        self.header_font = pygame.font.Font(None, base_font_size * 2)
        self.text_font = pygame.font.Font(None, base_font_size)
        self.small_font = pygame.font.Font(None, max(14, base_font_size - 4))
        
        # Setup buttons
        self.setup_buttons()
        
        # Reset animation
        self.animation_timer = 0.0
        
        print(f"EndGameView: Showing {'victory' if self.victory else 'defeat'} screen")

    def setup_buttons(self):
        """Setup responsive button layout"""
        button_width = self.window.get_scaled_size(200)
        button_height = self.window.get_scaled_size(50)
        button_spacing = self.window.get_scaled_size(20)
        
        center_x = self.window.width // 2
        bottom_area_y = self.window.height - self.window.get_scaled_size(120)
        
        # Calculate button positions
        total_buttons = 3
        total_width = (total_buttons * button_width) + ((total_buttons - 1) * button_spacing)
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

    def draw(self, screen):
        """Draw the end game screen"""
        # Background with fade-in effect
        alpha = min(255, int((self.animation_timer / self.fade_in_duration) * 255))
        
        if self.victory:
            bg_color = (20, 40, 20)  # Dark green
        else:
            bg_color = (40, 20, 20)  # Dark red
            
        screen.fill(bg_color)
        
        # Draw main content if animation has progressed enough
        if self.animation_timer > self.text_reveal_delay:
            self.draw_main_content(screen)
            
        # Draw buttons (always visible)
        self.draw_buttons(screen)

    def draw_main_content(self, screen):
        """Draw the main content of the end game screen"""
        center_x = self.window.width // 2
        current_y = self.window.get_scaled_size(80)
        
        # Title
        if self.victory:
            title_text = "VICTORY!"
            title_color = self.victory_color
        else:
            title_text = "GAME OVER"
            title_color = self.defeat_color
            
        title_surface = self.title_font.render(title_text, True, title_color)
        title_rect = title_surface.get_rect(center=(center_x, current_y))
        screen.blit(title_surface, title_rect)
        
        current_y += self.window.get_scaled_size(80)
        
        # Game Result Message
        self.draw_result_message(screen, center_x, current_y)
        current_y += self.window.get_scaled_size(60)
        
        # Player Statistics
        self.draw_statistics(screen, center_x, current_y)
        current_y += self.window.get_scaled_size(200)
        
        # Final Score Calculation
        self.draw_final_score(screen, center_x, current_y)
        current_y += self.window.get_scaled_size(80)
        
        # Performance Summary
        self.draw_performance_summary(screen, center_x, current_y)

    def draw_result_message(self, screen, center_x, y):
        """Draw the game result message"""
        if self.victory:
            message = "Congratulations! You reached your income goal!"
            subtitle = f"Goal achieved with {self.get_time_remaining()} remaining"
        else:
            reason = self.get_defeat_reason()
            if reason == "time":
                message = "Time's up! You didn't reach your income goal."
                subtitle = f"You earned ${self.player_stats.get('total_earnings', 0)} of ${self.player_stats.get('goal', 3000)}"
            elif reason == "reputation":
                message = "Game Over! Your reputation fell too low."
                subtitle = f"Final reputation: {self.player_stats.get('reputation', 0)}/100"
            else:
                message = "Game Over!"
                subtitle = "Better luck next time!"
        
        # Main message
        message_surface = self.header_font.render(message, True, self.window.colors['WHITE'])
        message_rect = message_surface.get_rect(center=(center_x, y))
        screen.blit(message_surface, message_rect)
        
        # Subtitle
        subtitle_surface = self.text_font.render(subtitle, True, self.window.colors['GRAY'])
        subtitle_rect = subtitle_surface.get_rect(center=(center_x, y + 30))
        screen.blit(subtitle_surface, subtitle_rect)

    def draw_statistics(self, screen, center_x, y):
        """Draw player statistics in two columns"""
        # Statistics header
        stats_title = self.header_font.render("Game Statistics", True, self.gold_color)
        stats_rect = stats_title.get_rect(center=(center_x, y))
        screen.blit(stats_title, stats_rect)
        
        stats_y = y + 40
        
        # Left column
        left_x = center_x - self.window.get_scaled_size(150)
        # Right column  
        right_x = center_x + self.window.get_scaled_size(150)
        
        # Left column stats
        left_stats = [
            ("Total Earnings:", f"${self.player_stats.get('total_earnings', 0)}"),
            ("Orders Completed:", str(self.player_stats.get('orders_completed', 0))),
            ("Orders Canceled:", str(self.player_stats.get('orders_canceled', 0))),
            ("On-Time Deliveries:", str(self.player_stats.get('on_time_deliveries', 0)))
        ]
        
        # Right column stats
        right_stats = [
            ("Final Reputation:", f"{self.player_stats.get('reputation', 70)}/100"),
            ("Late Deliveries:", str(self.player_stats.get('late_deliveries', 0))),
            ("Distance Traveled:", f"{self.player_stats.get('distance_traveled', 0)} tiles"),
            ("Times Exhausted:", str(self.player_stats.get('times_exhausted', 0)))
        ]
        
        # Draw left column
        for i, (label, value) in enumerate(left_stats):
            label_y = stats_y + (i * 25)
            
            label_surface = self.text_font.render(label, True, self.window.colors['WHITE'])
            screen.blit(label_surface, (left_x - 100, label_y))
            
            value_surface = self.text_font.render(value, True, self.gold_color)
            screen.blit(value_surface, (left_x + 20, label_y))
        
        # Draw right column
        for i, (label, value) in enumerate(right_stats):
            label_y = stats_y + (i * 25)
            
            label_surface = self.text_font.render(label, True, self.window.colors['WHITE'])
            screen.blit(label_surface, (right_x - 100, label_y))
            
            value_surface = self.text_font.render(value, True, self.gold_color)
            screen.blit(value_surface, (right_x + 20, label_y))

    def draw_final_score(self, screen, center_x, y):
        """Draw final score calculation"""
        # Score breakdown header
        score_title = self.header_font.render("Final Score Calculation", True, self.gold_color)
        score_rect = score_title.get_rect(center=(center_x, y))
        screen.blit(score_title, score_rect)
        
        score_y = y + 40
        
        # Score components
        base_score = self.player_stats.get('total_earnings', 0)
        reputation_bonus = self.calculate_reputation_bonus()
        time_bonus = self.calculate_time_bonus()
        penalties = self.calculate_penalties()
        final_score = base_score + reputation_bonus + time_bonus - penalties
        
        score_components = [
            ("Base Score (Earnings):", f"+${base_score}", self.window.colors['WHITE']),
            ("Reputation Bonus:", f"+${reputation_bonus}", self.victory_color if reputation_bonus > 0 else self.window.colors['GRAY']),
            ("Time Bonus:", f"+${time_bonus}", self.victory_color if time_bonus > 0 else self.window.colors['GRAY']),
            ("Penalties:", f"-${penalties}", self.defeat_color if penalties > 0 else self.window.colors['GRAY']),
            ("", "", self.window.colors['WHITE']),  # Spacer
            ("FINAL SCORE:", f"${final_score}", self.gold_color)
        ]
        
        for i, (label, value, color) in enumerate(score_components):
            if label:  # Skip spacer
                component_y = score_y + (i * 20)
                
                label_surface = self.text_font.render(label, True, self.window.colors['WHITE'])
                screen.blit(label_surface, (center_x - 120, component_y))
                
                value_surface = self.text_font.render(value, True, color)
                value_rect = value_surface.get_rect(right=center_x + 120)
                value_rect.y = component_y
                screen.blit(value_surface, value_rect)

    def draw_performance_summary(self, screen, center_x, y):
        """Draw performance summary and rank"""
        # Performance ranking
        rank = self.calculate_performance_rank()
        rank_color = self.get_rank_color(rank)
        
        rank_text = f"Performance Rank: {rank}"
        rank_surface = self.header_font.render(rank_text, True, rank_color)
        rank_rect = rank_surface.get_rect(center=(center_x, y))
        screen.blit(rank_surface, rank_rect)
        
        # Performance message
        message = self.get_performance_message(rank)
        message_surface = self.text_font.render(message, True, self.window.colors['WHITE'])
        message_rect = message_surface.get_rect(center=(center_x, y + 30))
        screen.blit(message_surface, message_rect)

    def draw_buttons(self, screen):
        """Draw the action buttons"""
        for button_key, button_data in self.buttons.items():
            rect = button_data["rect"]
            text = button_data["text"]
            
            # Button color based on hover state
            if self.hovered_button == button_key:
                if button_key == "quit":
                    bg_color = self.defeat_color
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
            text_surface = self.text_font.render(text, True, self.window.colors['WHITE'])
            text_rect = text_surface.get_rect(center=rect.center)
            screen.blit(text_surface, text_rect)

    # Helper methods for calculations (these would be implemented by your teammate)
    def get_time_remaining(self):
        """Get formatted time remaining when victory was achieved"""
        remaining_seconds = self.player_stats.get('time_remaining', 0)
        minutes = int(remaining_seconds // 60)
        seconds = int(remaining_seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def get_defeat_reason(self):
        """Get the reason for defeat"""
        return self.player_stats.get('defeat_reason', 'unknown')

    def calculate_reputation_bonus(self):
        """Calculate bonus based on reputation"""
        reputation = self.player_stats.get('reputation', 70)
        if reputation >= 90:
            return int(self.player_stats.get('total_earnings', 0) * 0.1)  # 10% bonus
        elif reputation >= 80:
            return int(self.player_stats.get('total_earnings', 0) * 0.05)  # 5% bonus
        return 0

    def calculate_time_bonus(self):
        """Calculate bonus for finishing early"""
        if not self.victory:
            return 0
        
        time_remaining = self.player_stats.get('time_remaining', 0)
        if time_remaining > 120:  # More than 2 minutes remaining
            return int(time_remaining * 2)  # 2 points per second remaining
        return 0

    def calculate_penalties(self):
        """Calculate penalties for poor performance"""
        penalties = 0
        penalties += self.player_stats.get('orders_canceled', 0) * 50  # 50 points per canceled order
        penalties += self.player_stats.get('late_deliveries', 0) * 30   # 30 points per late delivery
        return penalties

    def calculate_performance_rank(self):
        """Calculate performance rank based on various factors"""
        score = 0
        
        # Completion rate
        completed = self.player_stats.get('orders_completed', 0)
        canceled = self.player_stats.get('orders_canceled', 0)
        if completed + canceled > 0:
            completion_rate = completed / (completed + canceled)
            score += completion_rate * 30
        
        # On-time delivery rate
        on_time = self.player_stats.get('on_time_deliveries', 0)
        if completed > 0:
            on_time_rate = on_time / completed
            score += on_time_rate * 30
        
        # Reputation
        reputation = self.player_stats.get('reputation', 70)
        score += (reputation / 100) * 25
        
        # Victory bonus
        if self.victory:
            score += 15
        
        # Determine rank
        if score >= 85:
            return "S"
        elif score >= 75:
            return "A"
        elif score >= 65:
            return "B"
        elif score >= 50:
            return "C"
        else:
            return "D"

    def get_rank_color(self, rank):
        """Get color for performance rank"""
        if rank == "S":
            return self.gold_color
        elif rank == "A":
            return self.silver_color
        elif rank == "B":
            return self.bronze_color
        elif rank == "C":
            return self.window.colors['BLUE']
        else:
            return self.defeat_color

    def get_performance_message(self, rank):
        """Get performance message based on rank"""
        messages = {
            "S": "Outstanding performance! You're a master courier!",
            "A": "Excellent work! You're a skilled delivery professional!",
            "B": "Good job! You're getting the hang of it!",
            "C": "Not bad! There's room for improvement.",
            "D": "Keep practicing! You'll get better with experience."
        }
        return messages.get(rank, "Thanks for playing!")
