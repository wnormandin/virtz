import ConfigParser

class Level:

    def load_file(self, filename="resources/basic_level.map"):
        self.map = []
        self.key = {}
        parser = ConfigParser.ConfigParser()
        parser.read(filename)
        self.tileset = parser.get("level", "tileset")
        self.map = parser.get("level", "map").split('\n')
        for section in parser.sections():
            if len(section) == 1:
                desc = dict(parser.items(section))
                self.key[section] = desc
        self.width = len(self.map[0])
        self.height = len(self.map)

    def get_tile(self, x, y)
        try:
            char = self.map[y][x]
        except IndexError:
            return {}
        try:
            return self.key[char]
        except KeyError:
            return {}

    def get_bool(self, x, y, name):
        value = self.get_tile(x, y).get(name)
        return value in (True, 1, 'true', 'yes', 'True', 'Yes', '1', 'on', 'On')

    def is_wall(self, x, y):
        return self.get_bool(x, y, 'wall')

    def is_blocking(self, x, y):
        if not 0 <= x < self.width or not 0 <= y < self.height:
            return True
        return self.get_bool(x, y, 'block')

	def render(self):
			wall = self.is_wall
			tiles = MAP_CACHE[self.tileset]
			image = pygame.Surface((self.width*MAP_TILE_WIDTH, self.height*MAP_TILE_HEIGHT))
			overlays = {}
			for map_y, line in enumerate(self.map):
				for map_x, c in enumerate(line):
					if wall(map_x, map_y):
						if not wall(map_x, map_y+1):
							if wall(map_x+1, map_y) and wall(map_x-1, map_y):
								tile = 1, 2
							elif wall(map_x+1, map_y):
								tile = 0, 2
							elif wall(map_x-1, map_y):
								tile = 2, 2
							else:
								tile = 3, 2
						else:
							if wall(map_x+1, map_y+1) and wall(map_x-1, map_y+1):
								tile = 1, 1
							elif wall(map_x+1, map_y+1):
								tile = 0, 1
							elif wall(map_x-1, map_y+1):
								tile = 2, 1
							else:
								tile = 3, 1
						# Add overlays if the wall may be obscuring something
						if not wall(map_x, map_y-1):
							if wall(map_x+1, map_y) and wall(map_x-1, map_y):
								over = 1, 0
							elif wall(map_x+1, map_y):
								over = 0, 0
							elif wall(map_x-1, map_y):
								over = 2, 0
							else:
								over = 3, 0
							overlays[(map_x, map_y)] = tiles[over[0]][over[1]]
					else:
						try:
							tile = self.key[c]['tile'].split(',')
							tile = int(tile[0]), int(tile[1])
						except (ValueError, KeyError):
							# Default to ground tile
							tile = 0, 3
					tile_image = tiles[tile[0]][tile[1]]
					image.blit(tile_image,
						(map_x*MAP_TILE_WIDTH, map_y*MAP_TILE_HEIGHT))
			return image, overlays
