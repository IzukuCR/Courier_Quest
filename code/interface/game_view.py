import pygame

from code.interface.ai_view import AIView
from .base_view import BaseView
from ..game.game import Game
from .pause_menu import PauseMenu
from .weather_renderer import WeatherRenderer


class GameView(BaseView):
    def __init__(self):
        super().__init__()

        # Initialize Game singleton safely
        try:
            self.game = Game()
            self.player_name = self.game.get_player_name()
        except Exception as e:
            print(f"GameView: Error initializing Game: {e}")
            # Create a fallback game instance
            self.game = Game()
            self.player_name = "Player1"

        # Map configuration - now responsive
        self.city = self.game.get_city()
        if hasattr(self.city, 'tiles'):
            self.matrix = self.city.tiles
        else:
            self.matrix = []

        # Dynamic sizing - will be set in (on_show)()
        self.cell_size = 30
        self.map_offset_x = 20
        self.map_offset_y = 20

        # Tile colors (fallback if images not loaded)
        self.tile_colors = {
            "C": (128, 128, 128),    # GRAY
            "P": (34, 139, 34),      # FOREST_GREEN
            "B": (139, 69, 19),      # BROWN
        }

        self.font = pygame.font.Font(None, 24)
        self.big = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 18)
        self.title_font = pygame.font.Font(None, 28)

        self.retro_colors = {
            'COPPER': (184, 115, 51),         # Warm copper/bronze
            'SAGE_GREEN': (159, 190, 87),     # Muted sage green
            'STEEL_BLUE': (70, 130, 180),     # Classic steel blue
            'WARM_AMBER': (255, 191, 0),      # Elegant amber
            'SOFT_PINK': (221, 160, 221),     # Muted plum/pink

            # Background and UI colors
            'CHARCOAL': (54, 69, 79),         # dark gray
            'CREAM': (245, 245, 220),         # Warm off-white
            'DARK_NAVY': (36, 49, 56),        # Deep navy for backgrounds
            'SILVER': (192, 192, 192),        # Classic silver

            # Status indicators
            'SUCCESS': (106, 168, 79),        # Muted forest green
            'WARNING': (218, 165, 32),        # Goldenrod
            'DANGER': (205, 92, 92),          # Indian red
            'INFO': (100, 149, 237),          # Cornflower blue

            # Text hierarchy
            'PRIMARY_TEXT': (245, 245, 220),  # Cream for main text
            'SECONDARY_TEXT': (192, 192, 192),  # Silver for secondary
            'ACCENT_TEXT': (184, 115, 51),    # Copper for accents
            'DIM_TEXT': (128, 128, 128),      # Gray for less important
        }

        # Store original tile images for scaling
        self.original_tile_images = {}
        self.tile_images = {}
        self.current_tile_size = 30

        # Load tile images
        self.load_tile_images()

        # References - add safety checks
        self.player = self.game.get_player()  # May be None initially
        self.weather = self.game.get_weather()
        self.jobs = self.game.get_jobs()
        self.pinv = self.game.get_player_inventory()

        # Initialize WeatherRenderer
        self.weather_renderer = None

        # Toast
        self.toast = ""
        self.toast_timer = 0.0

        # Order selection - fix initialization
        self.jobs._selected_index = 0  # Start with first order
        # Try to get initial selection, but don't fail if no orders available yet
        try:
            self.selected = self.jobs.get_selected(self.game.get_game_time())
            if not self.selected:
                # If no order selected, try cycling to get first available
                self.selected = self.jobs.cycle_selection(
                    self.game.get_game_time())
        except Exception as e:
            print(f"GameView: Could not initialize order selection: {e}")
            self.selected = None

        # Pause menu will be initialized in on_show()
        self.pause_menu = None

        # Initialize AI view (will be set when AI is created)
        self.ai_view = None

    def load_tile_images(self):
        """Load original tile images without scaling - scaling happens dynamically"""
        self.original_tile_images = {}
        self.tile_images = {}

        tile_files = {
            "B": "code/assets/tiles/buildIngBorderless1.PNG",
            "P": "code/assets/tiles/grass.png"
        }

        for tile_type, file_path in tile_files.items():
            try:
                # Load original image without scaling (changed from fixed scaling)
                original_image = pygame.image.load(file_path)
                self.original_tile_images[tile_type] = original_image

                print(
                    f"DEBUG TILES - Loaded original '{tile_type}' size: {original_image.get_size()}")

                # Create initial scaled version
                scaled_image = pygame.transform.scale(
                    original_image, (self.cell_size, self.cell_size))
                self.tile_images[tile_type] = scaled_image

            except pygame.error as e:
                print(f"Error loading {file_path}: {e}")
                # Create placeholder for missing images
                placeholder = self.create_tile_placeholder(
                    tile_type, self.cell_size)
                self.original_tile_images[tile_type] = placeholder
                self.tile_images[tile_type] = placeholder

        if not self.tile_images:
            print("Game view: No tile images loaded, using colors")
            self.tile_images = None

    def create_tile_placeholder(self, tile_type, size):
        """Create colored placeholder for missing tile images"""
        surface = pygame.Surface((size, size))
        color = self.tile_colors.get(tile_type, (255, 255, 255))
        surface.fill(color)
        return surface

    def update_tile_scale(self):
        """Update tile image scaling when cell_size changes"""
        if self.cell_size != self.current_tile_size and self.original_tile_images:
            self.current_tile_size = self.cell_size

            # Rescale all tile images from originals
            for tile_type, original in self.original_tile_images.items():
                if original:
                    self.tile_images[tile_type] = pygame.transform.scale(
                        original, (self.cell_size, self.cell_size))

            print(
                f"DEBUG TILES - Rescaled tiles to {self.cell_size}x{self.cell_size}")

    def handle_event(self, event):
        # Check pause menu events first (if game is paused)
        if self.game.is_paused() and self.pause_menu:
            action = self.pause_menu.handle_event(event)
            if action:
                self.handle_pause_action(action)
                return  # Don't process other events when pause menu is active

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.game.is_paused():
                    # If already paused, resume game
                    self.game.resume_game()
                    if self.pause_menu:
                        self.pause_menu.hide()
                else:
                    # If not paused, pause game and show menu
                    self.game.pause_game()
                    if self.pause_menu:
                        self.pause_menu.show()
                return

            if self.game.is_paused():
                return  # ignore inputs while paused

            if event.key == pygame.K_TAB:
                self.selected = self.jobs.cycle_selection(
                    self.game.get_game_time())
                if self.selected:
                    self.toast, self.toast_timer = f"Selected {self.selected.id}", 2.0

            elif event.key == pygame.K_q:
                self.selected = self.jobs.cycle_selection_prev(
                    self.game.get_game_time())
                if self.selected:
                    self.toast, self.toast_timer = f"Selected {self.selected.id}", 2.0

            # UPDATED KEY: Use 'X' to discard (cancel) the active order
            elif event.key == pygame.K_x:
                # Discard active order with reputation penalty
                if self.pinv.active:
                    result = self.pinv.cancel_order()
                    self.toast, self.toast_timer = result, 2.0
                    # Check for game over
                    if "GAME OVER" in result:
                        # You might want to switch to a game over view here
                        pass
                else:
                    self.toast, self.toast_timer = "No active order to discard", 2.0

            elif event.key == pygame.K_c:
                # Cancel active order with reputation penalty (alternative key)
                if self.pinv.active:
                    result = self.pinv.cancel_order()
                    self.toast, self.toast_timer = result, 2.0
                    # Check for game over
                    if "GAME OVER" in result:
                        # You might want to switch to a game over view here
                        pass

            elif event.key == pygame.K_r:
                new_active = self.pinv.next_active()
                if new_active:
                    self.toast, self.toast_timer = f"Active: {new_active.id}", 2.0

            elif event.key == pygame.K_z:
                # Undo last move
                if self.player and self.player.undo_last_move():
                    undo_info = self.player.get_undo_info()
                    remaining = undo_info["undo_count"]
                    self.toast, self.toast_timer = f"Move undone! ({remaining} undos left)", 2.0
                else:
                    self.toast, self.toast_timer = "Cannot undo move", 2.0

            elif event.key == pygame.K_RETURN:
                if self.selected:
                    if self.pinv.accept(self.selected, self.game.get_game_time()):
                        self.toast, self.toast_timer = f"Accepted {self.selected.id}", 2.0
                    else:
                        self.toast, self.toast_timer = f"Could not accept {self.selected.id}", 2.0

            # Safety check for player existence
            elif self.player:
                new_x, new_y = self.player.x, self.player.y
                if event.key in (pygame.K_UP, pygame.K_w):
                    new_y -= 1
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    new_y += 1
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    new_x -= 1
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    new_x += 1

                # Intentar mover el jugador
                if (new_x, new_y) != (self.player.x, self.player.y):
                    ok = self.player.move_to(
                        new_x, new_y, self.city, self.weather)

    def handle_pause_action(self, action):
        """Handle actions from the pause menu"""
        print(f"GameView: Pause menu action received: {action}")

        if action == "continue":
            # Continue the game
            self.game.resume_game()
            self.pause_menu.hide()
            self.toast, self.toast_timer = "Game resumed", 1.0

        elif action == "save":
            # Save the game using Game's save method
            print("GameView: Save game action from pause menu")
            print(
                f"GameView: Current game state - playing={self.game._is_playing}, paused={self.game._paused}")

            success = self.game.save_game()
            if success:
                self.toast, self.toast_timer = "Game saved successfully", 2.0
                print("GameView: Game saved successfully from pause menu!")
            else:
                self.toast, self.toast_timer = "Failed to save game", 2.0
                print("GameView: Game save failed from pause menu!")

        elif action == "exit":
            # Exit to main menu - redirect to MenuView
            print("EXIT ACTION - Returning to main menu")
            from .menu_view import MenuView
            menu_view = MenuView()
            self.window.show_view(menu_view)

    def draw(self, screen):
        screen.fill(self.window.colors['BLACK'])
        self._draw_map(screen)
        if self.player:
            self.player.draw(screen, self.cell_size,
                             self.map_offset_x, self.map_offset_y)

        # Draw weather effects BEFORE HUD so they affect the game world
        if self.weather_renderer:
            current_weather = self.weather.get_current_condition()

            self.weather_renderer.draw(screen, current_weather)

        self._draw_hud(screen)

        # Draw pause menu on top of everything
        if self.game.is_paused() and self.pause_menu:
            self.pause_menu.draw(screen)

        # Toast (brief messages) - draw on top of everything
        if self.toast:
            toast_y = self.window.height - self.window.get_scaled_size(100)
            t = self.font.render(self.toast, True, (255, 255, 0))
            screen.blit(t, (self.window.hud_x, toast_y))

    def _draw_map(self, screen):
        if not self.matrix:
            return

        # Ensure tiles are properly scaled before drawing
        self.update_tile_scale()

        # tiles
        for r, row in enumerate(self.matrix):
            for c, cell in enumerate(row):
                x = self.map_offset_x + c * self.cell_size
                y = self.map_offset_y + r * self.cell_size

                if self.tile_images and cell in self.tile_images:
                    # Draw scaled tile image that matches cell_size exactly
                    screen.blit(self.tile_images[cell], (x, y))
                    pygame.draw.rect(screen, (0, 0, 0),
                                     (x, y, self.cell_size, self.cell_size), 1)
                else:
                    # Fallback to colored rectangles
                    color = self.tile_colors.get(
                        cell, self.window.colors["WHITE"])
                    rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                    pygame.draw.rect(screen, color, rect)
                    pygame.draw.rect(screen, (0, 0, 0), rect, 1)
        # pickup / dropoff markers (internal helper using self/screen)

        # Draw AI bot after map but before markers
        if self.ai_view:
            self.ai_view.draw(screen, self.cell_size,
                              self.map_offset_x, self.map_offset_y)

        def draw_enhanced_marker(pos, col, marker_type="pickup"):
            if not pos:
                return
            cx = self.map_offset_x + pos[0] * self.cell_size
            cy = self.map_offset_y + pos[1] * self.cell_size

            if marker_type == "pickup":
                # Pickup: Square border with 'P' text
                pygame.draw.rect(screen, col, pygame.Rect(
                    cx, cy, self.cell_size, self.cell_size), 4)
                # Add 'P' text in the center
                font = pygame.font.Font(None, max(16, self.cell_size // 2))
                text = font.render("P", True, col)
                text_rect = text.get_rect(
                    center=(cx + self.cell_size//2, cy + self.cell_size//2))
                screen.blit(text, text_rect)

            elif marker_type == "dropoff":
                # Dropoff: Filled circle with 'D' text
                center_x = cx + self.cell_size // 2
                center_y = cy + self.cell_size // 2
                radius = self.cell_size // 3
                pygame.draw.circle(screen, col, (center_x, center_y), radius)
                # Add 'D' text in white
                font = pygame.font.Font(None, max(16, self.cell_size // 2))
                text = font.render("D", True, (255, 255, 255))
                text_rect = text.get_rect(center=(center_x, center_y))
                screen.blit(text, text_rect)

        # Show active order markers (current task)
        if self.pinv.active:
            # Only show pickup marker if package hasn't been picked up yet
            if self.pinv.active.state == "accepted":
                draw_enhanced_marker(
                    # Bright green
                    self.pinv.active.pickup, (0, 255, 100), "pickup")
            # Always show dropoff marker when package is active
            draw_enhanced_marker(self.pinv.active.dropoff,
                                 (255, 100, 0), "dropoff")  # Bright orange

        # Show selected order markers (preview) - can be shown alongside active order
        if self.selected and (not self.pinv.active or self.selected.id != self.pinv.active.id):
            # Show selected order markers with different colors (only if different from active)
            draw_enhanced_marker(self.selected.pickup,
                                 (100, 150, 255), "pickup")  # Light blue
            draw_enhanced_marker(self.selected.dropoff,
                                 (255, 255, 100), "dropoff")  # Light yellow

    def _draw_hud(self, screen):
        # Dynamic HUD positioning
        x = self.window.hud_x

        primary_text = self.retro_colors['PRIMARY_TEXT']
        secondary_text = self.retro_colors['SECONDARY_TEXT']
        accent_text = self.retro_colors['ACCENT_TEXT']
        copper = self.retro_colors['COPPER']
        sage_green = self.retro_colors['SAGE_GREEN']
        steel_blue = self.retro_colors['STEEL_BLUE']
        warm_amber = self.retro_colors['WARM_AMBER']

        # Scale spacing dynamically
        line_height = self.window.get_scaled_size(20)
        section_spacing = self.window.get_scaled_size(30)

        small_font = self.small_font
        medium_font = self.font
        title_font = self.title_font

        # TOP SECTION - Time and Scoreboard in elegant panel
        panel_x = x - 10
        panel_y = 10
        panel_width = 400
        panel_height = 70

        # Draw top panel with border
        self._draw_panel_with_border(
            screen, panel_x, panel_y, panel_width, panel_height)

        # Time - countdown from 10 minutes
        time_x = panel_x + 15
        time_y = panel_y + 15
        remaining_time = self.game.get_game_time()
        mins = self.game.get_game_time_remaining_minutes()
        secs = self.game.get_game_time_remaining_seconds()

        if remaining_time <= 60:  # Last minute - danger
            time_color = self.retro_colors['DANGER']
        elif remaining_time <= 180:  # Last 3 minutes - warning
            time_color = self.retro_colors['WARNING']
        elif remaining_time <= 300:  # Last 5 minutes - amber
            time_color = warm_amber
        else:  # Normal - steel blue
            time_color = steel_blue

        time_text = f"TIME: {mins:02d}:{secs:02d}"
        screen.blit(self.big.render(time_text, True,
                    time_color), (time_x, time_y))

        # Scoreboard (right side of panel)
        scoreboard_x = panel_x + 200
        scoreboard_y = panel_y + 10

        scoreboard_title = small_font.render("SCORE", True, copper)
        screen.blit(scoreboard_title, (scoreboard_x, scoreboard_y))

        score_value = self.game._scoreboard.get_score(
        ) if hasattr(self.game, '_scoreboard') else 0
        score_text = f"${score_value:04d}"
        screen.blit(self.big.render(score_text, True, warm_amber),
                    (scoreboard_x, scoreboard_y + 20))

        # MIDDLE SECTION - Status bars (Reputation, Stamina) in elegant panel
        status_panel_y = panel_y + panel_height + 10
        status_panel_width = 300
        status_panel_height = 170  # Increased height for stamina bar

        # Draw status panel with title
        content_y = self._draw_panel_with_border(screen, panel_x, status_panel_y,
                                                 status_panel_width, status_panel_height,
                                                 "PLAYER STATUS", sage_green)

        # Reputation section
        reputation_y = content_y + 10
        reputation_label = "Reputation"
        screen.blit(medium_font.render(reputation_label, True,
                    secondary_text), (panel_x + 15, reputation_y))

        # Reputation progress bar
        reputation_value = getattr(
            self.player, 'reputation', 70) if self.player else 70  # Default 70
        reputation_bar_y = reputation_y + 25
        bar_width = status_panel_width - 40  # Adaptar al nuevo tamaño del panel
        bar_height = self.window.get_scaled_size(12)
        bar_x = panel_x + 15

        # Background bar with elegant styling
        pygame.draw.rect(screen, self.retro_colors['DARK_NAVY'],
                         (bar_x, reputation_bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, self.retro_colors['SILVER'],
                         (bar_x, reputation_bar_y, bar_width, bar_height), 1)

        # Reputation progress with color coding
        reputation_progress = reputation_value / 100.0
        reputation_width = int(bar_width * reputation_progress)

        # Color based on reputation level
        if reputation_value >= 90:
            # Forest green for excellence (≥90)
            rep_color = self.retro_colors['SUCCESS']
        elif reputation_value >= 70:
            # Warm amber for good (≥70)
            rep_color = warm_amber
        elif reputation_value >= 40:
            # Copper for medium (≥40)
            rep_color = copper
        elif reputation_value >= 20:
            # Goldenrod for low (≥20)
            rep_color = self.retro_colors['WARNING']
        else:
            # Indian red for critical (<20)
            rep_color = self.retro_colors['DANGER']

        if reputation_width > 0:
            pygame.draw.rect(screen, rep_color,
                             (bar_x, reputation_bar_y, reputation_width, bar_height))

        # Show reputation status text
        rep_status_y = reputation_bar_y + bar_height + 5

        if self.player:
            rep_stats = self.player.get_reputation_stats()

            # Show reputation status
            if rep_stats["excellence_bonus"]:
                rep_status = "EXCELLENT (+5% pay bonus)"
                rep_status_color = self.retro_colors['SUCCESS']
            elif rep_stats["first_late_discount"]:
                rep_status = "GOOD (Half penalty on first late delivery)"
                rep_status_color = warm_amber
            elif reputation_value < 30:
                rep_status = "WARNING: Low reputation!"
                rep_status_color = self.retro_colors['DANGER']
            elif reputation_value < 20:
                rep_status = "CRITICAL: Reputation too low!"
                rep_status_color = self.retro_colors['DANGER']
            else:
                rep_status = f"Normal"
                rep_status_color = (200, 200, 200)  # Light gray

            # Show streak if > 0
            if rep_stats["streak"] > 0:
                streak_txt = f" | Streak: {rep_stats['streak']}/3"
                rep_status += streak_txt

            screen.blit(small_font.render(rep_status, True, rep_status_color),
                        (panel_x + 15, rep_status_y))

        # Add divider line between sections
        divider_y = reputation_bar_y + 30
        self._draw_section_divider(
            screen, panel_x + 15, divider_y, status_panel_width - 30)

        # Stamina section
        stamina_y = divider_y + 15
        screen.blit(medium_font.render("Stamina", True, steel_blue),
                    (panel_x + 15, stamina_y))

        stamina_bar_y = stamina_y + 25

        if self.player:
            stamina_info = self.player.get_stamina_info()
            stamina = stamina_info["stamina"]
            is_in_recovery_mode = stamina_info["is_in_recovery_mode"]

            # Background bar with elegant styling
            pygame.draw.rect(screen, self.retro_colors['DARK_NAVY'],
                             (bar_x, stamina_bar_y, bar_width, bar_height))
            pygame.draw.rect(screen, self.retro_colors['SILVER'],
                             (bar_x, stamina_bar_y, bar_width, bar_height), 1)

            # Stamina progress bar color based on state (elegant colors)
            if is_in_recovery_mode:
                # Elegant red for recovery
                bar_color = self.retro_colors['DANGER']
            elif stamina > 30:
                # Forest green - normal
                bar_color = self.retro_colors['SUCCESS']
            elif stamina > 0:
                # Elegant yellow - tired
                bar_color = self.retro_colors['WARNING']
            else:
                # Elegant red - exhausted
                bar_color = self.retro_colors['DANGER']

            stamina_progress = stamina / 100.0
            stamina_width = int(bar_width * stamina_progress)
            if stamina_width > 0:
                pygame.draw.rect(screen, bar_color,
                                 (bar_x, stamina_bar_y, stamina_width, bar_height))

            # Draw recovery threshold marker if in recovery mode
            if is_in_recovery_mode:
                threshold_progress = stamina_info["recovery_threshold"] / 100.0
                threshold_x = bar_x + int(bar_width * threshold_progress)
                # Draw vertical line at threshold
                pygame.draw.line(screen, (255, 255, 255),
                                 (threshold_x, stamina_bar_y),
                                 (threshold_x, stamina_bar_y + bar_height + 2), 2)

            # Recovery status message below stamina bar
            recovery_status_y = stamina_bar_y + bar_height + 5
            recovery_threshold = stamina_info["recovery_threshold"]

            if is_in_recovery_mode:
                # Player is in recovery mode - cannot move until threshold is reached
                recovery_needed = max(0, recovery_threshold - stamina)
                if recovery_needed > 0:
                    # Still recovering
                    recovery_message = f"RECOVERY MODE - Need +{recovery_needed:.0f} stamina to move"
                    message_color = (255, 100, 100)  # Bright red
                else:
                    # Threshold reached, can move again
                    recovery_message = "Recovery complete! You can move again"
                    message_color = (100, 255, 100)  # Bright green

                screen.blit(small_font.render(recovery_message,
                            True, message_color), (x, recovery_status_y))

                # Add additional info line
                if stamina_info["is_recovering"]:
                    time_to_recovery = stamina_info["time_to_next_recovery"]
                    additional_info_y = recovery_status_y + \
                        int(line_height * 0.7)
                    recovery_time_msg = f"Recovering in {time_to_recovery:.1f}s"
                    screen.blit(small_font.render(recovery_time_msg,
                                True, (200, 150, 150)), (x, additional_info_y))

            elif stamina <= 0:
                # Stamina is 0 but somehow not in recovery mode (edge case)
                exhausted_message = "EXHAUSTED - Cannot move!"
                screen.blit(small_font.render(exhausted_message,
                            True, (255, 50, 50)), (x, recovery_status_y))

            elif stamina <= 10:
                # Very low stamina warning
                warning_message = f"Critical stamina! ({stamina:.0f}%)"
                screen.blit(small_font.render(warning_message, True,
                            (255, 200, 0)), (x, recovery_status_y))

            elif stamina <= 30:
                # Low stamina info
                tired_message = f"Tired - Reduced movement speed ({stamina:.0f}%)"
                screen.blit(small_font.render(tired_message, True,
                            (255, 255, 100)), (x, recovery_status_y))

            elif stamina_info["is_recovering"] and not is_in_recovery_mode:
                # Normal recovery (not in recovery mode)
                time_to_recovery = stamina_info["time_to_next_recovery"]
                if time_to_recovery > 0:
                    recovery_message = f"Resting... recovering in {time_to_recovery:.1f}s"
                    screen.blit(small_font.render(recovery_message,
                                True, (150, 255, 150)), (x, recovery_status_y))

        # ACTIVE ORDERS SECTION in elegant panel - show all accepted orders
        order_panel_y = status_panel_y + status_panel_height + 15
        order_panel_width = 350
        order_panel_height = 160  # Increased height for multiple orders

        # Draw order panel with title
        order_content_y = self._draw_panel_with_border(screen, panel_x, order_panel_y,
                                                       order_panel_width, order_panel_height,
                                                       "ACTIVE ORDERS", steel_blue)

        if self.pinv.accepted:
            # Calculate elapsed game time once for all orders
            elapsed_game_time = self.game._game_time_limit_s - self.game.get_game_time()

            current_y = order_content_y + 10

            # Show up to 3 orders (adjust based on panel height)
            visible_orders = self.pinv.accepted[:3]  # Show first 3 orders

            for i, order in enumerate(visible_orders):
                is_active = (order == self.pinv.active)

                # Order info line
                order_prefix = "► " if is_active else "  "
                order_text = f"{order_prefix}{order.id} (P:{order.priority})"
                text_color = primary_text if is_active else secondary_text
                screen.blit(small_font.render(order_text, True, text_color),
                            (panel_x + 15, current_y))

                # Time/status info on same line
                status_text = ""
                status_color = secondary_text

                if order.deadline_s:
                    time_remaining = order.deadline_s - elapsed_game_time
                    if time_remaining < 0:
                        # Overtime
                        overtime = abs(time_remaining)
                        status_text = f" +{overtime:.0f}s"
                        status_color = (255, 100, 100)  # Red for overtime
                    else:
                        # On time
                        status_text = f" {time_remaining:.0f}s"
                        status_color = (100, 255, 100) if time_remaining > 60 else (
                            255, 200, 100)

                # Payment info
                payment_text = f" ${int(order.payout)}"
                screen.blit(small_font.render(status_text + payment_text, True, status_color),
                            (panel_x + 160, current_y))

                current_y += 20

            # Show count if there are more orders
            if len(self.pinv.accepted) > 3:
                more_text = f"... and {len(self.pinv.accepted) - 3} more"
                screen.blit(small_font.render(more_text, True, self.retro_colors['DIM_TEXT']),
                            (panel_x + 15, current_y))
        else:
            no_order_y = order_content_y + 10
            screen.blit(medium_font.render("No active orders",
                        True, self.retro_colors['DIM_TEXT']), (panel_x + 15, no_order_y))

        # AVAILABLE JOBS SECTION in elegant panel
        jobs_panel_y = order_panel_y + order_panel_height + 15
        jobs_panel_width = 350
        jobs_panel_height = 200

        # Draw jobs panel with title
        jobs_content_y = self._draw_panel_with_border(screen, panel_x, jobs_panel_y,
                                                      jobs_panel_width, jobs_panel_height,
                                                      "AVAILABLE JOBS", copper)

        # Job list with scrolling
        job_list_y = jobs_content_y + 10
        scroll_info = self.jobs.get_scroll_info(self.game.get_game_time())
        visible_orders = self.jobs.get_visible_orders(
            self.game.get_game_time())

        # Calculate elapsed game time to check for unreleased orders
        elapsed_game_time = self.game._game_time_limit_s - self.game.get_game_time()

        # Add a message if no jobs are available yet
        if not visible_orders:
            no_jobs_y = job_list_y + 20
            screen.blit(small_font.render("No jobs available yet. More coming soon!",
                        True, (200, 200, 200)), (x, no_jobs_y))

        # Show upcoming jobs countdown (if any jobs haven't been released yet)
        unreleased_jobs = [o for o in self.jobs.all() if o.state == "available"
                           and getattr(o, 'release_time', 0) > elapsed_game_time]

        # Show countdown when few jobs are visible
        if unreleased_jobs and len(visible_orders) < 2:
            next_job = min(unreleased_jobs, key=lambda o: o.release_time)
            time_until_release = max(
                0, next_job.release_time - elapsed_game_time)

            # Only show if coming within 2 minutes
            if time_until_release < 120:
                next_job_y = job_list_y + \
                    (0 if not visible_orders else len(visible_orders) * 35 + 10)

                if time_until_release < 60:
                    countdown_text = f"Next job in: {time_until_release:.0f}s"
                else:
                    mins = int(time_until_release // 60)
                    secs = int(time_until_release % 60)
                    countdown_text = f"Next job in: {mins}m {secs}s"

                screen.blit(small_font.render(countdown_text, True,
                                              (150, 200, 255)), (x, next_job_y))

        # Draw visible job items
        for i, order in enumerate(visible_orders):
            job_y = job_list_y + i * 35

            # Determine if this job is selected
            is_selected = self.selected and self.selected.id == order.id

            # Enhanced job box design
            job_rect = pygame.Rect(
                x, job_y, self.window.get_scaled_size(180), 30)

            # Background gradient effect (simulate with multiple rectangles)
            # Base background - slightly darker than white
            pygame.draw.rect(screen, (245, 245, 245), job_rect)

            # Priority-based color accent on the left side
            accent_width = 4
            accent_rect = pygame.Rect(x, job_y, accent_width, 30)

            # Color based on priority
            if order.priority >= 3:
                accent_color = (255, 100, 100)  # Red for high priority
            elif order.priority >= 2:
                accent_color = (255, 200, 100)  # Orange for medium priority
            else:
                accent_color = (100, 200, 255)  # Blue for normal priority

            pygame.draw.rect(screen, accent_color, accent_rect)

            # Main border
            border_color = (0, 150, 255) if is_selected else (120, 120, 120)
            border_width = 2 if is_selected else 1
            pygame.draw.rect(screen, border_color, job_rect, border_width)

            # Selection glow effect
            if is_selected:
                # Outer glow
                glow_rect = pygame.Rect(
                    x - 2, job_y - 2, self.window.get_scaled_size(180) + 4, 34)
                pygame.draw.rect(screen, (100, 180, 255, 100), glow_rect, 1)

            # Job information display
            text_x = x + accent_width + 5  # Start after accent bar

            # Priority text (top line)
            priority_text = f"Priority: {order.priority}"
            priority_color = (80, 80, 80) if not is_selected else (40, 40, 40)
            screen.blit(small_font.render(priority_text, True,
                        priority_color), (text_x, job_y + 3))

            # Payment text (bottom line)
            payment_text = f"Payment: ${int(order.payout)}"
            payment_color = (0, 120, 0) if not is_selected else (
                0, 100, 0)  # Green for money
            screen.blit(small_font.render(payment_text, True,
                        payment_color), (text_x, job_y + 16))

            # Weight indicator (small icon on the right)
            weight_x = x + self.window.get_scaled_size(180) - 25
            weight_text = f"W:{int(order.weight)}"
            weight_color = (100, 100, 100)
            screen.blit(pygame.font.Font(None, 12).render(
                weight_text, True, weight_color), (weight_x, job_y + 2))

            # Deadline indicator (if urgent)
            if order.deadline_s:
                remaining = max(
                    0, order.deadline_s - (self.game._game_time_limit_s - self.game.get_game_time()))
                if remaining < 120:  # Less than 2 minutes - show warning
                    urgent_x = x + self.window.get_scaled_size(180) - 25
                    urgent_text = "!"
                    urgent_color = (
                        255, 0, 0) if remaining < 60 else (255, 150, 0)
                    screen.blit(pygame.font.Font(None, 16).render(
                        urgent_text, True, urgent_color), (urgent_x, job_y + 12))

        # Show bottom scroll indicator
        if scroll_info['total_orders'] > scroll_info['visible_count']:
            down_indicator_y = job_list_y + len(visible_orders) * 35 + 5

            # Down scroll indicator
            down_color = (100, 255, 100) if scroll_info['can_scroll_down'] else (
                60, 60, 60)
            down_text = "↓" if scroll_info['can_scroll_down'] else "―"
            screen.blit(small_font.render(down_text, True,
                        down_color), (x + 85, down_indicator_y))

            # Show position indicator
            position_text = f"{scroll_info['scroll_offset'] + 1}-{min(scroll_info['scroll_offset'] + scroll_info['visible_count'], scroll_info['total_orders'])} of {scroll_info['total_orders']}"
            screen.blit(small_font.render(position_text, True,
                        (128, 128, 128)), (x + 100, down_indicator_y))

        # INSTRUCTIONS AND MARKERS SECTION - lado a lado, más abajo para evitar solapamiento
        bottom_section_y = jobs_panel_y + jobs_panel_height + \
            15  # Positioned after jobs panel

        # INSTRUCTIONS COLUMN (izquierda)
        instructions_x = x
        screen.blit(small_font.render("Instructions", True,
                    (128, 128, 128)), (instructions_x, bottom_section_y))

        # Updated instructions
        instructions = [
            "TAB - Next job",
            "Q - Previous job",
            "ENTER - Accept job",
            "X - Discard active order",
            "R - Switch active order",
            "WASD - Move",
            "Z - Undo",
            "ESC - Pause"
        ]

        for i, instruction in enumerate(instructions):
            instruction_y = bottom_section_y + 20 + i * 15
            screen.blit(small_font.render(instruction, True,
                        (100, 100, 100)), (instructions_x, instruction_y))

        # MARKERS COLUMN (derecha) - alineado con instructions
        markers_x = instructions_x + 200  # Spacing between columns
        screen.blit(small_font.render("Markers Guide:", True,
                    (128, 128, 128)), (markers_x, bottom_section_y))

        # Marker size for guide
        guide_marker_size = 16
        guide_font = pygame.font.Font(None, 14)

        # Active Order Markers - ahora usando bottom_section_y
        active_guide_y = bottom_section_y + 20
        screen.blit(small_font.render("Active Order:", True,
                    (200, 200, 200)), (markers_x, active_guide_y))

        # Active Pickup marker (green square with P)
        pickup_guide_y = active_guide_y + 15
        pickup_color = (0, 255, 100)  # Bright green
        pygame.draw.rect(screen, pickup_color, pygame.Rect(
            markers_x, pickup_guide_y, guide_marker_size, guide_marker_size), 2)
        pickup_text = guide_font.render("P", True, pickup_color)
        pickup_rect = pickup_text.get_rect(
            center=(markers_x + guide_marker_size//2, pickup_guide_y + guide_marker_size//2))
        screen.blit(pickup_text, pickup_rect)
        screen.blit(small_font.render("= Pickup (Green)", True,
                    (150, 150, 150)), (markers_x + guide_marker_size + 8, pickup_guide_y + 2))

        # Active Dropoff marker (orange circle with D)
        dropoff_guide_y = pickup_guide_y + 20
        dropoff_color = (255, 100, 0)  # Bright orange
        center_x = markers_x + guide_marker_size // 2
        center_y = dropoff_guide_y + guide_marker_size // 2
        pygame.draw.circle(screen, dropoff_color, (center_x,
                           center_y), guide_marker_size // 3)
        dropoff_text = guide_font.render("D", True, (255, 255, 255))
        dropoff_rect = dropoff_text.get_rect(center=(center_x, center_y))
        screen.blit(dropoff_text, dropoff_rect)
        screen.blit(small_font.render("= Dropoff (Orange)", True,
                    (150, 150, 150)), (markers_x + guide_marker_size + 8, dropoff_guide_y + 2))

        # Selected Order Markers (Preview)
        selected_guide_y = dropoff_guide_y + 30
        screen.blit(small_font.render("Selected Order:", True,
                    (200, 200, 200)), (markers_x, selected_guide_y))

        # Selected Pickup marker (blue square with P)
        sel_pickup_guide_y = selected_guide_y + 15
        sel_pickup_color = (100, 150, 255)  # Light blue
        pygame.draw.rect(screen, sel_pickup_color, pygame.Rect(
            markers_x, sel_pickup_guide_y, guide_marker_size, guide_marker_size), 2)
        sel_pickup_text = guide_font.render("P", True, sel_pickup_color)
        sel_pickup_rect = sel_pickup_text.get_rect(
            center=(markers_x + guide_marker_size//2, sel_pickup_guide_y + guide_marker_size//2))
        screen.blit(sel_pickup_text, sel_pickup_rect)
        screen.blit(small_font.render("= Pickup (Blue)", True,
                    (150, 150, 150)), (markers_x + guide_marker_size + 8, sel_pickup_guide_y + 2))

        # Selected Dropoff marker (yellow circle with D)
        sel_dropoff_guide_y = sel_pickup_guide_y + 20
        sel_dropoff_color = (255, 255, 100)  # Light yellow
        sel_center_x = markers_x + guide_marker_size // 2
        sel_center_y = sel_dropoff_guide_y + guide_marker_size // 2
        pygame.draw.circle(screen, sel_dropoff_color,
                           (sel_center_x, sel_center_y), guide_marker_size // 3)
        sel_dropoff_text = guide_font.render(
            "D", True, (0, 0, 0))  # Black text on yellow
        sel_dropoff_rect = sel_dropoff_text.get_rect(
            center=(sel_center_x, sel_center_y))
        screen.blit(sel_dropoff_text, sel_dropoff_rect)
        screen.blit(small_font.render("= Dropoff (Yellow)", True,
                    (150, 150, 150)), (markers_x + guide_marker_size + 8, sel_dropoff_guide_y + 2))

        # Toast positioning (keep at bottom)
        if self.toast:
            toast_y = self.window.height - self.window.get_scaled_size(100)
            t = self.font.render(self.toast, True, (255, 255, 0))
            screen.blit(t, (x, toast_y))

    def update(self, delta_time: float):
        self.game.update(delta_time)

        # Update weather renderer
        if self.weather_renderer:
            current_weather = self.weather.get_current_condition()
            self.weather_renderer.update(delta_time, current_weather)

        # Check game over conditions
        game_over, reason = self.game.check_game_over_conditions()
        if game_over:
            # Determine victory or defeat
            is_victory = reason == "victory"

            # Prepare appropriate toast message
            if is_victory:
                self.toast, self.toast_timer = "¡VICTORIA! ¡Objetivo alcanzado!", 1.0
            elif reason == "time_up":
                self.toast, self.toast_timer = "¡TIEMPO AGOTADO!", 1.0
            elif reason == "reputation":
                self.toast, self.toast_timer = "¡REPUTACIÓN DEMASIADO BAJA!", 1.0
            elif reason == "no_jobs":
                self.toast, self.toast_timer = "¡NO HAY MÁS TRABAJOS DISPONIBLES!", 1.0
            else:
                self.toast, self.toast_timer = "GAME OVER", 1.0

            # Add a delay before transitioning to end game screen
            if not hasattr(self, '_end_game_transition_timer'):
                self._end_game_transition_timer = 1.5  # 1.5 second delay

            self._end_game_transition_timer -= delta_time

            if self._end_game_transition_timer <= 0:
                # Transition to end game screen with appropriate stats
                from .end_game import EndGameView
                player_stats = self.get_player_stats()

                # Add game over reason and current score vs goal
                player_stats["defeat_reason"] = reason
                player_stats["goal"] = self.game._goal
                player_stats["time_remaining"] = self.game._game_time_s

                # Show end game view
                self.window.show_view(EndGameView(
                    victory=is_victory, player_stats=player_stats))
                return

        # Update player reference in case it was created after view initialization
        if not self.player:
            self.player = self.game.get_player()

        if self.player:
            self.player.update(delta_time)
            if not self.player.is_moving:
                msg = self.game.on_player_moved(self.player.x, self.player.y)
                if msg:
                    self.toast, self.toast_timer = msg, 2.0

        # Check for weather changes and show notification
        weather_debug = self.game.get_weather_debug_info()
        if weather_debug["should_change"] and not hasattr(self, '_last_weather_notification'):
            current_condition = self.weather.get_current_condition()
            self.toast, self.toast_timer = f"Weather changing to {current_condition}", 3.0
            self._last_weather_notification = weather_debug["elapsed_game_time"]

        if self.toast_timer > 0:
            self.toast_timer -= delta_time
            if self.toast_timer <= 0:
                self.toast = ""

        # Update AI view animation
        if self.ai_view:
            self.ai_view.update(delta_time)

    def on_show(self):
        """Initialize responsive layout when view is shown"""
        if self.window:
            # Initialize WeatherRenderer with current window dimensions
            self.weather_renderer = WeatherRenderer(
                self.window.width, self.window.height)

            # Calculate responsive cell size (was fixed 30)
            available_width = self.window.map_area_width
            available_height = self.window.height - 40  # 40px margins

            if self.matrix:
                rows = len(self.matrix)
                cols = len(self.matrix[0]) if rows > 0 else 1

                # Calculate optimal cell size to fit map
                cell_width = available_width // cols if cols > 0 else 30
                cell_height = available_height // rows if rows > 0 else 30

                # Use smaller dimension to ensure map fits
                self.cell_size = max(20, min(50, min(cell_width, cell_height)))
            else:
                self.cell_size = self.window.get_scaled_size(30)

            # Update tile scaling when cell size changes
            self.update_tile_scale()

            # Center map in available space
            if self.matrix:
                map_width = len(self.matrix[0]) * self.cell_size
                map_height = len(self.matrix) * self.cell_size
                self.map_offset_x = (available_width - map_width) // 2 + 20
                self.map_offset_y = (self.window.height - map_height) // 2

            # Scale fonts
            base_font_size = self.window.get_scaled_size(24)
            big_font_size = self.window.get_scaled_size(32)
            self.font = pygame.font.Font(None, base_font_size)
            self.big = pygame.font.Font(None, big_font_size)

            # Reset any view-specific debug tracking
            if hasattr(self, '_last_deadline_debug'):
                delattr(self, '_last_deadline_debug')
            if hasattr(self, '_last_weather_notification'):
                delattr(self, '_last_weather_notification')

            # Initialize pause menu with save functionality
            self.pause_menu = PauseMenu(self.window)
            print("GameView: Pause menu initialized with save functionality")

            # Initialize and start AI if present
            if hasattr(self.game, 'ai_bot') and self.game.ai_bot:
                self.ai_view = AIView(self.game.ai_bot)
                print(
                    f"GameView: AI view initialized for {self.game.ai_bot.get_name()}")
                
                # Start the AI bot thread
                if not self.game.bot_running:
                    self.game.start_bot()
                    print(f"GameView: AI bot started - {self.game.ai_bot.get_name()}")

        print("Game view shown with responsive layout")

    def handle_button_click(self, button_key):
        """Handle actions from buttons clicked in the pause menu"""
        print(f"GameView: Button clicked: {button_key}")

        if button_key == "resume":
            print("GameView: Resuming game...")
            from ..game.game import Game
            game = Game()
            game.resume_game()
            self.show_pause_menu = False

        elif button_key == "save":
            print("GameView: Save game button clicked in pause menu")
            from ..game.game import Game
            game = Game()

            # Save the current game state
            print("GameView: Attempting to save game from pause menu...")
            if game.save_game():
                print("GameView: Game saved successfully from pause menu!")
                # You could add a visual feedback here (like a temporary message)
            else:
                print("GameView: Game save failed from pause menu!")

        elif button_key == "menu":
            print("GameView: Returning to main menu...")
            from .menu_view import MenuView
            menu_view = MenuView()
            self.window.show_view(menu_view)
            menu_view = MenuView()
            self.window.show_view(menu_view)

    def get_player_stats(self):
        """Collect player stats for end game screen"""
        stats = {}

        # Basic game stats
        stats["total_earnings"] = self.game._scoreboard.get_score(
        ) if hasattr(self.game, '_scoreboard') else 0
        stats["goal"] = self.game._goal
        stats["time_remaining"] = self.game._game_time_s

        # Player stats if available
        if self.player:
            stats["reputation"] = self.player.reputation

            # Get reputation stats for detailed breakdown
            if hasattr(self.player, "get_reputation_stats"):
                rep_stats = self.player.get_reputation_stats()
                stats["daily_stats"] = rep_stats.get("daily_stats", {})
                stats["on_time_deliveries"] = rep_stats.get("daily_stats", {}).get(
                    "on_time", 0) + rep_stats.get("daily_stats", {}).get("early", 0)
                stats["late_deliveries"] = rep_stats.get(
                    "daily_stats", {}).get("late", 0)
                stats["orders_canceled"] = rep_stats.get(
                    "daily_stats", {}).get("canceled", 0)
                stats["orders_lost"] = rep_stats.get(
                    "daily_stats", {}).get("lost", 0)

            # Calculate total orders completed
            stats["orders_completed"] = (
                stats.get("on_time_deliveries", 0) +
                stats.get("late_deliveries", 0)
            )

            # Add movement-related stats
            if hasattr(self.player, "get_stamina_info"):
                stamina_info = self.player.get_stamina_info()
                stats["times_exhausted"] = getattr(
                    self.player, 'was_exhausted', False)

        return stats

    def _draw_panel_with_border(self, screen, x, y, width, height, title=None, title_color=None):
        """Draw a panel with elegant border and shadow"""
        shadow_offset = 3

        # Draw shadow first
        shadow_rect = pygame.Rect(
            x + shadow_offset, y + shadow_offset, width, height)
        pygame.draw.rect(screen, (20, 20, 20), shadow_rect)  # Dark shadow

        # Draw main panel background
        panel_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, self.retro_colors['CHARCOAL'], panel_rect)

        # Draw elegant border
        pygame.draw.rect(screen, self.retro_colors['SILVER'], panel_rect, 2)

        # Draw inner border for depth
        inner_rect = pygame.Rect(x + 2, y + 2, width - 4, height - 4)
        pygame.draw.rect(screen, self.retro_colors['DARK_NAVY'], inner_rect, 1)

        # Draw title bar if provided
        if title and title_color:
            title_height = 25
            title_rect = pygame.Rect(x, y, width, title_height)
            pygame.draw.rect(
                screen, self.retro_colors['DARK_NAVY'], title_rect)
            pygame.draw.rect(screen, title_color, title_rect, 2)

            # Center title text
            title_surface = self.title_font.render(title, True, title_color)
            title_x = x + (width - title_surface.get_width()) // 2
            title_y = y + (title_height - title_surface.get_height()) // 2
            screen.blit(title_surface, (title_x, title_y))

            return y + title_height + 5  # Return content start position

        return y + 5  # Return content start position

    def _draw_section_divider(self, screen, x, y, width):
        """Draw an elegant section divider"""
        # Main line
        pygame.draw.line(screen, self.retro_colors['SILVER'],
                         (x, y), (x + width, y), 2)
        # Accent line below
        pygame.draw.line(screen, self.retro_colors['COPPER'],
                         (x, y + 3), (x + width // 3, y + 3), 1)
