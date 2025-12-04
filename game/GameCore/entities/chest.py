import pygame
from game.GameCore.entities.game_object import GameObject
from game.GameCore.config import GameConfig


class Chest(GameObject):
    def __init__(self, row, col, contents):
        super().__init__(row, col, "chest")
        self.contents = contents  # {'coins': 5, 'health': 1, etc.}
        self.opened = False
        self.animation_key = "chest_closed"

    def open(self):
        if not self.opened:
            self.opened = True
            return self.contents
        return {}

    def draw(self, screen):
        if self.opened:
            self.animation_key = "chest_open"
        else:
            self.animation_key = "chest_closed"
        super().draw(screen)
