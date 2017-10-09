#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import queue
import threading
import pygame

from game.characters import CharacterFactory
from game.levels import LevelMap
from game.display import DisplayManager
from game.util import Pathfinder
from game.load_tilemap import TileCache

this = sys.modules[__name__]
BASE_PATH = os.getcwd()

class Game:
    db_path = os.path.join(BASE_PATH, 'data/game_data.db')
    tile_map = os.path.join(BASE_PATH, 'resources/world_tilemap.png')
    char_map = os.path.join(BASE_PATH, 'resources/characters.png')
    game_map = os.path.join(BASE_PATH, 'data/test_map')  # for testing
    start_point = (2, 2, 0)     # for testing
    starting_virtz = 5          # for testing
    tile_w = 16
    tile_h = 16
    tile_m = 1

    def __init__(self):
        self.game_over = False
        self.display = DisplayManager()
        self.display_mode = (1024, 768) # Set initial resolution
        self.display.screen = self.display_mode
        self.sprite_cache = TileCache()[self.char_map]

        self.clock = pygame.time.Clock()

        self.task_q = queue.Queue(100)
        self.msg_q = queue.Queue(100)
        self.log_q = queue.Queue(10)
        self.q_lock = threading.Lock()
        queues = (self.task_q, self.msg_q, self.log_q, self.q_lock)

        self.level_map = LevelMap(self.tile_map, level_map=self.game_map, db_path=self.db_path)
        self.pathfinder = Pathfinder(self.level_map)
        self.virt_factory = CharacterFactory(self.db_path, queues, self.pathfinder, self.sprite_cache)
        self.virt_pool = {}
        self.item_pool = {}

    def _explore_tiles(self):
        positions = [self.virt_pool[virt_id].position for virt_id in self.virt_pool]
        self.level_map.explore(positions)

    def _get_messages(self):
        entries = []
        while not self.msg_q.empty():
            msg = self.msg_q.get_nowait()
            if msg is not None:
                entries.append(msg)
        return entries

    def _send_msg(self, message):
        self.msg_q.put(message)

    def _process_messages(self):
        msg_list = self._get_messages()
        for msg in msg_list:
            req = msg.get('request')
            if req == 'items':
                item_type = msg.get('item_type')
                if item_type is not None:
                    items = self._items(item_filter)
                else:
                    items = self._items()
                self.msg_q.task_done()
                self._send_msg({'id': msg['id'], 'items': items})

    def _print_logs(self):
        for msg in self._get_log_messages():
            print(msg)

    def _get_log_messages(self):
        entries = []
        while not self.log_q.empty():
            entries.append(self.log_q.get_nowait())
        return entries

    def _items(self, item_filter=None):
        retval = []
        for item_id in self.item_pool:
            item = self.item_pool[item_id]
            if item_filter is not None:
                if item.item_type == item_filter:
                    retval.append(item)
            else:
                retval.append(item)
        return retval

    def _prepare(self):
        self.level_map.prepare()
        for n in range(self.starting_virtz):
            # Instantiate and save virt list
            virt = self.virt_factory.get_virt(self.start_point)
            self.virt_pool[virt.id] = virt

    def _start_virtz(self):
        # Start virt worker threads
        for virt in self.virt_pool:
            self.virt_pool[virt].level_map = self.level_map
            self.virt_pool[virt].start()

    def _print_map(self):
        # blit MapTile images to the screen
        #self.display.screen.fill((255, 255, 255))
        for p in self.level_map.world_map:
            if p[2] == self.level_map.level:
                x_loc = p[0] * self.tile_w
                y_loc = p[1] * self.tile_h
                tile = self.level_map[p]
                self.display.screen.blit(self.level_map.get_maptile_image(tile), (x_loc, y_loc))

    def _print_items(self):
        # process item sprites
        for item_id in self.item_pool:
            item = self.item_pool[item_id]
            x, y, z = item.position
            x_loc = x * self.tile_w
            y_loc = y * self.tile_h
            if z == self.level_map.level:
                self.display.screen.blit(item.sprite, (x_loc, y_loc))

    def _print_virtz(self):
        # process virt sprites
        for virt_id in self.virt_pool:
            virt = self.virt_pool[virt_id]
            x, y, z = virt.position
            x_loc = x * self.tile_w
            y_loc = y * self.tile_h
            if z == self.level_map.level:
                self.display.screen.blit(virt.sprite, (x_loc, y_loc))

    def _pre_loop(self):
        self._explore_tiles()
        self._print_logs()
        self._print_map()
        self._print_items()
        self._print_virtz()
        pygame.display.flip()

    def _flash_map(self):
        for p in self.level_map.world_map:
            if p[2] == self.level_map.level:
                x_loc = p[0] * self.tile_w
                y_loc = p[1] * self.tile_h
                tile = self.level_map[p]
                self.display.screen.blit(self.level_map.default_tile, (x_loc, y_loc))

    def game_loop(self):
        self._prepare()
        self._start_virtz()
        self._flash_map()
        while not self.game_over:
            self._pre_loop()
            self.clock.tick(2)
            for event in pygame.event.get():
                # capture keypresses or quit
                if event.type == pygame.locals.QUIT:
                    self.game_over = True
                elif event.type == pygame.locals.KEYDOWN:
                    # Not doing anything with these yet
                    if event.key == pygame.K_q:
                        self.game_over = True

if __name__ == '__main__':
    game = Game()
    game.game_loop()
