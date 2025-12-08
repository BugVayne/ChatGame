from game.GameCore.config import GameConfig
from game.GameCore.entities.game_object import GameObject


class Player(GameObject):
    def __init__(self, row, col):
        super().__init__(row, col, "player")
        self.health = GameConfig.PLAYER_START_HEALTH
        self.max_health = GameConfig.PLAYER_MAX_HEALTH
        self.coins = 0
        self.has_sword = False
        self.has_bow = False
        self.dash_cooldown = 0
        self.inventory = {"health": 2, "arrows": 50}

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
        if target_obj is None or target_obj.type in [
            "item",
            "exit",
            "merchant",
            "chest",
        ]:
            grid[self.row][self.col] = None
            self.row, self.col = new_row, new_col
            grid[new_row][new_col] = self
            return True

        return False

    def dash(self, direction, grid, grid_width, grid_height):
        if self.dash_cooldown > 0:
            return False

        # Track the last safe place we can actually stand
        # Start at current position (in case we can't move at all)
        last_valid_row, last_valid_col = self.row, self.col

        # Temp variables for checking ahead
        check_row, check_col = self.row, self.col
        distance = GameConfig.DASH_DISTANCE

        for _ in range(distance):
            # 1. Calculate the coordinate of the next step
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

            # 3. Check Grid Content
            cell_content = grid[check_row][check_col]

            # BLOCKING LOGIC:
            if cell_content is not None:
                # A. WALLS: Hard stop. The dash ends immediately.
                if cell_content.type == "wall":
                    break

                # B. ENEMIES / SOLIDS:
                # We can pass THROUGH them, but we cannot LAND on them.
                # So we continue the loop, but we DO NOT update 'last_valid_row/col'
                if cell_content.type in ["enemy", "chest", "merchant"]:
                    continue

            # 4. If we are here, the tile is either None (Empty) or "item" (Walkable)
            # This is a valid spot to land.
            last_valid_row, last_valid_col = check_row, check_col

        # 5. Apply the move ONLY if we found a new valid spot
        if last_valid_row != self.row or last_valid_col != self.col:
            grid[self.row][self.col] = None  # Remove player from old spot
            self.row, self.col = last_valid_row, last_valid_col  # Update coords
            grid[self.row][self.col] = self  # Place player in new spot

            self.dash_cooldown = GameConfig.DASH_COOLDOWN
            return True

        return False

    def attack_sword(self, direction, enemies):
        if not self.has_sword:
            return []

        if direction == "left":
            self.facing_right = False
        elif direction == "right":
            self.facing_right = True

        self.play_animation("player_attack", 400)

        damage = GameConfig.PLAYER_BASE_DAMAGE
        range_distance = GameConfig.SWORD_RANGE
        hit_enemies = []

        for enemy in enemies:
            if not enemy.is_alive():
                continue

            row_diff = abs(enemy.row - self.row)
            col_diff = abs(enemy.col - self.col)

            if (
                direction == "up"
                and enemy.col == self.col
                and enemy.row < self.row
                and self.row - enemy.row <= range_distance
            ):
                hit_enemies.append(enemy)
            elif (
                direction == "down"
                and enemy.col == self.col
                and enemy.row > self.row
                and enemy.row - self.row <= range_distance
            ):
                hit_enemies.append(enemy)
            elif (
                direction == "left"
                and enemy.row == self.row
                and enemy.col < self.col
                and self.col - enemy.col <= range_distance
            ):
                hit_enemies.append(enemy)
            elif (
                direction == "right"
                and enemy.row == self.row
                and enemy.col > self.col
                and enemy.col - self.col <= range_distance
            ):
                hit_enemies.append(enemy)

        # Apply damage
        for enemy in hit_enemies:
            enemy.take_damage(damage)

        return hit_enemies

    def attack_bow(self, direction, enemies, walls):
        if not self.has_bow or self.inventory.get("arrows", 0) <= 0:
            return None

        if direction == "left":
            self.facing_right = False
        elif direction == "right":
            self.facing_right = True

        self.play_animation("player_bow", 400)

        self.inventory["arrows"] -= 1
        damage = GameConfig.PLAYER_BASE_DAMAGE
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

            for wall in walls:
                if wall.row == check_row and wall.col == check_col:
                    return {"type": "wall", "position": (check_row, check_col)}

        return None

    def collect_item(self, item):
        if item.item_type == "coin":
            self.coins += item.value
        elif item.item_type == "health":
            self.inventory["health"] += 1
        elif item.item_type == "arrow":
            self.inventory["arrows"] += item.value
        elif item.item_type == "sword":
            self.has_sword = True
        elif item.item_type == "bow":
            self.has_bow = True

    def use_item(self, item_type):
        if self.inventory.get(item_type, 0) > 0:
            self.inventory[item_type] -= 1
            if item_type == "health":
                self.health = min(
                    self.max_health, self.health + GameConfig.HEALTH_POTION_HEAL
                )
                return True
        return False

    def upgrade_health(self):
        if (
            self.max_health < 200
            and self.coins
            >= GameConfig.HEALTH_UPGRADE_COST[0 if self.max_health == 100 else 1]
        ):
            cost_index = 0 if self.max_health == 100 else 1
            self.coins -= GameConfig.HEALTH_UPGRADE_COST[cost_index]
            self.max_health += 50
            self.health = self.max_health
            return True
        return False

    def update_cooldowns(self):
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

    def draw(self, screen):
        super().draw(screen)
