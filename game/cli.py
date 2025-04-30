import pygame
import sys

from game.main import (
    animation_system,
    input_system,
    movement_system,
    pickup_system,
    render_system,
    restart_game,
    score_system,
)


def main():
    player = restart_game()
    clock = pygame.time.Clock()

    while True:
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            input_system(player, event)

        dt = clock.tick(60) / 1000.0
        movement_system()
        animation_system(dt)
        pickup_system()
        score_system()
        render_system()
