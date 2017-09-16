import pygame
import sys

from game.load_tiles import SPRITE_DIMS, SPRITE_SHEET_PATH, TileCache
from game.load_level import Level
from game.load_sprite import Sprite

this = sys.modules[__name__]

if __name__ == "__main__":
    screen = pygame.display.set_mode((600, 400))
    sheet_file = SPRITE_SHEET_PATH.split('/')[-1]
    this.MAP_CACHE = TileCache(*SPRITE_DIMS)

    level = Level()
    level.load_file('/home/pokeybill/virtz/resources/basic_level.map')

    clock = pygame.time.Clock()

    sprites = pygame.sprite.RenderUpdates()
    for pos, tile in level.items.items():
        sprite = Sprite(pos, tile)
        sprites.add(sprite)

    background, overlay_dict = level.render(MAP_CACHE, SPRITE_DIMS)
    overlays = pygame.sprite.RenderUpdates()
    for (x, y), image in overlay_dict.items():
        overlay = pygame.sprite.Sprite(overlays)
        overlay.image = image
        overlay.rect = image.get_rect().move(x * 16, y * 16 - 16)
    screen.blit(background, (0, 0))
    overlays.draw(screen)
    pygame.display.flip()

    # Basic 15hz game loop
    game_over = False
    while not game_over:
        sprites.clear(screen, background)
        dirty = sprites.draw(screen)
        overlays.draw(screen)
        pygame.display.update(dirty)
        #pygame.display.flip()
        clock.tick(15)
        for event in pygame.event.get():
            if event.type == pygame.locals.QUIT:
                game_over = True
            elif event.type == pygame.locals.KEYDOWN:
                pressed_key = event.key
