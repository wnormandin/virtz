#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import datetime
import time
import pygame
import random
import pdb

# async imports
import threading
from queue import Empty

# Database/ORM imports
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy import Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

# Module imports
from .util import distance_3d


Base = declarative_base()


class MapTile(Base):
    __tablename__ = 'tiles'
    id = Column(Integer, primary_key=True)
    char = Column(String(1), nullable=False, default='.')
    name = Column(String(50), nullable=False)

    # Indicates a 'wall' tile which might have edges to be rendered
    wall = Column(Boolean, unique=False, default=False)

    # When blocking is true, pc/npcs may not move into this tile
    blocking = Column(Boolean, unique=False, default=False)

    # Indicates this tile contains stairs down or up
    stairs = Column(Boolean, unique=False, default=False)

    # When has_edges is true, this tile has edge pieces in positions
    # surrounding the specified tile (top, top-left, top-right, left, right
    # bottom, bottom-left, bottom-right)
    has_edges = Column(Boolean, unique=False, default=False)

    # Coordinates for this tile's image in the core tile map
    tile_row = Column(Integer, unique=False)
    tile_col = Column(Integer, unique=False)

    # Explored/Visited flags
    explored = Column(Boolean, unique=False, default=False)
    visited = Column(Boolean, unique=False, default=False)

    # Movement cost penalty
    movement_cost = Column(Integer, unique=False, default=1)

    # Required skill to move
    required_skill = Column(String(15), unique=False)

    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.light = 0

    def __repr__(self):
        return "<MapTile(name={}, wall={}, blocking={}, image_loc={})>".format(
                self.name, self.wall, self.blocking, self.tile_row, self.tile_col)

    @property
    def image_location(self):
        return self.tile_row, self.tile_col

    @property
    def passable(self):
        return not self.blocking
        #return self.explored and not self.blocking

    @property
    def position(self):
        return self._x_pos, self._y_pos, self._z_pos

    @position.setter
    def position(self, position):
        self._x_pos, self._y_pos, self._z_pos = position


class MapItem(Base):
    __tablename__ = 'map_items'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    char = Column(String(1), nullable=False, default='.')

    # When can_get is true, the item may be picked up by a pc/npc in which
    # case the item is typically destroyed on the main map
    can_get = Column(Boolean, unique=False, default=False)

    # When can_destroy is true, the map item may be destroyed,
    # changing to the destroyed image
    can_destroy = Column(Boolean, unique=False, default=False)
    consumable = Column(Boolean, unique=False, default=False)

    # Indicates whether the map item has been destroyed
    destroyed = Column(Boolean, unique=False, default=False)

    # Nonzero values indicate a container-type object
    container_limit = Column(Integer, unique=False, default=0)

    # Indicates a container or door is locked
    locked = Column(Boolean, unique=False, default=False)

    # Coordinates for this tile's base image in the core tile map
    tile_row = Column(Integer, unique=False)
    tile_col = Column(Integer, unique=False)

    # Coordinates for this tile's destroyed image in the core tile map
    destroyed_row = Column(Integer, unique=False)
    destroyed_col = Column(Integer, unique=False)

    # item power impacts processed effects (i.e. rest amount)
    power = Column(Integer, unique=False, default=1)

    # name of item to fill if this is a pre-filled container
    fill_with = Column(String(50), unique=False, nullable=True)

    # Item type indicator
    is_food = Column(Boolean, unique=False, default=False)
    is_drink = Column(Boolean, unique=False, default=False)

    def __repr__(self):
        return '<Item(name={}, position={})>'.format(
                self.name, self.position)

    @property
    def contents(self):
        return [i for i in self.level_map.item_list if i.container is self]

    def add_item(self, item):
        if self.has_room:
            self._contents.append(item)
        else:
            raise AssertionError('No room in container: {}/{}'.format(
                len(self._contents, self.container_limit)))

    def remove_item(self, item):
        self._contents.remove(item)

    @property
    def is_container(self):
        return self.container_limit > 0

    @property
    def has_room(self):
        return len(self.contents) < self.container_limit

    @property
    def item_type(self):
        if self.is_food:
            return 'food'
        elif self.is_drink:
            return 'drink'
        elif '_' in self.name:
            return self.name.split('_')[0]
        else:
            return self.name

    @property
    def image_location(self):
        return self.tile_row, self.tile_col

    @property
    def position(self):
        return self._x_pos, self._y_pos, self._z_pos

    @position.setter
    def position(self, position):
        self._x_pos, self._y_pos, self._z_pos = position

    @property
    def sprite(self):
        return self.image

    @sprite.setter
    def sprite(self, image):
        self.image = image


