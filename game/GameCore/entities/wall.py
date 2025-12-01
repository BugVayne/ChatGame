import pygame

from game.GameCore.entities.game_object import GameObject
from game.GameCore.config import GameConfig


class Wall(GameObject):
    def __init__(self, row, col):
        super().__init__(row, col, "wall")

    def draw(self, screen):
        super().draw(screen)