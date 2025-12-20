import io
import threading

import numpy as np
import pygame
from PIL import Image

from game.GameCore.config import GameState
from game.streamer import start_stream_server


class GameController:
    def __init__(self, game_core, state_monitor, external_interface):
        self.game_core = game_core
        self.state_monitor = state_monitor
        self.external_interface = external_interface

        # Change: Store the raw pixel array, not the finished bytes
        self.latest_raw_frame = None
        self.frame_lock = threading.Lock()

        self.stream_thread = threading.Thread(
            target=start_stream_server, args=(self,), daemon=True
        )
        self.stream_thread.start()
        self.start_websocket_server()

        self.turn_timer = 0
        self.turn_interval = 3000

    def start_websocket_server(self):
        """Start WebSocket server in a separate thread"""
        ws_thread = threading.Thread(
            target=self.external_interface.start_websocket_server, daemon=True
        )
        ws_thread.start()

    def get_latest_frame(self):
        """Returns the raw pixels for the streamer thread to process"""
        with self.frame_lock:
            if self.latest_raw_frame is None:
                return None
            return np.copy(self.latest_raw_frame)

    def run(self):
        clock = pygame.time.Clock()
        running = True

        while running:
            dt = clock.tick(60)  # Game runs at 60 FPS

            if self.game_core.state == GameState.PLAYING:
                self.turn_timer += dt
                if self.turn_timer >= self.turn_interval:
                    self.turn_timer = 0
                    self.execute_game_turn()

            self.game_core.render(dt)

            # --- OPTIMIZED CAPTURE ---
            if self.game_core.screen:
                try:
                    # Get raw pixels from Pygame (This is very fast)
                    # We don't do any PIL or JPEG stuff here anymore
                    pixel_array = pygame.surfarray.array3d(self.game_core.screen)

                    with self.frame_lock:
                        self.latest_raw_frame = pixel_array
                except Exception as e:
                    print(f"Capture error: {e}")

            running = self.handle_pygame_events()

        pygame.quit()

    def execute_game_turn(self):
        if self.game_core.state != GameState.PLAYING:
            return

        self.game_core.execute_turn()
        events = self.state_monitor.check_events()
        for event in events:
            self.external_interface.broadcast_event(event)

    def handle_retry_action(self):
        """Handles logic for retrying based on state"""
        if self.game_core.state == GameState.VICTORY:
            # If we won, reset completely to Level 1
            self.game_core.level_manager.reset_to_level(1)
            self.game_core.initialize_level()
        else:
            # If we died, just restart the current level
            self.game_core.initialize_level()

        self.game_core.state = GameState.PLAYING

    def handle_pygame_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left Click
                mouse_pos = pygame.mouse.get_pos()

                # --- ЛОГИКА В ГЛАВНОМ МЕНЮ ---
                if self.game_core.state == GameState.START:
                    if self.game_core.btn_start_rect.collidepoint(mouse_pos):
                        self.game_core.state = GameState.PLAYING
                    elif self.game_core.btn_ai_mode_rect.collidepoint(mouse_pos):
                        self.game_core.start_ai_generation_mode()

                # --- ЛОГИКА В КОНЦЕ ИГРЫ ---
                elif self.game_core.state in [GameState.GAME_OVER, GameState.VICTORY]:
                    # Check Retry Button
                    if self.game_core.btn_retry_rect.collidepoint(mouse_pos):
                        self.handle_retry_action()

                    # Check Menu Button
                    elif self.game_core.btn_menu_rect.collidepoint(mouse_pos):
                        # При возврате в меню загружаем базовые уровни из JSON обратно
                        self.game_core.level_manager.load_levels()
                        self.game_core.level_manager.reset_to_level(0)
                        self.game_core.initialize_level()
                        self.game_core.state = GameState.START

            elif event.type == pygame.KEYDOWN:
                # Global Reset
                modifiers = pygame.key.get_mods()
                if event.key == pygame.K_r and modifiers & pygame.KMOD_CTRL:
                    self.game_core.level_manager.load_levels()  # Сброс на классику
                    self.game_core.initialize_level()
                    self.game_core.state = GameState.START

                # --- УПРАВЛЕНИЕ В МЕНЮ ---
                if self.game_core.state == GameState.START:
                    if event.key == pygame.K_RETURN:
                        self.game_core.state = GameState.PLAYING
                    elif event.key == pygame.K_a:  # Новая клавиша для ИИ режима
                        self.game_core.start_ai_generation_mode()
                    elif event.key == pygame.K_ESCAPE:
                        return False

                # --- УПРАВЛЕНИЕ ПОСЛЕ ИГРЫ ---
                if self.game_core.state in [GameState.GAME_OVER, GameState.VICTORY]:
                    if event.key == pygame.K_t:  # Try Again
                        self.handle_retry_action()
                    elif event.key == pygame.K_m:  # Main Menu
                        self.game_core.level_manager.load_levels()  # Восстанавливаем базу
                        self.game_core.level_manager.reset_to_level(0)
                        self.game_core.initialize_level()
                        self.game_core.state = GameState.START
                    elif event.key == pygame.K_ESCAPE:  # Exit to menu
                        self.game_core.level_manager.load_levels()
                        self.game_core.level_manager.reset_to_level(0)
                        self.game_core.initialize_level()
                        self.game_core.state = GameState.START

                # ... (остальные состояния: PAUSED, MERCHANT, CHEST_POPUP без изменений) ...

                elif self.game_core.state == GameState.PLAYING:
                    if not self.handle_keyboard_input(event):
                        return False

        return True

    def handle_merchant_input(self, event):
        if event.key in [pygame.K_SPACE, pygame.K_m, pygame.K_ESCAPE]:
            self.game_core.state = GameState.PLAYING
            return

        # Buy items with 1, 2
        key_map = {pygame.K_1: 0, pygame.K_2: 1}
        if event.key in key_map:
            if self.game_core.buy_item(key_map[event.key]):
                print("Item Purchased")
            else:
                print("Cannot buy item")

    def is_near_merchant(self):
        """Check if player is adjacent to merchant"""
        if not self.game_core.merchant:
            return False
        p = self.game_core.player
        m = self.game_core.merchant
        dist = abs(p.row - m.row) + abs(p.col - m.col)
        return dist <= 1

    def handle_keyboard_input(self, event):
        """Handle keyboard input for testing"""

        if event.key in [pygame.K_p, pygame.K_ESCAPE]:
            self.game_core.state = GameState.PAUSED
            return True

            # Check for Merchant Interaction (M key near merchant)
        if event.key == pygame.K_m:
            if self.is_near_merchant():
                self.game_core.state = GameState.MERCHANT
                return True

        # Get modifier keys
        modifiers = pygame.key.get_mods()

        command = None

        # Handle movement and dash (WASD keys)
        if event.key in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d]:
            direction_map = {
                pygame.K_w: "up",
                pygame.K_s: "down",
                pygame.K_a: "left",
                pygame.K_d: "right",
            }

            if modifiers & pygame.KMOD_SHIFT:
                # Dash command
                command = {"action": "dash", "direction": direction_map[event.key]}
            else:
                # Normal movement
                command = {"action": "move", "direction": direction_map[event.key]}

        # Handle sword attacks (Arrow keys)
        elif event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
            direction_map = {
                pygame.K_UP: "up",
                pygame.K_DOWN: "down",
                pygame.K_LEFT: "left",
                pygame.K_RIGHT: "right",
            }

            if modifiers & pygame.KMOD_CTRL:
                # Bow attack
                command = {
                    "action": "attack_bow",
                    "direction": direction_map[event.key],
                }
            else:
                # Sword attack
                command = {
                    "action": "attack_sword",
                    "direction": direction_map[event.key],
                }

        # Handle other keys
        else:
            key_commands = {
                # Items and inventory
                pygame.K_h: {"action": "use_item", "item_type": "health"},
                pygame.K_SPACE: {"action": "use_item", "item_type": "health"},
                # Upgrades
                pygame.K_3: {"action": "upgrade", "upgrade_type": "health"},
                # Game management
                pygame.K_r: {"action": "reset"},
                pygame.K_n: (
                    {"action": "next_level"} if modifiers & pygame.KMOD_SHIFT else None
                ),
                # Debug/cheat keys
                pygame.K_c: (
                    {"action": "add_coins"} if modifiers & pygame.KMOD_CTRL else None
                ),
                pygame.K_l: (
                    {"action": "heal_player"} if modifiers & pygame.KMOD_CTRL else None
                ),
            }

            if event.key in key_commands and key_commands[event.key] is not None:
                command = key_commands[event.key]

        if command:
            # Handle special debug commands
            if command.get("action") == "add_coins":
                self.game_core.player.coins += 50
                print(f"Added 50 coins. Total: {self.game_core.player.coins}")
            elif command.get("action") == "heal_player":
                self.game_core.player.health = self.game_core.player.max_health
                print("Player healed to full health")
            elif command.get("action") == "next_level":
                if self.game_core.level_manager.next_level():
                    self.game_core.initialize_level()
                    print("Advanced to next level")
                else:
                    print("No more levels")
            else:
                # Send normal command through the interface
                self.external_interface.handle_command(
                    {"type": "game_command", "command": command}
                )

            # Print debug info
            print(f"Executing command: {command}")

        return True
