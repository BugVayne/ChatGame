import pygame
import math
from game.GameCore.entities.game_object import GameObject
from game.GameCore.config import GameConfig

class Item(GameObject):
    def __init__(self, row, col, item_type, value=1):
        super().__init__(row, col, "item")
        self.item_type = item_type
        self.value = value
        self.pulse = 0

    def draw(self, screen, x, y, cell_size):
        self.pulse += 0.1
        pulse_offset = int(3 * abs(math.sin(self.pulse)))

        center_x = x + cell_size // 2
        center_y = y + cell_size // 2
        radius = cell_size // 4 + pulse_offset

        colors = {
            "health": GameConfig.COLORS['health_item'],
            "sword": GameConfig.COLORS['sword'],
            "bow": GameConfig.COLORS['bow'],
            "coin": GameConfig.COLORS['coin'],
            "arrow": (200, 200, 200)
        }

        color = colors.get(self.item_type, (255, 255, 255))
        pygame.draw.circle(screen, color, (center_x, center_y), radius)

        # Draw item icon
        self.draw_icon(screen, center_x, center_y)

    def draw_icon(self, screen, center_x, center_y):
        if self.item_type == "health":
            # Plus symbol
            pygame.draw.rect(screen, (255, 255, 255),
                           (center_x - 6, center_y - 2, 12, 4))
            pygame.draw.rect(screen, (255, 255, 255),
                           (center_x - 2, center_y - 6, 4, 12))
        elif self.item_type == "sword":
            # Sword shape
            pygame.draw.rect(screen, (100, 100, 100),
                           (center_x - 8, center_y, 16, 3))
            pygame.draw.polygon(screen, (200, 200, 200), [
                (center_x, center_y - 8),
                (center_x - 3, center_y),
                (center_x + 3, center_y)
            ])
        elif self.item_type == "bow":
            # Bow shape
            pygame.draw.arc(screen, (139, 69, 19),
                          (center_x - 8, center_y - 8, 16, 16), 0.5, 2.6, 3)
        elif self.item_type == "coin":
            # $ symbol
            font = pygame.font.Font(None, 20)
            text = font.render("$", True, (0, 0, 0))
            text_rect = text.get_rect(center=(center_x, center_y))
            screen.blit(text, text_rect)
        elif self.item_type == "arrow":
            # Arrow symbol
            pygame.draw.line(screen, (100, 100, 100),
                           (center_x - 5, center_y), (center_x + 5, center_y), 2)
            pygame.draw.polygon(screen, (100, 100, 100), [
                (center_x + 5, center_y),
                (center_x + 2, center_y - 2),
                (center_x + 2, center_y + 2)
            ])
