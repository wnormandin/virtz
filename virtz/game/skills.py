
import random

skills = ['melee', 'ranged', 'defense', 'construction', 'crafting',
        'magic', 'swimming', 'leadership']

attributes = ['strength', 'endurance', 'intelligence', 'wisdom',
        'dexterity', 'agility', 'charisma']

motivations = ['boredom', 'hunger', 'thirst', 'fear']

base_range = (1, 5)
favored_range = (4, 10)

class SkillFactory:

    def __getitem__(self, personality):
        self._personality = personality
        self._randomized = {}
        self._random_skills()
        return self._randomized

    def _score(self, values):
        scores = []
        for v in values:
            scores.append(self._personality[v])
        return sum(scores) / len(scores)

    def _random_skills(self):
        stats = {
            'melee': ('lazy', 'savage', 'energy', 'willpower'),
            'ranged': ('savage', 'ignorant', 'willpower'),
            'defense': ('willpower', 'energy', 'lazy', 'character'),
            'construction': ('energy', 'lazy', 'ignorant'),
            'crafting': ('ambition', 'lazy', 'character'),
            'magic': ('ignorant', 'energy', 'willpower'),
            'swimming': ('lazy', 'energy', 'follower'),
            'leadership': ('integrity', 'character', 'follower'),
            'strength': ('lazy', 'energy', 'willpower', 'willpower'),
            'endurance': ('willpower', 'energy', 'character'),
            'intelligence': ('ignorant', 'ambition', 'willpower'),
            'wisdom': ('willpower', 'ambition', 'character'),
            'dexterity': ('lazy', 'energy', 'savage', 'energy'),
            'agility': ('lazy', 'energy', 'willpower', 'lazy'),
            'charisma': ('character', 'integrity', 'willpower'),
            'boredom': ('lazy', 'ignorant', 'energy', 'ignorant'),
            'hunger': ('willpower', 'character', 'integrity'),
            'thirst': ('willpower', 'character', 'integrity'),
            'fear': ('willpower', 'character', 'ignorant')
            }

        for stat in stats:
            vals = base_range
            if self._score(stats[stat]) >= 3:
                vals = favored_range
            self._randomized[stat] = random.randint(*vals)
