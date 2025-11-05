class GameConfig:
    # Grid settings
    CELL_SIZE = 80

    # Player settings
    PLAYER_MAX_HEALTH = 100
    PLAYER_START_HEALTH = 100
    PLAYER_BASE_DAMAGE = 15

    # Enemy settings
    ENEMY_BASE_HEALTH = 50
    ENEMY_BASE_DAMAGE = 10
    ENEMY_DETECTION_RANGE = 5

    # Weapon settings
    SWORD_RANGE = 3
    BOW_RANGE = 5
    SWORD_UPGRADE_COST = [10, 25, 50]  # Cost for each level
    BOW_UPGRADE_COST = [15, 30, 60]
    HEALTH_UPGRADE_COST = [20, 40]

    # Item effects
    HEALTH_POTION_HEAL = 25
    DASH_DISTANCE = 3
    DASH_COOLDOWN = 3  # turns

    # Colors
    COLORS = {
        'grid_light': (50, 50, 70),
        'grid_dark': (60, 60, 80),
        'grid_border': (80, 80, 100),
        'player': (0, 255, 0),
        'enemy': (255, 0, 0),
        'ranged_enemy': (200, 50, 50),
        'health_item': (0, 200, 255),
        'sword': (200, 200, 200),
        'bow': (139, 69, 19),
        'coin': (255, 215, 0),
        'wall': (100, 100, 120),
        'exit': (0, 255, 255),
        'merchant': (0, 150, 255),
        'chest': (210, 180, 140),
        'ui_text': (255, 255, 255),
        'ui_secondary': (200, 200, 200)
    }
