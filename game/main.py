import pygame
from external_interface import ExternalInterface
from game_controller import GameController
from GameCore.core import GameCore
from state_monitor import StateMonitor


def main():
    """Main entry point - acts as dependency injector"""
    pygame.init()

    # Initialize core components
    game_core = GameCore()
    state_monitor = StateMonitor(game_core)
    external_interface = ExternalInterface(game_core, state_monitor)
    game_controller = GameController(game_core, state_monitor, external_interface)

    # Start the game
    game_controller.run()


if __name__ == "__main__":
    main()
