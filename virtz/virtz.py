import pygame
import sys
import time

from game.load_tiles import SPRITE_DIMS, SPRITE_SHEET_PATH, TileCache
from game.load_level import Level
from game.load_sprite import Sprite

this = sys.modules[__name__]

def min_wait():
    # < Planck time
    min_s = 0.000000000000000000000000000000000000000000001
    time.sleep(min_s)

if __name__ == "__main__":
    screen = pygame.display.set_mode((600, 400))
    sheet_file = SPRITE_SHEET_PATH.split('/')[-1]
    this.MAP_CACHE = TileCache(*SPRITE_DIMS)

    level = Level()
    level.load_file('/home/pokeybill/virtz/resources/basic_level.map')

    clock = pygame.time.Clock()

    background = level.render(MAP_CACHE, SPRITE_DIMS)
    screen.blit(background, (0, 0))
    pygame.display.flip()
    def_idx = level.get_tile(*(int(p) for p in level.default_tile_idx))
    default_tile = MAP_CACHE[def_idx[0]][def_idx[1]]

    sprites = pygame.sprite.RenderUpdates()
    print(level.items.items())
    for pos, tile in level.items.items():
        sprite = Sprite(pos, tile)
        sprites.add(sprite)

    # Basic 15hz game loop
    game_over = False
    while not game_over:
        sprites.update()
        sprites.clear(screen, default_tile)
        dirty = sprites.draw(screen)
        pygame.display.update(dirty)
        #pygame.display.flip()
        clock.tick(15)
        for event in pygame.event.get():
            if event.type == pygame.locals.QUIT:
                game_over = True
            elif event.type == pygame.locals.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()
