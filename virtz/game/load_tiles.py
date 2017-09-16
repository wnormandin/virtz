import sys
import pygame
import pygame.locals

SHEET_DIMS = (57, 31) # cols, rows
SPRITE_MARGIN = 1
SPRITE_DIMS = (16, 16) # width / height, in px
SPRITE_SHEET_PATH = '/home/pokeybill/virtz/resources/basic_level.png'


class TileCache:
    """Load the tilesets lazily into global cache"""

    def __init__(self,  width=16, height=None):
        self.width = width
        self.height = height or width
        self.cache = {}

    def __getitem__(self, filename):
        """Return a table of tiles, load it from disk if needed."""

        key = (filename, self.width, self.height)
        try:
            return self.cache[key]
        except KeyError:
            tile_table = self._load_tile_table(filename, self.width,
                                               self.height)
            self.cache[key] = tile_table
            return tile_table

    def _load_tile_table(self, filename, width, height, margin=1):
        image = pygame.image.load(filename).convert()
        image_width, image_height = image.get_size() # 968px x 526px
        tile_table = []
        for tile_x in range(SHEET_DIMS[0]):
            line = []
            tile_table.append(line)
            for tile_y in range(SHEET_DIMS[1]):
                x_loc = tile_x * (width + margin)
                y_loc = tile_y * (height + margin)
                rect = (x_loc, y_loc, width, height)
                line.append(image.subsurface(rect))
        return tile_table


def load_tile_table(filename, width, height, margin=1):
    image = pygame.image.load(filename).convert()
    image_width, image_height = image.get_size() # 968px x 526px
    tile_table = []
    for tile_x in range(SHEET_DIMS[0]):
        line = []
        tile_table.append(line)
        for tile_y in range(SHEET_DIMS[1]):
            x_loc = tile_x * (width + margin)
            y_loc = tile_y * (height + margin)
            rect = (x_loc, y_loc, width, height)
            line.append(image.subsurface(rect))
    return tile_table

if __name__ == '__main__':
    # When invoked as a script, display the passed tilemap
    # tiles split and slightly separated
    pygame.init()
    screen = pygame.display.set_mode((913, 496))
    screen.fill((255, 255, 255))
    table = load_tile_table(SPRITE_SHEET_PATH, *SPRITE_DIMS)
    for x, row in enumerate(table):
        for y, tile in enumerate(row):
            x_loc = x * SPRITE_DIMS[0]
            y_loc = y * SPRITE_DIMS[1]
            screen.blit(tile, (x_loc, y_loc))
    pygame.display.flip()

    # Wait for input after displaying the tile map
    while pygame.event.wait().type != pygame.locals.QUIT:
        pass
