#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import copy

from .models import MapTile, MapItem, Task, Base
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
        base_tile = copy.deepcopy(self.session.query(
                MapTile).filter(MapTile.char == char).one())
        base_tile.position = position
        return base_tile

class ItemFactory:
    ''' Factory class to return instantiated MapItems '''
    def __init__(self, db_path):
        session_init(db_path)
        self.engine = engine
        self.session = session

    def get_item(self, char, position, name=None):
        if name is not None:
            base_item = copy.deepcopy(self.session.query(
                MapItem).filter(MapItem.name == name).one())
        else:
            base_item = copy.deepcopy(self.session.query(
                MapItem).filter(MapItem.char == char).one())
        base_item.position = position
        return base_item


tiles = [
        ('~', 'water', False, True, False, True, 1, 3, 2, 'swimming'),
        ('.', 'grass', False, False, False, False, 0, 5, 1, ''),
        (',', 'grass_border', False, False, False, True, 16, 3, 1, ''),
        (':', 'dirt', False, False, False, False, 10, 8, 1, ''),
        (';', 'dirt_border', False, False, False, True, 10, 8, 1, ''),
        ('|', 'dirt_path_ns', False, False, False, False, 7, 9, 1, ''),
        ('-', 'dirt_path_ew', False, False, False, False, 8, 9, 1, ''),
        ('_', 'clay', False, False, False, False, 16, 8, 1, ''),
        ('=', 'clay_border', False, False, False, True, 16, 8, 1, ''),
        ('s', 'sand', False, False, False, False, 22, 8, 2, ''),
        ('S', 'sand_border', False, False, False, True, 22, 8, 2, ''),
        ('%', 'castle_wall_gray', True, True, False, False, 14, 22, 1, ''),
        ('$', 'castle_wall_desert', True, True, False, False, 14, 15, 1, ''),
        ('d', 'stairs_down_gray', False, False, False, False, 18, 22, 1, ''),
        ('u', 'stairs_up_gray', False, False, False, False, 18, 21, 1, ''),
        ('D', 'stairs_down_desert', False, False, True, False, 18, 14, 1, ''),
        ('U', 'stairs_up_desert', False, False, True, False, 18, 13, 1, '')
        ]

items = [
        ('<', 'rocks', False, False, True, False, False, 0, 1, 9, 1, None, False, False),
        ('>', 'flower_orange', False, False, True, False, False, 0, 9, 29, 1, None, False, False),
        ('/', 'flower_white', False, False, True, False, False, 0, 9, 31, 1, None, False, False),
        ('?', 'flower_blue', False, False, True, False, False, 0, 9, 28, 1, None, False, False),
        ('p', 'flower_purple', False, False, True, False, False, 0, 9, 30, 1, None, False, False),
        ('+', 'clay_path_ns', False, False, False, False, False, 0, 13, 9, 1, None, False, False),
        ('^', 'clay_path_ew', False, False, False, False, False, 0, 14, 9, 1, None, False, False),
        ('#', 'door_wood', False, False, True, False, False, 0, 0, 33, 1, None, False, False),
        ('@', 'door_bars', False, False, True, False, False, 0, 0, 34, 1, None, False, False),
        ('F', 'fence_wood', False, False, True, False, False, 0, 25, 48, 1, None, False, False),
        ('b', 'bed', False, False, False, False, False, 0, 3, 12, 10, None, False, False),
        ('t', 'tree', False, False, True, False, False, 0, 9, 18, 1, None, False, False),
        ('C', 'chest', False, False, True, False, False, 8, 7, 15, 1, None, False, False),
        ('w', 'well', False, False, True, False, False, 0, 7, 26, 10, None, False, True),
        ('f', 'berry_bush', False, False, True, False, False, 10, 9, 24, 1, 'berry', False, False),
        ('T', 'fruit_tree', False, False, True, False, False, 10, 9, 23, 1, 'fruit', False, False),
        ('o', 'fruit', True, True, False, False, False, 0, 9, 32, 5, None, True, False),
        ('O', 'berry', True, True, False, False, False, 0, 9, 33, 5, None, True, False),
        ('W', 'wood', True, True, False, False, False, 0, 22, 53, 1, None, False, False),
        ('S', 'stone', True, True, False, False, False, 0, 17, 44, 1, None, False, False)
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
        char, name, wall, block, stairs, edge, row, col, move_cost, skill = tile
        item = MapTile(char=char, name=name, wall=wall, blocking=block,
                       stairs=stairs, has_edges=edge, tile_row=row,
                       tile_col=col, movement_cost=move_cost, required_skill=skill)
        session.add(item)
        print(' -  {}'.format(name))

    print('Generating items...')
    for item in items:
        char, name, consumable, can_get, can_destroy, destroyed, locked, cont_limit, row, col, power, fill, is_food, is_drink = item
        item = MapItem(char=char, name=name, can_get=can_get, consumable=consumable,
                can_destroy=can_destroy, destroyed=destroyed, tile_row=row,
                container_limit=cont_limit, locked=locked, tile_col=col, is_food=is_food,
                is_drink=is_drink, power=power, fill_with=fill)
        session.add(item)
        print(' -  {}'.format(name))

    session.commit()
    print('Tiles written to {}'.format(sys.argv[1]))
