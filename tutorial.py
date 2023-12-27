import pygame
import settings
import sys
from os import listdir
from os.path import isfile, join
from pygame import mixer

pygame.init()

pygame.display.set_caption("Jump the block")

WIDTH, HEIGHT = settings.screen_width, settings.screen_height
FPS = 60
PLAYER_VEL = 5

window = pygame.display.set_mode((WIDTH, HEIGHT))


##
# mixer.music.load('mario.mp3')
# mixer.music.play(-1)#

def start_menu(screen):
    r = False
    image = pygame.image.load(join('assets', 'Menu', 'gameover.png')).convert_alpha()
    screen.blit(image, (0, 0))

    while not r:
        pygame.display.flip()
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                break

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                r = True
                print("hello")
                return r


# flip sprites
def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


# load sprite sheets adn make a left adn right copy
def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


# load block
def get_block(size, sprite_pos):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface(size, pygame.SRCALPHA, 32)
    rect = pygame.Rect(sprite_pos[0], sprite_pos[1], size[0], size[1])
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "PinkMan", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0

        self.hearts = 10
        self.heart_image = pygame.transform.scale2x(
            pygame.image.load(join("assets", "Menu", "heart.png")).convert_alpha())
        self.heart_offset = 50
        self.heart_pos = (WIDTH - self.heart_offset, self.heart_offset / 2)
        self.heart_offset_inb = self.heart_image.get_width() + self.heart_offset / 10

    def reduce_hearts(self, damage):
        self.hearts -= damage
        if self.hearts == 0:
            quit()

    # trigger when pressing spacebar
    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    # trigger when pressing left or right
    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    # trigger hurt
    def make_hit(self):
        self.hit = True

    # change sprite direction
    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / FPS) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def damage_knockback(self, dir):
        if dir == 'horizontal':
            self.x_vel = 40 * (-1 if self.direction == 'right' else 1)
        else:
            self.y_vel = -100

    # animation controller
    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    # update sprite
    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    # draw sprite
    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))
        for i in range(self.hearts):
            win.blit(self.heart_image, (self.heart_pos[0] - self.heart_offset_inb * i, self.heart_pos[1]))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Block(Object):
    def __init__(self, x, y, size, type_sprite_pos):
        super().__init__(x, y, size[0], size[1])
        block = get_block(size, type_sprite_pos)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Spike(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "spike")
        self.image = pygame.transform.scale2x(pygame.image.load(join("assets", "Traps", "Spikes", "Idle.png")))

    def loop(self):
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)


class Saw(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "spikehead")
        self.image = pygame.transform.scale2x(pygame.image.load(join("assets", "Traps", "Spike Head", "Idle.png")))

    def loop(self):
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)


class Start(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "start")
        self.image = pygame.transform.scale2x(
            pygame.image.load(join("assets", "Items", "Checkpoints", "Start", "Idle.png")))

    def loop(self):
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)


class End(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "end")
        self.image = pygame.transform.scale2x(
            pygame.image.load(join("assets", "Items", "Checkpoints", "End", "Idle.png")))

    def loop(self):
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)




class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "on"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)

        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


def get_background():
    image = pygame.image.load(join("assets", "Background", "Blue.png"))
    # draw blocks
    # for i in range(WIDTH // width + 1):
    #     for j in range(HEIGHT // height + 1):
    #         pos = (i * width, j * height)
    #         tiles.append(pos)

    return image


def draw(window, background, player, objects, traps, offset_x):
    window.blit(background, (0, 0))

    for obj in objects:
        obj.draw(window, offset_x)

    for trp in traps:
        trp.draw(window, offset_x)

    player.draw(window, offset_x)

    pygame.display.update()


def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
                # print('landed')
                collided_objects.append(obj)
                break
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()
                collided_objects.append(obj)
                break

            # elif dy < 0:
            #     player.rect.top = obj.rect.bottom
            #     player.hit_head()
            #     collided_objects.append(obj)
            #     break

    if collided_objects:
        # print(collided_objects)
        pass
    return collided_objects


def collide(player, objects, traps, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break
    for trp in traps:
        if pygame.sprite.collide_mask(player, trp):
            player.damage_knockback('horizontal')
            collided_object = trp
            break

    # print(collided_object)
    player.move(-dx, 0)
    player.update()
    return collided_object


def handle_move(player, objects, traps):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, traps, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, traps, PLAYER_VEL * 2)

    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]
    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()
            player.reduce_hearts(1)
            break
    for obj in to_check:
        if obj and obj.name == 'spike':
            player.make_hit()
            player.reduce_hearts(1)
            break
    for obj in to_check:
        if obj and obj.name == 'spikehead':
            player.make_hit()
            player.reduce_hearts(1)
            break
    for obj in to_check:
        if obj and obj.name == 'end':
            player.make_hit()
            quit()


def make_level(layout):
    objects = []
    traps = []
    for row_index, row in enumerate(layout):
        for column_index, cell in enumerate(row):
            x = column_index * settings.tile_size
            y = row_index * settings.tile_size
            tile_size = (192, 0)  # Default tile size

            if cell == 'B':
                tile = Block(x, y, (settings.tile_size, settings.tile_size / 3), (192, 128))
                objects.append(tile)
            elif cell == 'S':
                if layout[row_index + 1][column_index] == 'X':
                    tile = Spike(x + 32, y + 64, 16, 32)
                    traps.append(tile)
            elif cell == 's':
                tile = Saw(x, y + 2, 32, 32)
                traps.append(tile)

            elif cell == 'c':
                tile = Start(x + 32, y - 15, 32, 32)
                traps.append(tile)
            elif cell == 'e':
                tile = End(x + 4, y - 15, 32, 32)
                traps.append(tile)
            elif cell == 'a':
                tile = Fruit(x, y + 32, 16, 32)
                traps.append(tile)
            elif cell == 'X':
                # make boundaries
                if (0 < row_index < len(layout) - 1 and (
                        column_index == (len(layout[row_index]) - 1) or column_index == 0)):
                    tile_size = (0, 0)
                # make dirt block
                if (0 < row_index and layout[row_index - 1][column_index] != 'X'):
                    tile_size = (96, 0)

                tile = Block(x, y, (settings.tile_size, settings.tile_size), tile_size)
                objects.append(tile)

            elif cell == 'F':
                tile = Fire(x, y + 32, 16, 32)
                traps.append(tile)

    return objects, traps


def main(window):
    run = start_menu(window)
    print('hello bitch')
    clock = pygame.time.Clock()
    background = get_background()

    player = Player(100, -90, 50, 50)
    objects, traps = make_level(settings.level_map)

    offset_x = 0
    scroll_area_width = 200

    while run:
        # print(player.y_vel)
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

        player.loop(FPS)

        if traps:
            for i in traps:
                i.loop()

        # print(offset_x)
        handle_move(player, objects, traps)
        draw(window, background, player, objects, traps, offset_x)

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0 and not offset_x >= len(
                settings.level_map[0]) * settings.tile_size - WIDTH - 3) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0 and not offset_x <= 0):
            offset_x += player.x_vel
    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)
