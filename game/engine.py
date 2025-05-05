import math
import random
import sys
from dataclasses import dataclass, field

import pygame
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_MODELVIEW,
    GL_NEAREST,
    GL_PROJECTION,
    GL_QUADS,
    GL_RGBA,
    GL_BLEND,
    GL_SRC_ALPHA,
    GL_ONE_MINUS_SRC_ALPHA,
    glBlendFunc,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_UNSIGNED_BYTE,
    glBegin,
    glBindTexture,
    glClear,
    glClearColor,
    glColor4f,
    glDisable,
    glEnable,
    glEnd,
    glGenTextures,
    glLoadIdentity,
    glMatrixMode,
    glTexCoord2f,
    glTexImage2D,
    glTexParameterf,
    glVertex2f,
)
from OpenGL.GLU import gluOrtho2D

from game.assets import load_images
from game.components import Animal, Animation, Item, Position, Sprite, Trap, Wall
from game.types import AnimalType, ItemType, TrapType
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
        self.walls = {}
        for eid, wall in self.world.walls.items():
            position = self.world.positions[eid]
            self.walls[(position.x, position.y)] = eid

    def update(self, delta, events):
        new_positions = {}

        for eid, position in self.world.animals.items():
            if eid in self.world.animations:
                continue

            position = self.world.positions[eid]

            if position.dx == 0 and position.dy == 0:
                continue

            new_position = Position(position.x + position.dx, position.y + position.dy)

            blocked = (new_position.x, new_position.y) in self.walls
            out_of_bounds = not (0 <= new_position.x < self.world.size.x and 0 <= new_position.y < self.world.size.y)

            if blocked or out_of_bounds:
                self.world.animations[eid] = Animation(-position.dx / 3, -position.dy / 3)
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
            animation.step += delta / 0.1

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
            if item.kind in self.ALLOWED_PICKUPS[animal.kind]:
                position = self.world.positions[eid]
                self.pickups[(position.x, position.y)] = eid

    def update(self, delta, events):
        position = self.world.positions[self.game.player]

        if eid := self.pickups.pop((position.x, position.y), None):
            self.world.destroy_entity(eid)

        if not self.pickups:
            self.game.restart()


class RenderSystem(System):
    TILE_SIZE = 96

    def __init__(self, game):
        super().__init__(game)
        pygame.display.set_caption("Dudziogra")
        self.screen = pygame.display.set_mode(
            (self.world.size.x * self.TILE_SIZE, self.world.size.y * self.TILE_SIZE), pygame.DOUBLEBUF | pygame.OPENGL
        )

    def restart(self):
        self.textures = {}
        for k, surface in self.game.images.items():
            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            surface = pygame.transform.scale(surface, (self.TILE_SIZE, self.TILE_SIZE))
            surface = pygame.transform.flip(surface, False, True)
            image_data = pygame.image.tostring(surface, "RGBA", True)
            glTexImage2D(
                GL_TEXTURE_2D,
                0,
                GL_RGBA,
                surface.get_width(),
                surface.get_height(),
                0,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                image_data,
            )
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            self.textures[k] = texture_id

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, self.world.size.x * self.TILE_SIZE, self.world.size.y * self.TILE_SIZE, 0)
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def draw_tile(self, texture_id, x, y, alpha=1.0):
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glColor4f(alpha, alpha, alpha, 1.0)
        tx, ty = x * self.TILE_SIZE, y * self.TILE_SIZE
        size = self.TILE_SIZE

        glBegin(GL_QUADS)
        glTexCoord2f(0, 0)
        glVertex2f(tx, ty)
        glTexCoord2f(1, 0)
        glVertex2f(tx + size, ty)
        glTexCoord2f(1, 1)
        glVertex2f(tx + size, ty + size)
        glTexCoord2f(0, 1)
        glVertex2f(tx, ty + size)
        glEnd()

    def update(self, delta, events):
        glClearColor(0.3, 0.3, 0.3, 1.0)
        glLoadIdentity()

        for x in range(self.world.size.x):
            for y in range(self.world.size.y):
                light_level = self.world.light.get((x, y), 0.3)
                brightness = max(0.3, min(1.0, light_level))

                tx, ty = x * self.TILE_SIZE, y * self.TILE_SIZE
                size = self.TILE_SIZE

                glDisable(GL_TEXTURE_2D)
                glColor4f(brightness, brightness, brightness, 1.0)
                glBegin(GL_QUADS)
                glVertex2f(tx, ty)
                glVertex2f(tx + size, ty)
                glVertex2f(tx + size, ty + size)
                glVertex2f(tx, ty + size)
                glEnd()
                glEnable(GL_TEXTURE_2D)

        for eid, wall in self.world.walls.items():
            pos = self.world.positions[eid]
            if self.world.light and (pos.x, pos.y) not in self.world.light:
                continue
            self.draw_tile(self.textures[wall.kind], pos.x, pos.y)

        for eid, trap in self.world.traps.items():
            pos = self.world.positions[eid]
            if self.world.light and (pos.x, pos.y) not in self.world.light:
                continue
            self.draw_tile(self.textures[trap.kind], pos.x, pos.y)

        for eid, sprite in self.world.sprites.items():
            pos = self.world.positions[eid]
            if self.world.light and (pos.x, pos.y) not in self.world.light:
                continue

            x, y = pos.x, pos.y
            if animation := self.world.animations.get(eid):
                offset_x = -animation.dx * math.sin((1.0 - animation.step) * math.pi / 2)
                offset_y = -animation.dy * math.sin((1.0 - animation.step) * math.pi / 2)
                x += offset_x
                y += offset_y

            self.draw_tile(self.textures[sprite.kind], x, y)

        pygame.display.flip()


