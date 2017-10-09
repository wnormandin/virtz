#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import datetime
import time
import pygame
import random

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

    # When can_get is true, the item may be picked up by a pc/npc in which
    # case the item is typically destroyed on the main map
    can_get = Column(Boolean, unique=False, default=False)

    # When can_destroy is true, the map item may be destroyed,
    # changing to the destroyed image
    can_destroy = Column(Boolean, unique=False, default=False)

    # Indicates whether the map item has been destroyed
    destroyed = Column(Boolean, unique=False, default=False)

    # Coordinates for this tile's base image in the core tile map
    tile_row = Column(Integer, unique=False)
    tile_col = Column(Integer, unique=False)

    # Coordinates for this tile's destroyed image in the core tile map
    destroyed_row = Column(Integer, unique=False)
    destroyed_col = Column(Integer, unique=False)

    # Item sprite image location
    sprite_col = Column(Integer, nullable=False)
    sprite_row = Column(Integer, nullable=False)

    def __repr__(self):
        return '<Item(name={}, image_loc={})>'.format(
                self.name, self.image_location)

    @property
    def image_location(self):
        return self.tile_row, self.tile_col


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


class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('saves.id'), nullable=True)
    pos_x = Column(Integer, nullable=False, default=0)
    pos_y = Column(Integer, nullable=False, default=0)
    pos_z = Column(Integer, nullable=False, default=0)
    name = Column(String(50), nullable=False)
    task_done = Column(Boolean, nullable=False, default=False)

    # Name of skill required
    skill = Column(String(50), nullable=False)
    # Value of skill required
    skill_value = Column(Integer, nullable=False, default=1)
    # Activity points required for completion
    activity_points = Column(Integer, nullable=False, default=100)

    def __init__(self):
        self._points_left = self.activity_points
        self.target_item = None
        self._required_items = []
        self._callback = None

    @property
    def work(self):
        return self._points_left / self.activity_points

    @work.setter
    def work(self, points):
        self._points_left -= points
        if self._points_left <= 0:
            self.task_done = True

    @property
    def on_complete(self):
        return self._callback

    @on_complete.setter
    def on_complete(self, callback, args):
        self._callback = callback
        self.callback_args = args

