from collections import defaultdict
from dataclasses import dataclass, field
from itertools import count
from typing import Generator

from .components import Animal, Animation, Item, Position, Sprite, Trap, Wall


@dataclass
class Vector:
    x: int
    y: int


@dataclass
class World:
    entities: set[int] = field(default_factory=set)
    positions: dict[int, Position] = field(default_factory=dict)
    sprites: dict[int, Sprite] = field(default_factory=dict)
    animals: dict[int, Animal] = field(default_factory=dict)
    items: dict[int, Item] = field(default_factory=dict)
    walls: dict[int, Wall] = field(default_factory=dict)
    animations: dict[int, Animation] = field(default_factory=dict)
    traps: dict[int, Trap] = field(default_factory=dict)
    light: dict[tuple[int, int], float] = field(default_factory=lambda: defaultdict(lambda: 1.0))

    entities_seq: Generator[int, None, None] = field(default_factory=count, init=False)
    size: Vector = field(default_factory=lambda: Vector(32, 20))

    def clear(self):
        self.positions.clear()
        self.sprites.clear()
        self.animals.clear()
        self.items.clear()
        self.walls.clear()
        self.animations.clear()
        self.traps.clear()
        self.light.clear()

    def create_entity(self) -> int:
        eid = next(self.entities_seq)
        self.entities.add(eid)
        return eid

    def destroy_entity(self, eid: int):
        self.entities.discard(eid)
        self.positions.pop(eid, None)
        self.sprites.pop(eid, None)
        self.animals.pop(eid, None)
        self.items.pop(eid, None)
        self.walls.pop(eid, None)
        self.animations.pop(eid, None)
        self.traps.pop(eid, None)
