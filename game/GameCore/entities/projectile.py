import pygame

from game.GameCore.entities.game_object import GameObject


class Projectile(GameObject):
    def __init__(self, row, col, direction, damage):
        super().__init__(row, col, "projectile")
        self.direction = direction
        self.damage = damage
        self.active = True

        self.dr = 0
        self.dc = 0
        if direction == "up":
            self.dr = -1
        elif direction == "down":
            self.dr = 1
        elif direction == "left":
            self.dc = -1
        elif direction == "right":
            self.dc = 1

    def move(self):
        self.row += self.dr
        self.col += self.dc

    def draw(self, screen):

        center_x = self.visual_x + self.cell_size // 2
        center_y = self.visual_y + self.cell_size // 2

        color = (0, 255, 255)  # Cyan

        # Draw Arrow Shaft
        end_x = center_x + (self.dc * 15)
        end_y = center_y + (self.dr * 15)
        start_x = center_x - (self.dc * 10)
        start_y = center_y - (self.dr * 10)

        pygame.draw.line(screen, color, (start_x, start_y), (end_x, end_y), 3)
        pygame.draw.circle(screen, color, (end_x, end_y), 4)