class Virt(Base, threading.Thread):
    __tablename__ = 'virtz'
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('saves.id'), nullable=True)
    name = Column(String(50), nullable=False)
    alive = Column(Boolean, nullable=False, default=True)

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
        self.q, self.msg_q, self.log_q, self.q_lock = queues
        self._energy_used = 0
        self._thirst = -10
        self._hunger = -10
        self.exit = False
        self._saved_task = None
        self._clock = pygame.time.Clock()
        self.loop_count = 0

        # cache moves from a*
        self._moves = []
        self._destination = None

    def __repr__(self):
        return '<Virt(name={}, alive={}, personality={}, pos={})>'.format(
                self.name, self.alive, self.personality, self.position)

    def _get_task(self):
        if self._saved_task is not None:
            self.current_task = self._saved_task
            return
        try:
            self.q_lock.acquire()
            while not self.q.empty():
                task = self.q.get_nowait()
                if getattr(self, task.skill) < task.skill_level:
                    self.q.put_nowait(task)
                    self.current_task = None
                else:
                    self.current_task = task
                    break
        except Empty:
            self.current_task = None
        self.q_lock.release()

    def _send_log(self, msg):
        self.q_lock.acquire()
        self.log_q.put(msg)
        self.q_lock.release()

    def _get_message(self, target=None):
        try:
            while not self.msg_q.empty():
                self.q_lock.acquire()
                msg = self.msg_q.get()
                if msg is None: # Poison pill
                    self.exit = True
                elif msg.get('id') != self.id:
                    self.msg_q.put(msg)
                    msg = None
                elif target is not None:
                    if target not in msg:
                        self.msg_q.put(msg)
                        msg = None
        except Empty:
            msg = None
        self.q_lock.release()
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
            if self.position != task.position:
                return self._move_to, (task.position,)
            # Otherwise, do the task
            return self._do_task, None

    def _do_task(self):
        task = self.current_task
        if not self.current_task.task_done:
            # Reduce task work remaining
            self.current_task.work = getattr(self, self.current_task.skill)
            self._energy_used += getattr(self, self.current_task.skill)
        else:
            # Signal task completion and reset
            callback = self.current_task.on_complete
            if self.current_task.callback_args is not None:
                callback(*self.current_task.callback_args)
            else:
                callback()
            self.q.task_done()
            self.current_task = None

    def _closest_item(self, item_list):
        positions = [item.position for item in item_list]
        distances = {p: distance_3d(self.position, p) for p in positions}
        closest = min(distances, key=distances.get)
        for item in item_list:
            if item.position == closest:
                return item

    def _find_item(self, item_type):
        # Find an item of the specified type.
        # Locates the closest item by default.
        self._send_message({'id': self.id, 'request': 'items',
                                      'item_type': item_type})
        item_list = self._get_message('items')
        if item_list is not None:
            self.msg_q.task_done()
            item = self._closest_item(item_list)
        else:
            return
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

    def _handle_override(self, task_name, target_item, callback, callback_args=None):
        task = Task()
        task.name = task_name
        task.position = target_item.position
        task.target_item = target_item
        task.on_complete = callback, callback_args
        task.skill = 'endurance'    # Overrides always use endurance
        self._saved_task = self.current_task
        self.current_task = task

    def _eat(self):
        target_food = self._find_item('food')
        if target_food is not None:
            callback = self._adjust_value
            callback_args = ('_hunger', target_food.power)
            self._handle_override('eating', target_food, callback, callback_args)
        else:
            self._idle()

    def _drink(self):
        target_drink = self._find_item('drink')
        if target_drink is not None:
            callback = self._adjust_value
            callback_args = ('_thirst', target_drink.power)
            self._handle_override('drinking', target_drink, callback, callback_args)
        else:
            self._idle()

    def _rest(self):
        target_bed = self._find_item('bed')
        if target_drink is not None:
            callback = self._adjust_value
            callback_args = ('_energy_used', -target_bed.power)
            self._handle_override('resting', target_bed, callback, callback_args)
        else:
            self._idle()

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
        self._send_log(' -  Virt {} moved from {} to {}'.format(
                                    self.name, self.position, move))
        self.position = move
        self._energy_used += 0.001

    def _move_to(self, destination):
        if self._destination == destination and self._moves:
            next_move = self._moves.pop()
            self._move(next_move)
        else:
            self._destination = destination
            self._send_log(' -  Virt {} finding path from {} to {}'.format(
                                    self.name, self.position, destination))
            self._moves = self.pathfinder[(self.position, destination)]

    def work(self):
        action = self._next_task()
        if action is not None:
            func, args = action
            if args is not None:
                result = func(*args)
            else:
                result = func()
        else:
            self._send_log(' -  Virt {} is idling'.format(self.name))
            self._idle()

    @property
    def need_rest(self):
        if self._energy_used > self.daily_energy:
            self._send_log(' -  Virt {} is tired'.format(self.name))
            return True
        return False

    @property
    def need_food(self):
        if self._hunger >= 0:
            self._send_log(' -  Virt {} is hungry'.format(self.name))
            return True
        return False

    @property
    def need_drink(self):
        if self._thirst >= 0:
            self._send_log(' -  Virt {} is thirsty'.format(self.name))
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
        return (self.endurance * self.energy) * 2 + self.lazy

    @property
    def position(self):
        return self.pos_x, self.pos_y, self.pos_z

    @position.setter
    def position(self, pos):
        self.pos_x, self.pos_y, self.pos_z = pos

    def run(self):
        def pre_loop():
            if self.loop_count >= 1000000:
                self.loop_count = 0

        def post_loop():
            self.loop_count +=1
            self._hunger += 0.001
            self._thirst += 0.001

        # Main AI loop here
        # call using start()
        while not self.exit:
            pre_loop()
            self._clock.tick(2) # Sync with main thread
            self.work()
            post_loop()

def create_db(path):
    engine = create_engine(path, echo=True)
    Base.metadata.create_all(engine)

if __name__=='__main__':
    # Run this file as a script to create the database
    # passing the database path as the first required argument
    create_db('sqlite:///{}'.format(sys.argv[1]))
