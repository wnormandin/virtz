#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

from models import MapTile, Base
this = sys.modules[__name__]


class TileFactory:
    ''' Factory class to return instantiated MapTiles '''
    def __init__(self, db_path):
        session_init(db_path)
        self.engine = engine
        self.session = session

    def get_tile(self, char, position):
        ''' Returns a MapTile object matching the passed name.
            Used in map generation and conversion from saved data.
        '''
        base_tile = self.session.query(
                MapTile).filter(MapTile.char == char).one()
        base_tile.position = position
        return base_tile


tiles = [
        ('~', 'water', False, False, False, True, 1, 3),
        ('.', 'grass', False, False, False, False, 0, 5),
        (',', 'grass_border', False, False, False, True, 16, 3),
        ('<', 'grass_rocks', False, False, False, False, 1, 9),
        ('>', 'grass_flower_orange', False, False, False, True, 7, 3),
        ('/', 'grass_flower_white', False, False, False, True, 10, 3),
        ('?', 'grass_flower_blue', False, False, False, True, 13, 3),
        (':', 'dirt', False, False, False, False, 10, 8),
        (';', 'dirt_border', False, False, False, True, 10, 8),
        ('|', 'dirt_path_ns', False, False, False, False, 7, 9),
        ('-', 'dirt_path_ew', False, False, False, False, 8, 9),
        ('_', 'clay', False, False, False, False, 16, 8),
        ('=', 'clay_border', False, False, False, True, 16, 8),
        ('+', 'clay_path_ns', False, False, False, False, 13, 9),
        ('^', 'clay_path_ew', False, False, False, False, 14, 9),
        ('s', 'sand', False, False, False, False, 22, 8),
        ('S', 'sand_border', False, False, False, True, 22, 8),
        ('%', 'castle_wall_gray', True, True, False, False, 14, 22),
        ('$', 'castle_wall_desert', True, True, False, False, 14, 15),
        ('d', 'stairs_down_gray', False, False, False, False, 18, 22),
        ('u', 'stairs_up_gray', False, False, False, False, 18, 21),
        ('D', 'stairs_down_desert', False, False, True, False, 18, 14),
        ('U', 'stairs_up_desert', False, False, True, False, 18, 13),
        ('#', 'door_wood', False, True, False, False, 0, 33),
        ('@', 'door_bars', False, True, False, False, 0, 34),
        ('F', 'fence_wood', False, True, False, False, 25, 48)
        ]

def session_init(db_path=None):
    db_str = 'sqlite:///{}'.format(sys.argv[1]) if db_path is None else 'sqlite:///{}'.format(db_path)
    this.engine = create_engine(db_str)
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    this.session = DBSession()

if __name__ == '__main__':
    session_init()
    print('Generating tiles...')
    for tile in tiles:
        char, name, wall, block, stairs, edge, row, col = tile
        item = MapTile(char=char, name=name, wall=wall, blocking=block,
                       stairs=stairs, has_edges=edge, tile_row=row,
                       tile_col=col)
        session.add(item)
        print(' -  {}'.format(name))
    session.commit()
    print('Tiles written to {}'.format(sys.argv[1]))