# Models representing virtz, save game, and other related objects
class Memory(Base):
    __tablename__ = 'memories'
    id = Column(Integer, primary_key=True)
    virt_id = Column(Integer, ForeignKey('virtz.id'), nullable=False)
    memory_type = Column(String(25), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return '<Memory(memory_type={}, timestamp={}, virt_id={})>'.format(
                self.memory_type, self.timestamp, self.virt_id)

class SaveGame(Base):
    __tablename__ = 'saves'
    id = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False)

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)

    # Indicates whether the item is carried by a virt
    owner = Column(Integer, ForeignKey('virtz.id'), nullable=True)

    # Item name
    name = Column(String(25), nullable=False)
    # Item value (for when monetary values are implemented)
    value = Column(Integer, default=0, nullable=False)

    # Metadata
    desc = Column(String(300), nullable=True)
    item_type = Column(String(20), nullable=False)
    unique = Column(Boolean, nullable=False, default=False)
    power = Column(Integer, nullable=False, default=10)

    # Item sprite image location
    sprite_col = Column(Integer, nullable=False)
    sprite_row = Column(Integer, nullable=False)

    # Item map location
    pos_x = Column(Integer, nullable=False, default=0)
    pos_y = Column(Integer, nullable=False, default=0)
    pos_z = Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return '<Item(owner={}, name={}, value={}, image_loc={})>'.format(
                self.owner, self.name, self.value, self.image_location)

    @property
    def sprite(self):
        return self._sprite_image

    @sprite.setter
    def sprite(self, sprite):
        self._sprite_image = sprite

    @property
    def position(self):
        return self.pos_x, self.pos_y, self.pos_z

    @position.setter
    def position(self, position):
        self.pos_x, self.pos_y, self.pos_z = position


class Task:

    def __init__(self, **kwargs):
        self.task_done = False
        self.name = kwargs['name']
        self.game_id = kwargs.get('game_id', None)
        self.pos_x = kwargs.get('pos_x', None)
        self.pos_y = kwargs.get('pos_y', None)
        self.pos_z = kwargs.get('pos_z', None)
        self.skill = kwargs.get('skill', {'endurance':1})
        self.activity_points = kwargs.get('activity_points', 25)
        self.consume_item = kwargs['consume_item']
        self.target_item = kwargs.get('target_item', None)

    def prepare(self):
        self._points_left = self.activity_points
        self.target_item = None
        self._required_items = []
        self._callback = None

    @property
    def work(self):
        return self._points_left / self.activity_points

    @property
    def work_remaining(self):
        return min(1 - (self._points_left / self.activity_points), 1)

    @work.setter
    def work(self, points):
        self._points_left -= points
        if self._points_left <= 0:
            print('[!] Task completed: {}'.format(self.name))
            self.task_done = True

    @property
    def on_complete(self):
        return self._callback

    @on_complete.setter
    def on_complete(self, callback):
        func, _args = callback
        self._callback = func
        self.callback_args = _args

