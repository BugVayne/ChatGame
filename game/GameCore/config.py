import os


class GameConfig:
    # Grid settings
    CELL_SIZE = 100

    _CORE_DIR = os.path.dirname(os.path.abspath(__file__))

    _GAME_DIR = os.path.dirname(_CORE_DIR)

    ASSETS_DIR = os.path.join(_GAME_DIR, "Assets")

    MOVE_DURATION = 350

    # Player settings
    PLAYER_MAX_HEALTH = 100
    PLAYER_START_HEALTH = 100
    PLAYER_BASE_DAMAGE = 15

    # Enemy settings
    ENEMY_BASE_HEALTH = 50
    ENEMY_BASE_DAMAGE = 10
    ENEMY_DETECTION_RANGE = 5

    # Weapon settings
    SWORD_RANGE = 2
    BOW_RANGE = 7
    HEALTH_UPGRADE_COST = [20, 40]

    # Item effects
    HEALTH_POTION_HEAL = 25
    DASH_DISTANCE = 3
    DASH_COOLDOWN = 3  # turns

    # Colors
    COLORS = {
        "grid_light": (50, 50, 70),
        "grid_dark": (60, 60, 80),
        "grid_border": (80, 80, 100),
        "player": (0, 255, 0),
        "enemy": (255, 0, 0),
        "ranged_enemy": (200, 50, 50),
        "health_item": (0, 200, 255),
        "sword": (200, 200, 200),
        "bow": (139, 69, 19),
        "coin": (255, 215, 0),
        "wall": (100, 100, 120),
        "exit": (0, 255, 255),
        "merchant": (0, 150, 255),
        "chest": (210, 180, 140),
        "ui_text": (255, 255, 255),
        "ui_secondary": (200, 200, 200),
    }


class GameState:
    START = "start"
    PLAYING = "playing"
    PAUSED = "paused"
    MERCHANT = "merchant"
    CHEST_POPUP = "chest_popup"
    GAME_OVER = "game_over"
    VICTORY = "victory"


class UIStyle:
    BG_COLOR = (40, 35, 35)  # Dark Slate/Brown
    BORDER_COLOR = (180, 160, 100)  # Gold/Brass
    TEXT_COLOR = (220, 220, 220)  # Off-white
    TITLE_FONT_SIZE = 60
    BODY_FONT_SIZE = 30
    BORDER_WIDTH = 4
    PADDING = 40
