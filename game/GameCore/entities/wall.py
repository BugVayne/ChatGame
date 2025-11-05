import pygame

from game.GameCore.entities.game_object import GameObject
from game.GameCore.config import GameConfig


class Wall(GameObject):
    def __init__(self, row, col):
        super().__init__(row, col, "wall")

    def draw(self, screen, x, y, cell_size):
        pygame.draw.rect(screen, GameConfig.COLORS['wall'],
                         (x, y, cell_size, cell_size))
        # Draw brick pattern
        for i in range(0, cell_size, cell_size // 4):
            for j in range(0, cell_size, cell_size // 4):
                pygame.draw.rect(screen, (80, 80, 100),
                                 (x + i, y + j, cell_size // 4 - 1, cell_size // 4 - 1))