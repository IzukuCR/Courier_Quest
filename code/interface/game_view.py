import pygame
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

        # Dynamic sizing - will be set in on_show()
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

        # Store original tile images for scaling (new approach)
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

        # Initialize WeatherRenderer (will be properly sized in on_show)
        self.weather_renderer = None

        # Toast
        self.toast = ""
        self.toast_timer = 0.0

        # Order selection
        self.jobs._selected_index = -1
        self.selected = self.jobs.cycle_selection(self.game.get_game_time())

        # Pause menu will be initialized in on_show()
        self.pause_menu = None

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

            elif event.key == pygame.K_e:
                # Scroll down through orders (next page)
                if self.jobs.scroll_down(self.game.get_game_time()):
                    self.selected = self.jobs.get_selected(
                        self.game.get_game_time())
                    scroll_info = self.jobs.get_scroll_info(
                        self.game.get_game_time())
                    self.toast, self.toast_timer = f"Page {scroll_info['current_page']}/{scroll_info['total_pages']}", 1.5

            elif event.key == pygame.K_x:
                # Scroll up through orders (previous page)
                if self.jobs.scroll_up(self.game.get_game_time()):
                    self.selected = self.jobs.get_selected(
                        self.game.get_game_time())
                    scroll_info = self.jobs.get_scroll_info(
                        self.game.get_game_time())
                    self.toast, self.toast_timer = f"Page {scroll_info['current_page']}/{scroll_info['total_pages']}", 1.5

            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.selected:
                    if self.pinv.accept(self.selected, self.game.get_game_time()):
                        self.toast, self.toast_timer = f"Accepted {self.selected.id}", 2.0
                    else:
                        self.toast, self.toast_timer = f"Could not accept {self.selected.id}", 2.0

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
        # Dynamic HUD positioning (was fixed HUD_X)
        x = self.window.hud_x
        white = self.window.colors['WHITE']

        # Scale spacing dynamically
        line_height = self.window.get_scaled_size(20)
        section_spacing = self.window.get_scaled_size(50)

        # Define small_font early so it's available throughout the method
        small_font = pygame.font.Font(None, max(14, int(line_height * 0.7)))

        # Time - now showing countdown from 10 minutes
        remaining_time = self.game.get_game_time()
        mins = self.game.get_game_time_remaining_minutes()
        secs = self.game.get_game_time_remaining_seconds()

        # Color changes based on remaining time
        if remaining_time <= 60:  # Last minute - red
            time_color = (255, 50, 50)
        elif remaining_time <= 180:  # Last 3 minutes - yellow
            time_color = (255, 255, 0)
        else:  # Normal - white
            time_color = white

        time_text = f"Time {mins:02d}:{secs:02d}"
        screen.blit(self.big.render(time_text, True, time_color), (x, 40))

        # Time progress bar (optional visual indicator)
        progress = self.game.get_game_time_progress()
        bar_width = self.window.get_scaled_size(150)
        bar_height = self.window.get_scaled_size(8)
        bar_x = x
        bar_y = 40 + self.window.get_scaled_size(35)

        # Background bar
        pygame.draw.rect(screen, (60, 60, 60),
                         (bar_x, bar_y, bar_width, bar_height))

        # Progress bar (green to red based on time remaining)
        if progress < 0.5:
            bar_color = (0, 255, 0)  # Green
        elif progress < 0.8:
            bar_color = (255, 255, 0)  # Yellow
        else:
            bar_color = (255, 0, 0)  # Red

        progress_width = int(bar_width * progress)
        pygame.draw.rect(screen, bar_color,
                         (bar_x, bar_y, progress_width, bar_height))

        # Weather - enhanced with timing info and current condition display
        weather_y = 40 + line_height * 4
        current_condition = self.weather.get_current_condition()

        # Color-code weather conditions for better visibility
        weather_colors = {
            "clear": (255, 255, 100),    # Yellow
            "clouds": (150, 150, 150),   # Gray
            "rain_light": (100, 150, 255),  # Light blue
            "rain": (50, 100, 255),      # Blue
            "storm": (255, 100, 100),    # Red
            "fog": (200, 200, 200),      # Light gray
            "wind": (150, 255, 150),     # Light green
            "heat": (255, 150, 50),      # Orange
            "cold": (150, 200, 255)      # Light blue
        }

        weather_color = weather_colors.get(current_condition, white)
        weather_text = f"Weather: {current_condition.upper()}"
        screen.blit(self.font.render(weather_text, True,
                    weather_color), (x, weather_y))

        # Add weather effect indicator
        weather_indicator_y = weather_y + int(line_height * 0.7)

        # Map weather to visual effect name
        weather_mapping = {
            "clear": "SUNNY RAYS",
            "clouds": "GRAY OVERLAY",
            "rain_light": "LIGHT RAIN",
            "rain": "HEAVY RAIN",
            "storm": "STORM RAIN",
            "fog": "FOG PATCHES",
            "wind": "WIND LINES",
            "heat": "HEAT SHIMMER",
            "cold": "SNOW FALL"
        }

        effect_name = weather_mapping.get(current_condition, "NO EFFECT")
        effect_text = f"Effect: {effect_name}"
        screen.blit(small_font.render(effect_text, True,
                    (180, 180, 180)), (x, weather_indicator_y))

        # Weather timing debug info (optional - can be removed in production)
        weather_debug = self.game.get_weather_debug_info()
        time_until_change = weather_debug["time_until_next_change"]

        weather_timing_y = weather_y + line_height
        if time_until_change > 0:
            timing_text = f"Next change: {time_until_change:.1f}s"
            timing_color = (
                200, 200, 200) if time_until_change > 10 else (255, 200, 0)
        else:
            timing_text = "Weather changing..."
            timing_color = (255, 100, 100)

        screen.blit(self.font.render(timing_text, True,
                    timing_color), (x, weather_timing_y))

        # Weather burst indicator
        weather_condition_data = self.game.get_weather_condition()
        if weather_condition_data["has_active_burst"]:
            burst_y = weather_timing_y + line_height
            burst_remaining = weather_condition_data["burst_remaining_sec"]
            burst_text = f"Burst: {burst_remaining}s left"
            screen.blit(self.font.render(burst_text, True,
                        (100, 255, 100)), (x, burst_y))
            orders_y = burst_y + section_spacing
        else:
            orders_y = weather_timing_y + section_spacing

        # Orders section (adjusted position)
        screen.blit(self.big.render("Orders", True, white), (x, orders_y))

        sel = self.selected.id if self.selected else "-"
        act = self.pinv.active.id if self.pinv.active else "-"
        screen.blit(self.font.render(
            f"Selected: {sel}", True, white), (x, orders_y + line_height * 2))
        screen.blit(self.font.render(
            f"Active: {act}", True, white), (x, orders_y + line_height * 3))

        # Capacity
        capacity_y = orders_y + line_height * 4
        screen.blit(self.font.render(
            f"Capacity: {self.pinv.carried_weight():.1f} / {self.pinv.capacity_weight:.1f}",
            True, white), (x, capacity_y))

        # Player stamina information (if player exists)
        stamina_y = capacity_y + line_height
        if self.player:
            stamina_info = self.player.get_stamina_info()
            stamina = stamina_info["stamina"]
            resistance_state = stamina_info["resistance_state"]
            stamina_percentage = int(stamina)
            is_in_recovery_mode = stamina_info["is_in_recovery_mode"]
            recovery_threshold = stamina_info["recovery_threshold"]

            # Stamina label and percentage text
            if is_in_recovery_mode:
                stamina_label = f"Stamina: {stamina_percentage}% ({resistance_state}) - RECOVERY MODE"
                recovery_needed = max(0, recovery_threshold - stamina)
                if recovery_needed > 0:
                    stamina_label += f" (need +{recovery_needed:.0f})"
            else:
                stamina_label = f"Stamina: {stamina_percentage}% ({resistance_state})"

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

            # Draw stamina label
            screen.blit(self.font.render(stamina_label,
                        True, stamina_color), (x, stamina_y))

            # Draw stamina progress bar
            stamina_bar_y = stamina_y + int(line_height * 0.8)
            stamina_bar_width = self.window.get_scaled_size(150)
            stamina_bar_height = self.window.get_scaled_size(8)

            # Background bar (dark gray)
            pygame.draw.rect(screen, (60, 60, 60),
                             (x, stamina_bar_y, stamina_bar_width, stamina_bar_height))

            # Stamina progress bar (colored based on state)
            stamina_progress = stamina / 100.0  # Convert to 0.0-1.0 range
            stamina_progress_width = int(stamina_bar_width * stamina_progress)
            if stamina_progress_width > 0:  # Only draw if there's stamina
                pygame.draw.rect(screen, bar_color,
                                 (x, stamina_bar_y, stamina_progress_width, stamina_bar_height))

            # Draw recovery threshold marker if in recovery mode
            if is_in_recovery_mode:
                threshold_progress = recovery_threshold / 100.0
                threshold_x = x + int(stamina_bar_width * threshold_progress)
                # Draw vertical line at threshold
                pygame.draw.line(screen, (255, 255, 255),
                                 (threshold_x, stamina_bar_y),
                                 (threshold_x, stamina_bar_y + stamina_bar_height + 2), 3)

            # Show recovery indicator if player is idle and can recover
            current_y = stamina_bar_y + \
                stamina_bar_height + int(line_height * 0.3)
            if stamina_info["is_recovering"]:
                time_to_recovery = stamina_info["time_to_next_recovery"]
                if is_in_recovery_mode:
                    recovery_text = f"Recovering... {time_to_recovery:.1f}s (CANNOT MOVE)"
                    text_color = (255, 100, 100)
                else:
                    recovery_text = f"Recovering in {time_to_recovery:.1f}s"
                    text_color = (100, 255, 100)
                screen.blit(small_font.render(recovery_text,
                            True, text_color), (x, current_y))
                available_orders_y = current_y + line_height
            else:
                available_orders_y = current_y + int(line_height * 0.2)
        else:
            available_orders_y = stamina_y

        # Available orders list with improved scrolling display
        list_y = available_orders_y + int(section_spacing * 0.5)

        # Get scroll information
        scroll_info = self.jobs.get_scroll_info(self.game.get_game_time())
        page_orders = self.jobs.get_selectable_page(self.game.get_game_time())
        all_orders = self.jobs.all()

        # Debug information
        debug_text = f"Debug: Total={len(all_orders)}, Available={scroll_info['total_orders']}, Page={len(page_orders)}"
        screen.blit(small_font.render(debug_text, True,
                    (100, 100, 100)), (x, list_y - int(line_height * 0.8)))

        # Header with page information
        orders_header = f"Available ({scroll_info['total_orders']} total):"
        if scroll_info['total_pages'] > 1:
            orders_header += f" Page {scroll_info['current_page']}/{scroll_info['total_pages']}"

        screen.blit(self.font.render(orders_header, True,
                    self.window.colors['GRAY']), (x, list_y))

        # Show some order states for debugging
        debug_y = list_y + int(line_height * 0.6)
        order_states = {}
        for o in all_orders[:10]:  # First 10 orders
            state = o.state
            order_states[state] = order_states.get(state, 0) + 1

        states_text = " | ".join(
            [f"{state}:{count}" for state, count in order_states.items()])
        screen.blit(small_font.render(
            f"States: {states_text}", True, (150, 150, 150)), (x, debug_y))

        # Scroll indicators
        if scroll_info['total_pages'] > 1:
            indicator_y = list_y + line_height

            # Up arrow indicator
            up_color = (100, 255, 100) if scroll_info['can_scroll_up'] else (
                100, 100, 100)
            up_text = "↑ X - Previous page" if scroll_info['can_scroll_up'] else "↑ (no more)"
            screen.blit(small_font.render(
                up_text, True, up_color), (x, indicator_y))

            # Down arrow indicator
            down_y = indicator_y + int(line_height * 0.7)
            down_color = (100, 255, 100) if scroll_info['can_scroll_down'] else (
                100, 100, 100)
            down_text = "↓ E - Next page" if scroll_info['can_scroll_down'] else "↓ (no more)"
            screen.blit(small_font.render(
                down_text, True, down_color), (x, down_y))

            orders_start_y = down_y + int(line_height * 1.2)
        else:
            orders_start_y = list_y + line_height

        # Display current page of orders
        y = orders_start_y
        for i, o in enumerate(page_orders):
            tag = "►" if self.selected and self.selected.id == o.id else " "

            # Enhanced order display with more information
            deadline_remaining = ""
            if o.deadline_s is not None:
                remaining = max(
                    0, o.deadline_s - (self.game._game_time_limit_s - self.game.get_game_time()))
                deadline_remaining = f" ({remaining:.0f}s)"

            # Color coding based on priority and time
            if o.priority >= 3:
                text_color = (255, 200, 100)  # High priority - orange
            elif o.priority >= 2:
                text_color = (255, 255, 100)  # Medium priority - yellow
            else:
                text_color = white  # Normal priority - white

            # Check if order is about to expire (less than 60 seconds)
            if deadline_remaining and "s)" in deadline_remaining:
                remaining_time = float(
                    deadline_remaining.split("(")[1].split("s)")[0])
                if remaining_time < 60:
                    text_color = (255, 100, 100)  # Red for urgent

            left = f"{tag} {o.id} w{int(o.weight)} p{int(o.priority)} ${int(o.payout)}{deadline_remaining}"

            # Highlight selected order with background
            if self.selected and self.selected.id == o.id:
                # Draw selection background
                selection_rect = pygame.Rect(
                    x - 5, y - 2, self.window.get_scaled_size(200), int(line_height * 0.9))
                pygame.draw.rect(screen, (50, 50, 100), selection_rect)
                text_color = (255, 255, 255)  # White text for selected

            screen.blit(self.font.render(left, True, text_color), (x, y))
            y += int(line_height * 0.9)

        # Update controls instructions
        controls_y = y + section_spacing // 2
        screen.blit(self.font.render("Controls:", True,
                    self.window.colors['GRAY']), (x, controls_y))

        controls_info = [
            "TAB - Next order",
            "Q - Previous order",
            "E - Next page",
            "X - Previous page",
            "ENTER - Accept order",
            "R - Switch active order",
            "Z - Undo last move",
            "WASD/Arrows - Move",
            "ESC - Pause"
        ]

        controls_start_y = controls_y + line_height

        for i, control in enumerate(controls_info):
            control_y = controls_start_y + i * int(line_height * 0.8)
            screen.blit(small_font.render(control, True,
                        (200, 200, 200)), (x, control_y))

        # Order status legend with colors
        legend_y = controls_start_y + \
            len(controls_info) * int(line_height * 0.8) + line_height // 2
        screen.blit(self.font.render("Markers:", True,
                    self.window.colors['GRAY']), (x, legend_y))

        legend_start_y = legend_y + line_height

        # Active order markers (current task)
        screen.blit(small_font.render("Active Order:", True,
                    (255, 255, 255)), (x, legend_start_y))
        active_y = legend_start_y + int(line_height * 0.8)

        # Draw pickup marker example
        pickup_color = (0, 255, 100)  # Bright green
        marker_size = int(line_height * 0.6)
        pygame.draw.rect(screen, pickup_color, pygame.Rect(
            x, active_y, marker_size, marker_size), 2)
        pickup_font = pygame.font.Font(None, max(12, marker_size // 2))
        pickup_text = pickup_font.render("P", True, pickup_color)
        screen.blit(pickup_text, (x + marker_size //
                    4, active_y + marker_size//4))
        screen.blit(small_font.render("Pickup (Green)", True,
                    (200, 200, 200)), (x + marker_size + 5, active_y))

        # Draw dropoff marker example
        dropoff_color = (255, 100, 0)  # Bright orange
        dropoff_y = active_y + int(line_height * 0.8)
        center_x = x + marker_size // 2
        center_y = dropoff_y + marker_size // 2
        pygame.draw.circle(screen, dropoff_color,
                           (center_x, center_y), marker_size // 3)
        dropoff_text = pickup_font.render("D", True, (255, 255, 255))
        d_rect = dropoff_text.get_rect(center=(center_x, center_y))
        screen.blit(dropoff_text, d_rect)
        screen.blit(small_font.render("Dropoff (Orange)", True,
                    (200, 200, 200)), (x + marker_size + 5, dropoff_y))

        # Selected order markers (preview)
        selected_y = dropoff_y + int(line_height * 1.2)
        screen.blit(small_font.render("Selected Order:",
                    True, (255, 255, 255)), (x, selected_y))
        selected_start_y = selected_y + int(line_height * 0.8)

        # Selected pickup marker
        selected_pickup_color = (100, 150, 255)  # Light blue
        pygame.draw.rect(screen, selected_pickup_color, pygame.Rect(
            x, selected_start_y, marker_size, marker_size), 2)
        sel_pickup_text = pickup_font.render("P", True, selected_pickup_color)
        screen.blit(sel_pickup_text, (x + marker_size//4,
                    selected_start_y + marker_size//4))
        screen.blit(small_font.render("Pickup (Blue)", True,
                    (200, 200, 200)), (x + marker_size + 5, selected_start_y))

        # Selected dropoff marker
        selected_dropoff_color = (255, 255, 100)  # Light yellow
        sel_dropoff_y = selected_start_y + int(line_height * 0.8)
        sel_center_x = x + marker_size // 2
        sel_center_y = sel_dropoff_y + marker_size // 2
        pygame.draw.circle(screen, selected_dropoff_color,
                           (sel_center_x, sel_center_y), marker_size // 3)
        sel_dropoff_text = pickup_font.render(
            "D", True, (0, 0, 0))  # Black text on yellow
        sel_d_rect = sel_dropoff_text.get_rect(
            center=(sel_center_x, sel_center_y))
        screen.blit(sel_dropoff_text, sel_d_rect)
        screen.blit(small_font.render("Dropoff (Yellow)", True,
                    (200, 200, 200)), (x + marker_size + 5, sel_dropoff_y))

        # Toast positioning (was fixed at 700)
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

        # Check if game time is up
        if self.game.is_game_time_up():
            self.toast, self.toast_timer = "Time's Up! Game Over", 5.0

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

            # Initialize pause menu with save functionality
            self.pause_menu = PauseMenu(self.window)
            print("GameView: Pause menu initialized with save functionality")

        print("Game view shown with responsive layout")

    def handle_button_click(self, button_key):
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
