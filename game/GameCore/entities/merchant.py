import pygame
from game.GameCore.entities.game_object import GameObject
from game.GameCore.config import GameConfig


class Merchant(GameObject):
    def __init__(self, row, col):
        super().__init__(row, col, "merchant")

    def draw(self, screen, x, y, cell_size):
        center_x = x + cell_size // 2
        center_y = y + cell_size // 2

        # Body
        pygame.draw.circle(screen, GameConfig.COLORS['merchant'],
                           (center_x, center_y), cell_size // 3)

        # Money bag
        pygame.draw.ellipse(screen, (255, 215, 0),
                            (center_x - 10, center_y + 5, 20, 15))

        # "$" symbol
        font = pygame.font.Font(None, 24)
        text = font.render("$", True, (0, 0, 0))
        text_rect = text.get_rect(center=(center_x, center_y + 12))
        screen.blit(text, text_rect)