import os

import pygame

from game.GameCore.config import GameConfig


class ResourceManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ResourceManager, cls).__new__(cls)
            cls._instance.sprites = {}
            cls._instance.load_default_assets()
        return cls._instance

    def load_image(self, filename):
        """Loads an image from the Configured Assets Directory"""
        full_path = os.path.join(GameConfig.ASSETS_DIR, filename)

        try:
            img = pygame.image.load(full_path).convert_alpha()

            # Optional: Resize to fit grid if not already
            if img.get_width() != GameConfig.CELL_SIZE:
                img = pygame.transform.scale(
                    img, (GameConfig.CELL_SIZE, GameConfig.CELL_SIZE)
                )

            return img
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return self.create_surface((255, 0, 255))

    def load_frames(self, prefix, count):
        """Helper to load sequences like 'player_idle0.png', 'player_idle1.png'..."""
        frames = []
        for i in range(count):
            filename = f"{prefix}{i}.png"
            frames.append(self.load_image(filename))
        return frames

    def load_default_assets(self):
        """Generates placeholder animations so the game runs without .png files"""

        player_idle_anim = self.load_frames("player_idle", 6)
        player_run_anim = self.load_frames("player_walk", 8)
        player_sword_anim = self.load_frames("player_attack", 6)  # unused
        player_bow_anim = self.load_frames("player_bow_attack", 9)  # unused
        player_death_anim = self.load_frames("player_death", 4)  # unused
        player_hurt_anim = self.load_frames("player_hurt", 4)  # unused

        enemy_idle_anim = self.load_frames("enemy_idle", 6)
        enemy_run_anim = self.load_frames("enemy_walk", 8)
        enemy_death_anim = self.load_frames("enemy_death", 4)  # unused
        enemy_hurt_anim = self.load_frames("enemy_hurt", 4)  # unused

        shopkeeper_idle_anim = self.load_frames("shopkeeper_idle", 9)  # unused

        sword_img = [self.load_image("sword.png")]
        bow_img = [self.load_image("bow.png")]
        arrow_img = [self.load_image("arrow.png")]
        chest_closed_img = [self.load_image("chest_closed.png")]

        chest_idle_anim = self.load_frames("chest_idle", 5)  # unused
        heal_potion_anim = self.load_frames("heal_potion_idle", 8)  # unused
        portal_anim = self.load_frames("portal_idle", 6)

        coin_anim = self.load_frames("coin_idle", 4)

        self.sprites = {
            # Player
            "player_idle": player_idle_anim,
            "player_run": player_run_anim,
            "player_attack": player_sword_anim,
            "player_bow": player_bow_anim,
            "player_death": player_death_anim,
            "player_hurt": player_hurt_anim,
            # Enemy
            "enemy_hurt": enemy_hurt_anim,
            "enemy_idle": enemy_idle_anim,
            "enemy_run": enemy_run_anim,
            "enemy_death": enemy_death_anim,
            # NPC
            "merchant_idle": shopkeeper_idle_anim,
            # Objects
            "chest_closed": chest_idle_anim,
            "chest_open": chest_closed_img,
            "portal_idle": portal_anim,
            "wall_idle": [self.load_image("wall.png")],
            "floor": [self.load_image("floor.png")],
            "coin": coin_anim,
            "health": heal_potion_anim,
            "sword": sword_img,
            "bow": bow_img,
            "arrow": arrow_img,
        }

    def create_surface(self, color, width=64, height=64, circle=False):
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        if circle:
            pygame.draw.circle(surf, color, (width // 2, height // 2), width // 2 - 2)
            pygame.draw.circle(
                surf, (0, 0, 0), (width // 2, height // 2), width // 2 - 2, 2
            )
        else:
            pygame.draw.rect(surf, color, (2, 2, width - 4, height - 4))
            pygame.draw.rect(surf, (0, 0, 0), (2, 2, width - 4, height - 4), 2)
            # Eyes to see direction
            pygame.draw.rect(surf, (255, 255, 255), (width - 20, 15, 10, 10))
        return surf

    def create_placeholder(self, color, frames=2, circle=False):
        """Creates a list of surfaces to simulate an animation"""
        anim = []
        for i in range(frames):
            # Slight color variation to simulate animation pulse
            shade = (
                min(255, color[0] + i * 10),
                min(255, color[1] + i * 10),
                min(255, color[2] + i * 10),
            )
            anim.append(self.create_surface(shade, circle=circle))
        return anim

    def get_animation(self, key):
        return self.sprites.get(key, self.sprites["player_idle"])  # Fallback
