import pygame

from game.GameCore.entities.game_object import GameObject


class Projectile(GameObject):
    def __init__(self, row, col, direction, damage):
        # 1. Initialize as "arrow".
        # GameObject will automatically look for "arrow_idle" in ResourceManager.
        super().__init__(row, col, "arrow")

        self.direction = direction
        self.damage = damage
        self.active = True

        # 2. KEY SETTING: Animation Speed
        # Normal entities take ~350ms to move. Arrows should be much faster.
        # This makes the visual_x/y catch up to row/col very quickly.
        self.move_duration = 100

        # Logic deltas
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

        # Calculate Rotation (Assumes source image points UP)
        self.angle = 0
        if direction == "up":
            self.angle = 90
        elif direction == "left":
            self.angle = 180
        elif direction == "down":
            self.angle = 270
        elif direction == "right":
            self.angle = 0

    def move(self):
        # Update Logical Position (Instant)
        self.row += self.dr
        self.col += self.dc
        # The update_visuals(dt) call in GameCore will now detect this change
        # and smooth-slide the sprite to the new coordinates.

    def draw(self, screen):
        # Get the sprite
        frames = self.resources.get_animation(self.animation_key)

        if frames:
            image = frames[0]

            # Scale if needed
            if image.get_width() != self.cell_size:
                image = pygame.transform.scale(image, (self.cell_size, self.cell_size))

            # Rotate
            rotated_image = pygame.transform.rotate(image, self.angle)

            # Re-center after rotation
            rect = rotated_image.get_rect()
            rect.center = (
                self.visual_x + self.cell_size // 2,
                self.visual_y + self.cell_size // 2,
            )

            screen.blit(rotated_image, rect)
        else:
            # Fallback drawing (Cyan Line)
            center_x = self.visual_x + self.cell_size // 2
            center_y = self.visual_y + self.cell_size // 2
            color = (0, 255, 255)

            end_x = center_x + (self.dc * 15)
            end_y = center_y + (self.dr * 15)
            start_x = center_x - (self.dc * 10)
            start_y = center_y - (self.dr * 10)

            pygame.draw.line(screen, color, (start_x, start_y), (end_x, end_y), 3)
            pygame.draw.circle(screen, color, (end_x, end_y), 4)
