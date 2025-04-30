import importlib.resources
import random
import sys
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


@dataclass
class Sprite:
    image: pygame.Surface


@dataclass
class PlayerControlled:
    pass


@dataclass
class Animal:
    species: AnimalType


@dataclass
class Item:
    kind: ItemType


# === Component Stores ===
positions: Dict[int, Position] = {}
sprites: Dict[int, Sprite] = {}
animals: Dict[int, Animal] = {}
items: Dict[int, Item] = {}
player_controls: Set[int] = set()
walls: Set[int] = set()

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
    player_controls.discard(eid)


# === Pygame setup ===
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Animal Pickup ECS")
clock = pygame.time.Clock()

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


# === Spawn world ===
def spawn_random_animal(blocked_positions: Set[tuple] = None):
    animal_type = random.choice(list(AnimalType))
    eid = create_entity()
    animals[eid] = Animal(animal_type)
    sprites[eid] = Sprite(images[animal_type])

    # Find an unoccupied position
    used_positions = set(blocked_positions)
    while True:
        x = random.randint(0, GRID_WIDTH - 1)
        y = random.randint(0, GRID_HEIGHT - 1)
        if (x, y) not in used_positions:
            used_positions.add((x, y))
            break

    positions[eid] = Position(random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
    player_controls.add(eid)
    return eid


def spawn_random_items(n: int, blocked_positions: Set[tuple] = None):
    item_types = list(ItemType)
    used_positions = set(blocked_positions)

    item_coords = set()
    for _ in range(n):
        # Find an unoccupied position
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            if (x, y) not in used_positions:
                used_positions.add((x, y))
                item_coords.add((x, y))
                break

        kind = random.choice(item_types)
        eid = create_entity()
        items[eid] = Item(kind)
        sprites[eid] = Sprite(images[kind])
        positions[eid] = Position(x, y)

    return item_coords


def spawn_walls(count=15):
    wall_coords = set()
    while len(wall_coords) < count:
        x = random.randint(0, GRID_WIDTH - 1)
        y = random.randint(0, GRID_HEIGHT - 1)
        wall_coords.add((x, y))

    for x, y in wall_coords:
        eid = create_entity()
        positions[eid] = Position(x, y)
        walls.add(eid)

    return wall_coords


wall_positision = spawn_walls(25)
item_positions = spawn_random_items(30, wall_positision)
player = spawn_random_animal(wall_positision | item_positions)


# === Systems ===
def input_system(event):
    global pressed_keys

    dx, dy = 0, 0
    move = False

    if event.type == pygame.KEYDOWN:
        if event.key not in pressed_keys:
            pressed_keys.add(event.key)
            move = True
            if event.key == pygame.K_LEFT:
                dx = -1
            elif event.key == pygame.K_RIGHT:
                dx = 1
            elif event.key == pygame.K_UP:
                dy = -1
            elif event.key == pygame.K_DOWN:
                dy = 1

    elif event.type == pygame.KEYUP:
        pressed_keys.discard(event.key)

    if move:
        for eid in player_controls:
            if eid in positions:
                pos = positions[eid]
                new_x = pos.x + dx
                new_y = pos.y + dy

                # Before moving
                blocked = any(pos2.x == new_x and pos2.y == new_y for eid2, pos2 in positions.items() if eid2 in walls)

                if not blocked and 0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT:
                    pos.x, pos.y = new_x, new_y


def pickup_system():
    for player_id in player_controls:
        if player_id not in animals or player_id not in positions:
            continue
        animal_type = animals[player_id].species
        pos = positions[player_id]
        allowed = ALLOWED_PICKUPS.get(animal_type, set())

        for item_id in list(items):
            item = items[item_id]
            if item.kind not in allowed:
                continue
            if item_id in positions and positions[item_id].x == pos.x and positions[item_id].y == pos.y:
                remove_entity(item_id)


def render_system():
    screen.fill((200, 200, 200))
    draw_grid()
    for eid in entities:
        if eid in positions and eid in sprites:
            pos = positions[eid]
            img = sprites[eid].image
            screen.blit(img, (pos.x * TILE_SIZE, pos.y * TILE_SIZE))
    pygame.display.flip()


def draw_grid():
    for eid in walls:
        pos = positions[eid]
        pygame.draw.rect(
            screen, (100, 100, 100), pygame.Rect(pos.x * TILE_SIZE, pos.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        )

    for x in range(0, SCREEN_WIDTH, TILE_SIZE):
        pygame.draw.line(screen, (80, 80, 80), (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, TILE_SIZE):
        pygame.draw.line(screen, (80, 80, 80), (0, y), (SCREEN_WIDTH, y))


# === Main loop ===
while True:
    events = pygame.event.get()

    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        input_system(event)

    pickup_system()
    render_system()
    clock.tick(60)
