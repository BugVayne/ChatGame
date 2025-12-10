import copy
import random
from collections import deque

# Constants
EMPTY = 0
WALL = 1
ENEMY = 2
ITEM = 3
PLAYER = 4
EXIT = 5


class AdvancedLevelGenerator:
    def __init__(self, width=20, height=15, difficulty=1):
        self.width = width
        self.height = height
        self.difficulty = difficulty

        # Reduced from 0.45 to 0.38 for less walls (more open space)
        self.initial_wall_density = 0.38

    def initialize_grid_cellular(self):
        """Creates a noisy grid, then smooths it into a cave"""
        # 1. Start with random noise
        grid = [
            [
                WALL if random.random() < self.initial_wall_density else EMPTY
                for _ in range(self.width)
            ]
            for _ in range(self.height)
        ]

        # 2. Apply Cellular Automata Smoothing (4 steps)
        for _ in range(4):
            grid = self.apply_smoothing_step(grid)

        # 3. Ensure Borders
        for r in range(self.height):
            grid[r][0] = WALL
            grid[r][self.width - 1] = WALL
        for c in range(self.width):
            grid[0][c] = WALL
            grid[self.height - 1][c] = WALL

        return grid

    def apply_smoothing_step(self, grid):
        """Standard '4-5 Rule' for cave generation"""
        new_grid = copy.deepcopy(grid)
        for r in range(1, self.height - 1):
            for c in range(1, self.width - 1):
                neighbors = 0
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        if grid[r + i][c + j] == WALL:
                            neighbors += 1

                if neighbors > 4:
                    new_grid[r][c] = WALL
                elif neighbors < 4:
                    new_grid[r][c] = EMPTY
        return new_grid

    def prune_isolated_areas(self, grid):
        """Finds largest open space, fills all other small holes with walls"""
        largest_region = []
        visited = set()

        # Find all regions
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

        # Fill everything that isn't the largest region
        for r in range(self.height):
            for c in range(self.width):
                if grid[r][c] == EMPTY and (r, c) not in largest_region:
                    grid[r][c] = WALL

        return grid, largest_region

    def check_connectivity(self, grid, open_cells):
        """Helper to ensure the map isn't split in two"""
        if not open_cells:
            return False

        start = open_cells[0]
        visited = set([start])
        queue = deque([start])
        count = 0

        while queue:
            r, c = queue.popleft()
            count += 1
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.height and 0 <= nc < self.width:
                    if grid[nr][nc] == EMPTY and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))

        return count == len(open_cells)

    def add_wall_islands(self, grid, open_cells):
        """Adds specific obstacle islands based on requirements"""

        # Logic: 30% chance for exactly 1 island.
        # Otherwise: Random between 0 and 2.
        chance = random.random()
        if chance < 0.30:
            num_islands = 1
        else:
            num_islands = random.randint(0, 2)

        if num_islands == 0:
            return grid

        added_count = 0
        attempts = 0

        # Try to place islands
        while added_count < num_islands and attempts < 20:
            attempts += 1

            # Pick a random open spot (not near edges preferably)
            center = random.choice(open_cells)
            cr, cc = center

            # Don't place too close to border walls
            if cr < 2 or cr > self.height - 3 or cc < 2 or cc > self.width - 3:
                continue

            # Define an island shape (2x2 or cross)
            island_cells = []
            shape_type = random.choice(["square", "cross"])

            if shape_type == "square":
                island_cells = [(cr, cc), (cr + 1, cc), (cr, cc + 1), (cr + 1, cc + 1)]
            else:
                island_cells = [
                    (cr, cc),
                    (cr + 1, cc),
                    (cr - 1, cc),
                    (cr, cc + 1),
                    (cr, cc - 1),
                ]

            # Check if all potential island cells are currently empty
            valid_spot = True
            for r, c in island_cells:
                if (r, c) not in open_cells:  # It's already a wall or out of bounds
                    valid_spot = False
                    break

            if not valid_spot:
                continue

            # Temporarily apply walls
            backup_grid = copy.deepcopy(grid)
            temp_open_cells = [c for c in open_cells if c not in island_cells]

            for r, c in island_cells:
                grid[r][c] = WALL

            # CRITICAL: Check if we broke the map connectivity
            # If map is split, revert changes
            if self.check_connectivity(grid, temp_open_cells):
                # Success, commit changes
                open_cells = temp_open_cells
                added_count += 1
            else:
                # Failure, revert
                grid = backup_grid

        return grid

    def place_entities(self, grid, open_cells):
        if len(open_cells) < 10:
            return grid

        # 1. Place Player
        start_pos = random.choice(open_cells)
        grid[start_pos[0]][start_pos[1]] = PLAYER

        # 2. Place Exit (Furthest point)
        exit_pos = start_pos
        max_dist = 0
        dists = {start_pos: 0}
        queue = deque([start_pos])

        while queue:
            curr = queue.popleft()
            if curr != start_pos:
                d = dists[curr]
                if d > max_dist:
                    max_dist = d
                    exit_pos = curr

            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = curr[0] + dr, curr[1] + dc
                if 0 <= nr < self.height and 0 <= nc < self.width:
                    if grid[nr][nc] != WALL and (nr, nc) not in dists:
                        dists[(nr, nc)] = dists[curr] + 1
                        queue.append((nr, nc))

        grid[exit_pos[0]][exit_pos[1]] = EXIT

        # 3. Place Enemies
        num_enemies = 2 + int(self.difficulty * 0.8)
        valid_spawns = [
            pos for pos, dist in dists.items() if dist > 3 and pos != exit_pos
        ]

        for _ in range(num_enemies):
            if not valid_spawns:
                break
            epos = random.choice(valid_spawns)
            grid[epos[0]][epos[1]] = ENEMY
            valid_spawns.remove(epos)

        # 4. Place Items
        num_items = 3
        for _ in range(num_items):
            if not valid_spawns:
                break
            ipos = random.choice(valid_spawns)
            grid[ipos[0]][ipos[1]] = ITEM
            valid_spawns.remove(ipos)

        return grid

    def generate(self):
        """Main Pipeline"""
        # 1. Base Structure
        grid = self.initialize_grid_cellular()

        # 2. Ensure Connectivity (creates 1 big room)
        grid, open_cells = self.prune_isolated_areas(grid)

        # 3. Add obstacles (Islands)
        grid = self.add_wall_islands(grid, open_cells)

        # Re-calculate open cells after adding islands for entity placement
        open_cells = []
        for r in range(self.height):
            for c in range(self.width):
                if grid[r][c] == EMPTY:
                    open_cells.append((r, c))

        # 4. Content
        grid = self.place_entities(grid, open_cells)

        return grid

    def convert_to_game_format(self, grid):
        level_data = {
            "name": f"Cave of Trials (Diff {self.difficulty})",
            "grid_width": self.width,
            "grid_height": self.height,
            "walls": [],
            "enemies": [],
            "items": [],
            "chests": [],
            "completion_condition": "find_exit",
        }

        item_types = ["coin", "health", "arrows_item", "coin"]

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
                    chance_ranged = min(0.1 * self.difficulty, 0.5)
                    e_type = "ranged" if random.random() < chance_ranged else "melee"
                    level_data["enemies"].append({"type": e_type, "position": [r, c]})
                elif cell == ITEM:
                    i_type = random.choice(item_types)
                    val = 50 if i_type == "coin" else 5
                    level_data["items"].append(
                        {"type": i_type, "position": [r, c], "value": val}
                    )

        return level_data
