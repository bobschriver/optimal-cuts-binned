import sys

from scipy.spatial.distance import euclidean

from enum import Enum

class ClosestLandingState(Enum):
    KNOWN = 1 # Closest landing point is known and active
    UNKNOWN = 2 # Closest landing point is unknown
    SUBOPTIMAL = 3 # Closest landing point is no longer closest
    INACTIVE = 4 # Closest landing point is inactive

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

    @classmethod
    def configure(
        cls, 
        moving_cost_per_foot=0.01,
        felling_cost_per_non_harvested_tonne=12,
        felling_cost_per_harvested_tonne=10,
        processing_cost_per_harvested_tonne=15,
        skidding_cost_per_foot=0.061,
        skidding_cost_per_tonne=20,
        felling_value_per_tree=2,
        harvest_value_per_tonne=49.60 #71.65
    ):
        cls.moving_cost_per_foot = moving_cost_per_foot
        cls.felling_cost_per_non_harvested_tonne = felling_cost_per_non_harvested_tonne
        cls.felling_cost_per_harvested_tonne = felling_cost_per_harvested_tonne
        cls.processing_cost_per_harvested_tonne = processing_cost_per_harvested_tonne
        cls.skidding_cost_per_foot = skidding_cost_per_foot
        cls.skidding_cost_per_tonne = skidding_cost_per_tonne
        cls.felling_value_per_tree = felling_value_per_tree
        cls.harvest_value_per_tonne = harvest_value_per_tonne


    def reset_state(self):
        self.update_cached = True
        self.orphaned = False
        self.closest_landing_state = ClosestLandingState.UNKNOWN


    def __init__(self, top_left, bottom_right):
        self.reset_state()
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
        if updated_landing_point not in self.landing_point_distances:
            self.landing_point_distances[updated_landing_point] = self.compute_distance(updated_landing_point)

        # If our closest landing point is equal to the updated landing point
        # That means we are removing the landing point - need to find a new one

        # If it is not equal, that means we either added or removed it
        # If we removed it, and it is not the closest landing point, 
        # it could not have a closer landing point distance
        # If we added it, check if it is closer than our current landing point
        if updated_landing_point == self.closest_landing_point:
            self.closest_landing_state = ClosestLandingState.INACTIVE
            self.update_cached = True

        if self.landing_point_distances[updated_landing_point] < self.closest_landing_point_distance:
            self.closest_landing_state = ClosestLandingState.SUBOPTIMAL
            self.update_cached = True
    
    def compute_distance(self, landing_point):
        landing_x, landing_y, landing_elevation, landing_basin = landing_point

        basin_distance = 0

        if self.basin != landing_basin:
            basin_distance = 10000

        return euclidean((self.x, self.y), (landing_x, landing_y)) + basin_distance
        #return euclidean((self.x, self.y), (landing_x, landing_y))

    def find_closest_active_landing_point(self, active_landing_points):
        if (
            self.closest_landing_state == ClosestLandingState.UNKNOWN or 
            self.closest_landing_state == ClosestLandingState.SUBOPTIMAL or 
            self.closest_landing_state == ClosestLandingState.INACTIVE
        ):
            min_landing_point_distance = sys.maxsize
            for active_landing_point in active_landing_points:
                if active_landing_point not in self.landing_point_distances:
                    self.landing_point_distances[active_landing_point] = self.compute_distance(active_landing_point)

                if self.landing_point_distances[active_landing_point] < min_landing_point_distance:
                    min_landing_point_distance = self.landing_point_distances[active_landing_point]
                    closest_active_landing_point = active_landing_point

            self.closest_landing_point = closest_active_landing_point
            self.closest_landing_point_distance = min_landing_point_distance

            if (
                self.closest_landing_state == ClosestLandingState.INACTIVE and 
                self.closest_landing_point_distance > 10000
            ):
                self.orphaned = True
            else:
                self.orphaned = False

            self.closest_landing_state = ClosestLandingState.KNOWN
            

    def compute_value(self):
        if self.orphaned:
            return 0.0
            
        if self.update_cached: 
            self.equipment_moving_cost = self.closest_landing_point_distance * Cut.moving_cost_per_foot
            self.felling_cost = self.non_harvest_weight * Cut.felling_cost_per_non_harvested_tonne + self.harvest_weight * Cut.felling_cost_per_harvested_tonne
            self.processing_cost = self.harvest_weight * Cut.processing_cost_per_harvested_tonne
            self.skidding_cost = self.harvest_weight * (self.closest_landing_point_distance * Cut.skidding_cost_per_foot + Cut.skidding_cost_per_tonne)

            self.felling_value = self.num_trees * Cut.felling_value_per_tree
            self.harvest_value = self.harvest_weight * Cut.harvest_value_per_tonne

            self.value = (self.felling_value + self.harvest_value) - (self.equipment_moving_cost + self.felling_cost + self.processing_cost + self.skidding_cost)

            self.update_cached = False

        return self.value

    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return "XY {} W {} N {} V {}".format(self.top_left, self.total_weight, self.num_trees, self.value)


            