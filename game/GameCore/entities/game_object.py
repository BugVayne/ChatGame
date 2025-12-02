import pygame
from game.GameCore.config import GameConfig
from game.GameCore.resource_manager import ResourceManager


class GameObject:
    def __init__(self, row, col, object_type):
        self.row = row
        self.col = col
        self.type = object_type
        self.health = 100

        self.cell_size = GameConfig.CELL_SIZE

        # 1. First, calculate the starting visual position
        self.visual_x = col * self.cell_size
        self.visual_y = row * self.cell_size

        # 2. Then, initialize the Movement Interpolation variables using those values
        self.target_visual_x = self.visual_x
        self.target_visual_y = self.visual_y
        self.start_visual_x = self.visual_x
        self.start_visual_y = self.visual_y

        self.move_timer = 0
        self.move_duration = 350  # Time in ms to move 1 tile (Higher = Slower)
        self.is_moving = False

        # 3. Finally, setup Animation State
        self.resources = ResourceManager()
        self.state = "idle"  # idle, run, attack
        self.animation_key = f"{object_type}_idle"  # e.g. "player_idle"
        self.frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 150  # ms per frame
        self.facing_right = True

    def get_position(self):
        return (self.row, self.col)

    def set_position(self, row, col):
        self.row = row
        self.col = col

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)

        # This constructs "player_hurt" or "enemy_hurt" dynamically
        hurt_key = f"{self.type}_hurt"

        # Check if this animation exists before trying to play it
        if self.resources.get_animation(hurt_key):
            # Play for 400ms
            self.play_animation(hurt_key, duration_ms=400)
        return self.health <= 0

    def is_alive(self):
        return self.health > 0

    def play_animation(self, key_name, duration_ms=500):
        """Forces an animation to play for a set duration"""
        self.animation_key = key_name
        self.frame_index = 0
        self.animation_timer = 0
        self.locked_animation_timer = duration_ms

    def draw_health_bar(self, screen, x, y, cell_size, current_health, max_health):
        health_width = (current_health / max_health) * (cell_size - 10)
        pygame.draw.rect(screen, (255, 0, 0), (x + 5, y + 5, cell_size - 10, 5))
        pygame.draw.rect(screen, (0, 255, 0), (x + 5, y + 5, health_width, 5))

    def update_visuals(self, dt):
        """Called every frame to smooth movement and update animation"""

        # --- 1. SMOOTH MOVEMENT LOGIC (Ease-In-Out) ---

        # Calculate where we SHOULD be physically
        dest_x = self.col * self.cell_size
        dest_y = self.row * self.cell_size

        # Detect if a NEW movement command just happened
        if dest_x != self.target_visual_x or dest_y != self.target_visual_y:
            self.start_visual_x = self.visual_x
            self.start_visual_y = self.visual_y
            self.target_visual_x = dest_x
            self.target_visual_y = dest_y
            self.move_timer = 0
            self.is_moving = True

            # Face direction immediately upon input
            if dest_x > self.start_visual_x:
                self.facing_right = True
            elif dest_x < self.start_visual_x:
                self.facing_right = False

        # Apply Interpolation if moving
        if self.is_moving:
            self.move_timer += dt

            # Calculate percentage of completion (0.0 to 1.0)
            t = self.move_timer / self.move_duration

            if t >= 1.0:
                # Movement finished
                self.visual_x = self.target_visual_x
                self.visual_y = self.target_visual_y
                self.is_moving = False
            else:
                # --- SMOOTHSTEP FORMULA ---
                # This creates the "Slow Start, Fast Middle, Slow End" curve
                smooth_t = t * t * (3 - 2 * t)

                # Lerp: Start + (End - Start) * smooth_t
                self.visual_x = self.start_visual_x + (self.target_visual_x - self.start_visual_x) * smooth_t
                self.visual_y = self.start_visual_y + (self.target_visual_y - self.start_visual_y) * smooth_t

        # --- 2. ANIMATION LOGIC ---

        # Handle Locked Animations (Attack/Hurt)
        if hasattr(self, 'locked_animation_timer') and self.locked_animation_timer > 0:
            self.locked_animation_timer -= dt

            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                frames = self.resources.get_animation(self.animation_key)
                if frames and self.frame_index < len(frames) - 1:
                    self.frame_index += 1

            # Unlock when done
            if self.locked_animation_timer <= 0:
                self.animation_timer = 0
                self.frame_index = 0
            else:
                return  # Skip standard logic

        # Handle Standard Animations (Run/Idle)
        prev_key = self.animation_key

        if self.is_moving:
            self.state = "run"
            self.animation_key = f"{self.type}_run"
        else:
            self.state = "idle"
            self.animation_key = f"{self.type}_idle"

        if prev_key != self.animation_key:
            self.frame_index = 0
            self.animation_timer = 0

        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            frames = self.resources.get_animation(self.animation_key)
            if frames:
                self.frame_index = (self.frame_index + 1) % len(frames)

    def draw(self, screen):
        frames = self.resources.get_animation(self.animation_key)

        # Safety check
        if not frames: return
        if self.frame_index >= len(frames): self.frame_index = 0

        image = frames[self.frame_index]

        # Flip image if facing left
        if not self.facing_right:
            image = pygame.transform.flip(image, True, False)

        # Scale to cell size if needed
        if image.get_width() != self.cell_size:
            image = pygame.transform.scale(image, (self.cell_size, self.cell_size))

        # Draw Shadow
        shadow_rect = pygame.Rect(self.visual_x + 10, self.visual_y + self.cell_size - 10, self.cell_size - 20, 5)
        pygame.draw.ellipse(screen, (0, 0, 0, 100), shadow_rect)

        # Draw Sprite
        screen.blit(image, (self.visual_x, self.visual_y))


        if hasattr(self, 'health') and hasattr(self, 'max_health') and self.health < self.max_health:
            self.draw_health_bar(screen, self.visual_x, self.visual_y, self.cell_size, self.health, self.max_health)