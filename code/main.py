import pygame
from .game.game import Game
from .interface.main_window import MainWindow

print(f"pygame Version: {pygame.__version__}")

if __name__ == "__main__":
    try:
        game = Game()

        city = game.get_city()
        if city and hasattr(city, 'tiles'):
            print(
                f"Ciudad cargada: {len(city.tiles)}x{len(city.tiles[0])} tiles")
        else:
            print("Warning: No se pudo cargar la ciudad correctamente")
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
