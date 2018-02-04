#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import queue
import threading
import pygame
import argparse

from game.characters import CharacterFactory
from game.levels import LevelMap
from game.display import DisplayManager
from game.util import Pathfinder, InterruptHandler
from game.load_tilemap import TileCache

from game.models import MapTile, Virt, MapItem

this = sys.modules[__name__]
BASE_PATH = os.getcwd()

MAPTILE_OBJ = 0
VIRT_OBJ = 1
MAPITEM_OBJ = 2

def game_item_type(item):
    if isinstance(item, MapTile):
        return MAPTILE_OBJ
    elif isinstance(item, Virt):
        return VIRT_OBJ
    elif isinstance(item, MapItem):
        return MAPITEM_OBJ

class Game:
    # path to the game's SQLite3 database
    db_path = os.path.join(BASE_PATH, 'data/game_data.db')

    # path to the game map and character tile maps, 
    # be sure tile_w, tile_h, and tile_m match
    tile_map = os.path.join(BASE_PATH, 'resources/world_tilemap.png')
    char_map = os.path.join(BASE_PATH, 'resources/characters.png')

    # game_map will point to a map generator class eventually,
    # for now using a static test map to build out the mechanics
    game_map = os.path.join(BASE_PATH, 'data/test_map')  # for testing

    game_font = os.path.join(BASE_PATH, 'resources/Inconsolata.otf')

    # start_point will point to a generator class eventuall,
    # for now statically set
    start_point = (2, 2, 0)     # virt starting positions
    tile_w = 16                 # tile width for tile_map/char_map
    tile_h = 16                 # tile height for tile_map/char_map
    tile_m = 1                  # margin between tiles in tile_map/char_map

    # Reference values for the three game side window sections
    SELECTION_WINDOW = 0    # Upper-right corner window (932, 0) - (1280, 255)
    TILE_CONTENTS = 1       # Middle window (932, 258) - (1280, 512)
    TILE_META = 2           # Lower left window (932, 515) - (1280, 768)

    def __init__(self):
        if cli_args.test:
            self.starting_virtz = 5
            self.DEBUG = True
        else:
            self.starting_virtz = 5          # starting virt count
            self.DEBUG = False

        self.game_over = False

        # Initialize the display manager
        # (offload more of the display functions to this class)
        self.display = DisplayManager()
        self.display_mode = (1280, 768), cli_args.fullscreen # Set initial resolution
        self.display.screen = self.display_mode

        # The first read of the TileCache will cache all tiles in the specified file
        self.sprite_cache = TileCache()[self.char_map]

        # Internal tick counter
        self._tick_count = 0

        # Marks the x,y,z position of the selected MapTile
        self._selected = None

        # Stores the currently selected MapItem or Virt object
        self._selected_object = None

        # List of tuples (Rect, obj) for clickable text items in the side menu
        self.selectable = []

        # Initiate the game clock, queues, and thread lock
        self.clock = pygame.time.Clock()
        queues = self._threadmaster()

        # Initialize the LevelMap object which manages the world map and provides
        # conveience methods for MapItem instances
        self.level_map = LevelMap(self.tile_map, level_map=self.game_map, db_path=self.db_path)

        # Initialize the A* pathfinder
        self.pathfinder = Pathfinder()

        # The CharacterFactory is used to generate virtual villagers
        self.virt_factory = CharacterFactory(self.db_path, queues, self.pathfinder, self.sprite_cache)
        self.virt_pool = {}

        # Set up the game font renderers
        pygame.font.init()
        self.font_size = 15
        self.small_font_size = 11
        self.font_renderer = pygame.font.Font(self.game_font, self.font_size)
        self.small_font_renderer = pygame.font.Font(self.game_font, self.small_font_size)

    def _threadmaster(self):

        ''' The _threadmaster function initializes queues and threading lock/event objects '''

        # The task queue contains user-generated tasks created
        # via the interface
        self.task_q = queue.Queue(100)

        # The message queue allows the master thread to asynchronously communicate
        # with virt threads, answering virt requests for game info
        self.msg_q = queue.Queue(100)

        # The log queue receives log entries from virt worker threads to be
        # handled by the master thread
        self.log_q = queue.Queue(20)

        # Threading lock to sync threads
        self.q_lock = threading.Lock()

        # Kill switch for virt threads
        self.kill_event = threading.Event()
        self.kill_event.clear()

        return self.task_q, self.msg_q, self.log_q, self.q_lock, self.kill_event

    def _explore_tiles(self):

        ''' Detect and mark newly explored tiles each turn '''

        positions = [self.virt_pool[virt_id].position for virt_id in self.virt_pool]
        self.level_map.explore(positions)

    def _get_messages(self):

        ''' Pull messages from the message queue '''

        entries = []
        while not self.msg_q.empty():
            msg = self.msg_q.get_nowait()
            if msg is not None:
                entries.append(msg)
        return entries

    def _send_msg(self, message):

        ''' Send a message to the message queue
            The message should be a dictionary with a key 'id' directing it to
            a specific Virt thread
        '''
        self.msg_q.put(message)

    def _process_messages(self):

        ''' Process message requests which come through the message queue '''

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

        ''' Pull and print log entries arriving in the queue since the last loop '''

        for msg in self._get_log_messages():
            print(msg)

    def _get_log_messages(self):

        ''' Pull log entries from the queue '''

        entries = []
        while not self.log_q.empty():
            entries.append(self.log_q.get_nowait())
        return entries

    def _prepare(self):

        ''' Performs preparatory steps to be completed before the initial game loop '''

        self.level_map.prepare()    # Populate MapTiles and MapItems
        self.pathfinder.graph = self.level_map
        for n in range(self.starting_virtz):
            # Instantiate and save virt list
            virt = self.virt_factory.get_virt(self.start_point)
            self.virt_pool[virt.id] = virt

    def _start_virtz(self):

        ''' Start virt worker threads '''

        for virt in self.virt_pool:
            self.virt_pool[virt].level_map = self.level_map
            self.virt_pool[virt].start()

    def _print_map(self):

        ''' Blit MapTile images to the screen '''

        #self.display.screen.fill((255, 255, 255))
        for p in self.level_map.world_map:
            if p[2] == self.level_map.level:
                x_loc = p[0] * self.tile_w
                y_loc = p[1] * self.tile_h
                tile = self.level_map[p]
                self.display.screen.blit(self.level_map.get_maptile_image(tile),
                        (x_loc, y_loc))

    def _print_items(self):

        ''' Blit item sprites '''

        for item in self.level_map.items:
            if item.container is None:  # Only interested in map-level items
                x, y, z = item.position
                x_loc = x * self.tile_w
                y_loc = y * self.tile_h
                if z == self.level_map.level:
                    self.display.screen.blit(item.sprite, (x_loc, y_loc))

    def _print_virtz(self):

        ''' Blit virt sprites '''

        for virt_id in self.virt_pool:
            virt = self.virt_pool[virt_id]
            x, y, z = virt.position
            x_loc = x * self.tile_w
            y_loc = y * self.tile_h
            if z == self.level_map.level:
                self.display.screen.blit(virt.sprite, (x_loc, y_loc))

    def tick(self):

        ''' If the game is not paused, process the main loop '''

        if not self.paused:
            self.clock.tick(8)
            self._tick_count += 1

    @property
    def game_date(self):

        ''' Generate the game month, day, and minutes and return a string
            representation
        '''

        base_count = self._tick_count // 4
        hours_elapsed = base_count // 60
        mins_in = base_count % 60
        days_elapsed = hours_elapsed // 24
        hours_in = hours_elapsed % 24
        sep = 'pm' if hours_in > 12 else 'am'
        months_elapsed = days_elapsed // 30
        days_in = days_elapsed % 30
        date_str = 'Month {}, '.format(months_elapsed+1)
        date_str += 'day {}, '.format(days_in)
        date_str += '{}:{:02} {}'.format(hours_in, mins_in, sep)
        return date_str

    @property
    def night(self):

        ''' Indicates whether it is daytime (False) or nighttime (True) '''

        d = self.game_date
        # 12 hour cycles for simplicity for now
        return d['hours_in'] < 6 or d['hours_in'] >= 6

    def _pre_loop(self):

        ''' Events to run on every iteration BEFORE the main loop '''

        self._explore_tiles()
        self._print_logs()
        self.display.screen.fill((0, 0, 0))
        self._debug_info()
        self._print_map()
        self._render_borders()
        self._print_items()
        self._print_virtz()
        if self._selected is not None:
            self._render_selected()
            self._selected_box()
            self._render_tile_contents(self._selected_tile_contents())
        if self._selected_object is not None:
            # Print item meta in selection window
            self._render_selected_meta(self._selected_object)
            self._selected_obj_box()
        pygame.display.flip()

    def _cell_to_px(self, position):

        ''' Convert cell to px '''

        x, y, z = position
        return x * self.tile_w, y * self.tile_h, z

    def _px_to_cell(self, position):

        ''' Convert px to cell '''

        x, y, z = position
        return x // self.tile_w, y // self.tile_h, z

    def _selected_box(self):

        ''' Prints the box highlighting selected tiles in the game map '''

        x0, y0, _ = self._cell_to_px(self._selected)
        rect = pygame.Rect(x0, y0, self.tile_w, self.tile_h)
        mod = self._tick_count % 3
        if mod == 0:
            col = (255, 0, 0)
        elif mod == 1:
            col = (255, 70, 0)
        elif mod == 2:
            col = (255, 140, 0)
        pygame.draw.rect(self.display.screen, col, rect, 1)

    def _selected_obj_box(self):

        ''' Prints a box around selected items or virtz '''

        x0, y0, _ = self._cell_to_px(self._selected_object.position)
        rect = pygame.Rect(x0, y0, self.tile_w, self.tile_h)
        mod = self._tick_count % 3
        if mod == 0:
            col = (0, 0, 255)
        elif mod == 1:
            col = (135, 206, 250)
        elif mod == 2:
            col = (224, 255, 255)
        pygame.draw.rect(self.display.screen, col, rect, 1)

    def _debug_info(self):

        ''' Capture mouse position and render labels '''

        timestamp = self.font_renderer.render(self.game_date, 1, (255, 255, 255))
        selection = self.font_renderer.render('Selected: {}'.format(self._selected), 1, (255, 255, 255))
        self.display.screen.blit(timestamp, (3, 732))
        self.display.screen.blit(selection, (3, 748))
        if self.DEBUG:
            x, y = pygame.mouse.get_pos()
            x0, y0 = x // self.tile_w, y // self.tile_h
            mouse_str = 'Mouse @ ({}, {}) / ({}, {})'.format(x, y, x0, y0)
            mouse_loc = self.font_renderer.render(mouse_str, 1, (255, 255, 255))
            self.display.screen.blit(mouse_loc, (3, 716))
        if self.paused:
            pause_msg = self.font_renderer.render('Paused', 1, (0, 255, 50))
            self.display.screen.blit(pause_msg, (250, 748))

    def _flash_map(self):

        ''' Fill the map with the default tile '''

        for p in self.level_map.world_map:
            if p[2] == self.level_map.level:
                x_loc = p[0] * self.tile_w
                y_loc = p[1] * self.tile_h
                tile = self.level_map[p]
                self.display.screen.blit(self.level_map.default_tile, (x_loc, y_loc))

    def _render_virt_meta(self, virt):

        ''' Render virt metadata for the selection window '''

        # show virt details
        virt_meta = 'Virt Details\n'
        virt_meta += 'Name:          {}\n'.format(virt.name)
        virt_meta += 'Position:      {}\n'.format(virt.position)
        virt_meta += 'Hit Points:    {} / {}\n'.format(virt.hit_points, virt.max_hp)
        virt_meta += 'Stamina:       {} / {}\n'.format(virt.energy_left, virt.daily_energy)
        virt_meta += 'Tired:         {}\n'.format(virt.need_rest)
        virt_meta += 'Hungry:        {}\n'.format(virt.need_food)
        virt_meta += 'Thirsty:       {}\n'.format(virt.need_drink)
        virt_meta += 'Moving To:     {}\n'.format(virt.destination)

        fears = []
        if virt.fears_bears: fears.append('bears')
        if virt.fears_wolves: fears.append('wolves')
        if virt.fears_bats: fears.append('bats')
        if virt.fears_caves: fears.append('caves')
        if virt.fears_woods: fears.append('woods')
        if virt.fears_water: fears.append('water')
        if virt.fears_dark: fears.append('dark')
        if fears:
            virt_meta += 'Fears: {}\n'.format(', '.join(fears))
        else:
            virt_meta += 'Fears:           None\n'

        if self.DEBUG:
            if virt.current_task is None:
                virt_meta += 'Current Task:  Idle\n'
            else:
                virt_meta += 'Current Task:  {} ({:.0%})\n'.format(virt.current_task.name,
                        virt.current_task.work_remaining)
            virt_meta += 'Hunger Score:  {}\n'.format(virt.hunger_score)
            virt_meta += 'Thirst Score:  {}\n'.format(virt.thirst_score)
            virt_meta += 'Alive:         {}\n'.format(virt.alive)
            virt_meta += 'Object_ID:     {}\n'.format(hex(id(virt)))
        virt_meta += '\nCarrying:\n'
        for item in virt.carrying:
            virt_meta += ' ' + item
        return virt_meta

    def _virt_stats(self, v):
        virt_stats = 'Personality:    {}\n'.format(v.personality)
        lazy_label = 'Lazy' if v.lazy <= 0 else 'Industrious'
        virt_stats += 'Activity Level: {}\n'.format(lazy_label)
        follower_label = 'Follower' if v.follower <= 0 else 'Leader'
        virt_stats += 'Confidence:     {}\n'.format(follower_label)
        savage_label = 'Savage' if v.savage <= 0 else 'Civilized'
        virt_stats += 'Demeanor:       {}\n'.format(savage_label)
        ignorant_label = 'Ignorant' if v.ignorant <= 0 else 'Smart'
        virt_stats += 'Intellect:      {}\n'.format(ignorant_label)
        virt_stats += 'Ambition:       {}\n'.format(v.ambition)
        virt_stats += 'Energy:         {}\n'.format(v.energy)
        virt_stats += 'Willpower:      {}\n'.format(v.willpower)
        virt_stats += 'Character:      {}\n'.format(v.character)
        virt_stats += 'Integrity:      {}\n'.format(v.integrity)
        virt_stats += 'Strength:       {}\n'.format(v.strength)
        virt_stats += 'Endurance:      {}\n'.format(v.endurance)
        virt_stats += 'Intelligence:   {}\n'.format(v.intelligence)
        virt_stats += 'Wisdom:         {}\n'.format(v.wisdom)
        virt_stats += 'Dexterity:      {}\n'.format(v.dexterity)
        virt_stats += 'Agility:        {}\n'.format(v.dexterity)
        virt_stats += 'Charisma:       {}\n'.format(v.charisma)
        virt_stats += 'Melee:          {}\n'.format(v.melee)
        virt_stats += 'Ranged:         {}\n'.format(v.ranged)
        virt_stats += 'Defense:        {}\n'.format(v.defense)
        virt_stats += 'Construction:   {}\n'.format(v.construction)
        virt_stats += 'Crafting:       {}\n'.format(v.crafting)
        virt_stats += 'Magic:          {}\n'.format(v.magic)
        virt_stats += 'Swimming:       {}\n'.format(v.swimming)
        virt_stats += 'Leadership:     {}'.format(v.leadership)
        return virt_stats

    def _render_selected_meta(self, selection):
        item_type = game_item_type(selection)
        if item_type == MAPTILE_OBJ:
            meta = self._render_tile_meta(selection)
            window = self.TILE_META
        elif item_type == VIRT_OBJ:
            meta = self._render_virt_meta(selection)
            window = self.SELECTION_WINDOW
            stats = self._virt_stats(selection)
            self._side_window(stats, self.SELECTION_WINDOW, v_start=1115)
        elif item_type == MAPITEM_OBJ:
            meta = self._render_item_meta(selection)
            window = self.SELECTION_WINDOW
        self._side_window(meta, window)

    def _render_item_meta(self, item):
        # show item details
        item_meta = 'Item Details\n'
        item_meta += 'Name:         {}\n'.format(item.name)
        item_meta += 'Position:     {}\n'.format(item.position)
        item_meta += 'Is Container: {}\n'.format(item.is_container)
        if item.is_container:
            item_meta += 'Contents:    {}/{} items\n'.format(len(item.contents), item.container_limit)
        if item.container is not None:
            item_meta += 'Inside:       {} ({})\n'.format(item.container.name, item.container.position)
        item_meta += 'Locked:    {}\n'.format(item.locked)
        if self.DEBUG:
            item_meta += 'Power:          {}\n'.format(item.power)
            item_meta += 'Consumable:     {}\n'.format(item.consumable)
            item_meta += 'Destroyable:    {}\n'.format(item.can_destroy)
            item_meta += 'Object_ID:      {}\n'.format(hex(id(item)))
        return item_meta

    def _render_tile_meta(self, tile):
        # show selected tile metadata
        tile_meta = 'Map Tile Details\n'
        tile_meta += 'Name:           {}\n'.format(tile.name)
        tile_meta += 'Position:       {}\n'.format(tile.position)
        tile_meta += 'Blocked:        {}\n'.format(tile.blocking)
        tile_meta += 'Explored:       {}\n'.format(tile.explored)
        tile_meta += 'Visited:        {}\n'.format(tile.visited)
        if self.DEBUG:
            tile_meta += 'Wall:           {}\n'.format(tile.wall)
            tile_meta += 'Passable:       {}\n'.format(tile.passable)
            tile_meta += 'Movement Cost:  {}\n'.format(tile.movement_cost)
            tile_meta += 'Required Skill: {}\n'.format(tile.required_skill)
            tile_meta += 'Object_ID:      {}\n'.format(hex(id(tile)))
        return tile_meta

    def _side_window(self, meta_string, destination, v_start=None):
        if destination == self.SELECTION_WINDOW:
            h_start = 3
            small = True
        elif destination == self.TILE_CONTENTS:
            h_start = 257
            small = True
        elif destination == self.TILE_META:
            h_start = 516
            small = False
        else:
            raise ValueError
        self._multiline_text(meta_string, h_start, v_start=v_start, small=small)

    def _render_tile_contents(self, tile_contents):
        self.selectable = []
        v_start = 936
        h_start = 260
        if len(tile_contents) > 14:
            renderer = self.small_font_renderer
            step = 12
        else:
            renderer = self.font_renderer
            step = 18
        for item in tile_contents:
            name, obj = item
            meta_text = renderer.render(name, 1, (255, 255, 255))
            meta_rect = meta_text.get_rect()
            meta_rect.move_ip(v_start, h_start)
            self.display.screen.blit(meta_text, (v_start, h_start))
            meta_rect.inflate_ip(2, 2)
            pygame.draw.rect(self.display.screen, (0, 10, 225), meta_rect, 2)
            self.selectable.append((meta_rect, obj))
            h_start += step

    def _multiline_text(self, text, h_start, v_start=None, small=False):
        h_px = h_start
        v_start = v_start if v_start is not None else 935
        for line in text.split('\n'):
            if not small:
                step = 16
                meta_text = self.font_renderer.render(line, 1, (255, 255, 255))
            else:
                step = 10
                meta_text = self.small_font_renderer.render(line, 1, (255, 255, 255))

            self.display.screen.blit(meta_text, (v_start, h_px))
            h_px += step

    def _render_borders(self):
        gray = (49, 79, 79)
        step = 768 // 3
        cur = step
        pygame.draw.line(self.display.screen, gray, (0, 434), (929, 434), 3)
        pygame.draw.line(self.display.screen, gray, (929, 0), (929, 768), 3)
        pygame.draw.line(self.display.screen, gray, (0, 450), (929, 450), 3)
        for n in range(3):
            pygame.draw.line(self.display.screen, gray, (929, cur), (1280, cur), 3)
            cur += step

    def _render_selected(self):

        ''' Display the selected tile / obj  information '''

        self._render_selected_meta(self.level_map[self._selected])

    def _selected_tile_contents(self):

        ''' Gather items in the currently selected tile or container '''

        selected = []
        virts = [self.virt_pool[v] for v in self.virt_pool if self.virt_pool[v].position == self._selected]
        for virt in virts:
            selected.append((virt.name, virt))
        items = self.level_map.find_item(position=self._selected)
        for item in items:
            selected.append((item.name, item))
        return selected


    def _post_loop(self):
        pass

    def _failsafe(self):
        self.kill_event.set()
        print(' -  Failsafe triggered, kill signal sent to virtz\n -  Ctrl+C to force quit')
        pygame.display.quit()
        pygame.quit()
        self.game_over = True

    def select(self, position):
        # Check whether click was a selectable object
        for item in self.selectable:
            rect, obj = item
            if rect.collidepoint(position):
                self._selected_object = obj
                return

        # If the click didn't correspond to a selectable object, process map selection
        new_selection = position[0] // self.tile_w, position[1] // self.tile_h, self.level_map.level
        if self.level_map.in_map(new_selection):
            self._selected = new_selection
            print('[!] Tile Selected: {}'.format(self._selected))

    def deselect(self):
        self._selected = None

    def game_loop(self):
        self._prepare()
        self._start_virtz()
        self._flash_map()
        pygame.display.flip()
        self.paused = False
        with InterruptHandler() as h:
            while not self.game_over:
                if h.interrupted:
                    print('\n[!] Keyboard Interrupt Detected')
                    self._failsafe()
                    continue
                try:
                    self._pre_loop()
                    self.tick()
                    for event in pygame.event.get():
                        if event.type == pygame.locals.QUIT:
                            self._failsafe()
                            continue
                        elif event.type == pygame.locals.KEYDOWN:
                            if event.key == pygame.K_q:
                                self._failsafe()
                                continue
                            elif event.key == pygame.K_SPACE:
                                self.paused = not self.paused
                                for v in self.virt_pool:
                                    self.virt_pool[v].pause = self.paused
                            elif event.key == pygame.K_F1:
                                self.DEBUG = not self.DEBUG
                            elif event.key == pygame.K_ESCAPE:
                                self._selected = None
                                self._selected_object = None
                                continue
                            elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                                if self._selected is not None:
                                    if event.key == pygame.K_UP:
                                        move = self._selected[0], self._selected[1]-1, self._selected[2]
                                    elif event.key == pygame.K_DOWN:
                                        move = self._selected[0], self._selected[1]+1, self._selected[2]
                                    elif event.key == pygame.K_LEFT:
                                        move = self._selected[0]-1, self._selected[1], self._selected[2]
                                    elif event.key == pygame.K_RIGHT:
                                        move = self._selected[0]+1, self._selected[1], self._selected[2]
                                    if move in self.level_map.world_map:
                                        self._selected = move
                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            button = event.button
                            if button == 1:
                                self.select(event.pos)
                    self._post_loop()
                except InterruptedError:
                    continue

def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('-F', '--fullscreen', action='store_true',
            help='Run the game in fullscreen mode (default=OFF)')
    parser.add_argument('-t', '--test', action='store_true',
            help='Enable test mode (1 virt, DEBUG on)')
    return parser.parse_args()

if __name__ == '__main__':
    this.cli_args = cli()
    game = Game()
    game.game_loop()
