import random
import os
import json
import copy

from scipy.spatial import KDTree
from scipy.spatial.distance import euclidean

from landing import Landing

class Landings():
    @classmethod
    def from_json(cls, landings_json):
        active_landings = []
        for landing_json in landings_json["active_landings"]:
            landing = Landing.from_json(landing_json)
            active_landings.append(landing)
        
        inactive_landings = []
        for landing_json in landings_json["inactive_landings"]:
            landing = Landing.from_json(landing_json)
            inactive_landings.append(landing)

        landings = cls(inactive_landings)
        landings.active_landings = active_landings

        Landings.value = landings_json["fitness"]

        return landings

    def __init__(self, initial_landings):  
        self.value = 0.0
        self.component_name = "landings"

        self.active_landings = []    
        self.inactive_landings = initial_landings

        self.active_landing_points = []

        self.active_change_callbacks = []
        self.inactive_change_callbacks = []

        self.forward_options = [
            self.add_random_landing,
            self.remove_random_landing,
        ]
        
        self.forward_probabilities = [
            0.15,
            0.03,
        ]
        
        self.reverse_map = {
            self.add_random_landing: self.remove_landing,
            self.remove_random_landing: self.add_landing,
        }

        self.max_iterations = 100000

        self.starting_forward_probabilities = [
            0.15,
            0.03,
        ]

        self.ending_forward_probabilites = [
            0.03,
            0.15,
        ]

    def step(self):
        for i in range(len(self.forward_options)):
            self.forward_probabilities[i] = self.forward_probabilities[i] + \
                (self.ending_forward_probabilites[i] - self.starting_forward_probabilities[i]) * \
                (1 / self.max_iterations)

    def update_active_landings(self, landing):
        for active_change_callback in self.active_change_callbacks:
            active_change_callback(self.active_landing_points, landing.point)

    def add_landing(self, landing):
        #print("Add Landing {}".format(landing))

        self.active_landings.append(landing)
        self.active_landing_points.append(landing.point)
        
        self.inactive_landings.remove(landing)

        self.update_active_landings(landing)
        
    def add_random_landing(self):
        #print("Add Random Landing")
        if len(self.inactive_landings) == 0:
            return None

        choice = random.choice(self.inactive_landings)
        self.add_landing(choice)

        return choice
    
    def remove_landing(self, landing):
        #print("Remove Landing {}".format(landing))
        self.active_landings.remove(landing)
        self.active_landing_points.remove(landing.point)

        self.inactive_landings.append(landing)

        self.update_active_landings(landing)
    
    def remove_random_landing(self):
        #print("Removing Random Landing")
        if len(self.active_landings) == 1:
            return None
    
        choice = random.choice(self.active_landings)
        self.remove_landing(choice)

        return choice
    
    def exchange_random_landing(self):
        if len(self.inactive_landings) == 0:
            return None
        
        if len(self.active_landings) == 0:
            return None

        landing_pair = (random.choice(self.active_landings), random.choice(self.inactive_landings))

        self.exchange_landing(landing_pair)

        return (landing_pair[1], landing_pair[0])

    def exchange_landing(self, landing_pair):
        self.remove_landing(landing_pair[0])
        self.add_landing(landing_pair[1])    

    def compute_value(self):
        self.value = 0.0

        for landing in self.active_landings:
            self.value += landing.compute_value()
            
        return self.value
    
    def copy_writable(self):
        writable = Landings(self.inactive_landings[:])

        writable.active_landings = self.active_landings[:]
        
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

    def to_json(self):
        landings_json = {}

        landings_json["component_type"] = "landings"
        landings_json["fitness"] = self.value

        landings_json["active_landings"] = []
        for landing in self.active_landings:
            landings_json["active_landings"].append(landing.to_json())
        
        landings_json["inactive_landings"] = []
        for landing in self.inactive_landings:
            landings_json["inactive_landings"].append(landing.to_json())

        return landings_json

    def __str__(self):
        return "AL {} INAL {}".format(len(self.active_landings), len(self.inactive_landings))

    def __repr__(self):
        return self.__str__()