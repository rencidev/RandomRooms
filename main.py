import pygame
import random
import math

pygame.init()

# Видимое окно
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Карта
MAP_TILES_W = 100
MAP_TILES_H = 100
TILE_SIZE = 20

# Версия
VERSION = "1.0.0"

# Поверхности
map_surface = pygame.Surface((MAP_TILES_W * TILE_SIZE, MAP_TILES_H * TILE_SIZE))
walkable_mask = pygame.Surface((MAP_TILES_W * TILE_SIZE, MAP_TILES_H * TILE_SIZE), pygame.SRCALPHA)
walkable_mask.fill((0, 0, 0, 255))  # непроходимо по умолчанию

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("RandomRooms v.", VERSION)

# Цвета
WALL   = (50, 50, 70)
FLOOR  = (200, 180, 140)
GRID   = (40, 40, 60)
PLAYER = (255, 255, 0)
SPAWN  = (0, 255, 0)
EXIT   = (0, 100, 255)

font = pygame.font.SysFont("consolas", 18, bold=True)
clock = pygame.time.Clock()

rooms = []
player_pos = [0, 0]  # в пикселях на карте
spawn_pos = (0, 0)
exit_pos = (0, 0)

zoom = 1.0

def create_random_room():
    min_size, max_size = 10, 30
    w = random.randint(min_size, max_size)
    h = random.randint(min_size, max_size)
    x = random.randint(2, MAP_TILES_W - w - 2)
    y = random.randint(2, MAP_TILES_H - h - 2)
    return pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, w * TILE_SIZE, h * TILE_SIZE)

def rooms_overlap(r1, r2):
    return r1.colliderect(r2.inflate(TILE_SIZE*8, TILE_SIZE*8))

def dig_corridor(start, end):
    x1, y1 = start
    x2, y2 = end
    for x in range(min(x1, x2) - TILE_SIZE, max(x1, x2) + TILE_SIZE*2, TILE_SIZE):
        for off in range(-TILE_SIZE, TILE_SIZE*2, TILE_SIZE):
            rect = pygame.Rect(x + off, y1 - TILE_SIZE, TILE_SIZE, TILE_SIZE*3)
            map_surface.fill(FLOOR, rect)
            walkable_mask.fill((255, 255, 255, 255), rect)
    for y in range(min(y1, y2) - TILE_SIZE, max(y1, y2) + TILE_SIZE*2, TILE_SIZE):
        for off in range(-TILE_SIZE, TILE_SIZE*2, TILE_SIZE):
            rect = pygame.Rect(x2 + off, y - TILE_SIZE, TILE_SIZE, TILE_SIZE*3)
            map_surface.fill(FLOOR, rect)
            walkable_mask.fill((255, 255, 255, 255), rect)

def generate_dungeon():
    global rooms, player_pos, spawn_pos, exit_pos
    map_surface.fill(WALL)
    walkable_mask.fill((0, 0, 0, 255))
    rooms = []
    
    num_rooms = random.randint(10, 16)
    for _ in range(num_rooms * 5):
        if len(rooms) >= num_rooms:
            break
        room = create_random_room()
        if any(rooms_overlap(room, r["rect"]) for r in rooms):
            continue
        inner = room.inflate(-TILE_SIZE*2, -TILE_SIZE*2)
        map_surface.fill(FLOOR, inner)
        walkable_mask.fill((255, 255, 255, 255), inner)
        pygame.draw.rect(map_surface, WALL, room, TILE_SIZE*2)
        
        rooms.append({"rect": room, "center": room.center})
    
    for i in range(1, len(rooms)):
        dig_corridor(rooms[i-1]["center"], rooms[i]["center"])
    
    # Сетка и маркеры
    for x in range(0, MAP_TILES_W * TILE_SIZE, TILE_SIZE):
        pygame.draw.line(map_surface, GRID, (x, 0), (x, MAP_TILES_H * TILE_SIZE))
    for y in range(0, MAP_TILES_H * TILE_SIZE, TILE_SIZE):
        pygame.draw.line(map_surface, GRID, (0, y), (MAP_TILES_W * TILE_SIZE, y))
    
    if rooms:
        spawn_pos = rooms[0]["center"]
        exit_pos = max(rooms, key=lambda r: math.dist(r["center"], spawn_pos))["center"]
        player_pos = list(spawn_pos)
        
        pygame.draw.circle(map_surface, SPAWN, spawn_pos, TILE_SIZE // 2)
        pygame.draw.circle(map_surface, EXIT, exit_pos, TILE_SIZE // 2)

generate_dungeon()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                generate_dungeon()
                zoom = 1.0  # сброс зума
        elif event.type == pygame.MOUSEWHEEL:
            old_zoom = zoom
            zoom *= 1.2 if event.y > 0 else 0.8
            zoom = max(0.5, min(zoom, 3.0))

    # Движение (независимо от зума)
    keys = pygame.key.get_pressed()
    speed = 6
    dx = dy = 0
    if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx -= speed
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += speed
    if keys[pygame.K_UP] or keys[pygame.K_w]: dy -= speed
    if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy += speed
    
    new_x = player_pos[0] + dx
    new_y = player_pos[1] + dy
    
    # Коллизия на оригинальной карте
    points = [(new_x-8, new_y-8), (new_x+8, new_y-8), (new_x-8, new_y+8), (new_x+8, new_y+8)]
    can_move = all(0 <= int(px) < MAP_TILES_W*TILE_SIZE and 0 <= int(py) < MAP_TILES_H*TILE_SIZE and
                   walkable_mask.get_at((int(px), int(py)))[:3] == (255, 255, 255) for px, py in points)
    
    if can_move:
        player_pos[0] = new_x
        player_pos[1] = new_y
    
    # Рендер: масштабируем всю карту и блитим с оффсетом
    screen.fill((0, 0, 0))
    
    scaled_width = int(MAP_TILES_W * TILE_SIZE * zoom)
    scaled_height = int(MAP_TILES_H * TILE_SIZE * zoom)
    scaled_map = pygame.transform.smoothscale(map_surface, (scaled_width, scaled_height))
    
    # Оффсет для центрирования игрока
    offset_x = SCREEN_WIDTH // 2 - int(player_pos[0] * zoom)
    offset_y = SCREEN_HEIGHT // 2 - int(player_pos[1] * zoom)
    
    screen.blit(scaled_map, (offset_x, offset_y))
    
    # Игрок — фиксированный размер в центре
    pygame.draw.circle(screen, PLAYER, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 10)
    pygame.draw.circle(screen, (255, 255, 255), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 10, 2)  # обводка
    
    # Инфо
    info = f"Комнат: {len(rooms)}  Зум: {zoom:.1f}x  Тайл: ({int(player_pos[0]//TILE_SIZE)}, {int(player_pos[1]//TILE_SIZE)})"
    screen.blit(font.render(info, True, (255, 255, 200)), (10, 10))
    
    if math.dist(player_pos, exit_pos) < TILE_SIZE * 2:
        screen.blit(font.render("Нажми ENTER → следующий уровень", True, (100, 200, 255)), (SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT - 40))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()