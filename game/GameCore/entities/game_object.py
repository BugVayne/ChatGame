import pygame
import math

class GameObject:
    def __init__(self, row, col, object_type):
        self.row = row
        self.col = col
        self.type = object_type
        self.health = 100

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

    def draw(self, screen, x, y, cell_size):
        center_x = x + cell_size // 2
        center_y = y + cell_size // 2
        radius = cell_size // 3
        pygame.draw.circle(screen, (255, 255, 255), (center_x, center_y), radius)

    def draw_health_bar(self, screen, x, y, cell_size, current_health, max_health):
        health_width = (current_health / max_health) * (cell_size - 10)
        pygame.draw.rect(screen, (255, 0, 0), (x + 5, y + 5, cell_size - 10, 5))
        pygame.draw.rect(screen, (0, 255, 0), (x + 5, y + 5, health_width, 5))