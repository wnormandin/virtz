from lib import load_tiles
from lib import load_level

if __name__ == "__main__":
    screen = pygame.display.set_mode((600, 400))

    MAP_TILE_WIDTH, MAP_TILE_HEIGHT = load_tiles.SPRITE_DIMS
    sheet_file = load_tiles.SPRITE_SHEET_PATH.split('/')[-1]
    sheet_path = load_tiles.SPRITE_SHEET_PATH
    MAP_CACHE = {
        sheet_file: load_tile_table(sheet_path,
                        MAP_TILE_WIDTH, MAP_TILE_HEIGHT)}

    level = Level()
