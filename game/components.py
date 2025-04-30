from dataclasses import dataclass

import pygame

from game.types import AnimalType, ItemType


@dataclass
class Wall:
    pass


@dataclass
class Position:
    x: int
    y: int
    dx: int = 0
    dy: int = 0

    def __hash__(self):
        return hash((self.x, self.y))


@dataclass
class Animation:
    dx: int = 0
    dy: int = 0
    step: float = 0


@dataclass
class Sprite:
    surface: pygame.Surface
    x: int = None
    y: int = None


@dataclass
class Animal:
    species: AnimalType
    score: int = 0


@dataclass
class Item:
    kind: ItemType
