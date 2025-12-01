import pygame
from game.GameCore.entities.game_object import GameObject
from game.GameCore.config import GameConfig


class Chest(GameObject):
    def __init__(self, row, col, contents):
        super().__init__(row, col, "chest")
        self.contents = contents  # {'coins': 5, 'health': 1, etc.}
        self.opened = False

    def open(self):
        if not self.opened:
            self.opened = True
            return self.contents
        return {}

    def draw(self, screen):
        # Try to draw sprite
        frames = self.resources.get_animation(self.animation_key)

        if frames:
            super().draw(screen)
        else:
            # Fallback if no sprite loaded
            x, y = self.visual_x, self.visual_y
            color = (150, 120, 90) if self.opened else GameConfig.COLORS['chest']
            pygame.draw.rect(screen, color, (x + 10, y + 15, self.cell_size - 20, self.cell_size - 25))