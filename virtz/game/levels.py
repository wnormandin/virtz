#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
import pickle
import random
import pygame
import argparse
import copy

from .models import MapTile
from .tiles import TileFactory
from .load_tilemap import TileCache

this = sys.modules[__name__]
MAX_X = 60
MAX_Y = 60

test_level = (
            (
                (',,,%,,,>,<,,?,,'),
                (',,,,<,,?,,,.,,?'),
                ('%,,,>,,+,,,.,?,'),
                (',,,,<,,,+^^^^^,'),
                (',,,,,,.%%..~~~~')
            ),(
                ('~~~,,,>,<,,?,,'),
                ('~~,<,,?,,,.,,?'),
                ('~,,,>,,+,,.,?,'),
                ('~~,,<,,+^^^^^,'),
                ('~~~~~.....~~~~')
            ),)

def save_test():
    with open('../data/test_map', 'wb') as outfile:
        pickle.dump(test_level, outfile)


def random_size():
    # return a random x/y dimension pair where:
    # MAX_X/2 < x < MAX_X; MAX_Y/2 < y < MAX_Y
    return tuple(map(random.choice,
        [range(int(v-(v/2)),v) for v in [MAX_X, MAX_Y]]))


def translate_map(char_map, db_path):
    factory = TileFactory(db_path)
    out_map = {}
    for z in range(len(char_map)):
        for y in range(len(char_map[z])):
            for x in range(len(char_map[z][y])):
                position = x, y, z
                out_map[position] = factory.get_tile(char_map[z][y][x], position)
    return out_map


