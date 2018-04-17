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
    def __init__(self, top_left, cut_width, cut_height):
        self.top_left = top_left

        self.cut_width = cut_width
        self.cut_height = cut_height

        self.initial_cuts = {}

        self.inactive_cuts = set()
        self.active_cuts = set()

        self.landing_points_kdtree = None

        self.forward_options = [
            self.add_random_cut,
            self.remove_random_cut
        ]
        
        self.forward_probabilities = [
            1.0,
            0.75
        ]
        
        self.reverse_map = {
            self.add_random_cut: self.remove_cut,
            self.remove_random_cut: self.add_cut
        }

    def add_tree(self, x, y, weight):
        normalized_x = x - self.top_left[0]
        normalized_y = y - self.top_left[1]

        cut_x_center = self.top_left[0] + (math.floor(normalized_x / self.cut_width) * self.cut_width + self.cut_width / 2)
        cut_y_center = self.top_left[1] + (math.floor(normalized_y / self.cut_height) * self.cut_height + self.cut_height / 2)

        cut_center = (cut_x_center, cut_y_center)

        if cut_center not in self.initial_cuts:
            self.initial_cuts[cut_center] = Cut(cut_center)
    
        self.initial_cuts[cut_center].add_tree(x, y, weight)

    def set_feasible_cuts(self, all_landing_points_kdtree):
        for cut in self.initial_cuts.values():
            value = cut.compute_value(all_landing_points_kdtree)
            cut.update_cached = True

            if value > 1:
                self.inactive_cuts.add(cut)

     
    def add_cut(self, cut):
        self.active_cuts.add(cut)
        self.inactive_cuts.remove(cut)

    def add_random_cut(self):
        choice = self.inactive_cuts.pop()
        self.active_cuts.add(choice)

        choice.update_cached = True

        return choice

    def remove_cut(self, cut):
        self.active_cuts.remove(cut)
        self.inactive_cuts.add(cut)

    def remove_random_cut(self):
        if len(self.active_cuts) == 0:
            return None

        choice = self.active_cuts.pop()
        self.inactive_cuts.add(choice)

        return choice

    def update_landing_points(self, landing_points_kdtree):
        self.landing_points_kdtree = landing_points_kdtree

        for cut in self.active_cuts:
            cut.update_cached = True

    def copy_writable(self):
        writable = Cuts(self.top_left, self.cut_width, self.cut_height)
        writable.active_cuts = copy.copy(self.active_cuts)
        writable.inactive_cuts = copy.copy(self.inactive_cuts)

        writable.landing_points_kdtree = copy.copy(self.landing_points_kdtree)

        return writable

    def compute_value(self):
        value = 0

        for cut in self.active_cuts:
            value += cut.compute_value(self.landing_points_kdtree)

        #print("Cut Compute Value {}".format(time.time() - start_time))
        return value

    def export(self, output_dir):
        cuts_output_dir = os.path.join(output_dir, "cuts")
        if not os.path.exists(cuts_output_dir):
            os.makedirs(cuts_output_dir)
            
        for cut_index, cut in enumerate(self.active_cuts):
            output_dict = {}
            
            output_dict["fitness"] = cut.compute_value(self.landing_points_kdtree)
            output_dict["non_harvest_weight"] = cut.non_harvest_weight
            output_dict["harvest_weight"] = cut.harvest_weight
            output_dict["num_trees"] = cut.num_trees
            output_dict["closest_landing_point_distance"] = cut.closest_landing_point_distance

            x_center,y_center = cut.center

            x_left = x_center - self.cut_width / 2
            x_right = x_center + self.cut_width / 2

            y_top = y_center - self.cut_height / 2
            y_bottom = y_center + self.cut_height / 2

            output_dict["hull_points"] = [(x_left, y_top), (x_right, y_top),  (x_right, y_bottom), (x_left, y_bottom)]
        
            filename = "{}.json".format(cut_index)
       
            with open(os.path.join(cuts_output_dir, filename), 'w') as fp:
                json.dump(output_dict, fp)

    def __str__(self):
        return "{} Active Cuts {} Inactive Cuts".format(len(self.active_cuts), len(self.inactive_cuts))

    def __repr__(self):
        return self.__str__()