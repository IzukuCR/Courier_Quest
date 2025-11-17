import pygame
import random
import math


class WeatherRenderer:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.particles = []
        self.fog_surface = None

        # Pre-create overlay surfaces for reuse
        self.sunny_overlay = None
        self.rain_overlay = None
        self.cloudy_overlay = None
        self.snow_overlay = None
        self.wind_overlay = None

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
        """Initialize weather effect surfaces - create once and reuse"""
        # Fog overlay
        self.fog_surface = pygame.Surface(
            (self.screen_width, self.screen_height))
        self.fog_surface.set_alpha(120)
        self.fog_surface.fill((160, 160, 160))

        # Pre-create overlay surfaces for each weather type
        self.sunny_overlay = pygame.Surface(
            (self.screen_width, self.screen_height))
        self.sunny_overlay.set_alpha(50)
        self.sunny_overlay.fill((255, 255, 100))

        self.rain_overlay = pygame.Surface(
            (self.screen_width, self.screen_height))
        self.rain_overlay.set_alpha(80)
        self.rain_overlay.fill((40, 60, 100))

        self.cloudy_overlay = pygame.Surface(
            (self.screen_width, self.screen_height))
        self.cloudy_overlay.set_alpha(70)
        self.cloudy_overlay.fill((100, 100, 120))

        self.snow_overlay = pygame.Surface(
            (self.screen_width, self.screen_height))
        self.snow_overlay.set_alpha(40)
        self.snow_overlay.fill((180, 200, 255))

        self.wind_overlay = pygame.Surface(
            (self.screen_width, self.screen_height))
        self.wind_overlay.set_alpha(30)
        self.wind_overlay.fill((120, 120, 140))

        # Rain particles
        self.rain_particles = []
        for _ in range(200):
            self.rain_particles.append({
                'x': random.randint(0, self.screen_width),
                'y': random.randint(-self.screen_height, 0),
                'speed': random.uniform(400, 600),
                'length': random.randint(15, 25)
            })

        # Snow particles
        self.snow_particles = []
        for _ in range(150):
            self.snow_particles.append({
                'x': random.randint(0, self.screen_width),
                'y': random.randint(-self.screen_height, 0),
                'speed': random.uniform(30, 80),
                'size': random.randint(3, 6),
                'drift': random.uniform(-50, 50)
            })

        # Wind particles - REDUCIR cantidad para mejor performance
        self.wind_particles = []
        for _ in range(30):  # Reducido de 50 a 30
            self.wind_particles.append({
                'x': random.randint(-100, self.screen_width + 100),
                'y': random.randint(0, self.screen_height),
                'speed': random.uniform(200, 400),
                'length': random.randint(30, 60),
                'alpha': random.randint(50, 150)
            })

    def update(self, delta_time, weather_condition):
        """Update weather effects"""
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
            particle['x'] += 100 * delta_time

            if particle['y'] > self.screen_height:
                particle['y'] = random.randint(-200, -10)
                particle['x'] = random.randint(-50, self.screen_width + 50)

    def _update_snow(self, delta_time):
        """Update snow particles"""
        for particle in self.snow_particles:
            particle['y'] += particle['speed'] * delta_time
            particle['x'] += particle['drift'] * \
                delta_time * math.sin(particle['y'] * 0.01)

            if particle['y'] > self.screen_height:
                particle['y'] = random.randint(-200, -10)
                particle['x'] = random.randint(-50, self.screen_width + 50)

            if particle['x'] < -50:
                particle['x'] = self.screen_width + 50
            elif particle['x'] > self.screen_width + 50:
                particle['x'] = -50

    def _update_wind(self, delta_time):
        """Update wind particles"""
        for particle in self.wind_particles:
            particle['x'] += particle['speed'] * delta_time

            if particle['x'] > self.screen_width + 100:
                particle['x'] = -100
                particle['y'] = random.randint(0, self.screen_height)

    def draw(self, screen, weather_condition):
        """Draw weather effects on screen"""
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
        """Draw sunny weather effect - OPTIMIZADO"""
        # Usar overlay pre-creado
        screen.blit(self.sunny_overlay, (0, 0))

    def _draw_rain(self, screen):
        """Draw rain particles - OPTIMIZADO"""
        # Usar overlay pre-creado
        screen.blit(self.rain_overlay, (0, 0))

        # Dibujar partículas de lluvia directamente
        for particle in self.rain_particles:
            start_pos = (int(particle['x']), int(particle['y']))
            end_pos = (int(particle['x'] + 5),
                       int(particle['y'] + particle['length']))
            pygame.draw.line(screen, (150, 200, 255), start_pos, end_pos, 2)

    def _draw_cloudy_effect(self, screen):
        """Draw cloudy weather effect - OPTIMIZADO"""
        # Usar overlay pre-creado
        screen.blit(self.cloudy_overlay, (0, 0))

    def _draw_fog(self, screen):
        """Draw fog effect"""
        screen.blit(self.fog_surface, (0, 0))

        # Fog patches simplificados
        for i in range(5):
            x = (pygame.time.get_ticks() // 50 + i *
                 100) % (self.screen_width + 200) - 100
            y = 100 + i * 80
            fog_patch = pygame.Surface((200, 100), pygame.SRCALPHA)
            pygame.draw.ellipse(
                fog_patch, (200, 200, 200, 60), (0, 0, 200, 100))
            screen.blit(fog_patch, (x, y))

    def _draw_snow(self, screen):
        """Draw snow particles - OPTIMIZADO"""
        # Usar overlay pre-creado
        screen.blit(self.snow_overlay, (0, 0))

        # Dibujar partículas de nieve directamente
        for particle in self.snow_particles:
            pygame.draw.circle(screen, (255, 255, 255),
                               (int(particle['x']), int(particle['y'])),
                               particle['size'])
            # Glow simplificado
            pygame.draw.circle(screen, (240, 240, 255),
                               (int(particle['x']), int(particle['y'])),
                               particle['size'] + 1, 1)

    def _draw_windy_effect(self, screen):
        """Draw windy weather effect - MUY OPTIMIZADO"""
        # Usar overlay pre-creado
        screen.blit(self.wind_overlay, (0, 0))

        # Dibujar líneas de viento directamente sin crear superficies nuevas
        for particle in self.wind_particles:
            start_pos = (int(particle['x']), int(particle['y']))
            end_pos = (
                int(particle['x'] + particle['length']), int(particle['y']))

            # Calcular color con alpha basado en el alpha de la partícula
            # Usar gaaline para líneas suavizadas es más eficiente que crear superficies
            alpha_factor = particle['alpha'] / 255.0
            color = (int(200 * alpha_factor), int(200 *
                     alpha_factor), int(200 * alpha_factor))

            # Usar aalines que es más rápido
            pygame.draw.aaline(screen, color, start_pos, end_pos)
