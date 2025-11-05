# game/GameCore/entities/exit_portal.py
import math

import pygame

from game.GameCore.entities.game_object import GameObject
from game.GameCore.config import GameConfig


class ExitPortal(GameObject):
    def __init__(self, row, col):
        super().__init__(row, col, "exit")
        self.pulse = 0

    def draw(self, screen, x, y, cell_size):
        self.pulse += 0.1
        pulse_size = int(5 * abs(math.sin(self.pulse)))

        center_x = x + cell_size // 2
        center_y = y + cell_size // 2

        # Outer glow
        pygame.draw.circle(screen, (100, 255, 255),
                           (center_x, center_y), cell_size // 2 - 5)

        # Inner portal
        pygame.draw.circle(screen, GameConfig.COLORS['exit'],
                           (center_x, center_y), cell_size // 3 + pulse_size)

        # Swirl effect
        for i in range(4):
            angle = self.pulse + i * math.pi / 2
            start_x = center_x + math.cos(angle) * 10
            start_y = center_y + math.sin(angle) * 10
            end_x = center_x + math.cos(angle) * (cell_size // 3)
            end_y = center_y + math.sin(angle) * (cell_size // 3)
            pygame.draw.line(screen, (255, 255, 255),
                             (start_x, start_y), (end_x, end_y), 3)