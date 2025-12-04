import pygame
import random
import math
from collections import deque
from game.GameCore.entities.game_object import GameObject
from game.GameCore.config import GameConfig


class EnemyState:
    IDLE = "idle"
    CHASE = "chase"
    ATTACK = "attack"
    FLEE = "flee"


class Enemy(GameObject):
    def __init__(self, row, col, enemy_type="melee", health=None, damage=None):
        super().__init__(row, col, "enemy")
        self.enemy_type = enemy_type
        self.health = health or GameConfig.ENEMY_BASE_HEALTH
        self.max_health = self.health
        self.damage = damage or GameConfig.ENEMY_BASE_DAMAGE
        self.detection_range = GameConfig.ENEMY_DETECTION_RANGE
        self.has_detected_player = False
        self.ai_state = EnemyState.IDLE
        self.recovery_cooldown = 0

    def update_cooldowns(self):
        if self.recovery_cooldown > 0:
            self.recovery_cooldown -= 1

    def can_see_player(self, player, walls):
        # 1. Check distance
        distance = math.sqrt((self.row - player.row) ** 2 + (self.col - player.col) ** 2)
        if distance > self.detection_range:
            return False

        # 2. Check line of sight (Bresenham)
        return self.has_line_of_sight(player, walls)

    def has_line_of_sight(self, player, walls):
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

    def find_path_bfs(self, target_node, grid, grid_width, grid_height):
        """Returns the next step (row, col) to reach target using BFS"""
        start = (self.row, self.col)
        queue = deque([start])
        came_from = {start: None}

        target_pos = (target_node.row, target_node.col)

        found = False

        while queue:
            current = queue.popleft()

            if current == target_pos:
                found = True
                break

            # Check 4 neighbors
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                next_node = (current[0] + dr, current[1] + dc)

                # Bounds check
                if 0 <= next_node[0] < grid_height and 0 <= next_node[1] < grid_width:
                    # Obstacle check
                    cell = grid[next_node[0]][next_node[1]]

                    # Walkable if empty OR it is the player (target)
                    is_walkable = (cell is None) or (next_node == target_pos)

                    if is_walkable and next_node not in came_from:
                        queue.append(next_node)
                        came_from[next_node] = current

        if found:
            # Reconstruct path backwards
            curr = target_pos
            path = []
            while curr != start:
                path.append(curr)
                curr = came_from[curr]

            # path is reversed (Target -> ... -> Next Step)
            # We return the last element (which is the immediate next step)
            if path:
                return path[-1]

        return None

    def wander(self, grid, grid_width, grid_height):
        """Move randomly to an adjacent free tile"""
        possible_moves = []
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nr, nc = self.row + dr, self.col + dc
            if 0 <= nr < grid_height and 0 <= nc < grid_width:
                if grid[nr][nc] is None:
                    possible_moves.append((nr, nc))

        if possible_moves:
            next_step = random.choice(possible_moves)
            self.move_to(next_step, grid)

    def move_to(self, target_pos, grid):
        """Execute movement to a specific cell"""
        grid[self.row][self.col] = None
        self.row, self.col = target_pos
        grid[self.row][self.col] = self

    def move_towards_player(self, player, grid, grid_width, grid_height, walls, items):
        # 0. Check Recovery (Stun after attack)
        if self.recovery_cooldown > 0:
            return True

        # 1. State Update
        if self.can_see_player(player, walls):
            self.has_detected_player = True
            self.ai_state = EnemyState.CHASE
        else:
            # If we lost the player, go back to Idle/Wander
            self.ai_state = EnemyState.IDLE

        # 2. State Execution
        if self.ai_state == EnemyState.CHASE:
            next_step = self.find_path_bfs(player, grid, grid_width, grid_height)
            if next_step:
                # If the next step is the player, ATTACK instead of moving
                if next_step == (player.row, player.col):
                    player.take_damage(self.damage)
                    # Enemy pauses for 1 turn after attacking
                    self.recovery_cooldown = 2
                else:
                    self.move_to(next_step, grid)

        elif self.ai_state == EnemyState.IDLE:
            # 20% chance to move when idle
            if random.random() < 0.2:
                self.wander(grid, grid_width, grid_height)

        return True

    def draw(self, screen):
        super().draw(screen)
        center_x = self.visual_x + self.cell_size // 2
        center_y = self.visual_y + self.cell_size // 2

        # Debug: draw state indicator
        color = (255, 255, 255)
        if self.ai_state == EnemyState.CHASE:
            color = (255, 0, 0)  # Red
        elif self.ai_state == EnemyState.FLEE:
            color = (0, 0, 255)  # Blue

        pygame.draw.circle(screen, color, (center_x + 15, center_y - 20), 4)

        if self.enemy_type == "ranged":
            pygame.draw.circle(screen, GameConfig.COLORS['ranged_enemy'], (center_x, center_y - 10), 5)


