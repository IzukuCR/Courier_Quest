import pygame
import sys


class MainWindow:
    def __init__(self, width=None, height=None, title="Courier Quest"):
        pygame.init()

        # Get screen resolution for responsive design
        info = pygame.display.Info()
        screen_width = info.current_w
        screen_height = info.current_h

        # Calculate responsive dimensions (80% of screen, minimum 1200x800)
        if width is None:
            width = max(1200, int(screen_width * 0.8))
        if height is None:
            height = max(800, int(screen_height * 0.8))

        # Ensure aspect ratio is reasonable (width should be >= height)
        if width < height * 1.2:
            width = int(height * 1.2)

        self.width = width
        self.height = height

        # Calculate scaling factors for responsive UI
        self.scale_x = width / 1400  # Base resolution was 1400x1000
        self.scale_y = height / 1000
        self.scale = min(self.scale_x, self.scale_y)  # Uniform scaling

        # Dynamic HUD positioning (was fixed at 950)
        self.hud_x = int(width * 0.68)  # 68% from left edge
        self.map_area_width = self.hud_x - 40  # Leave 40px margin

        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)

        self.clock = pygame.time.Clock()
        self.current_view = None
        self.running = True

        # Basic colors
        self.colors = {
            'WHITE': (255, 255, 255),
            'BLACK': (0, 0, 0),
            'GRAY': (128, 128, 128),
            'DARK_GRAY': (64, 64, 64),
            'BLUE': (0, 100, 200),
            'GREEN': (0, 150, 0),
            'RED': (200, 0, 0)
        }

    def show_view(self, view):
        # Change the view to a new one
        self.current_view = view
        self.current_view.window = self
        self.current_view.on_show()

    def run(self):
        # Main loop
        while self.running:
            dt = self.clock.tick(60) / 1000.0  # seconds since last frame
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.current_view:
                    self.current_view.handle_event(event)

            # Update view
            if self.current_view:
                self.current_view.update(dt)
                self.current_view.draw(self.screen)

            # Refresh window
            pygame.display.flip()
            self.clock.tick(120)  # 120 FPS

        pygame.quit()
        sys.exit()

    def setup(self):
        # Start with the menu view
        from .menu_view import MenuView
        menu_view = MenuView()
        self.show_view(menu_view)

    def get_scaled_size(self, original_size):
        """Scale size based on current resolution"""
        return int(original_size * self.scale)

    def get_scaled_pos(self, x, y):
        """Scale position based on current resolution"""
        return int(x * self.scale_x), int(y * self.scale_y)
