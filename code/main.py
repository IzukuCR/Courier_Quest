import arcade
from .core.city import City
from .services.data_manager import DataManager
from .interface.interface import Interface

print(f"Arcade Version: {arcade.VERSION}")

if __name__ == "__main__":
    try:
        # Inicializar datos primero
        data_manager = DataManager()
        data_manager.save_map_data()
        data_manager.save_jobs_data()
        data_manager.save_weather_data()

        print("City map loaded successfully from API!\n")
        city = City.from_data_manager()
        print("City map loaded successfully!\n")
        print(city)

        # Luego crear la ventana y ejecutar la aplicación
        window = Interface()
        arcade.run()
    except Exception as e:
        print(f"Failed to load city: {e}")
        # Mantener la ventana abierta esperando input del usuario
        input("Presiona Enter para cerrar...")
