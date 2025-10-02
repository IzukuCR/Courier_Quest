
class Weather:
    # Speed multipliers for bicycle based on weather conditions
    SPEED_MULTIPLIERS = {
        "clear": 1.00,
        "clouds": 0.98,
        "rain_light": 0.90,
        "rain": 0.85,
        "storm": 0.75,
        "fog": 0.88,
        "wind": 0.92,
        "heat": 0.90,
        "cold": 0.92
    }

    def __init__(self,):

        self.city = "Unknown"
        self.initial_condition = {}
        self.conditions = ["clear"]
        self.transition_matrix = {}

        # Current weather state
        self.current_condition = "clear"
        self.current_intensity = 0.0

        # Burst events
        self.start_time = None
        self.bursts = []
        self.meta = {}

    def get_city(self):
        return self.city

    def get_current_condition(self):
        return self.current_condition

    def get_current_intensity(self):
        return self.current_intensity

    def get_speed_multiplier(self):
        # Default to 1.0 if condition not found
        return self.SPEED_MULTIPLIERS.get(self.current_condition, 1.0)

    def update_weather(self):
        import random

        # Get possible transitions for the current condition
        transitions = self.transition_matrix.get(self.current_condition, {})
        if not transitions:
            return  # No transitions available

        # Create a list of conditions and their corresponding probabilities
        conditions = list(transitions.keys())
        probabilities = list(transitions.values())

        # Choose the next condition based on the transition probabilities
        self.current_condition = random.choices(
            conditions, weights=probabilities)[0]
        self.current_intensity = random.uniform(
            0.0, 1.0)  # Reset intensity for new condition
        # Optionally, you could implement intensity changes based on condition

    def load_weather(self):
        from ..services.data_manager import DataManager
        # Get singleton instance of DataManager
        data_manager = DataManager().get_instance()

        weather_data = data_manager.load_weather()
        burst_data = data_manager.load_weather_burst()

        success_seed = False
        success_burst = False

        if weather_data:
            self.city = weather_data.get("city", "Unknown")
            self.initial_condition = weather_data.get("initial", {})
            self.conditions = weather_data.get("conditions", ["clear"])
            self.transition_matrix = weather_data.get("transition", {})

            # Set initial weather state
            self.current_condition = self.initial_condition.get(
                "condition", "clear")
            self.current_intensity = self.initial_condition.get(
                "intensity", 0.0)

            print(f"Weather class: Weather seed data loaded for {self.city}")
            success_seed = True
        else:
            print("Weather class: Failed to load weather seed data")

        # Procesar datos burst
        if burst_data:
            self.start_time = burst_data.get("start_time", None)
            self.bursts = burst_data.get("bursts", [])
            self.meta = burst_data.get("meta", {})

            print(
                f"Weather class: Weather burst data loaded: {len(self.bursts)} bursts")
            success_burst = True
        else:
            print("Weather class: Failed to load weather burst data")

        return success_seed or success_burst
