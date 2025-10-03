import pygame


class BaseView:
    def __init__(self):
        self.window = None

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
