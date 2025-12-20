import math
import os
import random
import sys
from collections import deque

sys.path.append(os.getcwd())

from game.GameCore.levels.ai_generation.ai_level_generator import AdvancedLevelGenerator

# Constants
EMPTY = 0
WALL = 1
ENEMY = 2
PLAYER = 4
EXIT = 5

# Detailed Item Constants
MERCHANT = 6
CHEST = 7
POTION = 8
ARROWS = 9
COIN = 10


class HybridLevelGenerator(AdvancedLevelGenerator):
    def __init__(self, ai_trainer):
        # Initialize parent with standard size
        super().__init__(width=16, height=10, difficulty=5)
        self.ai = ai_trainer

    def generate_with_ai(self):
        # 1. Ask Neural Net for the Raw Layout
        raw_grid = self.ai.generate_layout()

        # 2. APPLY RULES (The "Editor" Phase)
        clean_grid = self.clean_and_repair(raw_grid)

        # 3. Find the valid walkable area
        valid_floor_cells = self.get_largest_floor_region(clean_grid)

        # 4. Populate entities with PROBABILITY RULES
        final_grid = self.place_entities_smart(clean_grid, valid_floor_cells)

        return final_grid

    def clean_and_repair(self, grid):
        """Enforces strict rules on the AI's probabilistic output."""
        rows = self.height
        cols = self.width

        # RULE 1: OUTER WALLS MUST BE SOLID
        for r in range(rows):
            grid[r][0] = WALL
            grid[r][cols - 1] = WALL
        for c in range(cols):
            grid[0][c] = WALL
            grid[rows - 1][c] = WALL

        # RULE 2: REMOVE SINGULAR (NOISE) WALLS
        for r in range(1, rows - 1):
            for c in range(1, cols - 1):
                if grid[r][c] == WALL:
                    neighbors = 0
                    if grid[r - 1][c] == WALL:
                        neighbors += 1
                    if grid[r + 1][c] == WALL:
                        neighbors += 1
                    if grid[r][c - 1] == WALL:
                        neighbors += 1
                    if grid[r][c + 1] == WALL:
                        neighbors += 1

                    if neighbors == 0:
                        grid[r][c] = EMPTY

        # RULE 3: CONNECTIVITY
        grid, _ = self.prune_isolated_areas(grid)
        return grid

    def place_entities_smart(self, grid, open_cells):
        if len(open_cells) < 10:
            return grid

        # --- Helper: Check for Corners ---
        def is_corner(r, c):
            # Returns True if at least 2 adjacent sides are walls
            # N, S, W, E
            walls = []
            if grid[r - 1][c] == WALL:
                walls.append("N")
            if grid[r + 1][c] == WALL:
                walls.append("S")
            if grid[r][c - 1] == WALL:
                walls.append("W")
            if grid[r][c + 1] == WALL:
                walls.append("E")

            # Check for adjacent pairs
            if "N" in walls and "W" in walls:
                return True
            if "N" in walls and "E" in walls:
                return True
            if "S" in walls and "W" in walls:
                return True
            if "S" in walls and "E" in walls:
                return True

            # Also valid if surrounded by 3 walls (Dead End)
            if len(walls) >= 3:
                return True

            return False

        # --- 1. PLAYER & EXIT ---
        start_pos = random.choice(open_cells)
        grid[start_pos[0]][start_pos[1]] = PLAYER
        available = [c for c in open_cells if c != start_pos]

        # BFS for distance to find Exit
        dists = {start_pos: 0}
        queue = deque([start_pos])
        max_dist = 0
        exit_pos = start_pos

        while queue:
            curr = queue.popleft()
            if dists[curr] > max_dist:
                max_dist = dists[curr]
                exit_pos = curr

            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = curr[0] + dr, curr[1] + dc
                if (nr, nc) in available and (nr, nc) not in dists:
                    dists[(nr, nc)] = dists[curr] + 1
                    queue.append((nr, nc))

        grid[exit_pos[0]][exit_pos[1]] = EXIT
        if exit_pos in available:
            available.remove(exit_pos)

        # --- 2. IDENTIFY CORNERS ---
        # We do this after Player/Exit so we don't spawn a chest ON the player
        corner_candidates = [pos for pos in available if is_corner(pos[0], pos[1])]

        # --- 3. SPECIAL ITEMS (Corners Required) ---

        # A. MERCHANT (20% Chance, Must be in Corner)
        if random.random() < 0.20:
            if corner_candidates:
                spot = random.choice(corner_candidates)
                grid[spot[0]][spot[1]] = MERCHANT
                available.remove(spot)
                corner_candidates.remove(spot)

        # B. CHEST (60% Chance, Must be in Corner)
        if random.random() < 0.60:
            if corner_candidates:
                spot = random.choice(corner_candidates)
                grid[spot[0]][spot[1]] = CHEST
                available.remove(spot)
                corner_candidates.remove(spot)

        # --- 4. ENEMIES (Spacing Logic) ---
        num_enemies = 2 + int(self.difficulty * 0.6)
        placed_enemies = []
        candidates = [p for p in available if p in dists and dists[p] > 3]

        for _ in range(num_enemies):
            if not candidates:
                break
            for _ in range(10):
                epos = random.choice(candidates)
                too_close = False
                for existing in placed_enemies:
                    if math.dist(epos, existing) < 2.5:
                        too_close = True
                        break
                if not too_close:
                    grid[epos[0]][epos[1]] = ENEMY
                    placed_enemies.append(epos)
                    candidates.remove(epos)
                    available.remove(epos)
                    break

        # --- 5. COMMON ITEMS (Anywhere) ---

        def pick_spot():
            if not available:
                return None
            valid_spots = [p for p in available if grid[p[0]][p[1]] == EMPTY]
            if not valid_spots:
                return None
            spot = random.choice(valid_spots)
            available.remove(spot)
            return spot

        # C. HEALTH POTIONS
        chance = 0.70
        decay = 0.6
        while random.random() < chance:
            spot = pick_spot()
            if spot:
                grid[spot[0]][spot[1]] = POTION
                chance *= decay
            else:
                break

        # D. ARROWS
        chance = 0.90
        decay = 0.7
        while random.random() < chance:
            spot = pick_spot()
            if spot:
                grid[spot[0]][spot[1]] = ARROWS
                chance *= decay
            else:
                break

        # E. COINS
        for _ in range(2):
            spot = pick_spot()
            if spot:
                grid[spot[0]][spot[1]] = COIN

        return grid

    def get_largest_floor_region(self, grid):
        largest_region = []
        visited = set()
        for r in range(self.height):
            for c in range(self.width):
                if grid[r][c] == EMPTY and (r, c) not in visited:
                    region = []
                    queue = deque([(r, c)])
                    visited.add((r, c))
                    while queue:
                        curr_r, curr_c = queue.popleft()
                        region.append((curr_r, curr_c))
                        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            nr, nc = curr_r + dr, curr_c + dc
                            if 0 <= nr < self.height and 0 <= nc < self.width:
                                if grid[nr][nc] == EMPTY and (nr, nc) not in visited:
                                    visited.add((nr, nc))
                                    queue.append((nr, nc))
                    if len(region) > len(largest_region):
                        largest_region = region
        return largest_region

    def convert_to_game_format(self, grid):
        level_data = {
            "name": f"AI Gen (Diff {self.difficulty})",
            "grid_width": self.width,
            "grid_height": self.height,
            "walls": [],
            "enemies": [],
            "items": [],
            "chests": [],
            "completion_condition": "find_exit",
        }

        for r in range(self.height):
            for c in range(self.width):
                cell = grid[r][c]
                if cell == WALL:
                    level_data["walls"].append([r, c])
                elif cell == PLAYER:
                    level_data["player_start"] = [r, c]
                elif cell == EXIT:
                    level_data["exit"] = [r, c]
                elif cell == ENEMY:
                    e_type = "melee"
                    level_data["enemies"].append({"type": e_type, "position": [r, c]})
                elif cell == MERCHANT:
                    level_data["merchant"] = [r, c]
                elif cell == CHEST:
                    level_data["chests"].append(
                        {"position": [r, c], "contents": {"coins": 30, "health": 1}}
                    )
                elif cell == POTION:
                    level_data["items"].append({"type": "health", "position": [r, c]})
                elif cell == ARROWS:
                    level_data["items"].append(
                        {"type": "arrows_item", "position": [r, c], "value": 5}
                    )
                elif cell == COIN:
                    level_data["items"].append(
                        {"type": "coin", "position": [r, c], "value": 10}
                    )

        return level_data
