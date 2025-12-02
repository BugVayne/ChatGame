import math
import pygame
from game.GameCore.entities.game_object import GameObject


class ExitPortal(GameObject):
    def __init__(self, row, col):
        super().__init__(row, col, "exit")
        self.animation_key = "portal_idle"

    def draw(self, screen):
        self.animation_key = "portal_idle"
        super().draw(screen)
