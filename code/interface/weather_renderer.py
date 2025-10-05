import pygame
import random
import math


class WeatherRenderer:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.particles = []
        self.fog_surface = None

        # Weather condition mapping from game weather to visual effects
        self.weather_mapping = {
            "clear": "sunny",
            "clouds": "cloudy",
            "rain_light": "rainy",
            "rain": "rainy",
            "storm": "rainy",
            "fog": "foggy",
            "wind": "windy",
            "heat": "sunny",
            "cold": "snowy"
        }

        self.init_effects()

    def init_effects(self):
        """Initialize weather effect surfaces"""
        # Fog overlay - make it more visible
        self.fog_surface = pygame.Surface(
            (self.screen_width, self.screen_height))
        self.fog_surface.set_alpha(120)  # Increased from 100
        self.fog_surface.fill((160, 160, 160))

        # Rain particles - more visible
        self.rain_particles = []
        for _ in range(200):  # Increased from 150
            self.rain_particles.append({
                'x': random.randint(0, self.screen_width),
                'y': random.randint(-self.screen_height, 0),
                'speed': random.uniform(400, 600),  # Faster
                'length': random.randint(15, 25)  # Longer
            })

        # Snow particles - more visible
        self.snow_particles = []
        for _ in range(150):  # Increased from 100
            self.snow_particles.append({
                'x': random.randint(0, self.screen_width),
                'y': random.randint(-self.screen_height, 0),
                'speed': random.uniform(30, 80),  # Slower for realism
                'size': random.randint(3, 6),  # Bigger
                'drift': random.uniform(-50, 50)  # More drift
            })

        # Wind particles for windy effect
        self.wind_particles = []
        for _ in range(50):
            self.wind_particles.append({
                'x': random.randint(-100, self.screen_width + 100),
                'y': random.randint(0, self.screen_height),
                'speed': random.uniform(200, 400),
                'length': random.randint(30, 60),
                'alpha': random.randint(50, 150)
            })

    def update(self, delta_time, weather_condition):
        """Update weather effects"""
        # Map game weather condition to visual effect
        visual_condition = self.weather_mapping.get(
            weather_condition, weather_condition)

        if visual_condition == "rainy":
            self._update_rain(delta_time)
        elif visual_condition == "snowy":
            self._update_snow(delta_time)
        elif visual_condition == "windy":
            self._update_wind(delta_time)

    def _update_rain(self, delta_time):
        """Update rain particles"""
        for particle in self.rain_particles:
            particle['y'] += particle['speed'] * delta_time
            particle['x'] += 100 * delta_time  # More diagonal movement

            # Reset particle when it goes off screen
            if particle['y'] > self.screen_height:
                particle['y'] = random.randint(-200, -10)
                particle['x'] = random.randint(-50, self.screen_width + 50)

    def _update_snow(self, delta_time):
        """Update snow particles"""
        for particle in self.snow_particles:
            particle['y'] += particle['speed'] * delta_time
            particle['x'] += particle['drift'] * \
                delta_time * math.sin(particle['y'] * 0.01)

            # Reset particle when it goes off screen
            if particle['y'] > self.screen_height:
                particle['y'] = random.randint(-200, -10)
                particle['x'] = random.randint(-50, self.screen_width + 50)

            # Wrap around horizontally
            if particle['x'] < -50:
                particle['x'] = self.screen_width + 50
            elif particle['x'] > self.screen_width + 50:
                particle['x'] = -50

    def _update_wind(self, delta_time):
        """Update wind particles"""
        for particle in self.wind_particles:
            particle['x'] += particle['speed'] * delta_time

            # Reset particle when it goes off screen
            if particle['x'] > self.screen_width + 100:
                particle['x'] = -100
                particle['y'] = random.randint(0, self.screen_height)

    def draw(self, screen, weather_condition):
        """Draw weather effects on screen"""
        # Map game weather condition to visual effect
        visual_condition = self.weather_mapping.get(
            weather_condition, weather_condition)

        if visual_condition == "sunny":
            self._draw_sunny_effect(screen)
        elif visual_condition == "rainy":
            self._draw_rain(screen)
        elif visual_condition == "cloudy":
            self._draw_cloudy_effect(screen)
        elif visual_condition == "foggy":
            self._draw_fog(screen)
        elif visual_condition == "snowy":
            self._draw_snow(screen)
        elif visual_condition == "windy":
            self._draw_windy_effect(screen)

    def _draw_sunny_effect(self, screen):
        """Draw sunny weather effect"""
        # Bright golden overlay
        sunny_overlay = pygame.Surface((self.screen_width, self.screen_height))
        sunny_overlay.set_alpha(50)  # Increased from 30
        sunny_overlay.fill((255, 255, 100))  # More yellow
        screen.blit(sunny_overlay, (0, 0))

        # Add some light rays effect
        center_x = self.screen_width // 2
        center_y = self.screen_height // 4
        for i in range(8):
            angle = (i * 45) * math.pi / 180
            end_x = center_x + math.cos(angle) * 300
            end_y = center_y + math.sin(angle) * 300

            # Create a surface for the ray with alpha
            ray_surface = pygame.Surface(
                (self.screen_width, self.screen_height), pygame.SRCALPHA)
            pygame.draw.line(ray_surface, (255, 255, 150, 30),
                             (center_x, center_y), (int(end_x), int(end_y)), 3)
            screen.blit(ray_surface, (0, 0))

    def _draw_rain(self, screen):
        """Draw rain particles"""
        # Dark overlay for stormy atmosphere first
        rain_overlay = pygame.Surface((self.screen_width, self.screen_height))
        rain_overlay.set_alpha(80)  # Increased from 40
        rain_overlay.fill((40, 60, 100))  # Darker blue
        screen.blit(rain_overlay, (0, 0))

        # Then draw rain particles
        for particle in self.rain_particles:
            start_pos = (int(particle['x']), int(particle['y']))
            end_pos = (int(particle['x'] + 5),  # Wider
                       int(particle['y'] + particle['length']))
            pygame.draw.line(screen, (150, 200, 255),
                             start_pos, end_pos, 2)  # Thicker lines

    def _draw_cloudy_effect(self, screen):
        """Draw cloudy weather effect"""
        cloudy_overlay = pygame.Surface(
            (self.screen_width, self.screen_height))
        cloudy_overlay.set_alpha(70)  # Increased from 50
        cloudy_overlay.fill((100, 100, 120))  # Darker
        screen.blit(cloudy_overlay, (0, 0))

    def _draw_fog(self, screen):
        """Draw fog effect"""
        screen.blit(self.fog_surface, (0, 0))

        # Add moving fog patches
        for i in range(5):
            x = (pygame.time.get_ticks() // 50 + i *
                 100) % (self.screen_width + 200) - 100
            y = 100 + i * 80
            fog_patch = pygame.Surface((200, 100), pygame.SRCALPHA)
            pygame.draw.ellipse(
                fog_patch, (200, 200, 200, 60), (0, 0, 200, 100))
            screen.blit(fog_patch, (x, y))

    def _draw_snow(self, screen):
        """Draw snow particles"""
        # Cold blue overlay first
        snow_overlay = pygame.Surface((self.screen_width, self.screen_height))
        snow_overlay.set_alpha(40)  # Increased from 30
        snow_overlay.fill((180, 200, 255))  # More blue
        screen.blit(snow_overlay, (0, 0))

        # Then draw snow particles
        for particle in self.snow_particles:
            pygame.draw.circle(screen, (255, 255, 255),
                               (int(particle['x']), int(particle['y'])),
                               particle['size'])
            # Add a subtle glow
            pygame.draw.circle(screen, (240, 240, 255),
                               (int(particle['x']), int(particle['y'])),
                               particle['size'] + 1, 1)

    def _draw_windy_effect(self, screen):
        """Draw windy weather effect"""
        # Light gray overlay
        wind_overlay = pygame.Surface((self.screen_width, self.screen_height))
        wind_overlay.set_alpha(30)
        wind_overlay.fill((120, 120, 140))
        screen.blit(wind_overlay, (0, 0))

        # Draw wind lines
        for particle in self.wind_particles:
            start_pos = (int(particle['x']), int(particle['y']))
            end_pos = (
                int(particle['x'] + particle['length']), int(particle['y']))

            # Create a surface with alpha for the wind line
            wind_surface = pygame.Surface(
                (self.screen_width, self.screen_height), pygame.SRCALPHA)
            color = (200, 200, 200, particle['alpha'])
            pygame.draw.line(wind_surface, color, start_pos, end_pos, 2)
            screen.blit(wind_surface, (0, 0))
