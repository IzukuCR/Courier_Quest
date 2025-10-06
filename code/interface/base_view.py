import pygame


class BaseView:
    def __init__(self):
        self.window = None
        # If the window's colors dictionary doesn't include LIGHT_GRAY, add it here
        if hasattr(self, 'window') and hasattr(self.window, 'colors'):
            self.window.colors['LIGHT_GRAY'] = (200, 200, 200)

    def on_show(self):
        # Called when the view becomes active
        pass

    def handle_event(self, event):
        # Event handling
        pass

    def update(self, delta_time: float):
        # Update view logic
        pass

    def draw(self, screen):
        # Render elements on the screen
        pass
