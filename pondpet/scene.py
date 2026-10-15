"""The garden: bounded, time-based animation over original raster artwork."""

from __future__ import annotations

import math
import random
from datetime import datetime
from pathlib import Path

import pygame

ASSETS = Path(__file__).parent / "assets"


class Garden:
    def __init__(self):
        self.art = pygame.image.load(str(ASSETS / "garden.png")).convert()
        sprite = pygame.image.load(str(ASSETS / "koi.png")).convert_alpha()
        self.koi = sprite.subsurface(sprite.get_bounding_rect()).copy()
        self.ripples = []
        self.drops = []
        self.rain = []
        self.pellets = []
        self.fish = [
            {"x": 0.43, "y": 0.64, "angle": 0.2, "phase": 0.0},
            {"x": 0.67, "y": 0.73, "angle": 3.3, "phase": 2.8},
        ]
        self.elapsed = 0.0
        self._cache = {}
        self._fish_cache = {}
        self.random = random.Random()
        self._ripple_clock = 0.0

    def splash(self, x=0.5, y=0.7, big=False):
        if not self.in_water(x, y):
            return False
        self.ripples.append([x, y, 0.0, 0.10 if big else 0.055])
        for _ in range(9 if big else 4):
            self.drops.append(
                [x, y, self.random.uniform(-0.07, 0.07), self.random.uniform(-0.38, -0.18), 0.0]
            )
        self.ripples = self.ripples[-30:]
        self.drops = self.drops[-60:]
        return True

    @staticmethod
    def in_water(x, y):
        return ((x - 0.52) / 0.35) ** 2 + ((y - 0.69) / 0.21) ** 2 <= 1

    def feed(self, x=0.52, y=0.68):
        if self.in_water(x, y):
            self.splash(x, y)
            self.pellets = [
                [x + self.random.uniform(-0.025, 0.025), y + self.random.uniform(-0.02, 0.02), 0.0]
                for _ in range(5)
            ]

    @staticmethod
    def period(preferences, hour=None):
        if preferences["scene"] != "auto":
            return preferences["scene"]
        hour = datetime.now().hour if hour is None else hour
        return "night" if hour < 6 or hour >= 19 else "golden" if hour < 8 or hour >= 17 else "day"

    def update(self, dt, preferences):
        if preferences["reduced_motion"]:
            self.rain.clear()
            self.drops.clear()
            self.ripples.clear()
            self.pellets.clear()
            return
        dt = min(max(dt, 0), 0.1)  # Visuals stay stable after sleep; timer uses its own clock.
        self.elapsed += dt
        self._ripple_clock += dt
        if self._ripple_clock > 2.5:
            self._ripple_clock = 0
            self.ripples.append([self.random.uniform(0.32, 0.72), 0.7, 0.0, 0.04])
        for fish in self.fish:
            fish["phase"] += dt * 0.6
            if self.pellets:
                tx, ty = self.pellets[0][:2]
            else:
                tx = 0.52 + math.cos(fish["phase"]) * 0.21
                ty = 0.7 + math.sin(fish["phase"] * 1.4) * 0.095
            dx, dy = tx - fish["x"], ty - fish["y"]
            target = math.atan2(dy, dx)
            delta = (target - fish["angle"] + math.pi) % (2 * math.pi) - math.pi
            fish["angle"] += delta * min(1, dt * 2.0)
            speed = 0.045 if not self.pellets else 0.08
            fish["x"] += math.cos(fish["angle"]) * speed * dt
            fish["y"] += math.sin(fish["angle"]) * speed * dt
            fish["x"] = min(0.79, max(0.25, fish["x"]))
            fish["y"] = min(0.84, max(0.54, fish["y"]))
        for pellet in self.pellets:
            pellet[2] += dt
        self.pellets = [p for p in self.pellets if p[2] < 4]
        for ripple in self.ripples:
            ripple[2] += dt
        self.ripples = [r for r in self.ripples if r[2] < 1.6][-30:]
        for drop in self.drops:
            drop[0] += drop[2] * dt
            drop[1] += drop[3] * dt
            drop[3] += dt * 0.8
            drop[4] += dt
        self.drops = [d for d in self.drops if d[4] < 0.8][-60:]
        if preferences["rain"] and self.random.random() < dt * 35:
            self.rain.append([self.random.random(), -0.1, self.random.uniform(0.7, 1.2)])
        live_rain = []
        for rain in self.rain:
            rain[0] -= dt * 0.04
            rain[1] += rain[2] * dt
            if rain[1] < 0.85:
                live_rain.append(rain)
            elif self.in_water(rain[0], rain[1]):
                self.ripples.append([rain[0], rain[1], 0.0, 0.03])
        self.rain = live_rain[-70:]

    def background(self, size, period):
        key = (size, period)
        if key not in self._cache:
            # The artwork's aspect ratio matches the garden viewport; no screenshot cropping.
            image = pygame.transform.smoothscale(self.art, size)
            if period == "night":
                image.fill((75, 112, 145), special_flags=pygame.BLEND_RGB_MULT)
                tint = pygame.Surface(size, pygame.SRCALPHA)
                tint.fill((13, 30, 59, 45))
                image.blit(tint, (0, 0))
            elif period == "golden":
                tint = pygame.Surface(size, pygame.SRCALPHA)
                tint.fill((241, 173, 75, 22))
                image.blit(tint, (0, 0))
            self._cache[key] = image
        return self._cache[key]

    def draw(self, screen, rect, preferences, golden=False):
        size = rect.size
        w, h = size
        period = self.period(preferences)
        canvas = self.background(size, period).copy()
        effects = pygame.Surface(size, pygame.SRCALPHA)
        for fish in self.fish:
            length = int(w * 0.12)
            # Quantize rotation to bound the sprite cache and avoid transforming full-size art.
            angle = (int(-math.degrees(fish["angle"]) / 6) * 6) % 360
            key = (length, angle)
            if key not in self._fish_cache:
                sprite = pygame.transform.smoothscale(self.koi, (length, int(length * 0.55)))
                sprite.set_alpha(200)
                self._fish_cache[key] = pygame.transform.rotate(sprite, angle)
            sprite = self._fish_cache[key]
            canvas.blit(sprite, sprite.get_rect(center=(int(fish["x"] * w), int(fish["y"] * h))))
        for x, y, age in self.pellets:
            pygame.draw.circle(
                effects,
                (240, 195, 120, int(220 * (1 - age / 4))),
                (int(x * w), int(y * h)),
                max(1, int(w / 240)),
            )
        for x, y, age, limit in self.ripples:
            radius = (0.004 + limit * age / 1.6) * w
            alpha = int(150 * (1 - age / 1.6))
            pygame.draw.ellipse(
                effects,
                (228, 250, 241, alpha),
                (x * w - radius, y * h - radius * 0.35, radius * 2, radius * 0.7),
                max(1, int(w / 400)),
            )
        for x, y, vx, vy, age in self.drops:
            pygame.draw.circle(
                effects,
                (214, 244, 236, int(220 * (1 - age / 0.8))),
                (int(x * w), int(y * h)),
                max(1, int(w / 220)),
            )
        for x, y, speed in self.rain:
            pygame.draw.line(
                effects,
                (220, 239, 235, 125),
                (x * w, y * h),
                (x * w - w * 0.004, y * h + h * 0.035),
                max(1, int(w / 500)),
            )
        if (period == "night" or golden) and not preferences["reduced_motion"]:
            for i in range(13):
                x = (0.15 + (i * 0.071) % 0.7) * w
                y = (0.2 + 0.4 * (0.5 + math.sin(self.elapsed * 0.15 + i) * 0.5)) * h
                alpha = int(100 + 95 * math.sin(self.elapsed + i))
                pygame.draw.circle(
                    effects, (250, 226, 150, alpha), (int(x), int(y)), max(1, w // 300)
                )
        canvas.blit(effects, (0, 0))
        canvas = canvas.convert_alpha()
        mask = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255), mask.get_rect(), border_radius=int(w * 0.045))
        canvas.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(canvas, rect)
