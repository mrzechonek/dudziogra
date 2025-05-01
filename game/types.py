from enum import Enum, auto


class AnimalType(Enum):
    RABBIT = auto()
    SEAL = auto()
    FISH = auto()
    DOG = auto()
    SNAIL = auto()
    HEDGEHOG = auto()


class ItemType(Enum):
    CARROT = auto()
    BONE = auto()
    STAR = auto()
    SHELL = auto()
    WORM = auto()
    STRAWBERRY = auto()


class TrapType(Enum):
    SPIDER = auto()
    # PIT = auto()
    BALL = auto()


class WallType(Enum):
    FENCE = auto()
