import random
import sys
import os
import time
import copy
import json
import math


from scipy.spatial import KDTree

from cut import Cut

class Cuts():
    @classmethod
    def from_json(cls, cuts_json):
        active_cuts = set()
        for cut_json in cuts_json["active_cuts"]:
            cut = Cut.from_json(cut_json)
            active_cuts.add(cut)
        
        inactive_cuts = set()
        for cut_json in cuts_json["inactive_cuts"]:
            cut = Cut.from_json(cut_json)
            inactive_cuts.add(cut)

        cuts = cls(active_cuts, inactive_cuts)
        #cuts = cls(inactive_cuts)
        #cuts.active_cuts = active_cuts
        
        cuts.value = cuts_json["fitness"]

        return cuts

    def __init__(self, active_cuts, inactive_cuts):
        self.value = 0
        self.component_name = "cuts"

        #self.inactive_cuts = initial_cuts
        #self.active_cuts = set()

        self.active_cuts = active_cuts
        self.inactive_cuts = inactive_cuts
        
        self.active_landing_points = []

        self.forward_options = [
            self.add_random_cut,
            self.remove_random_cut,
            self.remove_orphaned_cuts
        ]
        
        self.forward_probabilities = [
           1.0,
           0.5,
           0.0001,
        ]
        
        self.reverse_map = {
            self.add_random_cut: self.remove_cut,
            self.remove_random_cut: self.add_cut
        }

        self.max_iterations = 200000.0

        self.starting_forward_probabilities = [
            1.0,
            0.5,
            0.0001,
        ]

        self.ending_forward_probabilites = [
            1.0,
            0.5,
            0.0001,
        ]

    def step(self):
        for i in range(len(self.forward_options)):
            self.forward_probabilities[i] = self.forward_probabilities[i] + \
                (self.ending_forward_probabilites[i] - self.starting_forward_probabilities[i]) * \
                (1 / self.max_iterations)

    def add_cut(self, cut):
        self.active_cuts.add(cut)
        self.inactive_cuts.remove(cut)

    def add_random_cut(self):
        if len(self.inactive_cuts) == 0:
            return None

        #print("Add Random Cut")

        choice = self.inactive_cuts.pop()
        self.active_cuts.add(choice)

        choice.reset_state()

        return choice

    def remove_cut(self, cut):
        self.active_cuts.remove(cut)
        self.inactive_cuts.add(cut)

    def remove_random_cut(self):
        if len(self.active_cuts) == 0:
            return None

        #print("Remove Random Cut")

        choice = self.active_cuts.pop()
        self.inactive_cuts.add(choice)

        return choice

    #TODO: Figure out how to do this on reset
    def update_landing_points(self, active_landing_points, landing_point):
        #print("Update Landing Points {}".format(landing_point))
        self.active_landing_points = active_landing_points
        
        for cut in self.active_cuts:
            cut.update_landing_points(landing_point)

    def remove_orphaned_cuts(self):   
        cuts_to_remove = set()
        for cut in self.active_cuts:
            if cut.orphaned:
                cuts_to_remove.add(cut)

        self.active_cuts.difference_update(cuts_to_remove)
        self.inactive_cuts.update(cuts_to_remove)


    def compute_value(self):
        self.value = 0

        for cut in self.active_cuts:
            cut.find_closest_active_landing_point(self.active_landing_points)

        for cut in self.active_cuts:
            self.value += cut.compute_value()

        return self.value

    def to_json(self):
        cuts_json = {}

        cuts_json["component_type"] = "cuts"
        cuts_json["fitness"] = self.value

        cuts_json["active_cuts"] = []
        for cut in self.active_cuts:
            cuts_json["active_cuts"].append(cut.to_json())
        
        cuts_json["inactive_cuts"] = []
        for cut in self.inactive_cuts:
            cuts_json["inactive_cuts"].append(cut.to_json())

        return cuts_json


    def export(self, output_dir):
        cuts_output_dir = os.path.join(output_dir, "cuts")
        if not os.path.exists(cuts_output_dir):
            os.makedirs(cuts_output_dir)
            
        for cut_index, cut in enumerate(self.active_cuts):
            output_dict = {}
            
            output_dict["fitness"] = cut.compute_value(self.active_landing_points)
            output_dict["felling_value"] = cut.felling_value
            output_dict["harvest_value"] = cut.harvest_value
            
            output_dict["equipment_moving_cost"] = cut.equipment_moving_cost
            output_dict["felling_cost"] = cut.felling_cost
            output_dict["processing_cost"] = cut.processing_cost
            output_dict["skidding_cost"] = cut.skidding_cost

            output_dict["non_harvest_weight"] = cut.non_harvest_weight
            output_dict["harvest_weight"] = cut.harvest_weight
            output_dict["num_trees"] = cut.num_trees
            output_dict["closest_landing_point_distance"] = cut.closest_landing_point_distance
            output_dict["closest_landing_point"] = cut.closest_landing_point

            x_left, y_top = cut.top_left
            x_right, y_bottom = cut.bottom_right

            output_dict["hull_points"] = [(x_left, y_top), (x_right, y_top),  (x_right, y_bottom), (x_left, y_bottom)]
        
            filename = "{}.json".format(cut_index)
       
            with open(os.path.join(cuts_output_dir, filename), 'w') as fp:
                json.dump(output_dict, fp)

    def __str__(self):
        return "AC {} INAC {}".format(len(self.active_cuts), len(self.inactive_cuts))

    def __repr__(self):
        return self.__str__()