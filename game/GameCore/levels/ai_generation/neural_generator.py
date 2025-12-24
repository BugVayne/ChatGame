import os

import torch
import torch.nn as nn
import torch.optim as optim

# Define tile types for the AI to learn
# 0 = Empty, 1 = Wall
NUM_TILES = 2


class DungeonGenNet(nn.Module):
    def __init__(self, latent_dim=32, height=10, width=16):
        super(DungeonGenNet, self).__init__()
        self.height = height
        self.width = width
        self.latent_dim = latent_dim

        # Project latent vector to a small spatial map
        self.l1 = nn.Sequential(nn.Linear(latent_dim, 128 * 2 * 4), nn.ReLU())

        # Upsample to full grid size
        self.conv_blocks = nn.Sequential(
            nn.BatchNorm2d(128),
            # Upsample 1: 2x4 -> 5x8 (approx)
            nn.ConvTranspose2d(
                128, 64, kernel_size=4, stride=2, padding=1, output_padding=(1, 0)
            ),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            # Upsample 2: 5x8 -> 10x16
            nn.ConvTranspose2d(64, 32, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            # Final Layer: Map to Tile Types (Walls vs Empty)
            nn.Conv2d(32, NUM_TILES, kernel_size=3, padding=1),
        )

    def forward(self, z):
        x = self.l1(z)
        x = x.view(-1, 128, 2, 4)  # Reshape to tensor
        x = self.conv_blocks(x)
        return x


class AITrainer:
    def __init__(self):
        self.height = 10
        self.width = 16
        self.latent_dim = 32
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.model = DungeonGenNet(self.latent_dim, self.height, self.width).to(
            self.device
        )
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)

        # Buffer to store state for training step
        self.current_log_prob = None
        self.current_z = None
        self.current_grid_snapshot = None

    def generate_layout(self):
        """Generates a raw grid of 0s (Floor) and 1s (Walls)"""
        z = torch.randn(1, self.latent_dim).to(self.device)
        logits = self.model(z)
        probs = torch.softmax(logits, dim=1)

        dist = torch.distributions.Categorical(probs.permute(0, 2, 3, 1))
        actions = dist.sample()

        log_prob = dist.log_prob(actions).sum()
        self.current_log_prob = log_prob
        self.current_z = z

        # Convert to python list
        grid = actions.squeeze().cpu().numpy().tolist()
        self.current_grid_snapshot = grid
        return grid

    def calculate_void_penalty(self, grid):
        """
        Analyzes the grid for 3x3 homogenous blocks.
        Returns a positive float representing the total penalty.
        """
        penalty = 0.0
        rows = len(grid)
        cols = len(grid[0])

        # Scan every possible 3x3 block
        for r in range(rows - 2):
            for c in range(cols - 2):
                block_sum = 0
                for i in range(3):
                    for j in range(3):
                        block_sum += grid[r + i][c + j]

                # Case A: Sum is 0 -> All cells are 0 (Floor Void)
                if block_sum == 0:
                    penalty += 0.2

                    # Case B: Sum is 9 -> All cells are 1 (Wall Void/Block)
                elif block_sum == 9:
                    penalty += 0.2

        return penalty

    def train_step(self, user_score):
        """
        REINFORCE Algorithm with Structural Penalties.
        """
        if self.current_log_prob is None or self.current_grid_snapshot is None:
            return 0.0, 0.0

        self.optimizer.zero_grad()

        # 1. Base Reward
        base_reward = user_score - 5.0

        # 2. Structural Penalty
        struct_penalty = self.calculate_void_penalty(self.current_grid_snapshot)

        # 3. Final Reward
        final_reward = base_reward - struct_penalty

        # Loss = -log_prob * reward
        loss = -self.current_log_prob * final_reward

        loss.backward()
        self.optimizer.step()

        return loss.item(), struct_penalty

    def save_model(self, path="dungeon_brain.pth"):
        torch.save(self.model.state_dict(), path)
        print("Brain saved.")

    def load_model(self, path="dungeon_brain.pth"):
        if os.path.exists(path):
            try:
                self.model.load_state_dict(torch.load(path))
                self.model.eval()
                print("Brain loaded.")
            except Exception as e:
                print(f"Error loading brain: {e}")
        else:
            print("No existing brain found, starting fresh.")
