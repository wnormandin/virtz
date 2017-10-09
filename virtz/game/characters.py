#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import random
import argparse
import time

from .models import Virt, Base
from .personality import PersonalityFactory, personalities
from .skills import SkillFactory, skills, attributes, motivations

this = sys.modules[__name__]


def random_name():
    names = ['Fred', 'Paul', 'Mark', 'Bill', 'Mike', 'Phil', 'John', 'James',
            'Josh', 'Chris', 'Steve', 'Peter', 'Carl', 'Adam', 'Blake']
    return random.choice(names)

def randomize_fears():
    ''' Everyone starts with one fear '''

    randomized = {}
    fears = ['bears', 'wolves', 'bats', 'caves', 'woods', 'water', 'dark']
    afraid = random.choice(fears)
    for fear in fears:
        val = False
        if fear == afraid:
            val = True
        randomized['fears_' + fear] = val
    return randomized

def session_init(db_path):
    db_path = 'sqlite://{}'.format(db_path)
    this.engine = create_engine(db_path)
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    this.session = DBSession()

class CharacterFactory:
    ''' Factory class to generate Virtz '''

    def __init__(self, db_path, queues, pathfinder, sprites):
        self.queues = queues
        self.sprites = sprites
        self.pf = pathfinder
        session_init(db_path)
        self.engine = engine
        self.session = session
        self.person_factory = PersonalityFactory()
        self.skill_factory = SkillFactory()
        self.queues = queues

    def get_virt(self, position=(0, 0, 0)):
        ''' Returns a Virt object of the specified type initialized
            in the specified position.
        '''
        personality_name = random.choice([k for k in personalities])
        person = self.person_factory[personality_name]
        skills = self.skill_factory[person]
        fears = randomize_fears()

        virt = Virt(random_name(), self.queues, self.pf)
        virt.id = time.clock()
        virt.sprite = self.sprites[0, 6]
        virt.personality = personality_name
        virt.position = position

        for trait in person:
            setattr(virt, trait, person[trait])

        for fear in fears:
            setattr(virt, fear, fears[fear])

        for skill in skills:
            setattr(virt, skill, skills[skill])

        return virt

def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dbpath', help='Specify a database path')
    this.args = parser.parse_args()

if __name__ == '__main__':
    cli()
    args.dbpath = 'sqlite:///{}'.format(args.dbpath)
    char_factory = CharacterFactory(args.dbpath)
    virt = char_factory.get_virt()
    print('[*] Virt Details')
    print(' -  Name:        {}'.format(virt.name))
    print(' -  Alive:       {}'.format(virt.alive))
    print(' -  Position:    {}'.format(virt.position))
    print(' -  Personality: {}'.format(virt.personality))
    print('      Lazy / Motivated:  {}'.format(virt.lazy))
    print('      Follower / Leader: {}'.format(virt.follower))
    print('      Savage / Civil:    {}'.format(virt.savage))
    print('      Ignorant / Smart:  {}'.format(virt.ignorant))
    print(' -  Attributes')
    print('      Strength:          {}'.format(virt.strength))
    print('      Endurance:         {}'.format(virt.endurance))
    print('      Intelligence:      {}'.format(virt.intelligence))
    print('      Wisdom:            {}'.format(virt.wisdom))
    print('      Dexterity:         {}'.format(virt.dexterity))
    print('      Agility:           {}'.format(virt.agility))
    print('      Charisma:          {}'.format(virt.charisma))
    print(' -  Characteristics')
    print('      Ambition:          {}'.format(virt.ambition))
    print('      Energy:            {}'.format(virt.energy))
    print('      Willpower:         {}'.format(virt.willpower))
    print('      Character:         {}'.format(virt.character))
    print('      Integrity:         {}'.format(virt.integrity))
    print(' -  Motivations')
    print('      Boredom:           {}'.format(virt.boredom))
    print('      Hunger:            {}'.format(virt.hunger))
    print('      Thirst:            {}'.format(virt.thirst))
    print('      Fear:              {}'.format(virt.fear))
    print(' -  Skills')
    print('      Melee:             {}'.format(virt.melee))
    print('      Ranged:            {}'.format(virt.ranged))
    print('      Defense:           {}'.format(virt.defense))
    print('      Construction:      {}'.format(virt.construction))
    print('      Crafting:          {}'.format(virt.crafting))
    print('      Magic:             {}'.format(virt.magic))
    print('      Swimming:          {}'.format(virt.swimming))
    print('      Leadership:        {}'.format(virt.leadership))
    print(' -  Fears')
    print('      Bears:             {}'.format(virt.fears_bears))
    print('      Wolves:            {}'.format(virt.fears_wolves))
    print('      Bats:              {}'.format(virt.fears_bats))
    print('      Caves:             {}'.format(virt.fears_caves))
    print('      Water:             {}'.format(virt.fears_water))
    print('      Dark:              {}'.format(virt.fears_dark))
