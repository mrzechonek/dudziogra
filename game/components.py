from dataclasses import dataclass

import pygame

from .types import AnimalType, ItemType, TrapType, WallType


@dataclass
class Wall:
    kind: WallType = WallType.FENCE


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
    kind: AnimalType
    x: int = None
    y: int = None


@dataclass
class Animal:
    kind: AnimalType
    score: int = 0


@dataclass
class Item:
    kind: ItemType


@dataclass
class Trap:
    kind: TrapType
    step: int = 0
