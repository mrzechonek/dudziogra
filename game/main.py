import pygame
import sys

# Configuration
TILE_SIZE = 64
GRID_WIDTH = 10
GRID_HEIGHT = 8
SCREEN_WIDTH = TILE_SIZE * GRID_WIDTH
SCREEN_HEIGHT = TILE_SIZE * GRID_HEIGHT

# ECS Structures
next_entity_id = 0
entities = set()
components = {
    "Position": {},
    "Sprite": {},
    "PlayerControlled": set(),
    "Item": set(),
}

def create_entity():
    global next_entity_id
    eid = next_entity_id
    next_entity_id += 1
    entities.add(eid)
    return eid

def add_component(eid, comp_type, data=None):
    if comp_type in components:
        if isinstance(components[comp_type], dict):
            components[comp_type][eid] = data
        elif isinstance(components[comp_type], set):
            components[comp_type].add(eid)

def remove_entity(eid):
    entities.discard(eid)
    for comp in components.values():
        if isinstance(comp, dict):
            comp.pop(eid, None)
        elif isinstance(comp, set):
            comp.discard(eid)

# Init pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("ECS Animal Game")
clock = pygame.time.Clock()

# Load assets
animal_img = pygame.image.load("animal.png").convert_alpha()
item_img = pygame.image.load("item.png").convert_alpha()

# Create entities
player = create_entity()
add_component(player, "Position", [1, 1])
add_component(player, "Sprite", animal_img)
add_component(player, "PlayerControlled")

item1 = create_entity()
add_component(item1, "Position", [3, 2])
add_component(item1, "Sprite", item_img)
add_component(item1, "Item")

item2 = create_entity()
add_component(item2, "Position", [5, 5])
add_component(item2, "Sprite", item_img)
add_component(item2, "Item")

# Systems
def input_system():
    keys = pygame.key.get_pressed()
    dx, dy = 0, 0
    if keys[pygame.K_LEFT]:
        dx = -1
    elif keys[pygame.K_RIGHT]:
        dx = 1
    elif keys[pygame.K_UP]:
        dy = -1
    elif keys[pygame.K_DOWN]:
        dy = 1

    for eid in components["PlayerControlled"]:
        if eid in components["Position"]:
            pos = components["Position"][eid]
            new_x = pos[0] + dx
            new_y = pos[1] + dy
            if 0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT:
                pos[0], pos[1] = new_x, new_y

def pickup_system():
    item_entities = components["Item"]
    item_positions = {eid: components["Position"][eid] for eid in item_entities}
    for eid in components["PlayerControlled"]:
        p_pos = components["Position"][eid]
        for item_eid, i_pos in list(item_positions.items()):
            if p_pos == i_pos:
                remove_entity(item_eid)

def render_system():
    screen.fill((30, 30, 30))
    draw_grid()
    for eid, pos in components["Position"].items():
        if eid in components["Sprite"]:
            img = components["Sprite"][eid]
            screen.blit(img, (pos[0] * TILE_SIZE, pos[1] * TILE_SIZE))
    pygame.display.flip()

def draw_grid():
    for x in range(0, SCREEN_WIDTH, TILE_SIZE):
        pygame.draw.line(screen, (100, 100, 100), (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, TILE_SIZE):
        pygame.draw.line(screen, (100, 100, 100), (0, y), (SCREEN_WIDTH, y))

# Main loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    input_system()
    pickup_system()
    render_system()
    clock.tick(60)
