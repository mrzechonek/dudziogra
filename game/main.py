import importlib.resources
import math
import random
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Set

import pygame

from game import assets


def load_image(name: str) -> pygame.Surface:
    path = importlib.resources.files(assets).joinpath(name)
    with path.open("rb") as f:
        return pygame.image.load(f).convert_alpha()


# === Enums ===
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


# === Constants ===
TILE_SIZE = 128
GRID_WIDTH = 18
GRID_HEIGHT = 12
SCREEN_WIDTH = TILE_SIZE * GRID_WIDTH
SCREEN_HEIGHT = TILE_SIZE * GRID_HEIGHT

# === ECS Structures ===
next_entity_id = 0
entities: Set[int] = set()
pressed_keys = set()


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


# === Component Stores ===
positions: Dict[int, Position] = {}
sprites: Dict[int, Sprite] = {}
animals: Dict[int, Animal] = {}
items: Dict[int, Item] = {}
walls: Dict[int, Wall] = {}
animations: Dict[int, Animation] = {}

# === Allowed pickups per species ===
ALLOWED_PICKUPS = {
    AnimalType.SEAL: {ItemType.SHELL},
    AnimalType.RABBIT: {ItemType.CARROT},
    AnimalType.FISH: {ItemType.STAR},
    AnimalType.DOG: {ItemType.BONE},
    AnimalType.HEDGEHOG: {ItemType.WORM},
    AnimalType.SNAIL: {ItemType.STRAWBERRY},
}


# === ECS functions ===
def create_entity() -> int:
    global next_entity_id
    eid = next_entity_id
    next_entity_id += 1
    entities.add(eid)
    return eid


def remove_entity(eid: int):
    entities.discard(eid)
    positions.pop(eid, None)
    sprites.pop(eid, None)
    animals.pop(eid, None)
    items.pop(eid, None)
    walls.pop(eid, None)


# === Pygame setup ===
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Animal Pickup ECS")

# === Load images ===
images = {
    AnimalType.RABBIT: load_image("rabbit.png"),
    AnimalType.SEAL: load_image("seal.png"),
    AnimalType.FISH: load_image("fish.png"),
    AnimalType.DOG: load_image("dog.png"),
    AnimalType.HEDGEHOG: load_image("hedgehog.png"),
    AnimalType.SNAIL: load_image("snail.png"),
    ItemType.CARROT: load_image("carrot.png"),
    ItemType.BONE: load_image("bone.png"),
    ItemType.STAR: load_image("star.png"),
    ItemType.SHELL: load_image("shell.png"),
    ItemType.WORM: load_image("worm.png"),
    ItemType.STRAWBERRY: load_image("strawberry.png"),
}


def new_position():
    used_positions = set(positions.values())

    while True:
        position = Position(random.randint(0, GRID_WIDTH - 1), y=random.randint(0, GRID_HEIGHT - 1))

        if position not in used_positions:
            break

    return position


# === Spawn world ===
def spawn_animal():
    kind = random.choice(list(AnimalType))

    position = new_position()
    eid = create_entity()
    animals[eid] = Animal(kind)
    sprites[eid] = Sprite(images[kind], position.x * TILE_SIZE, position.y * TILE_SIZE)
    positions[eid] = position

    return eid


def spawn_items(n: int):
    for _ in range(n):
        position = new_position()
        kind = random.choice(list(ItemType))
        eid = create_entity()
        items[eid] = Item(kind)
        sprites[eid] = Sprite(images[kind], position.x * TILE_SIZE, position.y * TILE_SIZE)
        positions[eid] = position


def spawn_walls(count=15):
    for _ in range(count):
        position = new_position()
        eid = create_entity()
        walls[eid] = Wall()
        positions[eid] = position


def restart_game():
    entities.clear()
    positions.clear()
    sprites.clear()
    animals.clear()
    items.clear()
    walls.clear()
    animations.clear()

    spawn_walls(25)
    spawn_items(30)
    return spawn_animal()


# === Systems ===
def movement_system():
    new_positions = {}

    wall_positions = {}
    for eid, wall in walls.items():
        position = positions[eid]
        wall_positions[(position.x, position.y)] = eid

    for eid, position in animals.items():
        position = positions[eid]

        if position.dx == 0 and position.dy == 0:
            continue

        new_position = Position(position.x + position.dx, position.y + position.dy)

        blocked = (new_position.x, new_position.y) in wall_positions
        out_of_bounds = not (0 <= new_position.x < GRID_WIDTH and 0 <= new_position.y < GRID_HEIGHT)

        if blocked or out_of_bounds:
            position.dx = 0
            position.dy = 0
            continue

        new_positions[eid] = new_position
        animations[eid] = Animation(position.dx, position.dy)

    positions.update(new_positions)


def animation_system(delta):
    for eid, sprite in sprites.items():
        position = positions[eid]

        sprite.x = position.x * TILE_SIZE
        sprite.y = position.y * TILE_SIZE

        if animation := animations.get(eid):
            animation.step += delta / 0.08
            if animation.step >= 1:
                animations.pop(eid)
            else:
                sprite.x -= animation.dx * math.sin((1.0 - animation.step) * math.pi / 2) * TILE_SIZE
                sprite.y -= animation.dy * math.sin((1.0 - animation.step) * math.pi / 2) * TILE_SIZE


def input_system(player, event):
    global pressed_keys

    pos = positions[player]

    if event.type == pygame.KEYDOWN:
        if event.key in pressed_keys:
            # Ignore if already pressed
            return

        pressed_keys.add(event.key)
        if event.key == pygame.K_LEFT:
            pos.dx = -1
        elif event.key == pygame.K_RIGHT:
            pos.dx = 1
        elif event.key == pygame.K_UP:
            pos.dy = -1
        elif event.key == pygame.K_DOWN:
            pos.dy = 1
        else:
            return

    elif event.type == pygame.KEYUP:
        pressed_keys.clear()


def pickup_system():
    item_positions = {}

    for eid, item in items.items():
        position = positions[eid]
        item_positions[(position.x, position.y)] = eid

    for eid, animal in animals.items():
        position = positions[eid]
        pickups = ALLOWED_PICKUPS.get(animal.species, set())

        if item_eid := item_positions.get((position.x, position.y)):
            item = items[item_eid]

            if item.kind in pickups:
                animal.score += 1
                remove_entity(item_eid)


def score_system():
    for eid, animal in animals.items():
        remaining_items = next(
            (item.kind for item in items.values() if item.kind in ALLOWED_PICKUPS[animal.species]), None
        )
        if not remaining_items:
            restart_game()
            return


def render_system():
    screen.fill((200, 200, 200))
    draw_grid()
    for eid, sprite in sprites.items():
        screen.blit(sprite.surface, (sprite.x, sprite.y))

    pygame.display.flip()


def draw_grid():
    for eid, wall in walls.items():
        position = positions[eid]
        pygame.draw.rect(
            screen, (100, 100, 100), pygame.Rect(position.x * TILE_SIZE, position.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        )

    for x in range(0, SCREEN_WIDTH, TILE_SIZE):
        pygame.draw.line(screen, (80, 80, 80), (x, 0), (x, SCREEN_HEIGHT))

    for y in range(0, SCREEN_HEIGHT, TILE_SIZE):
        pygame.draw.line(screen, (80, 80, 80), (0, y), (SCREEN_WIDTH, y))
