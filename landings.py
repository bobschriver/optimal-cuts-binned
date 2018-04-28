import random
import os
import json
import copy

from scipy.spatial import KDTree
from scipy.spatial.distance import euclidean

from landing import Landing

class Landings():
    def __init__(self):    
        self.active_landings = []    
        self.inactive_landings = []

        self.active_change_callbacks = []
        self.inactive_change_callbacks = []

        self.forward_options = [
            self.add_random_landing,
            self.remove_random_landing
        ]
        
        self.forward_probabilities = [
            0.05,
            0.02
        ]
        
        self.reverse_map = {
            self.add_random_landing: self.remove_landing,
            self.remove_random_landing: self.add_landing
        }

    def add_point(self, x, y):
        self.inactive_landings.append(Landing((x, y)))

    def update_active_landings(self):
        for active_change_callback in self.active_change_callbacks:
            active_change_callback([landing.point for landing in self.active_landings])

    def add_landing(self, landing):
        self.active_landings.append(landing)
        self.inactive_landings.remove(landing)

        self.update_active_landings()
        
    def add_random_landing(self):
        choice = random.choice(self.inactive_landings)
        self.add_landing(choice)

        return choice
    
    def remove_landing(self, landing):
        self.active_landings.remove(landing)
        self.inactive_landings.append(landing)

        self.update_active_landings()
    
    def remove_random_landing(self):
        if len(self.active_landings) == 1:
            return None
    
        choice = random.choice(self.active_landings)
        self.remove_landing(choice)

        return choice
    
    def compute_value(self):
        value = 0
        for landing in self.active_landings:
            value += landing.compute_value()
            
        return value
    
    def copy_writable(self):
        writable = Landings()
        writable.active_landings = copy.copy(self.active_landings)
        writable.inactive_landings = copy.copy(self.inactive_landings)
        
        return writable
    
    def export(self, output_dir):
        landings_output_dir = os.path.join(output_dir, "landings")
        if not os.path.exists(landings_output_dir):
            os.makedirs(landings_output_dir)
        
        landings_dict = {}
        
        landing_points = [landing.point for landing in self.active_landings]
        landings_dict["landing_points"] = landing_points
        
        with open(os.path.join(landings_output_dir, "landings.json"), 'w') as fp:
            json.dump(landings_dict, fp)

    def __str__(self):
        return "{} Active Landings {} Inactive Landings".format(len(self.active_landings), len(self.inactive_landings))

    def __repr__(self):
        return self.__str__()