class RangedEnemy(Enemy):
    def __init__(self, row, col):
        super().__init__(row, col, "ranged", health=40, damage=8)
        self.attack_range = 5
        self.flee_range = 2  # If player is closer than 2 tiles, run away
        self.attack_cooldown = 0

    def can_attack_player(self, player, walls):
        # Ranged enemies now only attack if they are in optimal range
        # If they are too close, they prefer to move (flee) instead of attacking
        if self.attack_cooldown > 0:
            return False

        distance = math.sqrt((self.row - player.row) ** 2 + (self.col - player.col) ** 2)

        # Can only attack if detected, in range, AND not too close (unless trapped)
        can_shoot = (self.has_detected_player and
                     distance <= self.attack_range and
                     distance > 1.5 and
                     self.has_line_of_sight(player, walls))

        return can_shoot

    def move_towards_player(self, player, grid, grid_width, grid_height, walls, items):
        # 1. Update Detection
        if self.can_see_player(player, walls):
            self.has_detected_player = True

        # 2. Determine State based on distance
        distance = math.sqrt((self.row - player.row) ** 2 + (self.col - player.col) ** 2)

        if not self.has_detected_player:
            self.ai_state = EnemyState.IDLE
        elif distance < self.flee_range:
            self.ai_state = EnemyState.FLEE
        elif distance > self.attack_range:
            self.ai_state = EnemyState.CHASE
        else:
            # Optimal range, stay put or slight adjustment could go here
            self.ai_state = EnemyState.ATTACK  # Basically "Wait/Aim"

        # 3. Execute State
        if self.ai_state == EnemyState.IDLE:
            if random.random() < 0.2:
                self.wander(grid, grid_width, grid_height)

        elif self.ai_state == EnemyState.CHASE:
            # Move CLOSER (standard BFS)
            next_step = self.find_path_bfs(player, grid, grid_width, grid_height)
            if next_step and next_step != (player.row, player.col):
                self.move_to(next_step, grid)

        elif self.ai_state == EnemyState.FLEE:
            # Move AWAY
            self.flee_from_player(player, grid, grid_width, grid_height)

    def flee_from_player(self, player, grid, grid_width, grid_height):
        """Greedy move to the neighbor that is FARTHEST from player"""
        best_move = None
        max_dist = -1

        current_dist = abs(self.row - player.row) + abs(self.col - player.col)

        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nr, nc = self.row + dr, self.col + dc

            if 0 <= nr < grid_height and 0 <= nc < grid_width:
                if grid[nr][nc] is None:
                    dist = abs(nr - player.row) + abs(nc - player.col)
                    if dist > max_dist and dist > current_dist:
                        max_dist = dist
                        best_move = (nr, nc)

        if best_move:
            self.move_to(best_move, grid)
        else:
            # Trapped! If we can't run, try to move anywhere or just shoot
            # Fallback to standard melee chase if trapped, so it doesn't freeze
            pass

    def attack(self, player):
        if self.attack_cooldown == 0:
            player.take_damage(self.damage)
            self.attack_cooldown = 2
            return True
        return False

    def update_cooldowns(self):
        super().update_cooldowns()
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1