class LightSystem(System):
    def restart(self):
        self.walls = {}
        for eid, wall in self.world.walls.items():
            position = self.world.positions[eid]
            self.walls[(position.x, position.y)] = eid

    @property
    def radius(self):
        return 12

    @staticmethod
    def bresenham(x0, y0, x1, y1):
        points = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1

        if dx > dy:
            err = dx // 2
            while x != x1:
                yield (x, y)
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy // 2
            while y != y1:
                yield (x, y)
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy

    def los_blocked(self, x0, y0, x1, y1):
        for x, y in self.bresenham(x0, y0, x1, y1):
            if (x, y) in self.walls and (x, y) != (x0, y0):
                return True
        return False

    def update(self, delta, events):
        if self.radius is None:
            return

        position = self.world.positions[self.game.player]

        self.world.light.clear()
        self.world.light[(position.x, position.y)] = 1.0

        for x in range(position.x - self.radius, position.x + self.radius + 1):
            for y in range(position.y - self.radius, position.y + self.radius + 1):
                if 0 <= x < self.world.size.x and 0 <= y < self.world.size.y:
                    dx = x - position.x
                    dy = y - position.y
                    if dx * dx + dy * dy <= self.radius * self.radius:
                        if not self.los_blocked(position.x, position.y, x, y):
                            self.world.light[(x, y)] = 1.0 - math.sqrt(dx * dx + dy * dy) / self.radius


class TrapSystem(System):
    def restart(self):
        self.traps = {}

        for eid, trap in self.world.traps.items():
            position = self.world.positions[eid]
            self.traps[(position.x, position.y)] = eid

        self.walls = {}
        for eid, wall in self.world.walls.items():
            position = self.world.positions[eid]
            self.walls[(position.x, position.y)] = eid

    def update(self, delta, events):
        position = self.world.positions[self.game.player]

        if eid := self.traps.get((position.x, position.y), None):
            trap = self.world.traps[eid]

            if trap.kind == TrapType.BALL:
                while True:
                    position.dx = random.choice((-1, 1)) * (2 + random.randint(-3, 3))
                    position.dy = random.choice((-1, 1)) * (2 + random.randint(-3, 3))

                    if (position.x + position.dx, position.y + position.dy) not in self.walls:
                        break

            if trap.kind == TrapType.SPIDER and (position.dx or position.dy):
                if trap.step == 0:
                    trap.step = 6

                trap.step -= 1

                if trap.step:
                    self.world.animations[self.game.player] = Animation(-position.dx / 3, -position.dy / 3)
                    position.dx = 0
                    position.dy = 0


@dataclass
class Game:
    world: World = field(default_factory=World)
    systems: list[System] = field(default_factory=list)
    images: dict[AnimalType | ItemType, pygame.Surface] = field(default_factory=dict)
    player: int = None
    level: int = 0

    def __post_init__(self):
        self.systems = [
            LightSystem(self),
            InputSystem(self),
            TrapSystem(self),
            AnimationSystem(self),
            PickupSystem(self),
            MovementSystem(self),
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
        self.world.sprites[eid] = Sprite(kind)
        self.world.positions[eid] = self.new_position()

        return eid

    def spawn_items(self, n: int):
        for _ in range(n):
            eid = self.world.create_entity()

            kind = random.choice(list(ItemType))
            self.world.items[eid] = Item(kind)
            self.world.sprites[eid] = Sprite(kind)
            self.world.positions[eid] = self.new_position()

    def spawn_walls(self, n: int):
        for _ in range(n):
            eid = self.world.create_entity()
            self.world.walls[eid] = Wall()
            self.world.positions[eid] = self.new_position()

    def spawn_traps(self, n: int):
        for _ in range(n):
            eid = self.world.create_entity()

            kind = random.choice(list(TrapType))
            self.world.traps[eid] = Trap(kind)
            self.world.positions[eid] = self.new_position()

    def restart(self):
        self.level += 1
        self.world.clear()
        self.spawn_walls(80)
        self.spawn_items(30)
        self.spawn_traps(15)
        self.player = self.spawn_animal()

        if self.level == 3:
            self.systems = [LightSystem(self), *self.systems]

        for system in self.systems:
            system.restart()

    def update(self, delta, events):
        for system in self.systems:
            system.update(delta, events)
