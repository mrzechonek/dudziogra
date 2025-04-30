import pygame

from game.main import Game


def main():
    pygame.init()
    clock = pygame.time.Clock()

    game = Game()

    while True:
        events = pygame.event.get()
        delta = clock.tick(60) / 1000.0
        game.update(delta, events)
