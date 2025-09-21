from core.city import City


def main():
    try:
        city = City.from_data_manager()
        print("City map loaded successfully!\n")
        print(city)
    except Exception as e:
        print(f"Failed to load city: {e}")


if __name__ == "__main__":
    main()
