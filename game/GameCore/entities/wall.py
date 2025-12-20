import random

from game.GameCore.config import GameConfig
from game.GameCore.entities.game_object import GameObject


class Wall(GameObject):
    def __init__(self, row, col):
        super().__init__(row, col, "wall")
        # Randomly choose one of the four cardinal directions
        self.angle = random.choice([0, 90, 180, 270])

    def draw(self, screen):
        # We override draw to apply the rotation
        from game.GameCore.resource_manager import ResourceManager

        res = ResourceManager()

        # Get the standard animation/image
        frames = res.get_animation("wall_idle")
        if frames:
            img = frames[0]
            # Rotate it
            rotated_img = res.get_rotated_surface(img, self.angle)

            # Calculate position (assuming GameObject uses row/col)
            # If your GameObject has visual_x/y for smoothing, use those instead
            draw_pos = (
                self.col * GameConfig.CELL_SIZE,
                self.row * GameConfig.CELL_SIZE,
            )
            screen.blit(rotated_img, draw_pos)
