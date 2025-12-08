import json
import os
import sys

import pygame

# 1. Setup Python Path to find game modules
sys.path.append(os.getcwd())

from game.GameCore.config import GameConfig
from game.GameCore.entities.chest import Chest
from game.GameCore.entities.enemy import DummyEnemy, Enemy, RangedEnemy
from game.GameCore.entities.exit_portal import ExitPortal
from game.GameCore.entities.item import Item
from game.GameCore.entities.player import Player
from game.GameCore.entities.wall import Wall
from game.GameCore.resource_manager import ResourceManager


class LevelViewer:
    def __init__(self, folder_path="generated_levels"):
        pygame.init()
        pygame.font.init()

        # --- FIX START ---
        # Initialize a temporary window so ResourceManager can convert images.
        # This will be resized immediately once a level loads.
        self.screen = pygame.display.set_mode((800, 600))
        # --- FIX END ---

        self.folder_path = folder_path
        self.files = self.get_json_files()
        self.current_index = 0

        self.cell_size = GameConfig.CELL_SIZE
        self.resource_manager = ResourceManager()
        self.font = pygame.font.SysFont("Arial", 24)

        self.running = True

        self.entities = []
        self.current_level_data = None
        self.current_filename = ""

        if not self.files:
            print(f"No JSON files found in '{folder_path}'")
            print("Please run 'generate_level_tool.py' first.")
            self.running = False
        else:
            self.load_level(self.current_index)

    def get_json_files(self):
        """Get list of .json files in folder"""
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)
            return []

        files = [f for f in os.listdir(self.folder_path) if f.endswith(".json")]
        files.sort()
        return files

    def load_level(self, index):
        """Parses the JSON and creates Game Entities for visualization"""
        if not self.files:
            return

        self.current_index = index % len(self.files)
        filename = self.files[self.current_index]
        self.current_filename = filename

        path = os.path.join(self.folder_path, filename)

        try:
            with open(path, "r") as f:
                raw_data = json.load(f)

            # generated files are { "ID": { DATA } }. Get the inner data.
            key = list(raw_data.keys())[0]
            data = raw_data[key]
            self.current_level_data = data

            # This will resize the window to fit the specific level
            self.setup_window(data["grid_width"], data["grid_height"])
            self.create_entities(data)

            print(f"Loaded: {filename}")

        except Exception as e:
            print(f"Error loading {filename}: {e}")

    def setup_window(self, grid_w, grid_h):
        """Resizes window based on level size"""
        width = grid_w * self.cell_size
        height = grid_h * self.cell_size + 60  # +60px for UI Header

        # Re-initialize the screen with exact dimensions
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(f"Level Viewer - {self.current_filename}")

    def create_entities(self, data):
        """Instantiates entities using the GameCore logic but purely for display"""
        self.entities = []

        # Walls
        for w in data.get("walls", []):
            self.entities.append(Wall(w[0], w[1]))

        # Items
        for i in data.get("items", []):
            pos = i["position"]
            self.entities.append(Item(pos[0], pos[1], i["type"], i.get("value", 0)))

        # Enemies
        for e in data.get("enemies", []):
            pos = e["position"]
            etype = e["type"]
            if etype == "ranged":
                self.entities.append(RangedEnemy(pos[0], pos[1]))
            elif etype == "dummy":
                self.entities.append(DummyEnemy(pos[0], pos[1]))
            else:
                self.entities.append(Enemy(pos[0], pos[1], "melee"))

        # Chests
        for c in data.get("chests", []):
            pos = c["position"]
            self.entities.append(Chest(pos[0], pos[1], {}))

        # Exit
        if "exit" in data:
            ex = data["exit"]
            self.entities.append(ExitPortal(ex[0], ex[1]))

        # Player (Visual only)
        if "player_start" in data:
            p = data["player_start"]
            self.entities.append(Player(p[0], p[1]))

    def draw(self):
        if not self.screen:
            return

        self.screen.fill((30, 30, 40))

        # 1. Draw UI Header
        header_rect = pygame.Rect(0, 0, self.screen.get_width(), 60)
        pygame.draw.rect(self.screen, (20, 20, 25), header_rect)
        pygame.draw.line(
            self.screen, (100, 100, 100), (0, 60), (self.screen.get_width(), 60)
        )

        txt = self.font.render(
            f"File: {self.current_filename} ({self.current_index + 1}/{len(self.files)})",
            True,
            (255, 255, 255),
        )
        self.screen.blit(txt, (20, 15))

        help_txt = self.font.render("<- PREV   |   NEXT ->", True, (255, 215, 0))
        self.screen.blit(
            help_txt, (self.screen.get_width() - help_txt.get_width() - 20, 15)
        )

        # 2. Draw Grid Offset
        offset_y = 60

        # Draw Floor
        floor_anim = self.resource_manager.get_animation("floor")
        floor_img = floor_anim[0] if floor_anim else None

        if floor_img:
            floor_img = pygame.transform.scale(
                floor_img, (self.cell_size, self.cell_size)
            )

        rows = self.current_level_data["grid_height"]
        cols = self.current_level_data["grid_width"]

        for r in range(rows):
            for c in range(cols):
                x = c * self.cell_size
                y = r * self.cell_size + offset_y
                if floor_img:
                    self.screen.blit(floor_img, (x, y))
                else:
                    pygame.draw.rect(
                        self.screen,
                        (50, 50, 60),
                        (x, y, self.cell_size, self.cell_size),
                        1,
                    )

        # 3. Draw Entities
        for entity in self.entities:
            # Manually adjust visual_y for drawing because GameObject logic assumes (0,0) screen
            original_y = entity.visual_y
            entity.visual_y += offset_y

            # Use existing draw method
            entity.draw(self.screen)

            # Reset so it doesn't drift
            entity.visual_y = original_y

        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()

        while self.running:
            clock.tick(30)  # 30 FPS is enough for a viewer

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT:
                        self.load_level(self.current_index + 1)
                    elif event.key == pygame.K_LEFT:
                        self.load_level(self.current_index - 1)
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False

            self.draw()

        pygame.quit()


if __name__ == "__main__":
    viewer = LevelViewer()
    viewer.run()
