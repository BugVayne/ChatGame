import pygame
import random
from game.GameCore.config import GameConfig
from game.GameCore.levels.level_manager import LevelManager


class GameCore:
    def __init__(self):
        self.level_manager = LevelManager()
        level_data = self.level_manager.get_current_level()

        self.cell_size = GameConfig.CELL_SIZE
        self.screen_width = level_data["grid_width"] * self.cell_size
        self.screen_height = level_data["grid_height"] * self.cell_size

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Dungeon Escape")

        # Game state
        self.grid = None
        self.player = None
        self.walls = []
        self.enemies = []
        self.items = []
        self.chests = []
        self.exit_portal = None
        self.merchant = None

        # Game counters
        self.turn_count = 0
        self.game_completed = False

        # UI
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        self.initialize_level()

    def initialize_level(self):
        level_data = self.level_manager.get_current_level()

        self.grid_width = level_data["grid_width"]
        self.grid_height = level_data["grid_height"]
        self.grid = [[None for _ in range(self.grid_width)] for _ in range(self.grid_height)]

        # Update screen size
        self.screen_width = self.grid_width * self.cell_size
        self.screen_height = self.grid_height * self.cell_size
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))

        # Create entities
        (self.player, self.walls, self.enemies, self.items,
         self.chests, self.exit_portal, self.merchant) = self.level_manager.create_level_entities(level_data)

        # Reset counters
        self.turn_count = 0

        # Place entities on grid
        self.place_entity(self.player)
        for wall in self.walls:
            self.place_entity(wall)
        for enemy in self.enemies:
            self.place_entity(enemy)
        for item in self.items:
            self.place_entity(item)
        for chest in self.chests:
            self.place_entity(chest)
        if self.exit_portal:
            self.place_entity(self.exit_portal)
        if self.merchant:
            self.place_entity(self.merchant)

    def place_entity(self, entity):
        self.grid[entity.row][entity.col] = entity

    def execute_turn(self):
        self.turn_count += 1
        self.player.update_cooldowns()

        # Update enemy cooldowns
        for enemy in self.enemies:
            if hasattr(enemy, 'update_cooldowns'):
                enemy.update_cooldowns()

        # Move enemies
        for enemy in self.enemies:
            if enemy.is_alive():
                if enemy.enemy_type == "ranged":
                    # Ranged enemies attack if possible
                    if enemy.can_attack_player(self.player, self.walls):
                        enemy.attack(self.player)
                    else:
                        enemy.move_towards_player(self.player, self.grid,
                                                  self.grid_width, self.grid_height, self.walls)
                else:
                    # Melee enemies move towards player
                    enemy.move_towards_player(self.player, self.grid,
                                              self.grid_width, self.grid_height, self.walls)

        # Check collisions
        self.check_collisions()

        # Check level completion
        self.check_level_completion()

    def check_collisions(self):
        # Check player-enemy collisions (melee combat)
        for enemy in self.enemies[:]:
            if (enemy.is_alive() and enemy.enemy_type == "melee" and
                    enemy.row == self.player.row and enemy.col == self.player.col):
                self.player.take_damage(enemy.damage)

        # Check player-item collisions
        for item in self.items[:]:
            if item.row == self.player.row and item.col == self.player.col:
                self.player.collect_item(item)
                self.items.remove(item)
                self.grid[item.row][item.col] = None

        # Check player-chest collisions
        for chest in self.chests:
            if not chest.opened and chest.row == self.player.row and chest.col == self.player.col:
                contents = chest.open()
                for item_type, amount in contents.items():
                    if item_type == "coins":
                        self.player.coins += amount
                    elif item_type == "health":
                        self.player.inventory["health"] += amount
                    elif item_type == "arrows":
                        self.player.inventory["arrows"] += amount

    def check_level_completion(self):
        level_data = self.level_manager.get_current_level()
        if self.level_manager.is_level_complete(self.player, self.enemies,
                                                self.exit_portal, level_data):
            if self.level_manager.has_more_levels():
                self.level_manager.next_level()
                self.initialize_level()
            else:
                self.game_completed = True

    def render(self):
        self.screen.fill((30, 30, 50))

        # Draw grid
        for row in range(self.grid_height):
            for col in range(self.grid_width):
                x = col * self.cell_size
                y = row * self.cell_size

                color = GameConfig.COLORS['grid_light'] if (row + col) % 2 == 0 else GameConfig.COLORS['grid_dark']
                pygame.draw.rect(self.screen, color, (x, y, self.cell_size, self.cell_size))
                pygame.draw.rect(self.screen, GameConfig.COLORS['grid_border'],
                                 (x, y, self.cell_size, self.cell_size), 1)

                # Draw objects
                obj = self.grid[row][col]
                if obj:
                    obj.draw(self.screen, x, y, self.cell_size)

        # Draw UI
        self.draw_ui()
        pygame.display.flip()

    def draw_ui(self):
        # Player stats
        health_text = self.font.render(f"Health: {self.player.health}/{self.player.max_health}",
                                       True, GameConfig.COLORS['ui_text'])
        self.screen.blit(health_text, (10, 10))

        coins_text = self.small_font.render(f"Coins: {self.player.coins}",
                                            True, (255, 215, 0))
        self.screen.blit(coins_text, (10, 50))

        # Equipment
        equipment_text = self.small_font.render(
            f"Sword: Lvl {self.player.sword_level} | Bow: Lvl {self.player.bow_level} | "
            f"Arrows: {self.player.inventory['arrows']}",
            True, GameConfig.COLORS['ui_secondary']
        )
        self.screen.blit(equipment_text, (10, 80))

        # Inventory
        inventory_text = self.small_font.render(
            f"Health Potions: {self.player.inventory['health']}",
            True, GameConfig.COLORS['ui_secondary']
        )
        self.screen.blit(inventory_text, (10, 110))

        # Dash cooldown
        dash_text = self.small_font.render(
            f"Dash: {'Ready' if self.player.dash_cooldown == 0 else f'{self.player.dash_cooldown} turns'}",
            True, (0, 200, 255) if self.player.dash_cooldown == 0 else (150, 150, 150)
        )
        self.screen.blit(dash_text, (10, 140))

        # Level info
        level_data = self.level_manager.get_current_level()
        level_text = self.small_font.render(
            f"Level {self.level_manager.current_level}: {level_data['name']}",
            True, (200, 200, 0)
        )
        self.screen.blit(level_text, (10, 170))

        # Completion condition
        condition = level_data.get("completion_condition", "defeat_enemies")
        condition_text = self.small_font.render(
            f"Goal: {'Defeat all enemies' if condition == 'defeat_enemies' else 'Find the exit'}",
            True, (200, 200, 0)
        )
        self.screen.blit(condition_text, (10, 200))

        # Game completed message
        if self.game_completed:
            completed_text = self.font.render("ESCAPE SUCCESSFUL!", True, (0, 255, 0))
            text_rect = completed_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.screen.blit(completed_text, text_rect)

    def execute_command(self, command):
        action = command.get("action")
        result = {"status": "success", "action": action}

        if action == "move":
            direction = command.get("direction")
            if self.player.move(direction, self.grid, self.grid_width, self.grid_height):
                result["direction"] = direction
                result["position"] = (self.player.row, self.player.col)
                self.check_collisions()
                self.execute_turn()  # Enemy turn after player move
            else:
                result["status"] = "error"
                result["message"] = "Cannot move in that direction"

        elif action == "dash":
            direction = command.get("direction")
            if self.player.dash(direction, self.grid, self.grid_width, self.grid_height):
                result["direction"] = direction
                result["position"] = (self.player.row, self.player.col)
                self.check_collisions()
                self.execute_turn()
            else:
                result["status"] = "error"
                result["message"] = "Cannot dash or on cooldown"

        elif action == "attack_sword":
            direction = command.get("direction")
            hit_enemies = self.player.attack_sword(direction, self.enemies)
            if hit_enemies:
                result["hit_enemies"] = [
                    {"position": (e.row, e.col), "damage": GameConfig.PLAYER_BASE_DAMAGE + self.player.sword_level * 5}
                    for e in hit_enemies]
                # Remove defeated enemies
                for enemy in hit_enemies[:]:
                    if not enemy.is_alive():
                        self.grid[enemy.row][enemy.col] = None
                        self.enemies.remove(enemy)
                self.execute_turn()
            else:
                result["status"] = "error"
                result["message"] = "No enemies in range"

        elif action == "attack_bow":
            direction = command.get("direction")
            attack_result = self.player.attack_bow(direction, self.enemies, self.walls)
            if attack_result:
                result["attack_result"] = attack_result
                if attack_result["type"] == "enemy" and not attack_result["enemy"].is_alive():
                    self.grid[attack_result["enemy"].row][attack_result["enemy"].col] = None
                    self.enemies.remove(attack_result["enemy"])
                self.execute_turn()
            else:
                result["status"] = "error"
                result["message"] = "No arrows or no target"

        elif action == "use_item":
            item_type = command.get("item_type")
            if self.player.use_item(item_type):
                result["item_type"] = item_type
            else:
                result["status"] = "error"
                result["message"] = f"No {item_type} available"

        elif action == "upgrade":
            upgrade_type = command.get("upgrade_type")
            if upgrade_type == "sword":
                if self.player.upgrade_sword():
                    result["new_level"] = self.player.sword_level
                else:
                    result["status"] = "error"
                    result["message"] = "Cannot upgrade sword"
            elif upgrade_type == "bow":
                if self.player.upgrade_bow():
                    result["new_level"] = self.player.bow_level
                else:
                    result["status"] = "error"
                    result["message"] = "Cannot upgrade bow"
            elif upgrade_type == "health":
                if self.player.upgrade_health():
                    result["new_max_health"] = self.player.max_health
                else:
                    result["status"] = "error"
                    result["message"] = "Cannot upgrade health"

        elif action == "reset":
            self.initialize_level()
            result["message"] = "Level reset"

        else:
            result["status"] = "error"
            result["message"] = f"Unknown action: {action}"

        return result

    def get_game_state(self):
        level_data = self.level_manager.get_current_level()

        return {
            "level": self.level_manager.current_level,
            "level_name": level_data["name"],
            "player": {
                "position": (self.player.row, self.player.col),
                "health": self.player.health,
                "max_health": self.player.max_health,
                "coins": self.player.coins,
                "sword_level": self.player.sword_level,
                "bow_level": self.player.bow_level,
                "inventory": self.player.inventory.copy(),
                "dash_cooldown": self.player.dash_cooldown
            },
            "stats": {
                "turn_count": self.turn_count,
                "enemies_remaining": sum(1 for e in self.enemies if e.is_alive())
            },
            "completion_condition": level_data.get("completion_condition", "defeat_enemies"),
            "game_completed": self.game_completed,
            "grid_dimensions": (self.grid_width, self.grid_height)
        }