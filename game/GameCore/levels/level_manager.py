import json
import os

from game.GameCore.entities.chest import Chest
from game.GameCore.entities.enemy import DummyEnemy, Enemy, RangedEnemy
from game.GameCore.entities.exit_portal import ExitPortal
from game.GameCore.entities.item import Item
from game.GameCore.entities.merchant import Merchant
from game.GameCore.entities.player import Player
from game.GameCore.entities.wall import Wall


class LevelManager:
    def __init__(self):
        self.levels = {}
        self.load_levels()

        if 0 in self.levels:
            self.current_level = 0
        elif len(self.levels) > 0:
            # Sort keys and pick the first one (e.g., converts [5] to start at 5)
            self.current_level = min(self.levels.keys())
            print(f"Level 0 not found. Starting at Level {self.current_level}")
        else:
            print("CRITICAL ERROR: No levels found in levels.json!")
            self.current_level = 0

            # Update max level based on keys found
        self.max_level = max(self.levels.keys()) if self.levels else 0

    def load_levels(self):
        """Loads levels from levels.json"""
        try:
            # Build path relative to this script file
            base_path = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(base_path, "base_levels.json")

            with open(json_path, "r") as f:
                raw_data = json.load(f)

            # Convert string keys "0" to int 0, and lists to tuples
            for key, data in raw_data.items():
                level_id = int(key)
                self.levels[level_id] = data

        except FileNotFoundError:
            print("ERROR: levels.json not found!")
            self.levels = {}
        except Exception as e:
            print(f"ERROR loading levels: {e}")
            self.levels = {}

    def set_custom_ai_levels(self, levels_dict):
        """
        Принимает словарь в формате { "0": level_data, "1": ... }
        аналогичный тому, что загружается из файла.
        """
        self.levels = {}
        for key, data in levels_dict.items():
            level_id = int(key)
            self.levels[level_id] = data

        self.current_level = 0
        self.max_level = max(self.levels.keys()) if self.levels else 0
        print(f"AI Mode active. Levels loaded: {len(self.levels)}")

    def get_level(self, level_number):
        return self.levels.get(level_number)

    def get_current_level(self):
        return self.get_level(self.current_level)

    def next_level(self):
        if self.current_level < self.max_level:
            self.current_level += 1
            return True
        return False

    def reset_to_level(self, level_number):
        if 0 <= level_number <= self.max_level:
            self.current_level = level_number
            return True
        return False

    def create_level_entities(self, level_data):
        # Create player
        # JSON lists [r,c] need to be accessed by index, just like tuples
        p_pos = level_data["player_start"]
        player = Player(p_pos[0], p_pos[1])

        # Apply starting equipment

        # Read the equipment from the JSON data we generated
        start_equip = level_data.get("start_equipment", [])
        if "sword" in start_equip:
            player.has_sword = True
        if "bow" in start_equip:
            player.has_bow = True
            # Also give some starting arrows so the bow is useful!
            player.inventory["arrows"] = player.inventory.get("arrows", 0) + 10

        # Create walls
        walls = []
        for wall_pos in level_data.get("walls", []):
            # Ensure coordinates are integers
            w_r, w_c = int(wall_pos[0]), int(wall_pos[1])
            walls.append(Wall(w_r, w_c))

        # Create enemies
        enemies = []
        for enemy_def in level_data.get("enemies", []):
            pos = enemy_def["position"]
            e_type = enemy_def["type"]

            if e_type == "ranged":
                enemy = RangedEnemy(pos[0], pos[1])
            elif e_type == "dummy":
                enemy = DummyEnemy(pos[0], pos[1])
            else:
                enemy = Enemy(pos[0], pos[1], "melee")
            enemies.append(enemy)

        # Create items
        items = []
        for item_def in level_data.get("items", []):
            pos = item_def["position"]
            item = Item(
                pos[0],
                pos[1],
                item_def["type"],
                item_def.get("value", 1),
            )
            items.append(item)

        # Create chests
        chests = []
        for chest_def in level_data.get("chests", []):
            pos = chest_def["position"]
            chest = Chest(
                pos[0],
                pos[1],
                chest_def["contents"],
            )
            chests.append(chest)

        # Create exit
        exit_portal = None
        if level_data.get("exit") is not None:
            exit_pos = level_data["exit"]
            exit_portal = ExitPortal(exit_pos[0], exit_pos[1])

        # Create merchant
        merchant = None
        if level_data.get("merchant") is not None:
            merch_pos = level_data["merchant"]
            merchant = Merchant(merch_pos[0], merch_pos[1])
        return player, walls, enemies, items, chests, exit_portal, merchant

    def is_level_complete(self, player, enemies, exit_portal, level_data):
        if (
            exit_portal
            and player.row == exit_portal.row
            and player.col == exit_portal.col
        ):
            return True

        return False

    def has_more_levels(self):
        return self.current_level < self.max_level
