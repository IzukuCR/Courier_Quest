import pygame
from .game.game import Game
from .interface.main_window import MainWindow
from .services.api_client import APIClient

print(f"pygame Version: {pygame.__version__}")

if __name__ == "__main__":
    try:
        game = Game()

        city = game.get_city()
        if city and hasattr(city, 'tiles'):
            print(
                f"City loaded: {len(city.tiles)}x{len(city.tiles[0])} tiles")
        else:

            print("Warning: Could not load city correctly")
            print(f"City type: {type(city)}")
            print(f"City value: {city}")

        window = MainWindow()
        window.setup()
        window.run()

    except Exception as e:
        print(f"Failed to load city (main): {e}")
        input("Press enter to close...")

        import traceback
        traceback.print_exc()
