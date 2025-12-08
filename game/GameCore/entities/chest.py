from game.GameCore.entities.game_object import GameObject


class Chest(GameObject):
    def __init__(self, row, col, contents):
        super().__init__(row, col, "chest")
        self.contents = contents
        self.opened = False
        # Set initial key
        self.animation_key = "chest_closed"

    def open(self):
        if not self.opened:
            self.opened = True
            return self.contents
        return {}

    def update_visuals(self, dt):
        """
        Override GameObject logic to prevent it from forcing
        keys like 'chest_idle' or 'chest_run'.
        """

        # 1. Update State
        if self.opened:
            self.animation_key = "chest_open"
        else:
            self.animation_key = "chest_closed"

        # 2. Advance Animation Frames
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0

            frames = self.resources.get_animation(self.animation_key)
            if frames:
                # Loop the animation
                self.frame_index = (self.frame_index + 1) % len(frames)

                # OPTIONAL: If you want the chest to stay open on the last frame
                # instead of looping (if you add an opening animation later):
                # if self.opened and self.frame_index == len(frames) - 1:
                #     self.frame_index = len(frames) - 1

    def draw(self, screen):
        # Just call super, the keys are now handled correctly in update_visuals
        super().draw(screen)
