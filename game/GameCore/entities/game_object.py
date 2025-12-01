import pygame
import math

from game.GameCore.config import GameConfig
from game.GameCore.resource_manager import ResourceManager


class GameObject:
    def __init__(self, row, col, object_type):
        self.row = row
        self.col = col
        self.type = object_type
        self.health = 100

        self.cell_size = GameConfig.CELL_SIZE

        # Visual Position (Pixels)
        self.visual_x = col * self.cell_size
        self.visual_y = row * self.cell_size

        # Animation State
        self.resources = ResourceManager()
        self.state = "idle"  # idle, run, attack
        self.animation_key = f"{object_type}_idle"  # e.g. "player_idle"
        self.frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 150  # ms per frame
        self.facing_right = True

    def get_position(self):
        return (self.row, self.col)

    def set_position(self, row, col):
        self.row = row
        self.col = col

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        return self.health <= 0

    def is_alive(self):
        return self.health > 0


    def draw_health_bar(self, screen, x, y, cell_size, current_health, max_health):
        health_width = (current_health / max_health) * (cell_size - 10)
        pygame.draw.rect(screen, (255, 0, 0), (x + 5, y + 5, cell_size - 10, 5))
        pygame.draw.rect(screen, (0, 255, 0), (x + 5, y + 5, health_width, 5))

    def update_visuals(self, dt):
        """Called every frame to smooth movement and update animation"""

        # 1. Smooth Movement (Lerp)
        target_x = self.col * self.cell_size
        target_y = self.row * self.cell_size

        # Speed of sliding (10 = slow, 25 = fast)
        slide_speed = 15 * (dt / 16.0)

        if abs(self.visual_x - target_x) < 2:
            self.visual_x = target_x
        else:
            self.visual_x += (target_x - self.visual_x) / 5

        if abs(self.visual_y - target_y) < 2:
            self.visual_y = target_y
        else:
            self.visual_y += (target_y - self.visual_y) / 5

        # Determine State based on movement
        is_moving = abs(self.visual_x - target_x) > 5 or abs(self.visual_y - target_y) > 5

        # Face direction
        if target_x > self.visual_x:
            self.facing_right = True
        elif target_x < self.visual_x:
            self.facing_right = False

        prev_key = self.animation_key

        # Update Key
        if is_moving:
            self.state = "run"
            self.animation_key = f"{self.type}_run"
        else:
            self.state = "idle"
            self.animation_key = f"{self.type}_idle"

        # Reset frame if animation changed
        if prev_key != self.animation_key:
            self.frame_index = 0

        # 2. Cycle Frames
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            frames = self.resources.get_animation(self.animation_key)
            self.frame_index = (self.frame_index + 1) % len(frames)

    def draw(self, screen):
        frames = self.resources.get_animation(self.animation_key)

        # Safety check
        if not frames: return
        if self.frame_index >= len(frames): self.frame_index = 0

        image = frames[self.frame_index]

        # Flip image if facing left
        if not self.facing_right:
            image = pygame.transform.flip(image, True, False)

        # Scale to cell size if needed
        if image.get_width() != self.cell_size:
            image = pygame.transform.scale(image, (self.cell_size, self.cell_size))

        # Draw Shadow
        shadow_rect = pygame.Rect(self.visual_x + 10, self.visual_y + self.cell_size - 10, self.cell_size - 20, 5)
        pygame.draw.ellipse(screen, (0, 0, 0, 100), shadow_rect)

        # Draw Sprite
        screen.blit(image, (self.visual_x, self.visual_y))

        # Draw Health Bar (Existing code)
        if hasattr(self, 'health') and hasattr(self, 'max_health') and self.health < self.max_health:
            self.draw_health_bar(screen, self.visual_x, self.visual_y, self.cell_size, self.health, self.max_health)