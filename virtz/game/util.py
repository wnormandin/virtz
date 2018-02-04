
import heapq
import signal
from collections import defaultdict
from math import inf as Infinity
#import pdb

def distance_3d(pt1, pt2):
    delta_x_2 = (pt1[0] - pt2[0]) ** 2
    delta_y_2 = (pt1[1] - pt2[1]) ** 2
    delta_z_2 = (pt1[2] - pt2[2]) ** 2
    return (delta_x_2 + delta_y_2 + delta_z_2) ** 0.5


class InterruptHandler:

    ''' Interrupt handler as a context manager '''

    def __init__(self, sig=signal.SIGINT):
        self.sig = sig

    def __enter__(self):
        self.interrupted = False
        self.released = False
        self.sig_orig = signal.getsignal(self.sig)

        def handler(signum, frame):
            self.release()
            self.interrupted = True

        signal.signal(self.sig, handler)
        return self

    def __exit__(self, _type, value, tb):
        self.release()

    def release(self):
        if self.released:
            return False
        signal.signal(self.sig, self.sig_orig)
        self.released = True
        return True

class Pathfinder:
    def __getitem__(self, points):
        ''' Points should be (start, goal)

            Be sure to set graph to a GridWithWeights graph before getting an item
        '''
        if hasattr(self, '_graph'):
            return self._a_star(*points)

    def _heuristic(self, a, b):
        x1, y1, z1 = a
        x2, y2, z2 = b
        # Need to implement 3d distance here
        return abs(x1-x2) + abs(y1-y2)

    def _reconstruct(self, came_from, current):
        total_path = [current]
        while current in came_from:
            current = came_from[current]
            total_path.append(current)
        return total_path

    def _a_star(self, start, goal):
        # Set of evaluated nodes
        closed_set = []

        # Set of discovered but unevaluated nodes
        open_set = [start]

        # dict containing path taken from node to node
        came_from = {}

        # cost of getting from start to a particular node
        g_score = defaultdict(lambda: Infinity)
        g_score[start] = 0

        # cost of getting from start to goal using a
        # particular node (g + h)
        f_score = defaultdict(lambda: Infinity)
        f_score[start] = self._heuristic(start, goal)

        while open_set:
            current = min({pos: f_score[pos] for pos in f_score if pos in open_set}, key=f_score.get)
            if current == goal:
                return self._reconstruct(came_from, goal)

            if current in open_set:
                open_set.remove(current)
            closed_set.append(current)

            for point in self.graph.level_map.get_neighbors(current):
                movement_cost = self.graph.level_map[point].movement_cost

                if point in closed_set:
                    continue
                elif point not in open_set:
                    open_set.append(point)

                temp_score = g_score[current] + self._heuristic(current, point) * movement_cost
                if temp_score > g_score[point]:
                    continue

                came_from[point] = current
                g_score[point] = temp_score
                f_score[point] = g_score[point] + self._heuristic(point, goal)
        return False

    @property
    def graph(self):
        return self._graph

    @graph.setter
    def graph(self, level_map):
        self._graph = GridWithWeights(level_map)


class GridWithWeights:
    def __init__(self, level_map):
        self.level_map = level_map
        self._walls = []
        self.weights = {}

    @property
    def walls(self):
        if not self._walls:
            self._walls = [p for p in self.level_map.world_map if self.level_map[p].wall]
        return self._walls

    def passable(self, pt):
        return self.level_map[pt].passable

    def in_bounds(self, position):
        return position in self.level_map.world_map

    def cost(self, from_node, to_node):
        return self.weights.get(to_node, 1)

    def neighbors(self, position):
        x, y, z = position
        compare = [(x+1, y, z), (x+1, y+1, z), (x+1, y-1, z), (x, y+1, z),
                (x, y-1, z), (x-1, y, z), (x-1, y-1, z), (x-1, y+1, z)]
        if (x + y) % 2 == 0:
            compare.reverse()

        # Filter to in-bound and passable neighbors
        filtered = filter(self.in_bounds, compare)
        filtered = filter(self.passable, filtered)
        return filtered

