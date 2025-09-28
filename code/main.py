import pygame
from .core.city import City
from .services.data_manager import DataManager
from .interface.main_window import MainWindow

print(f"pygame Version: {pygame.__version__}")

if __name__ == "__main__":
    try:

        window = MainWindow()
        window.setup()
        window.run()

    except Exception as e:
        print(f"Failed to load city: {e}")
        input("Press enter to close...")

        import traceback
        traceback.print_exc()
