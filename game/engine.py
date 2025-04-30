import math
import random
import sys
from dataclasses import dataclass, field

import pygame

from game.assets import load_images
from game.components import Animal, Animation, Item, Position, Sprite, Wall
from game.types import AnimalType, ItemType
from game.world import World


class System:
    def __init__(self, game):
        self.game = game

    @property
    def world(self):
        return self.game.world

    def update(self, delta, events):
        raise NotImplementedError()

    def restart(self):
        pass


class MovementSystem(System):
    def restart(self):
        self.wall_positions = {}
        for eid, wall in self.world.walls.items():
            position = self.world.positions[eid]
            self.wall_positions[(position.x, position.y)] = eid

    def update(self, delta, events):
        new_positions = {}

        for eid, position in self.world.animals.items():
            if eid in self.world.animations:
                continue

            position = self.world.positions[eid]

            if position.dx == 0 and position.dy == 0:
                continue

            new_position = Position(position.x + position.dx, position.y + position.dy)

            blocked = (new_position.x, new_position.y) in self.wall_positions
            out_of_bounds = not (0 <= new_position.x < self.world.size.x and 0 <= new_position.y < self.world.size.y)

            if blocked or out_of_bounds:
                position.dx = 0
                position.dy = 0
                continue

            new_positions[eid] = new_position
            self.world.animations[eid] = Animation(position.dx, position.dy)

        self.world.positions.update(new_positions)


class AnimationSystem(System):
    def update(self, delta, events):
        done = set()

        for eid, animation in self.world.animations.items():
            animation.step += delta / 0.08

            if animation.step >= 1:
                done.add(eid)

        for eid in done:
            self.world.animations.pop(eid)


class InputSystem(System):
    def restart(self):
        self.pressed_keys = set()

    def update(self, delta, events):
        position = self.world.positions[self.game.player]

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key in self.pressed_keys:
                    return

                self.pressed_keys.add(event.key)
                if event.key == pygame.K_LEFT:
                    position.dy = 0
                    position.dx = -1
                elif event.key == pygame.K_RIGHT:
                    position.dy = 0
                    position.dx = 1
                elif event.key == pygame.K_UP:
                    position.dy = -1
                    position.dx = 0
                elif event.key == pygame.K_DOWN:
                    position.dy = 1
                    position.dx = 0
                else:
                    return

            elif event.type == pygame.KEYUP:
                self.pressed_keys.clear()


class PickupSystem(System):
    ALLOWED_PICKUPS = {
        AnimalType.SEAL: {ItemType.SHELL},
        AnimalType.RABBIT: {ItemType.CARROT},
        AnimalType.FISH: {ItemType.STAR},
        AnimalType.DOG: {ItemType.BONE},
        AnimalType.HEDGEHOG: {ItemType.WORM},
        AnimalType.SNAIL: {ItemType.STRAWBERRY},
    }

    def restart(self):
        self.pickups = {}

        animal = self.world.animals[self.game.player]

        for eid, item in self.world.items.items():
            if item.kind in self.ALLOWED_PICKUPS[animal.species]:
                position = self.world.positions[eid]
                self.pickups[(position.x, position.y)] = eid

    def update(self, delta, events):
        position = self.world.positions[self.game.player]

        if eid := self.pickups.pop((position.x, position.y), None):
            self.world.destroy_entity(eid)

        if not self.pickups:
            self.game.restart()


class RenderSystem(System):
    TILE_SIZE = 128

    def __init__(self, game):
        super().__init__(game)
        pygame.display.set_caption("Dudziogra")
        self.screen = pygame.display.set_mode((self.world.size.x * self.TILE_SIZE, self.world.size.y * self.TILE_SIZE))

    def update(self, delta, events):
        self.screen.fill((200, 200, 200))

        for eid, wall in self.world.walls.items():
            position = self.world.positions[eid]
            pygame.draw.rect(
                self.screen,
                (100, 100, 100),
                pygame.Rect(position.x * self.TILE_SIZE, position.y * self.TILE_SIZE, self.TILE_SIZE, self.TILE_SIZE),
            )

        for x in range(0, self.world.size.x * self.TILE_SIZE, self.TILE_SIZE):
            pygame.draw.line(self.screen, (80, 80, 80), (x, 0), (x, self.world.size.y * self.TILE_SIZE))

        for y in range(0, self.world.size.y * self.TILE_SIZE, self.TILE_SIZE):
            pygame.draw.line(self.screen, (80, 80, 80), (0, y), (self.world.size.x * self.TILE_SIZE, y))

        for eid, sprite in self.world.sprites.items():
            position = self.world.positions[eid]

            x = position.x * self.TILE_SIZE
            y = position.y * self.TILE_SIZE

            if animation := self.world.animations.get(eid):
                x -= animation.dx * math.sin((1.0 - animation.step) * math.pi / 2) * self.TILE_SIZE
                y -= animation.dy * math.sin((1.0 - animation.step) * math.pi / 2) * self.TILE_SIZE

            self.screen.blit(sprite.surface, (x, y))

        pygame.display.flip()


@dataclass
class Game:
    world: World = field(default_factory=World)
    systems: list[System] = field(default_factory=list)
    images: dict[AnimalType | ItemType, pygame.Surface] = field(default_factory=dict)
    player: int = None

    def __post_init__(self):
        self.systems = [
            InputSystem(self),
            AnimationSystem(self),
            MovementSystem(self),
            PickupSystem(self),
            RenderSystem(self),
        ]
        self.images = load_images()
        self.restart()

    def new_position(self):
        used_positions = set(self.world.positions.values())

        while True:
            position = Position(x=random.randint(0, self.world.size.x - 1), y=random.randint(0, self.world.size.y - 1))

            if position not in used_positions:
                break

        return position

    def spawn_animal(self):
        eid = self.world.create_entity()

        kind = random.choice(list(AnimalType))
        self.world.animals[eid] = Animal(kind)
        self.world.sprites[eid] = Sprite(self.images[kind])
        self.world.positions[eid] = self.new_position()

        return eid

    def spawn_items(self, n: int):
        for _ in range(n):
            eid = self.world.create_entity()

            kind = random.choice(list(ItemType))
            self.world.items[eid] = Item(kind)
            self.world.sprites[eid] = Sprite(self.images[kind])
            self.world.positions[eid] = self.new_position()

    def spawn_walls(self, count=15):
        for _ in range(count):
            eid = self.world.create_entity()
            self.world.walls[eid] = Wall()
            self.world.positions[eid] = self.new_position()

    def restart(self):
        self.world.clear()
        self.spawn_walls(25)
        self.spawn_items(30)
        self.player = self.spawn_animal()

        for system in self.systems:
            system.restart()

    def update(self, delta, events):
        for system in self.systems:
            system.update(delta, events)
