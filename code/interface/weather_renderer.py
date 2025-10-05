import pygame
import random
import math


class WeatherRenderer:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.particles = []
        self.fog_surface = None
        self.init_effects()

    def init_effects(self):
        """Initialize weather effect surfaces"""
        # Fog overlay
        self.fog_surface = pygame.Surface(
            (self.screen_width, self.screen_height))
        self.fog_surface.set_alpha(100)
        self.fog_surface.fill((180, 180, 180))

        # Rain particles
        self.rain_particles = []
        for _ in range(150):
            self.rain_particles.append({
                'x': random.randint(0, self.screen_width),
                'y': random.randint(-self.screen_height, 0),
                'speed': random.uniform(300, 500),
                'length': random.randint(10, 20)
            })

        # Snow particles
        self.snow_particles = []
        for _ in range(100):
            self.snow_particles.append({
                'x': random.randint(0, self.screen_width),
                'y': random.randint(-self.screen_height, 0),
                'speed': random.uniform(50, 100),
                'size': random.randint(2, 4),
                'drift': random.uniform(-30, 30)
            })

    def update(self, delta_time, weather_condition):
        """Update weather effects"""
        if weather_condition == "rainy":
            self._update_rain(delta_time)
        elif weather_condition == "snowy":
            self._update_snow(delta_time)

    def _update_rain(self, delta_time):
        """Update rain particles"""
        for particle in self.rain_particles:
            particle['y'] += particle['speed'] * delta_time
            particle['x'] += 50 * delta_time  # Slight diagonal

            # Reset particle when it goes off screen
            if particle['y'] > self.screen_height:
                particle['y'] = random.randint(-100, -10)
                particle['x'] = random.randint(0, self.screen_width)

    def _update_snow(self, delta_time):
        """Update snow particles"""
        for particle in self.snow_particles:
            particle['y'] += particle['speed'] * delta_time
            particle['x'] += particle['drift'] * delta_time

            # Reset particle when it goes off screen
            if particle['y'] > self.screen_height:
                particle['y'] = random.randint(-100, -10)
                particle['x'] = random.randint(0, self.screen_width)

    def draw(self, screen, weather_condition):
        """Draw weather effects on screen"""
        if weather_condition == "sunny":
            self._draw_sunny_effect(screen)
        elif weather_condition == "rainy":
            self._draw_rain(screen)
        elif weather_condition == "cloudy":
            self._draw_cloudy_effect(screen)
        elif weather_condition == "foggy":
            self._draw_fog(screen)
        elif weather_condition == "snowy":
            self._draw_snow(screen)
        elif weather_condition == "windy":
            self._draw_windy_effect(screen)

    def _draw_sunny_effect(self, screen):
        """Draw sunny weather effect"""
        # Light golden overlay
        sunny_overlay = pygame.Surface((self.screen_width, self.screen_height))
        sunny_overlay.set_alpha(30)
        sunny_overlay.fill((255, 255, 150))
        screen.blit(sunny_overlay, (0, 0))

    def _draw_rain(self, screen):
        """Draw rain particles"""
        for particle in self.rain_particles:
            start_pos = (int(particle['x']), int(particle['y']))
            end_pos = (int(particle['x'] + 3),
                       int(particle['y'] + particle['length']))
            pygame.draw.line(screen, (100, 150, 255), start_pos, end_pos, 1)

        # Dark overlay for stormy atmosphere
        rain_overlay = pygame.Surface((self.screen_width, self.screen_height))
        rain_overlay.set_alpha(40)
        rain_overlay.fill((60, 80, 120))
        screen.blit(rain_overlay, (0, 0))

    def _draw_cloudy_effect(self, screen):
        """Draw cloudy weather effect"""
        cloudy_overlay = pygame.Surface(
            (self.screen_width, self.screen_height))
        cloudy_overlay.set_alpha(50)
        cloudy_overlay.fill((120, 120, 140))
        screen.blit(cloudy_overlay, (0, 0))

    def _draw_fog(self, screen):
        """Draw fog effect"""
        screen.blit(self.fog_surface, (0, 0))

    def _draw_snow(self, screen):
        """Draw snow particles"""
        for particle in self.snow_particles:
            pygame.draw.circle(screen, (255, 255, 255),
                               (int(particle['x']), int(particle['y'])),
                               particle['size'])

        # Cold blue overlay
        snow_overlay = pygame.Surface((self.screen_width, self.screen_height))
        snow_overlay.set_alpha(30)
        snow_overlay.fill((200, 220, 255))
        screen.blit(snow_overlay, (0, 0))

    def _draw_windy_effect(self, screen):
        """Draw windy weather effect"""
        # Subtle movement lines
        for i in range(10):
            x = random.randint(0, self.screen_width)
            y = random.randint(0, self.screen_height)
            end_x = x + random.randint(20, 50)
            pygame.draw.line(screen, (180, 180, 180), (x, y), (end_x, y), 1)
