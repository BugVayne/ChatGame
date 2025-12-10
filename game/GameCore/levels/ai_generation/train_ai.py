import os
import sys

import pygame

# Setup Paths
sys.path.append(os.getcwd())

from game.GameCore.config import GameConfig
from game.GameCore.entities.chest import Chest
from game.GameCore.entities.enemy import Enemy
from game.GameCore.entities.exit_portal import ExitPortal
from game.GameCore.entities.item import Item
from game.GameCore.entities.merchant import Merchant
from game.GameCore.entities.player import Player
from game.GameCore.entities.wall import Wall
from game.GameCore.levels.ai_generation.hybrid_generator import HybridLevelGenerator
from game.GameCore.levels.ai_generation.neural_generator import AITrainer
from game.GameCore.resource_manager import ResourceManager

# Import constants directly to match generator
# 0-5 defined in generator, plus these:
MERCHANT = 6
CHEST = 7
POTION = 8
ARROWS = 9
COIN = 10
WALL = 1
ENEMY = 2
PLAYER = 4
EXIT = 5


class AITrainingInterface:
    def __init__(self):
        pygame.init()
        self.width = 16 * GameConfig.CELL_SIZE
        self.height = 10 * GameConfig.CELL_SIZE + 100
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("AI Dungeon Trainer v2")

        self.font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 18)
        self.resource_manager = ResourceManager()

        # Initialize AI
        self.trainer = AITrainer()
        self.trainer.load_model()

        self.generator = HybridLevelGenerator(self.trainer)

        self.current_level_grid = None
        self.generation_count = 0
        self.last_loss = 0.0
        self.last_penalty = 0.0

        self.generate_new_level()

    def generate_new_level(self):
        self.current_level_grid = self.generator.generate_with_ai()
        self.generation_count += 1

    def handle_input(self, score):
        print(f"Rating Level: {score}/9")

        # Pass score to AI
        loss, penalty = self.trainer.train_step(score)

        self.last_loss = loss
        self.last_penalty = penalty

        if self.generation_count % 10 == 0:
            self.trainer.save_model()

        self.generate_new_level()

    def draw_level(self):
        offset_y = 100
        grid = self.current_level_grid

        # Draw Floor
        floor_anim = self.resource_manager.get_animation("floor")
        floor_img = floor_anim[0] if floor_anim else None
        if floor_img:
            floor_img = pygame.transform.scale(
                floor_img, (GameConfig.CELL_SIZE, GameConfig.CELL_SIZE)
            )

        for r in range(10):
            for c in range(16):
                x = c * GameConfig.CELL_SIZE
                y = r * GameConfig.CELL_SIZE + offset_y

                if floor_img:
                    self.screen.blit(floor_img, (x, y))

                cell = grid[r][c]
                entity = None

                # Visual placeholders
                if cell == WALL:
                    entity = Wall(r, c)
                elif cell == PLAYER:
                    entity = Player(r, c)
                elif cell == ENEMY:
                    entity = Enemy(r, c)
                elif cell == EXIT:
                    entity = ExitPortal(r, c)
                elif cell == MERCHANT:
                    entity = Merchant(r, c)
                elif cell == CHEST:
                    entity = Chest(r, c, {})
                elif cell == POTION:
                    entity = Item(r, c, "health", 0)
                elif cell == ARROWS:
                    entity = Item(r, c, "arrows_item", 5)
                elif cell == COIN:
                    entity = Item(r, c, "coin", 10)

                if entity:
                    entity.visual_y += offset_y
                    entity.draw(self.screen)

    def draw_ui(self):
        pygame.draw.rect(self.screen, (40, 40, 50), (0, 0, self.width, 100))

        pen_text = f"Void Pen: {self.last_penalty:.2f}"
        title = self.font.render(
            f"Gen #{self.generation_count} | Loss: {self.last_loss:.4f} | {pen_text}",
            True,
            (255, 255, 255),
        )
        self.screen.blit(title, (20, 20))

        instr = self.small_font.render(
            "Rate Layout: 1 (Bad) to 9 (Perfect). 0 to Quit.", True, (200, 200, 200)
        )
        self.screen.blit(instr, (20, 60))

    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            clock.tick(30)
            self.screen.fill((20, 20, 30))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        score = event.key - pygame.K_0
                        self.handle_input(score)
                    elif event.key == pygame.K_0:
                        self.trainer.save_model()
                        running = False

            self.draw_ui()
            self.draw_level()
            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    app = AITrainingInterface()
    app.run()
