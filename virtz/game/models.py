import os
import sys
import datetime
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy import Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

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

    def __repr__(self):
        return "<MapTile(name={}, wall={}, blocking={}, image_loc={})>".format(
                self.name, self.wall, self.blocking, self.tile_row, self.tile_col)

    @property
    def image_location(self):
        return self.tile_row, self.tile_col

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
    owner = Column(Integer, ForeignKey('virtz.id'), nullable=True)
    name = Column(String(25), nullable=False)
    value = Column(Integer, default=0, nullable=False)
    desc = Column(String(300), nullable=True)
    unique = Column(Boolean, nullable=False, default=False)
    tile_row = Column(Integer, nullable=False)
    tile_col = Column(Integer, nullable=False)

    def __repr__(self):
        return '<Item(owner={}, name={}, value={}, image_loc={})>'.format(
                self.owner, self.name, self.value, self.image_location)

    @property
    def image_location(self):
        return tile_row, tile_col


class Virt(Base):
    __tablename__ = 'virtz'
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('saves.id'), nullable=True)
    name = Column(String(50), nullable=False, unique=True)
    alive = Column(Boolean, nullable=False, default=True)

    # Virt location details
    map_path = Column(String(50), nullable=False)
    pos_x = Column(Integer, nullable=False, default=0)
    pos_y = Column(Integer, nullable=False, default=0)

    # Personality name and behaviors
    personality = Column(String(50), nullable=False)
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
    ambition = Column(Integer, nullable=False, default=1)
    energy = Column(Integer, nullable=False, default=1)
    willpower = Column(Integer, nullable=False, default=1)
    character = Column(Integer, nullable=False, default=1)
    integrity = Column(Integer, nullable=False, default=1)

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

    # Convenience lists
    personality_scores = (lazy, follower, savage, ignorant)
    skills = (melee, ranged, defense, construction, crafting, magic,
            swimming, leadership)
    attributes = (strength, endurance, intelligence, wisdom, dexterity,
            agility, charisma, ambition, energy, willpower, character,
            integrity)
    motivations = (boredom, hunger, thirst, fear)
    fears = (fears_bears, fears_wolves, fears_bats, fears_caves,
            fears_woods, fears_water, fears_dark)

    def __repr__(self):
        return '<Virt(name={}, alive={}, personality={}, pos={})>'.format(
                self.name, self.alive, self.personality, self.position)

    @property
    def position(self):
        return self.pos_x, self.pos_y

    @position.setter
    def position(self, pos):
        self.pos_x, self.pos_y = pos

def create_db(path):
    engine = create_engine(path, echo=True)
    Base.metadata.create_all(engine)

if __name__=='__main__':
    # Run this file as a script to create the database
    # passing the database path as the first required argument
    create_db('sqlite:///{}'.format(sys.argv[1]))