class LevelMap:
    def __init__(self, tile_map, level_map='../data/test_map', **kwargs):
        ''' The LevelMap class requires a filename and accommodates
        several keyword arguments for customized tilemap scale and size

        width:      tile width in pixels (default=16)
        height:     tile height in pixels (default=16)
        margin:     margin between tiles in pixels (default=1)
        '''

        if 'width' not in kwargs:
            # Defaulting to 16x16px if not set
            kwargs['width'] = 16
        if 'height' not in kwargs:
            kwargs['height'] = 16
        if 'margin' not in kwargs:
            kwargs['margin'] = 1
        assert 'db_path' in kwargs

        w = kwargs['width']
        h = kwargs['height']
        m = kwargs['margin']
        self.kwargs = kwargs
        self.level_map = level_map
        self.tile_map = tile_map
        self.ready = False  # Indicates level map is loaded
        self.loaded = False # Indicates tile map is loaded
        self._depth = 0
        self.cache = TileCache(w, h, m)
        self._raw_map = None
        self._real_map = None

    def __getitem__(self, position):
        try:
            return self._real_map[position]
        except KeyError:
            return
        except AttributeError:
            print('Map is not loaded!')
            raise

    def __setitem__(self, position, tile):
        assert isinstance(tile, MapTile), 'tile is not a MapTile instance'
        assert hasattr(self, '_real_map'), 'Map is not loaded'
        assert position in self._real_map, 'Position does not exist'
        self._real_map[position] = tile

    def _save_map(self):
        try:
            with open(self.level_map, 'wb') as outfile:
                pickle.dump(self._raw_map, outfile)
        except pickle.PicklingError:
            raise

    def _open_map(self):
        try:
            with open(self.level_map, 'rb') as infile:
                return pickle.load(infile)
        except pickle.UnpicklingError:
            return

    def in_map(self, point):
        if point in self.world_map:
            return True
        return False

    def get_neighbors(self, point):
        return self._neighbors(point)

    def _neighbors(self, point):
        x, y, z = point
        positions = [(x+1, y, z), (x-1, y, z), (x+1, y+1, z), (x+1, y-1, z), (x-1, y+1, z),
                (x-1, y-1, z), (x, y+1, z), (x, y-1, z)]
        return [pos for pos in positions if self.in_map(pos) and self[pos].passable]

    def explore(self, position_list):
        for position in position_list:
            self[position].explored = True
            for pos in self._neighbors(position):
                self[pos].explored = True

    def _load_tiles(self):
        self._tiles = self.cache[self.tile_map]
        self.loaded = True

    def _populate_map(self):
        self._raw_map = self._open_map()
        self._real_map = translate_map(self._raw_map, self.kwargs['db_path'])
        for position in self._real_map:
            map_tile = self._real_map[position]
            if '_' in map_tile.name:
                map_tile.tile_type = map_tile.name.split('_')[0]
            else:
                map_tile.tile_type = map_tile.name
            y, x = map_tile.tile_row, map_tile.tile_col
            self._real_map[position].image = self.tile_image(y, x)
            if map_tile.has_edges:
                if map_tile.tile_type == 'water':
                    map_tile.top_right_corner = self.tile_image(y+1, x-3)
                    map_tile.top_left_corner = self.tile_image(y+1, x-2)
                    map_tile.bot_right_corner = self.tile_image(y, x-3)
                    map_tile.bot_left_corner = self.tile_image(y, x-2)
                else:
                    map_tile.top_right_corner = self.tile_image(y, x-3)
                    map_tile.top_left_corner = self.tile_image(y, x-2)
                    map_tile.bot_right_corner = self.tile_image(y-1, x-3)
                    map_tile.bot_left_corner = self.tile_image(y-1, x-2)
                map_tile.top_left_image = self.tile_image(y-1, x-1)
                map_tile.top_image = self.tile_image(y-1, x)
                map_tile.top_right_image = self.tile_image(y-1, x+1)
                map_tile.left_image = self.tile_image(y, x-1)
                map_tile.right_image = self.tile_image(y, x+1)
                map_tile.bot_left_image = self.tile_image(y+1, x-1)
                map_tile.bot_image = self.tile_image(y+1, x)
                map_tile.bot_right_image = self.tile_image(y+1, x+1)
        self.ready = True

    def prepare(self):
        # Load the tile_map, level_map, and make sure all is ready
        try:
            self._load_tiles()
            self._populate_map()
            self.default_tile = self._tiles[1, 5]
        except:
            if not self.loaded:
                print('Failed to load tiles')
            if not self.ready:
                print('Failed to populate map')
            raise

    def get_maptile_image(self, tile):
        return self._check_edges(tile)

    def _check_edges(self, tile):
        if not tile.has_edges:
            return tile.image
        else:
            x, y, z = tile.position

            # Gather tile types
            if (x, y-1, z) in self.world_map:
                tile_top = self[x, y-1, z].tile_type
            else:
                tile_top = tile.tile_type
            if (x+1, y-1, z) in self.world_map:
                tile_top_right = self[x+1, y-1, z].tile_type
            else:
                tile_top_right = tile.tile_type
            if (x-1, y-1, z) in self.world_map:
                tile_top_left = self[x-1, y-1, z].tile_type
            else:
                tile_top_left = tile.tile_type
            if (x-1, y, z) in self.world_map:
                tile_left = self[x-1, y, z].tile_type
            else:
                tile_left = tile.tile_type
            if (x+1, y, z) in self.world_map:
                tile_right = self[x+1, y, z].tile_type
            else:
                tile_right = tile.tile_type
            if (x, y+1, z) in self.world_map:
                tile_bot = self[x, y+1, z].tile_type
            else:
                tile_bot = tile.tile_type
            if (x+1, y+1, z) in self.world_map:
                tile_bot_right = self[x+1, y+1, z].tile_type
            else:
                tile_bot_right = tile.tile_type
            if (x-1, y+1, z) in self.world_map:
                tile_bot_left = self[x-1, y+1, z].tile_type
            else:
                tile_bot_left = tile.tile_type

            # Return appropriate edge tile image
            if tile.tile_type != tile_top_right and tile.tile_type == tile_top and tile.tile_type == tile_right:
                return tile.top_right_corner
            elif tile.tile_type != tile_top_left and tile.tile_type == tile_top and tile.tile_type == tile_left:
                return tile.top_left_corner
            elif tile.tile_type != tile_bot_right and tile.tile_type == tile_bot and tile.tile_type == tile_right:
                return tile.bot_right_corner
            elif tile.tile_type != tile_bot_left and tile.tile_type == tile_bot and tile.tile_type == tile_left:
                return tile.bot_left_corner
            elif tile.tile_type != tile_right and tile.tile_type != tile_top:
                return tile.top_right_image
            elif tile.tile_type != tile_right and tile.tile_type != tile_bot:
                return tile.bot_right_image
            elif tile.tile_type != tile_left and tile.tile_type != tile_top:
                return tile.top_left_image
            elif tile.tile_type != tile_left and tile.tile_type != tile_bot:
                return tile.bot_left_image
            elif tile.tile_type != tile_right:
                return tile.right_image
            elif tile.tile_type != tile_left:
                return tile.left_image
            elif tile.tile_type != tile_top:
                return tile.top_image
            elif tile.tile_type != tile_bot:
                return tile.bot_image
            else:
                return tile.image


    def tile_image(self, y, x):
        # Note the reversed order
        return self._tiles[x,y]

    @property
    def world_map(self):
        return self._real_map

    @property
    def level(self):
        return self._depth

    @level.setter
    def level(self, depth):
        assert [pt for pt in self._real_map if pt[2] == depth]
        self._depth = depth


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('tile_map')
    parser.add_argument('--width', default=16)
    parser.add_argument('--height', default=16)
    parser.add_argument('--margin', default=1)
    return parser.parse_args()

if __name__ == '__main__':
    this.cli_args = cli()
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))

    # Automatically creating and reading from the test map for now
    save_test()
    cli_args.level_map = '../data/test_map'
    db_path = '../data/game_data.db'

    level_map = LevelMap(cli_args.tile_map, cli_args.level_map,
            width=cli_args.width,
            height=cli_args.height,
            margin=cli_args.margin,
            db_path=db_path)
    level_map.prepare()

    for p in level_map.world_map:
        if p[2] == level_map.level:
            x_loc = p[0] * cli_args.width
            y_loc = p[1] * cli_args.height
            screen.blit(level_map[p].image, (x_loc, y_loc))
    pygame.display.flip()

    while pygame.event.wait().type != pygame.locals.QUIT:
        pass
