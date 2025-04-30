import importlib.resources

import pygame

from game import assets


def load_image(name: str) -> pygame.Surface:
    path = importlib.resources.files(assets).joinpath(name)
    with path.open("rb") as f:
        return pygame.image.load(f).convert_alpha()
