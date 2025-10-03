
import datetime


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

    def next_weather(self):
        import random

        old_condition = self.current_condition  # Save old condition (aux)
        old_intensity = self.current_intensity  # Save old intensity (aux)

        # Get conditions and probabilities for current condition
        transitions = self.transition_matrix.get(self.current_condition, {})

        if transitions:
            # Get lists of conditions and their probabilities
            conditions = list(transitions.keys())
            probabilities = list(transitions.values())

            # Update to the new condition using Markov
            self.current_condition = random.choices(
                conditions, weights=probabilities)[0]
            # Intensity random between 0.0 and 1.0 for new condition, later overridden if burst found
            self.current_intensity = random.uniform(0.0, 1.0)
        else:
            # If no transitions, keep current condition and intensity
            print(
                f"Weather Class: No transitions available for {self.current_condition}")

        # Search for active burst for the new condition
        active_burst = self._get_active_burst_for_condition(
            self.current_condition)

        if active_burst:
            # If there's an active burst, override intensity
            self.current_intensity = active_burst["intensity"]

            return {
                "source": "markov_with_burst",
                "old_condition": old_condition,
                "new_condition": self.current_condition,
                "old_intensity": old_intensity,
                "new_intensity": self.current_intensity,
                "burst_info": active_burst,
                "transitions_used": len(transitions)
            }
        else:
            # If no active burst, keep the random intensity from Markov
            return {
                "source": "markov_only",
                "old_condition": old_condition,
                "new_condition": self.current_condition,
                "old_intensity": old_intensity,
                "new_intensity": self.current_intensity,
                "transitions_used": len(transitions)
            }

    def _get_active_burst_for_condition(self, target_condition):

        from datetime import datetime, timezone, timedelta

        try:
            current_time = datetime.now(timezone.utc)
        except Exception as e:
            print(f"Weather Class: Error getting current time: {e}")
            return None

        for burst in self.bursts:
            if burst["condition"] == target_condition:
                try:
                    # Mover la declaración de variables dentro del try específico
                    burst_start = datetime.fromisoformat(
                        burst["from"].replace('Z', '+00:00'))
                    burst_end = burst_start + \
                        timedelta(seconds=burst["duration_sec"])

                    # Verificar si el burst está activo en este momento
                    if burst_start <= current_time < burst_end:
                        remaining_sec = int(
                            (burst_end - current_time).total_seconds())

                        return {
                            "condition": burst["condition"],
                            "intensity": burst["intensity"],
                            "duration_sec": burst["duration_sec"],
                            "remaining_sec": remaining_sec,
                            "from": burst["from"]
                        }

                except Exception as e:
                    print(
                        f"Weather Class: Error parsing burst for condition '{target_condition}': {e}")
                    continue

        return None

    def _get_active_burst(self):

        from datetime import datetime, timezone, timedelta

        # Obtener tiempo actual una sola vez
        try:
            current_time = datetime.now(timezone.utc)
        except Exception as e:
            print(f"Weather Class: Error getting current time: {e}")
            return None

        for burst in self.bursts:
            try:
                # Variables dentro del try específico para cada burst
                burst_start = datetime.fromisoformat(
                    burst["from"].replace('Z', '+00:00'))
                burst_end = burst_start + \
                    timedelta(seconds=burst["duration_sec"])

                if burst_start <= current_time < burst_end:
                    remaining_sec = int(
                        (burst_end - current_time).total_seconds())

                    return {
                        "condition": burst["condition"],
                        "intensity": burst["intensity"],
                        "duration_sec": burst["duration_sec"],
                        "remaining_sec": remaining_sec,
                        "from": burst["from"]
                    }

            except Exception as e:
                print(f"Weather Class: Error parsing burst: {e}")
                continue  # Continuar con el siguiente burst

        return None


