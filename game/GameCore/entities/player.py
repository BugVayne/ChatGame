import pygame
from game.GameCore.entities.game_object import GameObject
from game.GameCore.config import GameConfig


class Player(GameObject):
    def __init__(self, row, col):
        super().__init__(row, col, "player")
        self.health = GameConfig.PLAYER_START_HEALTH
        self.max_health = GameConfig.PLAYER_MAX_HEALTH
        self.coins = 0
        self.sword_level = 0
        self.bow_level = 0
        self.dash_cooldown = 0
        self.inventory = {"health": 2, "arrows": 5}

    def move(self, direction, grid, grid_width, grid_height):
        new_row, new_col = self.row, self.col

        if direction == "up" and self.row > 0:
            new_row = self.row - 1
        elif direction == "down" and self.row < grid_height - 1:
            new_row = self.row + 1
        elif direction == "left" and self.col > 0:
            new_col = self.col - 1
        elif direction == "right" and self.col < grid_width - 1:
            new_col = self.col + 1
        else:
            return False

        # Check if target cell is passable
        target_obj = grid[new_row][new_col]
        if target_obj is None or target_obj.type in ["item", "exit", "merchant", "chest"]:
            grid[self.row][self.col] = None
            self.row, self.col = new_row, new_col
            grid[new_row][new_col] = self
            return True

        return False

    def dash(self, direction, grid, grid_width, grid_height):
        if self.dash_cooldown > 0:
            return False

        # Start tracking where we will end up (initially where we are now)
        target_row, target_col = self.row, self.col
        distance = GameConfig.DASH_DISTANCE

        for _ in range(distance):
            # 1. Calculate the coordinate we WANT to step into
            check_row, check_col = target_row, target_col

            if direction == "up":
                check_row -= 1
            elif direction == "down":
                check_row += 1
            elif direction == "left":
                check_col -= 1
            elif direction == "right":
                check_col += 1

            # 2. Check Boundaries
            if not (0 <= check_row < grid_height and 0 <= check_col < grid_width):
                break  # Hit edge of map

            # 3. Check for Obstacles
            cell_content = grid[check_row][check_col]

            # If there is something there...
            if cell_content is not None:
                # ...and it is a solid object, STOP.
                # Note: Items are 'walkable', so we don't stop for them.
                if cell_content.type in ["wall", "enemy", "chest", "merchant"]:
                    break

                    # 4. If we made it here, the step is safe. Update our target.
            target_row, target_col = check_row, check_col

        # 5. Apply the move ONLY if the target is different from start
        if target_row != self.row or target_col != self.col:
            grid[self.row][self.col] = None  # Remove player from old spot
            self.row, self.col = target_row, target_col  # Update coords
            grid[self.row][self.col] = self  # Place player in new spot

            self.dash_cooldown = GameConfig.DASH_COOLDOWN
            return True

        return False

    def attack_sword(self, direction, enemies):
        if self.sword_level == 0:
            return []

        damage = GameConfig.PLAYER_BASE_DAMAGE + self.sword_level * 5
        range_distance = GameConfig.SWORD_RANGE
        hit_enemies = []

        for enemy in enemies:
            if not enemy.is_alive():
                continue

            row_diff = abs(enemy.row - self.row)
            col_diff = abs(enemy.col - self.col)

            # Check if enemy is in sword range and direction
            if direction == "up" and enemy.col == self.col and enemy.row < self.row and self.row - enemy.row <= range_distance:
                hit_enemies.append(enemy)
            elif direction == "down" and enemy.col == self.col and enemy.row > self.row and enemy.row - self.row <= range_distance:
                hit_enemies.append(enemy)
            elif direction == "left" and enemy.row == self.row and enemy.col < self.col and self.col - enemy.col <= range_distance:
                hit_enemies.append(enemy)
            elif direction == "right" and enemy.row == self.row and enemy.col > self.col and enemy.col - self.col <= range_distance:
                hit_enemies.append(enemy)

        # Apply damage
        for enemy in hit_enemies:
            enemy.take_damage(damage)

        return hit_enemies

    def attack_bow(self, direction, enemies, walls):
        if self.bow_level == 0 or self.inventory.get("arrows", 0) <= 0:
            return None

        self.inventory["arrows"] -= 1
        damage = GameConfig.PLAYER_BASE_DAMAGE + self.bow_level * 3
        range_distance = GameConfig.BOW_RANGE

        # Find first enemy or wall in line of fire
        for distance in range(1, range_distance + 1):
            check_row, check_col = self.row, self.col

            if direction == "up":
                check_row = self.row - distance
            elif direction == "down":
                check_row = self.row + distance
            elif direction == "left":
                check_col = self.col - distance
            elif direction == "right":
                check_col = self.col + distance

            # Check walls first (they block arrows)
            for wall in walls:
                if wall.row == check_row and wall.col == check_col:
                    return {"type": "wall", "position": (check_row, check_col)}

            # Check enemies
            for enemy in enemies:
                if enemy.is_alive() and enemy.row == check_row and enemy.col == check_col:
                    enemy.take_damage(damage)
                    return {"type": "enemy", "enemy": enemy, "position": (check_row, check_col)}

        return None

    def collect_item(self, item):
        if item.item_type == "coin":
            self.coins += item.value
        elif item.item_type == "health":
            self.inventory["health"] += 1
        elif item.item_type == "arrow":
            self.inventory["arrows"] += item.value
        elif item.item_type == "sword" and self.sword_level == 0:
            self.sword_level = 1
        elif item.item_type == "bow" and self.bow_level == 0:
            self.bow_level = 1

    def use_item(self, item_type):
        if self.inventory.get(item_type, 0) > 0:
            self.inventory[item_type] -= 1
            if item_type == "health":
                self.health = min(self.max_health, self.health + GameConfig.HEALTH_POTION_HEAL)
                return True
        return False

    def upgrade_sword(self):
        if self.sword_level < 3 and self.coins >= GameConfig.SWORD_UPGRADE_COST[self.sword_level]:
            self.coins -= GameConfig.SWORD_UPGRADE_COST[self.sword_level]
            self.sword_level += 1
            return True
        return False

    def upgrade_bow(self):
        if self.bow_level < 3 and self.coins >= GameConfig.BOW_UPGRADE_COST[self.bow_level]:
            self.coins -= GameConfig.BOW_UPGRADE_COST[self.bow_level]
            self.bow_level += 1
            return True
        return False

    def upgrade_health(self):
        if self.max_health < 200 and self.coins >= GameConfig.HEALTH_UPGRADE_COST[0 if self.max_health == 100 else 1]:
            cost_index = 0 if self.max_health == 100 else 1
            self.coins -= GameConfig.HEALTH_UPGRADE_COST[cost_index]
            self.max_health += 50
            self.health = self.max_health
            return True
        return False

    def update_cooldowns(self):
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

    def draw(self, screen, x, y, cell_size):
        center_x = x + cell_size // 2
        center_y = y + cell_size // 2
        radius = cell_size // 3

        # Body
        pygame.draw.circle(screen, GameConfig.COLORS['player'], (center_x, center_y), radius)

        # Equipment indicators
        if self.sword_level > 0:
            pygame.draw.rect(screen, (200, 200, 200),
                             (center_x - 15, center_y - 20, 5, 15))
        if self.bow_level > 0:
            pygame.draw.arc(screen, (139, 69, 19),
                            (center_x + 5, center_y - 15, 20, 20), 0, 3.14, 3)

        # Health bar
        self.draw_health_bar(screen, x, y, cell_size, self.health, self.max_health)