#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Loads tilemaps, slices, returns a dict with x,y coordinates as keys

import sys
from math import ceil
import pygame
import pygame.locals
import argparse

# grab a module instance
this = sys.modules[__name__]

def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--map', help='Path to tilemap')
    parser.add_argument('-M', '--margin', help='Margin width in px',
            default=1, type=int)
    parser.add_argument('-s', '--scale', help='Specify image scale in px',
            default='16x16')
    return parser.parse_args()

class TileCache:
    """ Lazily load tilesets into the global cache """

    def __init__(self, width=16, height=None, margin=1):
        self.width = width
        self.height = height or width
        self.margin = margin
        self._cache = {}

    def __getitem__(self, filename):
        key = (filename, self.width, self.height)
        try:
            return self._cache[key]
        except KeyError:
            new_table = load_tile_table(filename, self.width,
                    self.height, self.margin)
            self._cache[key] = new_table
            return new_table

def load_tile_table(filename, w, h, m):
    ''' w=width(px), h=height(px), m=margin(px) '''

    image = pygame.image.load(filename).convert_alpha()
    img_width, img_height = image.get_size()
    sheet_dims = (ceil(img_width / (w + m)),
            ceil(img_height / (h + m)))
    print('{}: {} x {}'.format(filename, *sheet_dims))
    tile_table = {}
    for x in range(sheet_dims[0]):
        for y in range(sheet_dims[1]):
            x_loc = x * (w + m)
            y_loc = y * (h + m)
            rect = (x_loc, y_loc, w, h)
            tile_table[x,y] = image.subsurface(rect)
    return tile_table

def split_dims(dim_str):
    assert 'x' in dim_str
    x, y = dim_str.split('x')
    try:
        return int(x), int(y)
    except:
        raise AssertionError('Invalid format, required: XxY, i.e. 16x16')
        sys.exit(1)

if __name__ == '__main__':
    this.cli_args = cli()
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    screen.fill((255, 255, 255))
    column_px, row_px = split_dims(cli_args.scale.lower())
    table = load_tile_table(cli_args.map, column_px, row_px, cli_args.margin)
    for x, y in table:
        x_loc = x * column_px
        y_loc = y * row_px
        screen.blit(table[x,y], (x_loc, y_loc))
    pygame.display.flip()

    # Wait for input before exiting
    while pygame.event.wait().type != pygame.locals.QUIT:
        pass
