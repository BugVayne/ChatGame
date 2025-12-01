import math
import pygame
from game.GameCore.entities.game_object import GameObject


class ExitPortal(GameObject):
    def __init__(self, row, col):
        super().__init__(row, col, "exit")
        self.pulse = 0

    def draw(self, screen):
        # Draw sprite if available
        super().draw(screen)

        # Keep the procedural effect on top because it looks cool
        self.pulse += 0.1
        pulse_size = int(5 * abs(math.sin(self.pulse)))

        center_x = int(self.visual_x + self.cell_size // 2)
        center_y = int(self.visual_y + self.cell_size // 2)

        # Swirl effect
        for i in range(4):
            angle = self.pulse + i * math.pi / 2
            start_x = center_x + math.cos(angle) * 10
            start_y = center_y + math.sin(angle) * 10
            end_x = center_x + math.cos(angle) * (self.cell_size // 3)
            end_y = center_y + math.sin(angle) * (self.cell_size // 3)
            pygame.draw.line(screen, (255, 255, 255),
                             (start_x, start_y), (end_x, end_y), 3)