from game.GameCore.levels.level_definitions import LEVELS
from game.GameCore.entities.player import Player
from game.GameCore.entities.enemy import Enemy, RangedEnemy
from game.GameCore.entities.item import Item
from game.GameCore.entities.wall import Wall
from game.GameCore.entities.exit_portal import ExitPortal
from game.GameCore.entities.chest import Chest
from game.GameCore.entities.merchant import Merchant


class LevelManager:
    def __init__(self):
        self.levels = LEVELS
        self.current_level = 1
        self.max_level = len(LEVELS)

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
        if 1 <= level_number <= self.max_level:
            self.current_level = level_number
            return True
        return False

    def create_level_entities(self, level_data):
        # Create player
        player_data = level_data["player_start"]
        player = Player(player_data[0], player_data[1])

        # Create walls
        walls = []
        for wall_pos in level_data.get("walls", []):
            wall = Wall(wall_pos[0], wall_pos[1])
            walls.append(wall)

        # Create enemies
        enemies = []
        for enemy_def in level_data.get("enemies", []):
            pos = enemy_def["position"]
            if enemy_def["type"] == "ranged":
                enemy = RangedEnemy(pos[0], pos[1])
            else:
                enemy = Enemy(pos[0], pos[1], "melee")
            enemies.append(enemy)

        # Create items
        items = []
        for item_def in level_data.get("items", []):
            item = Item(item_def["position"][0], item_def["position"][1],
                        item_def["type"], item_def.get("value", 1))
            items.append(item)

        # Create chests
        chests = []
        for chest_def in level_data.get("chests", []):
            chest = Chest(chest_def["position"][0], chest_def["position"][1],
                          chest_def["contents"])
            chests.append(chest)

        # Create exit
        exit_portal = None
        if "exit" in level_data:
            exit_pos = level_data["exit"]
            exit_portal = ExitPortal(exit_pos[0], exit_pos[1])

        # Create merchant
        merchant = None
        if "merchant" in level_data:
            merchant_pos = level_data["merchant"]
            merchant = Merchant(merchant_pos[0], merchant_pos[1])

        return player, walls, enemies, items, chests, exit_portal, merchant

    def is_level_complete(self, player, enemies, exit_portal, level_data):
        # The level is complete ONLY if the player stands on the exit portal
        # The state of enemies does not matter
        if exit_portal and player.row == exit_portal.row and player.col == exit_portal.col:
            return True

        return False

    def has_more_levels(self):
        return self.current_level < self.max_level
