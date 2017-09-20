#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#***********************************************
#
#   Script and objects to load and slice
#   tilemaps.  The TileCache provides access
#   
#
#
#***********************************************

import sys
from math import ceil
import pygame
import pygame.locals
import argparse

SPRITE_SHEET_PATH = '/home/pokeybill/virtz/resources/basic_level.png'
# Grabbing a module instance
this = sys.modules[__name__]


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename', default=SPRITE_SHEET_PATH,
            help='Specify a tilemap path')
    parser.add_argument('-c', '--column-px',
            help='Define column width in pixels', default=16, type=int)
    parser.add_argument('-r', '--row-px', help='Define row width in pixels',
            default=16, type=int)
    parser.add_argument('-m', '--margin',
            help='Specify tile margin in pizels', default=1, type=int)
    return parser.parse_args()

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
            tile_table = load_tile_table(filename, self.width,
                                               self.height)
            self.cache[key] = tile_table
            return tile_table

def load_tile_table(filename, width, height):
    margin = cli_args.margin
    image = pygame.image.load(filename).convert_alpha()
    img_width, img_height = image.get_size()
    sheet_dims = (ceil(img_width / (width + margin)),
            ceil(img_height / (height + margin)))
    print('{}: {} x {}'.format(filename, *sheet_dims))
    tile_table = []
    for tile_x in range(sheet_dims[0]):
        line = []
        tile_table.append(line)
        for tile_y in range(sheet_dims[1]):
            x_loc = tile_x * (width + cli_args.margin)
            y_loc = tile_y * (height + cli_args.margin)
            rect = (x_loc, y_loc, width, height)
            line.append(image.subsurface(rect))
    return tile_table

if __name__ == '__main__':
    # When invoked as a script, display the passed tilemap
    # tiles split and slightly separated
    this.cli_args = cli()
    pygame.init()
    screen = pygame.display.set_mode((913, 496))
    screen.fill((255, 255, 255))
    table = load_tile_table(cli_args.filename,
                    cli_args.column_px, cli_args.row_px)
    for x, row in enumerate(table):
        for y, tile in enumerate(row):
            x_loc = x * cli_args.column_px
            y_loc = y * cli_args.row_px
            screen.blit(tile, (x_loc, y_loc))
    pygame.display.flip()

    # Wait for input after displaying the tile map
    while pygame.event.wait().type != pygame.locals.QUIT:
        pass
