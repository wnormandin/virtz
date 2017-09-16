import configparser
import pygame
import os

class Level:

    def load_file(self, filename="resources/basic_level.map"):
        self.map = []
        self.key = {}
        self.items = {}
        parser = configparser.ConfigParser()
        parser.read(filename)
        self.tileset = parser.get("level", "tileset")
        self.default_tile = parser.get('level', 'default')
        self.tileset_path = parser.get("level", "tilepath")
        self.map = parser.get("level", "map").split('\n')
        for section in parser.sections():
            if len(section) == 1:
                desc = dict(parser.items(section))
                self.key[section] = desc
        self.width = len(self.map[0])
        self.height = len(self.map)

    def get_tile(self, x, y):
        try:
            char = self.map[y][x]
        except IndexError:
            return {}
        try:
            return self.key[char]
        except KeyError:
            return {}

    def get_bool(self, x, y, name):
        value = self.get_tile(x, y).get(name)
        return value in (True, 1, 'true', 'yes',
                 'True', 'Yes', '1', 'on', 'On')

    def is_wall(self, x, y):
        return self.get_bool(x, y, 'wall')

    def is_liquid(self, x, y):
        return self.get_bool(x, y, 'liquid')

    def is_blocking(self, x, y):
        if not 0 <= x < self.width or not 0 <= y < self.height:
            return True
        return self.get_bool(x, y, 'block')

    def is_sprite(self, x, y):
        return self.get_bool(x, y, 'sprite')

    def render(self, cache, tile_dims):
        wall = self.is_wall
        tiles = cache[os.path.join(self.tileset_path, self.tileset)]
        width = self.width * tile_dims[0]
        height = self.height * tile_dims[1]
        image = pygame.Surface((width, height))
        overlays = {}
        for map_y, line in enumerate(self.map):
            for map_x, c in enumerate(line):
                if self.is_sprite(map_x, map_y) and not wall(map_x, map_y):
                    pos = [int(p) for p in self.key[c]['tile'].split(',')]
                    self.items[(map_x, map_y)] = tiles[pos[0]][pos[1]]
                    c = self.default_tile
                tile = [int(p) for p in self.key[c]['tile'].split(',')]
                tile_image = tiles[tile[0]][tile[1]]
                image.blit(tile_image,
                    (map_x * tile_dims[0], map_y * tile_dims[1]))
        return image, overlays
