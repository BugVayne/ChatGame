import time


class StateMonitor:
    def __init__(self, game_core):
        self.game_core = game_core
        self.previous_state = self.get_current_state()
        self.last_event_time = 0
        self.event_cooldown = 0.5

    def get_current_state(self):
        """Get current game state"""
        alive_enemies = [e for e in self.game_core.enemies if e.health > 0]

        return {
            "turn": self.game_core.turn_count,
            "player_health": self.game_core.player.health,
            "player_position": (self.game_core.player.row, self.game_core.player.col),
            "inventory": self.game_core.player.inventory.copy(),
            "enemies_count": len(alive_enemies),
            "enemies_positions": [(e.row, e.col) for e in alive_enemies],
            "items_count": len(self.game_core.items),
            "items_positions": [(i.row, i.col, i.type) for i in self.game_core.items],
        }

    def check_events(self):
        """Check for state changes and generate events"""
        current_time = time.time()
        if current_time - self.last_event_time < self.event_cooldown:
            return []

        current_state = self.get_current_state()
        events = []

        # Player health changes
        if current_state["player_health"] < self.previous_state["player_health"]:
            events.append(
                {
                    "type": "player_damaged",
                    "health": current_state["player_health"],
                    "damage": self.previous_state["player_health"]
                    - current_state["player_health"],
                    "position": current_state["player_position"],
                }
            )

        # Low health warning
        if current_state["player_health"] < 30 <= self.previous_state["player_health"]:
            events.append(
                {
                    "type": "low_health_warning",
                    "health": current_state["player_health"],
                    "urgency": "high",
                }
            )

        # Item collection
        for item_type in current_state["inventory"]:
            if (
                current_state["inventory"][item_type]
                > self.previous_state["inventory"][item_type]
            ):
                events.append(
                    {
                        "type": "item_collected",
                        "item_type": item_type,
                        "count": current_state["inventory"][item_type],
                        "position": current_state["player_position"],
                    }
                )

        # Enemy defeat
        if current_state["enemies_count"] < self.previous_state["enemies_count"]:
            events.append(
                {"type": "enemy_defeated", "remaining": current_state["enemies_count"]}
            )

        # Enemy proximity
        closest_enemy_distance = self.get_closest_enemy_distance()
        if 0 < closest_enemy_distance <= 2:
            events.append(
                {
                    "type": "enemy_nearby",
                    "distance": closest_enemy_distance,
                    "urgency": "high" if closest_enemy_distance == 1 else "medium",
                }
            )

        # Turn completion
        if current_state["turn"] > self.previous_state["turn"]:
            events.append({"type": "turn_completed", "turn": current_state["turn"]})

        self.previous_state = current_state
        if events:
            self.last_event_time = current_time

        return events

    def get_closest_enemy_distance(self):
        """Get distance to closest enemy"""
        alive_enemies = [e for e in self.game_core.enemies if e.health > 0]
        if not alive_enemies:
            return -1

        player_row, player_col = self.game_core.player.row, self.game_core.player.col
        min_distance = float("inf")

        for enemy in alive_enemies:
            distance = abs(player_row - enemy.row) + abs(player_col - enemy.col)
            min_distance = min(min_distance, distance)

        return min_distance
