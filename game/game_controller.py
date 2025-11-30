import pygame
import threading

from game.GameCore.config import GameState


class GameController:
    def __init__(self, game_core, state_monitor, external_interface):
        self.game_core = game_core
        self.state_monitor = state_monitor
        self.external_interface = external_interface
        self.stream_thread = threading.Thread(target=start_stream_server, args=(self,), daemon=True)
        self.stream_thread.start()
        self.start_websocket_server()

        self.turn_timer = 0
        self.turn_interval = 3000

    def start_websocket_server(self):
        """Start WebSocket server in a separate thread"""
        ws_thread = threading.Thread(
            target=self.external_interface.start_websocket_server,
            daemon=True
        )
        ws_thread.start()

    def run(self):
        clock = pygame.time.Clock()
        running = True

        while running:
            dt = clock.tick(60)

            # Handle Auto-Turn (Only when playing)
            if self.game_core.state == GameState.PLAYING:
                self.turn_timer += dt
                if self.turn_timer >= self.turn_interval:
                    self.turn_timer = 0
                    self.execute_game_turn()

            # Render
            self.game_core.render()

            # Input
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
                if self.game_core.state in [GameState.GAME_OVER, GameState.VICTORY]:
                    mouse_pos = pygame.mouse.get_pos()

                    # Check Retry Button
                    if self.game_core.btn_retry_rect.collidepoint(mouse_pos):
                        self.handle_retry_action()

                    # Check Menu Button
                    elif self.game_core.btn_menu_rect.collidepoint(mouse_pos):
                        self.game_core.state = GameState.START
            elif event.type == pygame.KEYDOWN:
                # Global Reset
                modifiers = pygame.key.get_mods()
                if event.key == pygame.K_r and modifiers & pygame.KMOD_CTRL:
                    self.game_core.initialize_level()
                    self.game_core.state = GameState.START

                # Route Input based on State
                if self.game_core.state == GameState.START:
                    if event.key == pygame.K_RETURN:
                        self.game_core.state = GameState.PLAYING
                    elif event.key == pygame.K_ESCAPE:
                        return False

                if self.game_core.state in [GameState.GAME_OVER, GameState.VICTORY]:
                    if event.key == pygame.K_t:  # Try Again
                        self.handle_retry_action()
                    elif event.key == pygame.K_m:  # Main Menu
                        self.game_core.state = GameState.START
                    elif event.key == pygame.K_ESCAPE:  # Exit to menu
                        self.game_core.state = GameState.START

                elif self.game_core.state == GameState.PAUSED:
                    if event.key in [pygame.K_p, pygame.K_ESCAPE]:
                        self.game_core.state = GameState.PLAYING
                    elif event.key == pygame.K_q:
                        return False

                elif self.game_core.state == GameState.MERCHANT:
                    self.handle_merchant_input(event)

                elif self.game_core.state == GameState.PLAYING:
                    if not self.handle_keyboard_input(event):
                        return False

        return True

    def handle_merchant_input(self, event):
        if event.key in [pygame.K_SPACE, pygame.K_m, pygame.K_ESCAPE]:
            self.game_core.state = GameState.PLAYING
            return

        # Buy items with 1, 2, 3, 4
        key_map = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3}
        if event.key in key_map:
            if self.game_core.buy_item(key_map[event.key]):
                print("Item Purchased")
            else:
                print("Cannot buy item")

    def is_near_merchant(self):
        """Check if player is adjacent to merchant"""
        if not self.game_core.merchant: return False
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
                pygame.K_d: "right"
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
                pygame.K_RIGHT: "right"
            }

            if modifiers & pygame.KMOD_CTRL:
                # Bow attack
                command = {"action": "attack_bow", "direction": direction_map[event.key]}
            else:
                # Sword attack
                command = {"action": "attack_sword", "direction": direction_map[event.key]}

        # Handle other keys
        else:
            key_commands = {
                # Items and inventory
                pygame.K_h: {"action": "use_item", "item_type": "health"},
                pygame.K_SPACE: {"action": "use_item", "item_type": "health"},

                # Upgrades
                pygame.K_1: {"action": "upgrade", "upgrade_type": "sword"},
                pygame.K_2: {"action": "upgrade", "upgrade_type": "bow"},
                pygame.K_3: {"action": "upgrade", "upgrade_type": "health"},

                # Game management
                pygame.K_r: {"action": "reset"},
                pygame.K_n: {"action": "next_level"} if modifiers & pygame.KMOD_SHIFT else None,

                # Debug/cheat keys
                pygame.K_c: {"action": "add_coins"} if modifiers & pygame.KMOD_CTRL else None,
                pygame.K_l: {"action": "heal_player"} if modifiers & pygame.KMOD_CTRL else None,
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
                self.external_interface.handle_command({
                    "type": "game_command",
                    "command": command
                })

            # Print debug info
            print(f"Executing command: {command}")

        return True


import io
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from PIL import Image
import numpy as np


class GameStreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()

            last_frame_time = 0
            frame_interval = 0.01

            while True:
                try:
                    current_time = time.time()
                    if current_time - last_frame_time < frame_interval:
                        time.sleep(0.01)
                        continue

                    last_frame_time = current_time

                    # Get the game screen surface
                    screen = self.server.game_controller.game_core.screen

                    # Convert pygame surface to numpy array (much faster)
                    pixel_array = pygame.surfarray.array3d(screen)

                    # Convert to PIL Image
                    img = Image.fromarray(np.transpose(pixel_array, (1, 0, 2)))

                    # Compress to JPEG with lower quality for speed
                    buf = io.BytesIO()
                    img.save(buf, format='JPEG', quality=70, optimize=True)
                    frame = buf.getvalue()

                    self.wfile.write(b'--frame\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')

                except (BrokenPipeError, ConnectionResetError):
                    # Client disconnected
                    break
                except Exception as e:
                    print(f"Stream error: {e}")
                    time.sleep(0.1)  # Prevent tight loop on error

    def log_message(self, format, *args):
        # Suppress normal HTTP logging to reduce output spam
        pass


class GameStreamServer(HTTPServer):
    def __init__(self, game_controller):
        super().__init__(('localhost', 8080), GameStreamHandler)
        self.game_controller = game_controller
        self.timeout = 1  # Set timeout to prevent blocking


def start_stream_server(game_controller):
    server = GameStreamServer(game_controller)
    print("Game stream server started at http://localhost:8080/stream")
    server.serve_forever()