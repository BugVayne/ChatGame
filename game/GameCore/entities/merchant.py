import pygame
from game.GameCore.entities.game_object import GameObject


class Merchant(GameObject):
    def __init__(self, row, col):
        super().__init__(row, col, "merchant")
        self.animation_key = "merchant_idle"

    def draw(self, screen):
        self.animation_key = "merchant_idle"
        super().draw(screen)

        # Floating Dollar Sign
        center_x = self.visual_x + self.cell_size // 2
        center_y = self.visual_y + self.cell_size // 2

        font = pygame.font.Font(None, 48)
        text = font.render("$", True, (255, 215, 0))
        text_rect = text.get_rect(center=(center_x, center_y - 20))
        screen.blit(text, text_rect)