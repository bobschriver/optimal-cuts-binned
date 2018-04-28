import sys

from scipy.spatial.distance import euclidean

class Cut():
    def __init__(self, center):
        self.center = center

        self.total_weight = 0
        self.non_harvest_weight = 0
        self.harvest_weight = 0

        self.num_trees = 0

        self.cost_to_centroid = 0

        self.landing_point_distances = {}

        self.closest_landing_point_distance = sys.maxsize
        self.closest_landing_point = (sys.maxsize, sys.maxsize)

        self.update_cached = True
        self.value = 0

    def add_tree(self, x, y, weight):
        self.total_weight += weight
        self.num_trees += 1

        if weight < 0.3:
            self.non_harvest_weight += weight
        else:
            distance_to_centroid = euclidean((x, y), self.center)
            tree_cost_to_centroid = self.harvest_weight * (distance_to_centroid * 0.061)

            self.cost_to_centroid += tree_cost_to_centroid
            self.harvest_weight += weight


    def compute_value(self, active_landing_points):
        if self.update_cached:
            if self.closest_landing_point not in active_landing_points:
                min_landing_point_distance = sys.maxsize
                for active_landing_point in active_landing_points:
                    if active_landing_point not in self.landing_point_distances:
                        self.landing_point_distances[active_landing_point] = euclidean(self.center, active_landing_point)

                    if self.landing_point_distances[active_landing_point] < min_landing_point_distance:
                        min_landing_point_distance = self.landing_point_distances[active_landing_point]
                        closest_active_landing_point = active_landing_point
            else:
                min_landing_point_distance = self.closest_landing_point_distance
                closest_active_landing_point = self.closest_landing_point

            self.closest_landing_point_distance = min_landing_point_distance
            self.closest_landing_point = closest_active_landing_point

            equipment_moving_cost = self.closest_landing_point_distance * 0.01
            felling_cost = self.non_harvest_weight * 12 + self.harvest_weight * 10
            processing_cost = self.harvest_weight * 15
            skidding_cost = self.harvest_weight * (self.closest_landing_point_distance * 0.061 + 20)

            felling_value = 3 * self.num_trees
            harvest_value = self.harvest_weight * 71.65

            self.value = (felling_value + harvest_value) - (equipment_moving_cost + felling_cost + processing_cost + skidding_cost + self.cost_to_centroid)

            self.update_cached = False

        return self.value

    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return "XY {} W {} N {} V {}".format(self.center, self.total_weight, self.num_trees, self.value)


            