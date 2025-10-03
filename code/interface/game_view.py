import pygame
from .base_view import BaseView
from ..game.game import Game

HUD_X = 950


class GameView(BaseView):
    def __init__(self):
        super().__init__()
        self.game = Game()
        self.player_name = self.game.get_player_name()

        # Map configuration
        self.city = self.game.get_city()
        if hasattr(self.city, 'tiles'):
            self.matrix = self.city.tiles
        else:
            self.matrix = []

        self.cell_size = 30
        self.map_offset_x = 20
        self.map_offset_y = 20  # Tiles size 30x30

        # Tile colors (fallback if images not loaded)
        self.tile_colors = {
            "C": (128, 128, 128),    # GRAY
            "P": (34, 139, 34),      # FOREST_GREEN
            "B": (139, 69, 19),      # BROWN
        }

        self.font = pygame.font.Font(None, 24)
        self.big = pygame.font.Font(None, 32)

        # Load tile images
        self.load_tile_images()

        # References
        self.player = self.game.get_player()
        self.weather = self.game.get_weather()
        self.jobs = self.game.get_jobs()
        self.pinv = self.game.get_player_inventory()

        # Toast
        self.toast = ""
        self.toast_timer = 0.0

        # Order selection
        self.jobs._selected_index = -1
        self.selected = self.jobs.cycle_selection(self.game.get_game_time())

    def load_tile_images(self):

        self.tile_images = {}

        tile_files = {
            "B": "code/assets/tiles/buildIngBorderless1.PNG"
        }

        for tile_type, file_path in tile_files.items():  # Load only specified tiles
            try:
                image = pygame.image.load(file_path)
                original_size = image.get_size()
                print(
                    f"DEBUG TILES - Original '{tile_type}' size: {original_size}")

                # VERIFY: Is it scaling correctly?
                scaled_image = pygame.transform.scale(
                    image, (self.cell_size, self.cell_size))
                final_size = scaled_image.get_size()
                print(f"DEBUG TILES - Scaled '{tile_type}' size: {final_size}")

                self.tile_images[tile_type] = scaled_image

            except pygame.error as e:
                print(f"Error loading {file_path}: {e}")

        if not self.tile_images:
            print("Game view: No tile images loaded, using colors")
            self.tile_images = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.toggle_pause()
                return

            if self.game.is_paused():
                return  # ignore inputs while paused

            if event.key == pygame.K_TAB:
                self.selected = self.jobs.cycle_selection(self.game.get_game_time())
                if self.selected:
                    self.toast, self.toast_timer = f"Selected {self.selected.id}", 2.0

            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.selected:
                    if self.pinv.accept(self.selected, self.game.get_game_time()):
                        self.toast, self.toast_timer = f"Accepted {self.selected.id}", 2.0
                    else:
                        self.toast, self.toast_timer = f"Could not accept {self.selected.id}", 2.0

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
                    ok = self.player.move_to(new_x, new_y, self.city, self.weather)
                    if not ok:
                        self.toast, self.toast_timer = "You can't move there", 1.5


    def draw(self, screen):
        screen.fill(self.window.colors['BLACK'])
        self._draw_map(screen)
        if self.player:
            self.player.draw(screen, self.cell_size, self.map_offset_x, self.map_offset_y)

        self._draw_hud(screen)

        # Pause overlay
        if self.game.is_paused():
            s = pygame.Surface((self.window.width, self.window.height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 160))
            screen.blit(s, (0, 0))
            txt = self.big.render("PAUSED - ESC to continue", True, self.window.colors['WHITE'])
            screen.blit(txt, txt.get_rect(center=(self.window.width//2, self.window.height//2)))

        # Toast (brief messages)
        if self.toast:
            t = self.font.render(self.toast, True, (255, 255, 0))
            screen.blit(t, (HUD_X, 700))


    def _draw_map(self, screen):
        if not self.matrix:
            return

        # tiles
        for r, row in enumerate(self.matrix):
            for c, cell in enumerate(row):
                x = self.map_offset_x + c * self.cell_size
                y = self.map_offset_y + r * self.cell_size
                if self.tile_images and cell in self.tile_images:
                    screen.blit(self.tile_images[cell], (x, y))
                    pygame.draw.rect(screen, (0, 0, 0), (x, y, self.cell_size, self.cell_size), 1)
                else:
                    color = self.tile_colors.get(cell, self.window.colors["WHITE"])
                    rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                    pygame.draw.rect(screen, color, rect)
                    pygame.draw.rect(screen, (0, 0, 0), rect, 1)
        # pickup / dropoff markers (internal helper using self/screen)
        def draw_marker(pos, col):
            if not pos:
                return
            cx = self.map_offset_x + pos[0] * self.cell_size
            cy = self.map_offset_y + pos[1] * self.cell_size
            pygame.draw.rect(screen, col, pygame.Rect(cx, cy, self.cell_size, self.cell_size), 3)

        if self.pinv.active:
            draw_marker(self.pinv.active.pickup, (0, 200, 255))
            draw_marker(self.pinv.active.dropoff, (255, 200, 0))
        elif self.selected:
            draw_marker(self.selected.pickup, (0, 120, 200))
            draw_marker(self.selected.dropoff, (200, 140, 0))

    def _draw_hud(self, screen):
        x = HUD_X
        white = self.window.colors['WHITE']

        # Time
        t = self.game.get_game_time()
        mins, secs = int(t//60), int(t%60)
        screen.blit(self.big.render(f"Time {mins:02d}:{secs:02d}", True, white), (x, 40))

        # Weather
        screen.blit(self.font.render(f"Weather: {self.weather.get_current_condition()}", True, white), (x, 80))

        # Orders
        screen.blit(self.big.render("Orders", True, white), (x, 130))
        sel = self.selected.id if self.selected else "-"
        act = self.pinv.active.id if self.pinv.active else "-"
        screen.blit(self.font.render(f"Selected: {sel}", True, white), (x, 170))
        screen.blit(self.font.render(f"Active: {act}", True, white), (x, 195))

        # Capacity
        screen.blit(self.font.render(
            f"Capacity: {self.pinv.carried_weight():.1f} / {self.pinv.capacity_weight:.1f}",
            True, white), (x, 225))

        # Brief list of available orders
        y = 260
        screen.blit(self.font.render("Available:", True, self.window.colors['GRAY']), (x, y))
        y += 20
        for o in self.jobs.selectable(self.game.get_game_time())[:6]:
            tag = "<" if self.selected and self.selected.id == o.id else " "
            left = f"{tag} {o.id} w{int(o.weight)} pr{int(o.priority)}"
            screen.blit(self.font.render(left, True, white), (x, y))
            y += 18

    def update(self, delta_time: float):
        self.game.update(delta_time)

        if self.player:
            self.player.update(delta_time)
            if not self.player.is_moving:
                msg = self.game.on_player_moved(self.player.x, self.player.y)
                if msg:
                    self.toast, self.toast_timer = msg, 2.0

        if self.toast_timer > 0:
            self.toast_timer -= delta_time
            if self.toast_timer <= 0:
                self.toast = ""

    def on_show(self):
        print("Game view shown")
