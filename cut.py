import sys

class Cut():
    def __init__(self, center):
        self.center = center

        self.total_weight = 0
        self.non_harvest_weight = 0
        self.harvest_weight = 0

        self.num_trees = 0

        self.closest_landing_point_distance = sys.maxsize

        self.update_cached = True
        self.value = 0

    def add_tree(self, x, y, weight):
        self.total_weight += weight
        self.num_trees += 1

        if weight < 0.3:
            self.non_harvest_weight += weight
        else:
            self.harvest_weight += weight


    def compute_value(self, points_kdtree):
        if self.update_cached:
            distances, _ = points_kdtree.query([self.center])

            self.closest_landing_point_distance = distances[0]

            felling_cost = self.non_harvest_weight * 12 + self.harvest_weight * 10
            processing_cost = self.harvest_weight * 15
            skidding_cost = self.harvest_weight * (self.closest_landing_point_distance * 0.061 + 20)

            felling_value = 3 * self.num_trees
            harvest_value = self.harvest_weight * 71.65

            self.value = (felling_value + harvest_value) - (felling_cost + processing_cost + skidding_cost)

            self.update_cached = False

        return self.value

    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return "XY {} W {} N {} V {}".format(self.center, self.total_weight, self.num_trees, self.value)


            