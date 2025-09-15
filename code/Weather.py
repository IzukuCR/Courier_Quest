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

    # Markov chain transition matrix
    TRANSITION_MATRIX = {
        "clear": {"clear": 0.6, "clouds": 0.25, "rain_light": 0.1, "rain": 0.03, "storm": 0.01, "fog": 0.005, "wind": 0.005},
        "clouds": {"clear": 0.3, "clouds": 0.5, "rain_light": 0.15, "rain": 0.03, "storm": 0.01, "fog": 0.005, "wind": 0.005},
        "rain_light": {"clear": 0.1, "clouds": 0.3, "rain_light": 0.4, "rain": 0.15, "storm": 0.03, "fog": 0.01, "wind": 0.01},
        "rain": {"clear": 0.05, "clouds": 0.2, "rain_light": 0.3, "rain": 0.35, "storm": 0.08, "fog": 0.01, "wind": 0.01},
        "storm": {"clear": 0.02, "clouds": 0.15, "rain_light": 0.2, "rain": 0.4, "storm": 0.2, "fog": 0.02, "wind": 0.01},
        "fog": {"clear": 0.3, "clouds": 0.4, "rain_light": 0.15, "rain": 0.1, "storm": 0.02, "fog": 0.02, "wind": 0.01},
        "wind": {"clear": 0.4, "clouds": 0.3, "rain_light": 0.15, "rain": 0.1, "storm": 0.02, "fog": 0.02, "wind": 0.01}
    }

    def __init__(self, weather_data):
        self.city = weather_data.get("city", "")
        self.date = weather_data.get("date", "")
        self.bursts = weather_data.get("bursts", [])
        self.meta = weather_data.get("meta", {})

    def get_city(self):
        return self.city

    def get_date(self):
        return self.date

    def get_bursts(self):
        return self.bursts

    def get_meta(self):
        return self.meta

    def get_burst_by_condition(self, condition):
        return [burst for burst in self.bursts if burst.get("condition") == condition]

    def get_total_duration(self):
        # Calculate total duration of all weather bursts.
        return sum(burst.get("duration_sec", 0) for burst in self.bursts)

    def __str__(self):
        # String representation of the Weather object
        return f"Weather in {self.city} on {self.date} - {len(self.bursts)} bursts"

    def __repr__(self):
        # Detailed representation of the Weather object.
        return f"Weather(city='{self.city}', date='{self.date}', bursts={len(self.bursts)})"

    def get_speed_multiplier(self, condition, intensity=1.0):
        """
        Get speed multiplier for a given weather condition and intensity.

        Args:
            condition (str): Weather condition
            intensity (float): Intensity level (0-1)

        Returns:
            float: Speed multiplier adjusted by intensity
        """
        base_multiplier = self.SPEED_MULTIPLIERS.get(condition, 1.0)
        # Apply intensity: higher intensity = more impact on speed
        # Formula: base + (1 - base) * (1 - intensity)
        return base_multiplier + (1 - base_multiplier) * (1 - intensity)

    def get_next_weather_probability(self, current_condition):
        """
        Get probability distribution for next weather condition.

        Args:
            current_condition (str): Current weather condition

        Returns:
            dict: Probability distribution for next conditions
        """
        return self.TRANSITION_MATRIX.get(current_condition, {})

    def predict_next_condition(self, current_condition):

        probabilities = self.get_next_weather_probability(current_condition)
        if not probabilities:
            return current_condition

        # Return condition with highest probability
        return max(probabilities, key=probabilities.get)

    def interpolate_multiplier(self, from_condition, to_condition, progress):
        """
        Interpolate speed multiplier between two weather conditions.
        Used for smooth transitions (3-5 seconds).

        Args:
            from_condition (str): Starting weather condition
            to_condition (str): Target weather condition
            progress (float): Transition progress (0.0 to 1.0)

        Returns:
            float: Interpolated speed multiplier
        """
        from_multiplier = self.SPEED_MULTIPLIERS.get(from_condition, 1.0)
        to_multiplier = self.SPEED_MULTIPLIERS.get(to_condition, 1.0)

        # Linear interpolation
        return from_multiplier + (to_multiplier - from_multiplier) * progress

    def calculate_burst_effect(self, burst):
        """
        Calculate the effect of a weather burst on speed.

        Args:
            burst (dict): Weather burst with condition, duration_sec, and intensity

        Returns:
            dict: Effect information including speed multiplier and duration
        """
        condition = burst.get("condition", "clear")
        intensity = burst.get("intensity", 1.0)
        duration = burst.get("duration_sec", 0)

        speed_multiplier = self.get_speed_multiplier(condition, intensity)

        return {
            "condition": condition,
            "intensity": intensity,
            "duration_sec": duration,
            "speed_multiplier": speed_multiplier,
            # Percentage reduction
            "speed_reduction": (1.0 - speed_multiplier) * 100
        }
