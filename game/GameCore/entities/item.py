import pygame
import math
from game.GameCore.entities.game_object import GameObject
from game.GameCore.config import GameConfig


class Item(GameObject):
    def __init__(self, row, col, item_type, value=1):
        # We still pass "item" as type for logic purposes
        super().__init__(row, col, "item")

        self.item_type = item_type
        self.value = value
        self.pulse = 0
        self.animation_key = item_type

    def update_visuals(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= 150:
            self.animation_timer = 0
            frames = self.resources.get_animation(self.animation_key)
            if frames:
                self.frame_index = (self.frame_index + 1) % len(frames)

    def draw(self, screen):
        # Calculate Floating Effect (Bobbing up and down)
        self.pulse += 0.1
        float_offset = int(3 * math.sin(self.pulse))

        frames = self.resources.get_animation(self.animation_key)

        if not frames:
            return

        if self.frame_index >= len(frames):
            self.frame_index = 0

        image = frames[self.frame_index]

        screen.blit(image, (self.visual_x, self.visual_y + float_offset))