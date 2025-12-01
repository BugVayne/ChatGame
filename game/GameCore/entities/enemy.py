import pygame
import random
import math
from game.GameCore.entities.game_object import GameObject
from game.GameCore.config import GameConfig


class Enemy(GameObject):
    def __init__(self, row, col, enemy_type="melee", health=None, damage=None):
        super().__init__(row, col, "enemy")
        self.enemy_type = enemy_type
        self.health = health or GameConfig.ENEMY_BASE_HEALTH
        self.max_health = self.health
        self.damage = damage or GameConfig.ENEMY_BASE_DAMAGE
        self.detection_range = GameConfig.ENEMY_DETECTION_RANGE
        self.has_detected_player = False

    def can_see_player(self, player, walls):
        if not self.has_detected_player:
            # Check distance first
            distance = math.sqrt((self.row - player.row) ** 2 + (self.col - player.col) ** 2)
            if distance > self.detection_range:
                return False

            # Check line of sight through walls
            return self.has_line_of_sight(player, walls)

        return True

    def has_line_of_sight(self, player, walls):
        # Bresenham's line algorithm to check for walls between enemy and player
        x0, y0 = self.col, self.row
        x1, y1 = player.col, player.row

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        n = 1 + dx + dy
        x_inc = 1 if x1 > x0 else -1
        y_inc = 1 if y1 > y0 else -1
        error = dx - dy
        dx *= 2
        dy *= 2

        for _ in range(n):
            # Check if current position has a wall (excluding start and end points)
            if (x, y) != (x0, y0) and (x, y) != (x1, y1):
                for wall in walls:
                    if wall.col == x and wall.row == y:
                        return False

            if error > 0:
                x += x_inc
                error -= dy
            else:
                y += y_inc
                error += dx

        return True

    def move_towards_player(self, player, grid, grid_width, grid_height, walls, items):
        if not self.can_see_player(player, walls):
            return False

        self.has_detected_player = True

        # Pathfinding logic
        best_move = None
        best_distance = float('inf')

        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_row, new_col = self.row + dr, self.col + dc


            if 0 <= new_row < grid_height and 0 <= new_col < grid_width:

                target_cell = grid[new_row][new_col]

                if target_cell is None:
                    # Calculating distance
                    distance = abs(new_row - player.row) + abs(new_col - player.col)
                    if distance < best_distance:
                        best_distance = distance
                        best_move = (new_row, new_col)
                # --- FIX END ---

        if best_move:
            # Move the enemy
            grid[self.row][self.col] = None
            self.row, self.col = best_move
            grid[self.row][self.col] = self
            return True

        return False

    def draw(self, screen):
        # 1. Draw Sprite
        super().draw(screen)

        center_x = self.visual_x + self.cell_size // 2
        center_y = self.visual_y + self.cell_size // 2
        radius = self.cell_size // 3

        # 2. Draw Type Indicator (Overlay)
        # Since sprites might look the same, we add a colored dot or ring to distinguish
        if self.enemy_type == "ranged":
            pygame.draw.circle(screen, GameConfig.COLORS['ranged_enemy'], (center_x, center_y - 10), 5)

        # 3. Detection indicator
        if not self.has_detected_player:
            pygame.draw.circle(screen, (100, 100, 100), (center_x, center_y), radius, 2)


class RangedEnemy(Enemy):
    def __init__(self, row, col):
        super().__init__(row, col, "ranged", health=40, damage=8)
        self.attack_range = 4
        self.attack_cooldown = 0

    def can_attack_player(self, player, walls):
        if self.attack_cooldown > 0:
            return False

        distance = math.sqrt((self.row - player.row) ** 2 + (self.col - player.col) ** 2)
        return (distance <= self.attack_range and
                self.has_line_of_sight(player, walls))

    def attack(self, player):
        if self.attack_cooldown == 0:
            player.take_damage(self.damage)
            self.attack_cooldown = 2
            return True
        return False

    def update_cooldowns(self):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1