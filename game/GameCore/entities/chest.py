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

    def draw(self, screen, x, y, cell_size):
        color = GameConfig.COLORS['chest']
        if self.opened:
            color = (150, 120, 90)  # Darker when opened

        # Chest body
        pygame.draw.rect(screen, color,
                         (x + 10, y + 15, cell_size - 20, cell_size - 25))

        # Chest lid
        lid_height = 10 if self.opened else 5
        pygame.draw.rect(screen, (180, 150, 110),
                         (x + 5, y + 10, cell_size - 10, lid_height))

        # Lock
        if not self.opened:
            pygame.draw.circle(screen, (200, 200, 0),
                               (x + cell_size // 2, y + 20), 5)