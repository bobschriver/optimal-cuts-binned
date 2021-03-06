import random
import functools
import time

from collections import deque

from cuts import Cuts
from landings import Landings

class Solution():
    @classmethod
    def from_json(cls, solution_json):
        solution = Solution()

        solution_components_json = solution_json["components"]

        for solution_component_json in solution_components_json:
            component_type = solution_component_json["component_type"]

            if component_type is "cuts":
                solution.add_component(Cuts.from_json(solution_component_json))
            elif component_type is "landings":
                solution.add_component(Landings.from_json(solution_component_json))
        
        solution.value = solution_json["fitness"]
        return solution

    def __init__(self):
        self.iterations = 0

        self.forward_options = []  
        self.forward_probabilities = []
        self.reverse_map = {}

        self.components = []
        
        self.reverse_queue = deque()


    def add_component(self, component):
        self.forward_options += component.forward_options
        self.forward_probabilities += component.forward_probabilities
        self.reverse_map.update(component.reverse_map)
        
        self.components.append(component)
    
    def compute_value(self):
        self.value = 0
        
        for component in self.components:
            self.value += component.compute_value()
        
        return self.value
        
    def forward(self):
        self.iterations += 1

        # This means we haven't reversed since last moving forward aka a solution has been accepted
        if self.reverse_queue:
            self.reverse_queue.clear()
        
        # Yes, this is weird
        self.forward_probabilities = []
        for component in self.components:
            component.step()
            self.forward_probabilities += component.forward_probabilities

        # Theoretically we could have this do multiple steps at a time
        # But for now we just have one
        for i in range(1):
            chose_option = False
            while not chose_option:
                forward_index = random.randint(0, len(self.forward_options) - 1)
                if random.random() < self.forward_probabilities[forward_index]:
                    forward_function = self.forward_options[forward_index]
                    result = forward_function()
                    #print("Forward {} {}".format(forward_index, time.time() - start_time))
                    
                    if result is not None and forward_function in self.reverse_map:
                        reverse_choice = self.reverse_map[forward_function]
                        self.reverse_queue.append(functools.partial(reverse_choice, result))
                    
                    chose_option = True
            
    def reverse(self):
        while self.reverse_queue:
            #print("Reversing")
            reverse_function = self.reverse_queue.pop()
            reverse_function()
            
    def export(self, output_dir):
        for component in self.components:
            component.export(output_dir)
            
    def copy_writable(self):
        writeable = Solution()
        
        for component in self.components:
            writeable.add_component(component.copy_writable())
        
        return writeable

    def to_json(self):
        solution_json = {}

        solution_json["fitness"] = self.value
        solution_json["iterations"] = self.iterations

        solution_json["components"] = []

        for component in self.components:
            solution_json["components"].append(component.to_json())

        return solution_json

    def __str__(self):
        string = ""

        for component in self.components:
            string += str(component) + "\t"
        
        return string

    def __repr__(self):
        return self.__str__()