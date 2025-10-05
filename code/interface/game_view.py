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

            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
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
                    if not ok:
                        self.toast, self.toast_timer = "You can't move there", 1.5

    def handle_pause_action(self, action):
        """Handle actions from the pause menu"""
        if action == "continue":
            # Continue the game
            self.game.resume_game()
            self.pause_menu.hide()
            self.toast, self.toast_timer = "Game resumed", 1.0

        elif action == "save":
            # Save game functionality - you'll implement this
            self.toast, self.toast_timer = "Game saved", 2.0
            print("SAVE ACTION - Implement save game logic here")

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

        self._draw_hud(screen)

        # Draw weather effects on top of everything except UI
        if self.weather_renderer:
            current_weather = self.weather.get_current_condition()
            self.weather_renderer.draw(screen, current_weather)

        # Draw pause menu instead of simple overlay
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

        def draw_marker(pos, col):
            if not pos:
                return
            cx = self.map_offset_x + pos[0] * self.cell_size
            cy = self.map_offset_y + pos[1] * self.cell_size
            pygame.draw.rect(screen, col, pygame.Rect(
                cx, cy, self.cell_size, self.cell_size), 3)

        if self.pinv.active:
            draw_marker(self.pinv.active.pickup, (0, 200, 255))
            draw_marker(self.pinv.active.dropoff, (255, 200, 0))
        elif self.selected:
            draw_marker(self.selected.pickup, (0, 120, 200))
            draw_marker(self.selected.dropoff, (200, 140, 0))

    def _draw_hud(self, screen):
        # Dynamic HUD positioning (was fixed HUD_X)
        x = self.window.hud_x
        white = self.window.colors['WHITE']

        # Scale spacing dynamically
        line_height = self.window.get_scaled_size(20)
        section_spacing = self.window.get_scaled_size(50)

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

        # Weather - enhanced with timing info
        weather_y = 40 + line_height * 4
        current_condition = self.weather.get_current_condition()
        screen.blit(self.font.render(
            f"Weather: {current_condition}", True, white),
            (x, weather_y))

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

        # Available orders list
        list_y = capacity_y + section_spacing
        screen.blit(self.font.render("Available:", True,
                    self.window.colors['GRAY']), (x, list_y))

        y = list_y + line_height
        for o in self.jobs.selectable(self.game.get_game_time())[:6]:
            tag = "<" if self.selected and self.selected.id == o.id else " "
            left = f"{tag} {o.id} w{int(o.weight)} pr{int(o.priority)}"
            screen.blit(self.font.render(left, True, white), (x, y))
            y += int(line_height * 0.9)

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

            # Initialize pause menu
            self.pause_menu = PauseMenu(self.window)

        print("Game view shown with responsive layout")