class Virt(Base, threading.Thread):
    __tablename__ = 'virtz'
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('saves.id'), nullable=True)
    name = Column(String(50), nullable=False)
    alive = Column(Boolean, nullable=False, default=True)
    level = Column(Integer, nullable=False, default=1)

    # Virt sprite image location details
    sprite_col = Column(Integer, nullable=False, default=0)
    sprite_row = Column(Integer, nullable=False, default=6)

    # Virt location details
    pos_x = Column(Integer, nullable=False, default=0)
    pos_y = Column(Integer, nullable=False, default=0)
    pos_z = Column(Integer, nullable=False, default=0)

    # Personality name and behaviors
    personality = Column(String(50))
    lazy = Column(Integer, nullable=False, default=0)
    follower = Column(Integer, nullable=False, default=0)
    savage = Column(Integer, nullable=False, default=0)
    ignorant = Column(Integer, nullable=False, default=0)

    # Base attributes
    strength = Column(Integer, nullable=False, default=1)
    endurance = Column(Integer, nullable=False, default=1)
    intelligence = Column(Integer, nullable=False, default=1)
    wisdom = Column(Integer, nullable=False, default=1)
    dexterity = Column(Integer, nullable=False, default=1)
    agility = Column(Integer, nullable=False, default=1)
    charisma = Column(Integer, nullable=False, default=1)

    # Personality- and life-event-driven attributes
    ambition = Column(Integer, nullable=False, default=0)
    energy = Column(Integer, nullable=False, default=0)
    willpower = Column(Integer, nullable=False, default=0)
    character = Column(Integer, nullable=False, default=0)
    integrity = Column(Integer, nullable=False, default=0)

    # Base motivations
    boredom = Column(Integer, nullable=False, default=0)
    hunger = Column(Integer, nullable=False, default=0)
    thirst = Column(Integer, nullable=False, default=0)
    fear = Column(Integer, nullable=False, default=0)

    # Skill points
    melee = Column(Integer, nullable=False, default=1)
    ranged = Column(Integer, nullable=False, default=1)
    defense = Column(Integer, nullable=False, default=1)
    construction = Column(Integer, nullable=False, default=1)
    crafting = Column(Integer, nullable=False, default=1)
    magic = Column(Integer, nullable=False, default=1)
    swimming = Column(Integer, nullable=False, default=1)
    leadership = Column(Integer, nullable=False, default=1)

    # Fear flags
    fears_bears = Column(Boolean, unique=False, default=False)
    fears_wolves = Column(Boolean, unique=False, default=False)
    fears_bats = Column(Boolean, unique=False, default=False)
    fears_caves = Column(Boolean, unique=False, default=False)
    fears_woods = Column(Boolean, unique=False, default=False)
    fears_water = Column(Boolean, unique=False, default=False)
    fears_dark = Column(Boolean, unique=False, default=False)

    def __init__(self, name, queues, pf):
        threading.Thread.__init__(self)
        self.name = name
        self.current_task = None
        self.pathfinder = pf
        self.q, self.msg_q, self.log_q, self.q_lock, self.kill_switch = queues
        self._energy_used = 0
        self._thirst = 0
        self._hunger = 0
        self._damage = 0
        self.exit = False
        self._saved_task = None
        self._clock = pygame.time.Clock()
        self.loop_count = 0
        self._death_notify = False
        self._tired_notify = False
        self._thirst_notify = False
        self._hunger_notify = False
        self.alive = True
        self._trash = []

        # cache moves from a*
        self._moves = []
        self._destination = None

        # vital statistic decay rates
        self._hunger_rate = self._random_rate(5)
        self._thirst_rate = self._random_rate(5)
        self._energy_rate = self._random_rate(5)

        # virt inventory
        self._inventory = []
        self._inventory_limit = 6

    def __repr__(self):
        return '<Virt(name={}, alive={}, personality={}, pos={})>'.format(
                self.name, self.alive, self.personality, self.position)

    def _random_rate(self, attribute_weight=1):
        margin = 0.01 * (attribute_weight / 100)
        return random.uniform(0.01 - margin, 0.01 + margin)

    def _get_task(self):
        if self._saved_task is not None:
            self.current_task = self._saved_task
            return
        try:
            self.q_lock.acquire()
            while not self.q.empty():
                task = self.q.get_nowait()
                can_do = all([getattr(self, skill) >= task.skill[skill] for skill in task.skill])
                if not can_do:
                    self.q.put_nowait(task)
                    self.current_task = None
                else:
                    self.current_task = task
                    break
        except Empty:
            self.current_task = None
        self.q_lock.release()

    def pick_up(self, item):
        if not item.consumable:
            return
        inventory = self.flat_inventory
        if len(self._inventory) < self._inventory_limit:
            self._inventory.append(item)
        else:
            for i in self._inventory:
                if i is not None:
                    if i.is_container and i.has_room:
                        i.add_item(item)
                        item.container = i
                        break

        if item.container is None:
            self.level_map.trash_item(item, False)

        print('{} picked up {}'.format(self.name, item))

    def consume_item(self, target_item):
        assert target_item in self.flat_inventory
        if target_item in self._inventory:
            self._inventory.remove(target_item)
        else:
            for item in self._inventory:
                if item.contains(target_item):
                    item.remove_item(target_item)
                    break
        del target_item

    @property
    def carrying(self):
        retval = []
        for i in self._inventory:
            if i.is_container:
                retval.append('{} ({})'.format(i.name, len(i.contents)))
            else:
                retval.append('{}'.format(i.name))
        return retval

    @property
    def flat_inventory(self):
        inventory = [i for i in self._inventory if i is not None]
        for item in inventory:
            if item.is_container:
                inventory.extend([i for i in item.contents if i is not None])
        return inventory

    @property
    def max_hp(self):
        return 10 + (self.endurance / 2)

    @property
    def hit_points(self):
        return self.max_hp - self.damage

    def _send_log(self, msg, nospam=False):
        # Set nospam=True when a log message is sent each loop
        if nospam and self.loop_count % 15 != 0:
            return

        self.q_lock.acquire()
        self.log_q.put(msg)
        self.q_lock.release()

    def _get_message(self, target=None):
        try:
            while not self.msg_q.empty():
                msg = self.msg_q.get_nowait()
                if msg.get('id') != self.id:
                    self.msg_q.put(msg)
                    msg = None
                elif target is not None:
                    if target not in msg:
                        self.msg_q.put(msg)
                        msg = None
        except Empty:
            msg = None
        return msg

    def _send_message(self, msg):
        try:
            self.q_lock.acquire()
            self.msg_q.put(msg)
            self.q_lock.release()
        except:
            raise
        else:
            return True
        return False

    def _next_task(self):
        # Cover basic needs first
        overrides = [self.resting, self.eating, self.drinking]
        if self.need_drink and not any(overrides):
            self._drink()
        elif self.need_food and not any(overrides):
            self._eat()
        elif self.need_rest and not any(overrides):
            self._rest()

        # Try to fetch a task
        if self.current_task is None:
            self._get_task()

        # If a task is assigned, process it
        if self.current_task is not None:
            # Move to task location if not already there
            if self.position != self.current_task.position:
                return self._move_to, (self.current_task.position,)
            # Otherwise, do the task
            return self._do_task, None

    def has_item(self, target_item):
        if target_item in self._inventory:
            return True
        for i in self._inventory:
            if i is not None:
                if i.is_container:
                    if target_item in item.contents:
                        return True
        return False

    def _do_task(self):
        task = self.current_task
        if task.target_item is not None and not self.has_item(task.target_item):
            self.pick_up(task.target_item)
        if not task.task_done:
            # Reduce task work remaining
            task.work = getattr(self, task.skill)
        else:
            # Signal task completion and reset
            callback = task.on_complete
            if self.current_task.callback_args is not None:
                callback(*self.current_task.callback_args)
            else:
                callback()
            if task.consume_item and task.target_item.consumable:
                self.consume_item(task.target_item)
                task.target_item = None
            self.current_task = None
            self._destination = None

    def _closest_item(self, item_list):
        positions = [i.position for i in item_list]
        distances = {p: distance_3d(self.position, p) for p in positions}
        if distances:
            closest = min(distances, key=distances.get)
            for item in item_list:
                if item.position == closest:
                    return item

    def _find_item(self, item_type):
        # Find an item of the specified type.
        # Locates the closest item by default.
        print('{} is looking for {}'.format(self.name, item_type))
        item_list = self.level_map.find_item(item_type=item_type)
        if item_list:
            item = self._closest_item(item_list)
        else:
            print('{} could not find {}'.format(self.name, item_type))
            return
        print('{} found {}'.format(self.name, item.name))
        return item

    def _idle(self):
        # Wander to random points
        try:
            choice = random.choice(self.level_map.get_neighbors(self.position))
        except IndexError:
            choice = self.position
        self._move(choice)

    def _adjust_value(self, name, value):
        setattr(self, name, value)

    def _handle_override(self, task_name, target_item,
            callback, callback_args=None, consume_item=False):
        task = Task(name=task_name, consume_item=consume_item)
        task.prepare()
        task.name = task_name
        task.position = target_item.position
        task.target_item = target_item
        task.on_complete = (callback, callback_args)
        task.skill = 'endurance'    # Overrides always use endurance
        self._saved_task = self.current_task
        self.current_task = task

    def _eat(self):
        target_food = self._find_item('food')
        if target_food is not None:
            callback = self._adjust_value
            callback_args = ('_hunger', -target_food.power)
            self._handle_override('eating', target_food,
                    callback, callback_args, target_food.consumable)
        else:
            self._idle()

    def _drink(self):
        target_drink = self._find_item('drink')
        if target_drink is not None:
            callback = self._adjust_value
            callback_args = ('_thirst', -target_drink.power)
            self._handle_override('drinking', target_drink,
                    callback, callback_args, target_drink.consumable)
        else:
            self._idle()

    def _rest(self):
        target_bed = self._find_item('bed')
        if target_bed is not None:
            callback = self._adjust_value
            callback_args = ('_energy_used', -target_bed.power)
            self._handle_override('resting', target_bed,
                    callback, callback_args, target_bed.consumable)
        else:
            self._idle()

    @property
    def damage(self):
        return self._damage

    @damage.setter
    def damage(self, val):
        self._damage += val
        if self._damage > self.max_hp:
            self._die('damage')

    @property
    def eating(self):
        try:
            if self.current_task.name == 'eating':
                return True
        except AttributeError:
            pass
        return False

    @property
    def drinking(self):
        try:
            if self.current_task.name == 'drinking':
                return True
        except AttributeError:
            pass
        return False

    @property
    def resting(self):
        try:
            if self.current_task.name == 'resting':
                return True
        except AttributeError:
            pass
        return False

    def _move(self, move):
        #self._send_log(' -  Virt {} moved from {} to {}'.format(
        #                            self.name, self.position, move))
        self.position = move
        if self.current_task not in ('resting', 'eating', 'drinking'):
            self._energy_used += self._energy_rate

    def _move_to(self, destination):
        if self._destination == destination and self._moves:
            next_move = self._moves.pop()
            self._move(next_move)
        else:
            self._destination = destination
            path = self.pathfinder[(self.position, destination)]
            if path:
                self._moves = path
                self._move(self._moves.pop())
            else:
                self._send_log(' -  No path found! {} is idling'.format(self.name))
                self._idle()

    def work(self):
        action = self._next_task()
        if action is not None:
            func, args = action
            if args is not None:
                result = func(*args)
            else:
                result = func()
        else:
            self._idle()

    @property
    def need_rest(self):
        if float(self.energy_left) < 0:
            if not self._tired_notify:
                self._send_log(' -  Virt {} is tired'.format(self.name), True)
            self._tired_notify = True
            return True
        self._thirst_notify = False
        return False

    @property
    def need_food(self):
        if self._hunger >= 0:
            if not self._hunger_notify:
                self._send_log(' -  Virt {} is hungry'.format(self.name), True)
            self._hunger_notify = True
            return True
        self._hunger_notify = False
        return False

    @property
    def need_drink(self):
        if self._thirst >= 0:
            if not self._thirst_notify:
                self._send_log(' -  Virt {} is thirsty'.format(self.name), True)
            self._thirst_notify = True
            return True
        return False

    @property
    def sprite(self):
        return self._sprite_image

    @sprite.setter
    def sprite(self, tile):
        self._sprite_image = tile


    @property
    def daily_energy(self):
        return max((self.endurance * self.energy) + self.lazy, 10)

    @property
    def energy_left(self):
        return '{:0.2f}'.format(self.daily_energy - self._energy_used)

    @property
    def hunger_score(self):
        return '{:0.2f}'.format(self._hunger)

    @property
    def thirst_score(self):
        return '{:0.2f}'.format(self._thirst)

    @property
    def position(self):
        return self.pos_x, self.pos_y, self.pos_z

    @position.setter
    def position(self, pos):
        self.pos_x, self.pos_y, self.pos_z = pos

    @property
    def destination(self):
        return self._destination

    def _die(self, reason=None):
        if not self._death_notify:
            if reason is not None:
                death_str = ' - {} has died of {}!'.format(self.name, reason)
            else:
                death_str = ' - {} has died!'.format(self.name)
            self._send_log(death_str)
            self.sprite = pygame.transform.rotate(self._sprite_image, 90)
        self._death_notify = True
        self.alive = False

    def run(self):
        def pre_loop():
            if self.loop_count >= 1000000:
                self.loop_count = 0

        def post_loop():
            self.loop_count += 1
            self._hunger += self._hunger_rate
            self._thirst += self._thirst_rate
            if self._hunger > 10:
                self._die('hunger')
            elif self._thirst > 10:
                self._die('thirst')

        def tick(rate=2):
            self._clock.tick(rate)

        # Main AI loop here
        # call using start()
        self.pause = False
        while not self.kill_switch.is_set():
            #pdb.set_trace()
            try:
                if not self.alive:
                    return
                if not self.pause:
                    pre_loop()
                    tick()
                    self.work()
                    post_loop()
                else:
                    tick()
            except:
                raise

def create_db(path):
    engine = create_engine(path, echo=True)
    Base.metadata.create_all(engine)

if __name__=='__main__':
    # Run this file as a script to create the database
    # passing the database path as the first required argument
    create_db('sqlite:///{}'.format(sys.argv[1]))
