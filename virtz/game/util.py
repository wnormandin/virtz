
def distance_3d(pt1, pt2):
    delta_x_2 = (pt1[0] - pt2[0]) ** 2
    delta_y_2 = (pt1[1] - pt2[1]) ** 2
    delta_z_2 = (pt1[2] - pt2[2]) ** 2
    return (delta_x_2 + delta_y_2 + delta_z_2) ** 0.5


class Pathfinder:
    def __init__(self, map_obj):
        self.map_obj = map_obj

    def __getitem__(self, points):
        return self._find_path(*points)

    def _find_path(self, start, end):
        # A* algorithm
        pass
