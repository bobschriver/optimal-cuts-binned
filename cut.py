import sys

from scipy.spatial.distance import euclidean



class Cut():
    @classmethod
    def from_json(cls, cut_json):
        top_left = cut_json["hull_points"][0]
        bottom_right = cut_json["hull_points"][2]

        cut = cls(top_left, bottom_right)

        cut.update_cached = True
        cut.value = cut_json["fitness"]
        
        cut.non_harvest_weight = cut_json["non_harvest_weight"]
        cut.harvest_weight = cut_json["harvest_weight"] 
        cut.num_trees = cut_json["num_trees"] 

        cut.x = cut_json["x"]
        cut.y = cut_json["y"]

        cut.basin = cut_json["basin"]
        cut.elevation = cut_json["elevation"]

        if "orphaned" in cut_json:
            cut.orphaned = cut_json["orphaned"]

        return cut

    def __init__(self, top_left, bottom_right):
        self.update_cached = True
        self.orphaned = False
        self.value = 0

        self.total_weight = 0
        self.non_harvest_weight = 0
        self.harvest_weight = 0

        self.num_trees = 0

        self.felling_value = 0
        self.harvest_value = 0
            
        self.equipment_moving_cost = 0
        self.felling_cost = 0
        self.processing_cost = 0
        self.skidding_cost = 0

        self.landing_point_distances = {}

        self.closest_landing_point_distance = sys.maxsize
        self.closest_landing_point = (sys.maxsize, sys.maxsize)

        self.top_left = top_left
        self.bottom_right = bottom_right

        self.x = (bottom_right[0] - top_left[0]) / 2.0 + top_left[0]
        self.y = (bottom_right[1] - top_left[1]) / 2.0 + top_left[1]
        
    def copy_writable(self):
        cut = Cut(self.top_left, self.bottom_right)
        cut.non_harvest_weight = self.non_harvest_weight
        cut.harvest_weight = self.harvest_weight
        cut.num_trees = self.num_trees
        cut.closest_landing_point = self.closest_landing_point
        cut.closest_landing_point_distance = self.closest_landing_point_distance

        cut.felling_value = self.felling_value
        cut.harvest_value = self.harvest_value

        cut.equipment_moving_cost = self.equipment_moving_cost
        cut.felling_cost = self.felling_cost
        cut.processing_cost = self.processing_cost
        cut.skidding_cost = self.skidding_cost

        cut.update_cached = True
        cut.value = self.value

        return cut

    def to_json(self):
        cut_json = {}

        cut_json["fitness"] = self.value

        cut_json["felling_value"] = self.felling_value
        cut_json["harvest_value"] = self.harvest_value
            
        cut_json["equipment_moving_cost"] = self.equipment_moving_cost
        cut_json["felling_cost"] = self.felling_cost
        cut_json["processing_cost"] = self.processing_cost
        cut_json["skidding_cost"] = self.skidding_cost

        cut_json["non_harvest_weight"] = self.non_harvest_weight
        cut_json["harvest_weight"] = self.harvest_weight
        cut_json["num_trees"] = self.num_trees

        cut_json["closest_landing_point_distance"] = self.closest_landing_point_distance
        cut_json["closest_landing_point"] = self.closest_landing_point

        cut_json["x"] = self.x
        cut_json["y"] = self.y

        x_left, y_top = self.top_left
        x_right, y_bottom = self.bottom_right

        cut_json["hull_points"] = [(x_left, y_top), (x_right, y_top),  (x_right, y_bottom), (x_left, y_bottom)]

        cut_json["basin"] = self.basin
        cut_json["elevation"] = self.elevation

        cut_json["orphaned"] = self.orphaned

        return cut_json        

    def add_tree(self, x, y, weight, elevation, basin):
        self.total_weight += weight
        self.num_trees += 1

        self.elevation = elevation
        self.basin = basin

        if weight < 0.3:
            self.non_harvest_weight += weight
        else:
            #distance_to_centroid = euclidean((x, y), self.center)
            #tree_cost_to_centroid = self.harvest_weight * (distance_to_centroid * 0.061)

            #self.cost_to_centroid += tree_cost_to_centroid
            self.harvest_weight += weight

    def update_landing_points(self, updated_landing_point):
        # If our closest landing point is equal to the updated landing point
        # That means we are removing the landing point - need to find a new one

        # If it is not equal, that means we either added or removed it
        # If we removed it, and it is not the closest landing point, 
        # it could not have a closer landing point distance
        # If we added it, check if it is closer than our current landing point
        """
        if updated_landing_point == self.closest_landing_point:
            self.closest_landing_point = (sys.maxsize, sys.maxsize)
            self.closest_landing_point_distance = sys.maxsize

            self.update_cached = True
        else:
            if updated_landing_point not in self.landing_point_distances:
                self.landing_point_distances[updated_landing_point] = self.compute_distance(updated_landing_point)
            
            
                self.closest_landing_point = updated_landing_point
                self.closest_landing_point_distance = self.landing_point_distances[updated_landing_point]

                self.update_cached = True
        """
        if updated_landing_point == self.closest_landing_point:
            self.update_cached = True

        if updated_landing_point not in self.landing_point_distances:
            self.landing_point_distances[updated_landing_point] = self.compute_distance(updated_landing_point)

        if self.landing_point_distances[updated_landing_point] < self.closest_landing_point_distance:
            self.update_cached = True
    
    def compute_distance(self, landing_point):
        landing_x, landing_y, landing_elevation, landing_basin = landing_point

        basin_distance = 0

        if self.basin != landing_basin:
            basin_distance = 10000

        return euclidean((self.x, self.y), (landing_x, landing_y)) + basin_distance
        #return euclidean((self.x, self.y), (landing_x, landing_y))

    def find_closest_active_landing_point(self, active_landing_points):
        if self.update_cached:
            min_landing_point_distance = sys.maxsize
            for active_landing_point in active_landing_points:
                if active_landing_point not in self.landing_point_distances:
                    self.landing_point_distances[active_landing_point] = self.compute_distance(active_landing_point)

                if self.landing_point_distances[active_landing_point] < min_landing_point_distance:
                    min_landing_point_distance = self.landing_point_distances[active_landing_point]
                    closest_active_landing_point = active_landing_point

            self.closest_landing_point = closest_active_landing_point
            self.closest_landing_point_distance = min_landing_point_distance

            if self.closest_landing_point_distance > 10000:
                self.orphaned = True
            else:
                self.orphaned = False
            

    def compute_value(self):
        """
        if self.closest_landing_point_distance == sys.maxsize or self.closest_landing_point not in active_landing_points:
            min_landing_point_distance = sys.maxsize
            for active_landing_point in active_landing_points:
                if active_landing_point not in self.landing_point_distances:
                    self.landing_point_distances[active_landing_point] = self.compute_distance(active_landing_point)

                if self.landing_point_distances[active_landing_point] < min_landing_point_distance:
                    min_landing_point_distance = self.landing_point_distances[active_landing_point]
                    closest_active_landing_point = active_landing_point

            self.closest_landing_point = closest_active_landing_point
            self.closest_landing_point_distance = min_landing_point_distance

            self.update_cached = True
        """

        if self.orphaned:
            return 0.0
            
        if self.update_cached: 
            self.equipment_moving_cost = self.closest_landing_point_distance * 0.01
            self.felling_cost = self.non_harvest_weight * 12 + self.harvest_weight * 10
            self.processing_cost = self.harvest_weight * 15
            self.skidding_cost = self.harvest_weight * (self.closest_landing_point_distance * 0.061 + 20)

            self.felling_value = 2 * self.num_trees
            self.harvest_value = self.harvest_weight * 71.65

            self.value = (self.felling_value + self.harvest_value) - (self.equipment_moving_cost + self.felling_cost + self.processing_cost + self.skidding_cost)

            self.update_cached = False

        return self.value

    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return "XY {} W {} N {} V {}".format(self.top_left, self.total_weight, self.num_trees, self.value)


            