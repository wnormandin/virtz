
import random

template = {'lazy':0, 'follower':0, 'savage':0, 'ignorant':0,
        'ambition':0, 'energy':0, 'willpower':0, 'character':0,
        'integrity':0}

personalities = {
        'urchin': template.copy(),
        'politician': template.copy(),
        'fighter': template.copy(),
        'worker': template.copy()
        }

ranges = {
        'urchin': {
            'lazy': (-5, -1),
            'follower': (-3, 0),
            'savage': (-1, 3),
            'ignorant': (-6, -3),
            'ambition': (-3, 1),
            'energy': (1, 4),
            'willpower': (-1, 3),
            'character': (-6, -3),
            'integrity': (-7, -4)
            },
        'politician': {
            'lazy': (-2, 2),
            'follower': (1, 5),
            'savage': (-3, 1),
            'ignorant': (0, 4),
            'ambition': (3, 7),
            'energy': (1, 5),
            'willpower': (2, 6),
            'character': (0, 4),
            'integrity': (-2, 2)
            },
        'fighter': {
            'lazy': (0, 5),
            'follower': (-1, 1),
            'savage': (-5, -2),
            'ignorant': (-5, -2),
            'ambition': (-2, 2),
            'energy': (3, 7),
            'willpower': (2, 6),
            'character': (-2, 2),
            'integrity': (-3, 3)
            },
        'worker': {
            'lazy': (2, 6),
            'follower': (-6, -3),
            'savage': (2, 5),
            'ignorant': (-6, -3),
            'ambition': (-4, 1),
            'energy': (2, 6),
            'willpower': (-2, 2),
            'character': (-2, 2),
            'integrity': (-2, 2)
            }
        }

class PersonalityFactory:

    def __init__(self):
        self._list = personalities

    def __getitem__(self, name):
        return self._randomize(name)

    def _randomize(self, name):
        personality = self._list[name]
        for key in template:
            low, high = ranges[name][key]
            personality[key] = random.randint(low, high)
        return personality

    @property
    def base_personality(self):
        return template.copy()
