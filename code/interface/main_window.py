import pygame
import sys


class MainWindow:
    def __init__(self, width=1400, height=1000, title="Courier Quest"):
        pygame.init()
        self.width = width
        self.height = height
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
