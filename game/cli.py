import pygame
import asyncio

from game.main import Game


async def loop():
    pygame.init()
    clock = pygame.time.Clock()

    game = Game()

    while True:
        events = pygame.event.get()
        delta = clock.tick() / 1000.0
        game.update(delta, events)
        await asyncio.sleep(0)


def main():
    asyncio.run(loop())
