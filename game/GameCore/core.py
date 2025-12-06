import pygame

from game.GameCore.config import GameConfig, GameState, UIStyle
from game.GameCore.entities.projectile import Projectile
from game.GameCore.levels.level_manager import LevelManager
from game.GameCore.resource_manager import ResourceManager


class GameCore:
    def __init__(self):
        self.level_manager = LevelManager()
        level_data = self.level_manager.get_current_level()

        self.cell_size = GameConfig.CELL_SIZE
        self.screen_width = level_data["grid_width"] * self.cell_size
        self.screen_height = level_data["grid_height"] * self.cell_size

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Dungeon Escape")

        self.resource_manager = ResourceManager()

        # Game Logic State
        self.state = GameState.START

        # Define Merchant Shop Items
        self.shop_items = [
            {"name": "Health Potion", "cost": 10, "action": "buy_potion", "key": "1"},
            {"name": "Arrows (x5)", "cost": 15, "action": "buy_arrows", "key": "2"},
        ]

        self.grid = None
        self.player = None
        self.walls = []
        self.enemies = []
        self.items = []
        self.chests = []
        self.projectiles = []
        self.exit_portal = None
        self.merchant = None
        self.turn_count = 0
        self.game_completed = False
        self.font = pygame.font.Font(None, 36)
        self.large_font = pygame.font.Font(None, 72)
        self.small_font = pygame.font.Font(None, 24)
        self.btn_retry_rect = pygame.Rect(0, 0, 0, 0)
        self.btn_menu_rect = pygame.Rect(0, 0, 0, 0)

        self.initialize_level()

    def check_death(self):
        """Checks if player died"""
        if self.player.health <= 0:
            self.state = GameState.GAME_OVER
            print("Player Died")

    def initialize_level(self):
        level_data = self.level_manager.get_current_level()

        self.grid_width = level_data["grid_width"]
        self.grid_height = level_data["grid_height"]
        self.grid = [
            [None for _ in range(self.grid_width)] for _ in range(self.grid_height)
        ]

        # Update screen size
        target_width = self.grid_width * self.cell_size
        target_height = self.grid_height * self.cell_size

        # Only recreate window if size changed or it doesn't exist
        # This prevents GL Context crashes in threading
        if (
            self.screen is None
            or self.screen.get_width() != target_width
            or self.screen.get_height() != target_height
        ):
            self.screen_width = target_width
            self.screen_height = target_height
            self.screen = pygame.display.set_mode(
                (self.screen_width, self.screen_height)
            )

        self.projectiles = []
        # Create entities
        (
            self.player,
            self.walls,
            self.enemies,
            self.items,
            self.chests,
            self.exit_portal,
            self.merchant,
        ) = self.level_manager.create_level_entities(level_data)

        # Reset counters
        self.turn_count = 0
        self.game_completed = False

        # Place entities on grid
        self.place_entity(self.player)
        for wall in self.walls:
            self.place_entity(wall)
        for enemy in self.enemies:
            self.place_entity(enemy)
        for chest in self.chests:
            self.place_entity(chest)

    def place_entity(self, entity):
        self.grid[entity.row][entity.col] = entity

    def update_projectiles(self):
        """Moves arrows and handles collisions"""
        for proj in self.projectiles[:]:  # Iterate over copy to allow removal
            if not proj.active:
                self.projectiles.remove(proj)
                continue

            # Move the projectile
            proj.move()

            # 1. Check Bounds
            if not (
                0 <= proj.row < self.grid_height and 0 <= proj.col < self.grid_width
            ):
                self.projectiles.remove(proj)
                continue

            # 2. Check Collision with Grid Objects (Walls, Enemies)
            target_cell = self.grid[proj.row][proj.col]

            if target_cell:
                if target_cell.type == "wall":
                    # Hit Wall - Destroy Arrow
                    self.projectiles.remove(proj)

                elif target_cell.type == "enemy":
                    # Hit Enemy - Damage Enemy, Destroy Arrow
                    enemy = target_cell
                    enemy.take_damage(proj.damage)
                    self.projectiles.remove(proj)

                    # If enemy died, remove from grid
                    if not enemy.is_alive():
                        self.grid[enemy.row][enemy.col] = None
                        if enemy in self.enemies:
                            self.enemies.remove(enemy)

                elif target_cell.type == "chest":
                    # Hit Chest - Destroy Arrow
                    self.projectiles.remove(proj)

    def execute_turn(self):
        if self.state != GameState.PLAYING:
            return
        self.turn_count += 1
        self.player.update_cooldowns()
        self.update_projectiles()
        # Update enemy cooldowns
        for enemy in self.enemies:
            if hasattr(enemy, "update_cooldowns"):
                enemy.update_cooldowns()

        # Move enemies
        for enemy in self.enemies:
            if enemy.is_alive():
                if enemy.enemy_type == "ranged":
                    # Ranged enemies attack if possible
                    if enemy.can_attack_player(self.player, self.walls):
                        enemy.attack(self.player)
                    else:
                        enemy.move_towards_player(
                            self.player,
                            self.grid,
                            self.grid_width,
                            self.grid_height,
                            self.walls,
                            self.items,
                        )
                else:
                    # Melee enemies move towards player
                    enemy.move_towards_player(
                        self.player,
                        self.grid,
                        self.grid_width,
                        self.grid_height,
                        self.walls,
                        self.items,
                    )

        # Check collisions
        self.check_collisions()

        self.check_death()
        if self.state == GameState.GAME_OVER:
            return

        # Check level completion
        self.check_level_completion()

    def check_collisions(self):
        # Check player-enemy collisions (melee combat)
        for enemy in self.enemies[:]:
            if (
                enemy.is_alive()
                and enemy.enemy_type == "melee"
                and enemy.row == self.player.row
                and enemy.col == self.player.col
            ):
                self.player.take_damage(enemy.damage)

        # Check player-item collisions
        for item in self.items[:]:
            if item.row == self.player.row and item.col == self.player.col:
                self.player.collect_item(item)
                self.items.remove(item)
                # self.grid[item.row][item.col] = None

        # Check player-chest collisions
        for chest in self.chests:
            if (
                not chest.opened
                and chest.row == self.player.row
                and chest.col == self.player.col
            ):
                contents = chest.open()

                # Prepare popup content
                self.loot_lines = ["You found:"]

                for item_type, amount in contents.items():
                    # Add to player inventory
                    if item_type == "coins":
                        self.player.coins += amount
                        self.loot_lines.append(f"+ {amount} Gold")
                    elif item_type == "health":
                        self.player.inventory["health"] += amount
                        self.loot_lines.append(f"+ {amount} Potion")
                    elif item_type == "arrows":
                        self.player.inventory["arrows"] += amount
                        self.loot_lines.append(f"+ {amount} Arrows")

                # Switch state to popup
                self.state = GameState.CHEST_POPUP

    def check_level_completion(self):
        level_data = self.level_manager.get_current_level()
        if self.level_manager.is_level_complete(
            self.player, self.enemies, self.exit_portal, level_data
        ):
            if self.level_manager.has_more_levels():
                self.level_manager.next_level()
                self.initialize_level()
            else:
                self.game_completed = True
                self.state = GameState.VICTORY

    def render(self, dt=0):
        """Decides which screen to draw based on state"""

        # 1. Handle START Screen separately (it usually has a black background)
        if self.state == GameState.START:
            self.screen.fill((10, 10, 15))  # Clear screen for menu
            self.draw_start_screen()

        # 2. For all other states, Draw the Game World FIRST (Grid + Entities + HUD)
        else:
            self.draw_game_world(dt)

            # 3. Then Draw the specific UI Popup ON TOP
            if self.state == GameState.MERCHANT:
                self.draw_merchant_screen()
            elif self.state == GameState.PAUSED:
                self.draw_pause_screen()
            elif self.state == GameState.GAME_OVER:
                self.draw_game_over_screen()
            elif self.state == GameState.VICTORY:
                self.draw_victory_screen()
            elif self.state == GameState.CHEST_POPUP:
                self.draw_chest_popup()
            # If state is PLAYING, we already drew the world, so we are done.

        pygame.display.flip()

    def draw_end_screen(self, is_victory):
        # Dark Overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Title Text
        if is_victory:
            title_text = "VICTORY!"
            title_color = (255, 215, 0)  # Gold
            sub_text = "You have escaped the dungeon!"
        else:
            title_text = "GAME OVER"
            title_color = (200, 50, 50)  # Red
            sub_text = "The dungeon claimed another soul."

        # Draw Title
        title_surf = self.large_font.render(title_text, True, title_color)
        title_rect = title_surf.get_rect(
            center=(self.screen_width // 2, self.screen_height // 3)
        )
        self.screen.blit(title_surf, title_rect)

        sub_surf = self.small_font.render(sub_text, True, (200, 200, 200))
        sub_rect = sub_surf.get_rect(
            center=(self.screen_width // 2, self.screen_height // 3 + 50)
        )
        self.screen.blit(sub_surf, sub_rect)

        # --- DRAW BUTTONS ---
        btn_width, btn_height = 220, 50
        center_x = self.screen_width // 2

        # Button 1: Try Again / Play Again
        btn1_y = self.screen_height // 2 + 30
        self.btn_retry_rect = pygame.Rect(
            center_x - btn_width // 2, btn1_y, btn_width, btn_height
        )

        # Hover Effect 1
        mouse_pos = pygame.mouse.get_pos()
        color1 = (
            (50, 150, 50)
            if self.btn_retry_rect.collidepoint(mouse_pos)
            else (30, 100, 30)
        )

        pygame.draw.rect(self.screen, color1, self.btn_retry_rect)
        pygame.draw.rect(self.screen, (100, 200, 100), self.btn_retry_rect, 2)

        btn1_label = "Play Again" if is_victory else "Try Again"
        text1 = self.font.render(f"{btn1_label} (T)", True, (255, 255, 255))
        text1_rect = text1.get_rect(center=self.btn_retry_rect.center)
        self.screen.blit(text1, text1_rect)

        # Button 2: Main Menu
        btn2_y = btn1_y + 70
        self.btn_menu_rect = pygame.Rect(
            center_x - btn_width // 2, btn2_y, btn_width, btn_height
        )

        # Hover Effect 2
        color2 = (
            (150, 50, 50)
            if self.btn_menu_rect.collidepoint(mouse_pos)
            else (100, 30, 30)
        )

        pygame.draw.rect(self.screen, color2, self.btn_menu_rect)
        pygame.draw.rect(self.screen, (200, 100, 100), self.btn_menu_rect, 2)

        text2 = self.font.render("Main Menu (M)", True, (255, 255, 255))
        text2_rect = text2.get_rect(center=self.btn_menu_rect.center)
        self.screen.blit(text2, text2_rect)

    def draw_game_world(self, dt=0):
        self.screen.fill((30, 30, 50))

        # Draw Floor Tiles (Static)
        floor_anim = self.resource_manager.get_animation("floor")

        if floor_anim:
            floor_img = floor_anim[0]
            # Scale it once to match cell size
            floor_img = pygame.transform.scale(
                floor_img, (self.cell_size, self.cell_size)
            )

            # Draw floor grid
            for r in range(self.grid_height):
                for c in range(self.grid_width):
                    self.screen.blit(
                        floor_img, (c * self.cell_size, r * self.cell_size)
                    )
        else:
            # Fallback if resource missing: Draw basic rectangles
            for r in range(self.grid_height):
                for c in range(self.grid_width):
                    rect = (
                        c * self.cell_size,
                        r * self.cell_size,
                        self.cell_size,
                        self.cell_size,
                    )
                    pygame.draw.rect(self.screen, (30, 30, 40), rect)
                    pygame.draw.rect(self.screen, (40, 40, 50), rect, 1)
        # --- UPDATE & DRAW ENTITIES ---

        # Define all entities to draw
        all_entities = []

        # Walkable items
        if self.exit_portal:
            all_entities.append(self.exit_portal)
        if self.merchant:
            all_entities.append(self.merchant)
        all_entities.extend(self.items)

        # Solids
        all_entities.extend(self.walls)
        all_entities.extend(self.enemies)
        all_entities.extend(self.chests)
        all_entities.append(self.player)

        # Draw them
        for entity in all_entities:
            # Make sure entity has the update_visuals method
            if hasattr(entity, "update_visuals"):
                entity.update_visuals(dt)
            entity.draw(self.screen)  # No args needed now

        # Draw Projectiles (keep line drawing or make sprite)
        for proj in self.projectiles:
            proj.draw(self.screen)

        self.draw_ui()

    def draw_start_screen(self):
        self.draw_ui_window(
            title="DUNGEON ESCAPE",
            title_color=(200, 50, 50),
            content_lines=[
                "Welcome, brave adventurer.",
                "",
                "Navigate the grid, defeat enemies,",
                "and find the exit portal.",
            ],
            footer_text="Controls: WASD (Move) | SHIFT (Dash) | SPACE (Interact) | ENTER to Start",
        )

    def draw_pause_screen(self):
        self.draw_ui_window(
            title="GAME PAUSED",
            title_color=(255, 255, 255),
            content_lines=["Take a breath.", "The dungeon will wait."],
            footer_text="Press P or ESC to Resume | Q to Quit",
        )

    def draw_merchant_screen(self):
        # Prepare content lines dynamically based on player coins
        lines = []
        lines.append(f"Your Gold: {self.player.coins}")
        lines.append("")  # Spacer

        for item in self.shop_items:
            # Color logic: Green if affordable, Red if not
            can_afford = self.player.coins >= item["cost"]
            color = (100, 255, 100) if can_afford else (200, 80, 80)

            text = f"[{item['key']}] {item['name']} ... {item['cost']} G"
            lines.append((text, color))  # Passing tuple for custom color

        self.draw_ui_window(
            title="MERCHANT SHOP",
            title_color=(255, 215, 0),  # Gold
            content_lines=lines,
            footer_text="Press Number Keys to Buy | M or ESC to Leave",
        )

    def draw_game_over_screen(self):
        # Define the buttons structure
        buttons = [
            {"text": "Try Again", "key": "T", "rect": self.btn_retry_rect},
            {"text": "Main Menu", "key": "M", "rect": self.btn_menu_rect},
        ]

        self.draw_ui_window(
            title="GAME OVER",
            title_color=(200, 0, 0),
            content_lines=[
                "You have fallen in battle.",
                f"Level Reached: {self.level_manager.current_level}",
                f"Gold Collected: {self.player.coins}",
            ],
            buttons=buttons,
        )

    def draw_victory_screen(self):
        # Using same buttons, different text
        buttons = [
            {"text": "Play Again", "key": "T", "rect": self.btn_retry_rect},
            {"text": "Main Menu", "key": "M", "rect": self.btn_menu_rect},
        ]

        self.draw_ui_window(
            title="VICTORY!",
            title_color=(0, 255, 100),
            content_lines=[
                "You have escaped the dungeon!",
                "The surface sun feels warm.",
                "",
                f"Final Gold: {self.player.coins}",
            ],
            buttons=buttons,
        )

    def draw_chest_popup(self):
        self.draw_ui_window(
            title="CHEST OPENED",
            title_color=(255, 215, 0),  # Gold
            content_lines=getattr(self, "loot_lines", ["Empty"]),
            footer_text="Press SPACE or ENTER to Continue",
        )

    def buy_item(self, index):
        if 0 <= index < len(self.shop_items):
            item = self.shop_items[index]
            if self.player.coins >= item["cost"]:

                # Apply purchase logic
                if item["action"] == "buy_potion":
                    self.player.inventory["health"] += 1
                elif item["action"] == "buy_arrows":
                    self.player.inventory["arrows"] += 5

                self.player.coins -= item["cost"]
                return True
        return False

    def draw_ui(self):
        # Player stats
        health_text = self.font.render(
            f"Health: {self.player.health}/{self.player.max_health}",
            True,
            GameConfig.COLORS["ui_text"],
        )
        self.screen.blit(health_text, (10, 10))

        coins_text = self.small_font.render(
            f"Coins: {self.player.coins}", True, (255, 215, 0)
        )
        self.screen.blit(coins_text, (10, 50))

        # Equipment
        sword_status = "Equipped" if self.player.has_sword else "None"
        bow_status = "Equipped" if self.player.has_bow else "None"
        equipment_text = self.small_font.render(
            f"Sword: {sword_status} | Bow: {bow_status} | Arrows: {self.player.inventory['arrows']}",
            True,
            GameConfig.COLORS["ui_secondary"],
        )
        self.screen.blit(equipment_text, (10, 80))

        # Inventory
        inventory_text = self.small_font.render(
            f"Health Potions: {self.player.inventory['health']}",
            True,
            GameConfig.COLORS["ui_secondary"],
        )
        self.screen.blit(inventory_text, (10, 110))

        # Dash cooldown
        dash_text = self.small_font.render(
            f"Dash: {'Ready' if self.player.dash_cooldown == 0 else f'{self.player.dash_cooldown} turns'}",
            True,
            (0, 200, 255) if self.player.dash_cooldown == 0 else (150, 150, 150),
        )
        self.screen.blit(dash_text, (10, 140))

        # Level info
        level_data = self.level_manager.get_current_level()
        level_text = self.small_font.render(
            f"Level {self.level_manager.current_level}: {level_data['name']}",
            True,
            (200, 200, 0),
        )
        self.screen.blit(level_text, (10, 170))

        # Completion condition
        condition_text = self.small_font.render(
            "Goal: Find and Enter the Portal", True, (200, 200, 0)
        )
        self.screen.blit(condition_text, (10, 200))

        # Game completed message
        if self.game_completed:
            completed_text = self.font.render("ESCAPE SUCCESSFUL!", True, (0, 255, 0))
            text_rect = completed_text.get_rect(
                center=(self.screen_width // 2, self.screen_height // 2)
            )
            self.screen.blit(completed_text, text_rect)

    def execute_command(self, command):
        action = command.get("action")
        result = {"status": "success", "action": action}

        if action == "move":
            direction = command.get("direction")
            if self.player.move(
                direction, self.grid, self.grid_width, self.grid_height
            ):
                result["direction"] = direction
                result["position"] = (self.player.row, self.player.col)
                self.check_collisions()
                self.execute_turn()  # Enemy turn after player move
            else:
                result["status"] = "error"
                result["message"] = "Cannot move in that direction"

        elif action == "dash":
            direction = command.get("direction")
            if self.player.dash(
                direction, self.grid, self.grid_width, self.grid_height
            ):
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
                    {
                        "position": (e.row, e.col),
                        "damage": GameConfig.PLAYER_BASE_DAMAGE,
                    }
                    for e in hit_enemies
                ]
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
            if not self.player.has_bow:
                result["status"] = "error"
                result["message"] = "You don't have a bow"
                return result

            if self.player.inventory.get("arrows", 0) > 0:

                direction = command.get("direction")
                damage = GameConfig.PLAYER_BASE_DAMAGE

                # Calculate spawn position (1 tile in front of player)
                spawn_r, spawn_c = self.player.row, self.player.col

                if direction == "up":
                    spawn_r -= 1

                elif direction == "down":
                    spawn_r += 1

                elif direction == "left":
                    spawn_c -= 1

                elif direction == "right":
                    spawn_c += 1

                # Check if spawn point is valid
                if 0 <= spawn_r < self.grid_height and 0 <= spawn_c < self.grid_width:

                    self.player.inventory["arrows"] -= 1
                    target_obj = self.grid[spawn_r][spawn_c]

                    if target_obj and target_obj.type == "wall":
                        pass

                    elif target_obj and target_obj.type == "enemy":
                        target_obj.take_damage(damage)
                        if not target_obj.is_alive():
                            self.grid[spawn_r][spawn_c] = None
                            self.enemies.remove(target_obj)

                    else:
                        proj = Projectile(spawn_r, spawn_c, direction, damage)
                        self.projectiles.append(proj)
                    self.execute_turn()
                    result["message"] = "Arrow shot"

                else:
                    result["status"] = "error"
                    result["message"] = "Cannot shoot into void"

            else:
                result["status"] = "error"
                result["message"] = "No arrows"

        elif action == "use_item":
            item_type = command.get("item_type")
            if self.player.use_item(item_type):
                result["item_type"] = item_type
            else:
                result["status"] = "error"
                result["message"] = f"No {item_type} available"

        elif action == "upgrade":
            upgrade_type = command.get("upgrade_type")
            if upgrade_type == "health":
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
                "has_sword": self.player.has_sword,
                "has_bow": self.player.has_bow,
                "inventory": self.player.inventory.copy(),
                "dash_cooldown": self.player.dash_cooldown,
            },
            "stats": {
                "turn_count": self.turn_count,
                "enemies_remaining": sum(1 for e in self.enemies if e.is_alive()),
            },
            "completion_condition": level_data.get(
                "completion_condition", "defeat_enemies"
            ),
            "game_completed": self.game_completed,
            "grid_dimensions": (self.grid_width, self.grid_height),
        }

    def draw_ui_window(
        self,
        title,
        content_lines,
        footer_text=None,
        title_color=(255, 255, 255),
        buttons=None,
    ):
        """
        Generic method to draw a consistent popup window.

        Args:
            title (str): Main header text.
            content_lines (list): List of strings OR tuples (text, color) to display in the body.
            footer_text (str): Optional instructional text at the bottom.
            title_color (tuple): RGB color for the title.
            buttons (list): Optional list of dicts [{'text': str, 'rect': pygame.Rect, 'key': str}]
        """
        # 1. Draw Semi-Transparent Overlay (dims the game behind)
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # 2. Calculate Window Dimensions
        window_width = self.screen_width * 0.7
        window_height = self.screen_height * 0.7
        window_x = (self.screen_width - window_width) // 2
        window_y = (self.screen_height - window_height) // 2

        window_rect = pygame.Rect(window_x, window_y, window_width, window_height)

        # 3. Draw Main Box and Border
        pygame.draw.rect(self.screen, UIStyle.BG_COLOR, window_rect)
        pygame.draw.rect(
            self.screen, UIStyle.BORDER_COLOR, window_rect, UIStyle.BORDER_WIDTH
        )

        # Inner decorative line
        pygame.draw.rect(self.screen, (20, 20, 20), window_rect.inflate(-10, -10), 1)

        # 4. Draw Title
        title_surf = self.large_font.render(title, True, title_color)
        title_rect = title_surf.get_rect(
            center=(self.screen_width // 2, window_y + UIStyle.PADDING + 20)
        )
        self.screen.blit(title_surf, title_rect)

        # Draw separator line under title
        pygame.draw.line(
            self.screen,
            UIStyle.BORDER_COLOR,
            (window_x + 50, title_rect.bottom + 10),
            (window_x + window_width - 50, title_rect.bottom + 10),
            2,
        )

        # 5. Draw Body Content
        start_y = title_rect.bottom + 40
        line_height = 40

        for i, line_data in enumerate(content_lines):
            # Handle plain strings or (text, color) tuples
            if isinstance(line_data, tuple):
                text, color = line_data
            else:
                text = line_data
                color = UIStyle.TEXT_COLOR

            line_surf = self.font.render(text, True, color)
            line_rect = line_surf.get_rect(
                center=(self.screen_width // 2, start_y + (i * line_height))
            )
            self.screen.blit(line_surf, line_rect)

        # 6. Draw Buttons (if any)
        if buttons:
            btn_start_y = (
                window_y + window_height - UIStyle.PADDING - (len(buttons) * 60)
            )
            mouse_pos = pygame.mouse.get_pos()

            for i, btn in enumerate(buttons):
                # Update the Rect position in place so the Controller knows where it is
                rect_width = 250
                rect_height = 50
                btn["rect"].x = (self.screen_width // 2) - (rect_width // 2)
                btn["rect"].y = btn_start_y + (i * 60)
                btn["rect"].width = rect_width
                btn["rect"].height = rect_height

                # Hover Effect
                is_hovered = btn["rect"].collidepoint(mouse_pos)
                bg_color = (60, 60, 60) if not is_hovered else (80, 80, 100)
                border_col = UIStyle.BORDER_COLOR if not is_hovered else (255, 255, 255)

                # Draw Button
                pygame.draw.rect(self.screen, bg_color, btn["rect"])
                pygame.draw.rect(self.screen, border_col, btn["rect"], 2)

                # Button Text
                btn_text = f"{btn['text']} ({btn['key']})"
                text_surf = self.font.render(btn_text, True, (255, 255, 255))
                text_rect = text_surf.get_rect(center=btn["rect"].center)
                self.screen.blit(text_surf, text_rect)

        # 7. Draw Footer (if no buttons, or below buttons)
        if footer_text and not buttons:
            footer_surf = self.small_font.render(footer_text, True, (150, 150, 150))
            footer_rect = footer_surf.get_rect(
                center=(self.screen_width // 2, window_y + window_height - 30)
            )
            self.screen.blit(footer_surf, footer_rect)
