import os
import csv
import random
import sys
import time
import copy
import math
import json

import numpy as np

from cut import Cut
from cuts import Cuts
from landing import Landing
from landings import Landings

from solution import Solution
from heuristic import RecordToRecord,SimulatedAnnealing

def solution_json_to_str(solution_json):
    active_landings = 0
    inactive_landings = 0

    active_cuts = 0
    inactive_cuts = 0

    for component in solution_json["components"]:
        if component["component_type"] is "landings":
            active_landings = len(component["active_landings"])
            inactive_landings = len(component["inactive_landings"])
        elif component["component_type"] is "cuts":
            active_cuts = len(component["active_cuts"])
            inactive_cuts = len(component["inactive_cuts"])

    return "AL {} INAL {}\tAC {} INAC {}".format(
        active_landings, 
        inactive_landings,
        active_cuts, 
        inactive_cuts)

class Solver():
    def __init__(self, heuristic, solution):
        self.heuristic = heuristic
        self.solution = solution
            
    def solve(self):
        iterations = 0
        start_time = time.time()
        while self.heuristic.continue_solving(iterations):
            iterations += 1

            #print("{}\t{}\t{}".format(self.solution, self.solution.compute_value(), self.heuristic.final_value))
            self.solution.forward()
            #print("{}\t{}\t{}".format(self.solution, self.solution.compute_value(), self.heuristic.final_value))

            accept_solution = self.heuristic.accept_solution(self.solution)
            if not accept_solution:
                #print("{} \t NA \t {:03.2f} \t {:03.2f} \t {:03.2f}".format(iterations, self.solution.compute_value(), self.heuristic.base_value, self.heuristic.best_value))
                self.solution.reverse()
            else:
                #print("{} \t A \t {:03.2f} \t {:03.2f} \t {:03.2f}".format(iterations, self.solution.compute_value(), self.heuristic.base_value, self.heuristic.best_value))
                self.heuristic.set_base_solution(self.solution)
            
            #print("{}\t{}\t{}".format(self.solution, self.solution.compute_value(), self.heuristic.final_value))
            #print()


            if iterations % 10000 == 0:
                print("{} Curr Value {} Base Value {} Best Value {} seconds {}".format(iterations, self.solution.compute_value(), self.heuristic.base_value, self.heuristic.best_value, time.time() - start_time))
                print("Curr\t{}".format(self.solution))
                print("Final\t{}".format(solution_json_to_str(self.heuristic.final_solution_json)))
                start_time = time.time()
            
            if iterations % 1000 == 0:
                json.dump(self.heuristic.final_solution_json, open("latest_solution.json", "wb"), indent=2)
                

        #self.heuristic.final_solution.export("final")
        return self.heuristic.final_solution_json

def landings_from_csv(csv_path):
    initial_landings_coordinates = []
    
    """
    for i in range(100):
        x = random.randint(0, 1000)
        y = random.randint(0, 1000)
        z = random.randint(0, 1000)
        basin = int(x / 100) + int(y / 100)
        coordinate = (x, y, z, basin)

        initial_landings_coordinates.append(coordinate)
    """
    with open(csv_path) as landing_points_file:
        landing_points_reader = csv.reader(landing_points_file)
        _ = next(landing_points_reader)
    
        for landing_point_line in landing_points_reader:
            _, _, _, x_str, y_str, elev_str, basin_str = landing_point_line
    
            x = float(x_str)
            y = float(y_str)

            elevation = float(elev_str)
            basin = int(basin_str)
            coordinate = (x, y, elevation, basin)
    
            initial_landings_coordinates.append(coordinate)
    

    return [Landing(coordinate) for coordinate in initial_landings_coordinates]

def binned_cuts_from_csv(csv_path, global_top_left, cut_width, cut_height):
    initial_tree_coordinates = []
    """
    for i in range(10000):
        x = random.randint(0, 1000)
        y = random.randint(0, 1000)
        z = random.randint(0, 1000)
        basin = int(x / 100) + int(y / 100)
        weight = random.random() * 2

        coordinate = (x, y, z, basin, weight)

        initial_tree_coordinates.append(coordinate)

    """
    with open(csv_path) as tree_points_file:
        tree_points_reader = csv.reader(tree_points_file)
        _ = next(tree_points_reader)
    
        for tree_point_line in tree_points_reader:
            _, _, _, _, elev_str, basin_str, x_str, y_str, height_str = tree_point_line
            x = float(x_str)
            y = float(y_str)
    

            elevation = float(elev_str)
            basin = int(basin_str)
   
            height = float(height_str)
            weight = height * 0.82 * 49.91 * 0.000454

            #Yes, it is weird that weight is in the coordinate
            coordinate = (x, y, elevation, basin, weight)

            initial_tree_coordinates.append(coordinate)
    

    min_x, min_y = global_top_left

    initial_cuts = {}
    for cut_coordinate in initial_tree_coordinates:
        x, y, elevation, basin, weight = cut_coordinate
        normalized_x = x - min_x
        normalized_y = y - min_y

        top_left = (
            math.floor(normalized_x / cut_width) * cut_width + min_x,
            math.floor(normalized_y / cut_height) * cut_height + min_y
            )

        bottom_right = (
            top_left[0] + cut_width, 
            top_left[1] + cut_height
            )

        if top_left not in initial_cuts:
            initial_cuts[top_left] = Cut(top_left, bottom_right)
    
        initial_cuts[top_left].add_tree(x, y, weight, elevation, basin)

    return initial_cuts.values()

def binned_get_feasible_cuts(initial_cuts, all_landing_points):
    maximal_fitness = 0
    print(time.time())
    feasible_cuts = set()
    for cut in initial_cuts:
        value = cut.compute_value(all_landing_points)

        cut.closest_landing_point_distance = sys.maxsize
        cut.update_cached = True

        if value > 1:
            maximal_fitness += value
            feasible_cuts.add(cut)

    print(time.time())
    print("Max Fitness {}".format(maximal_fitness))
    return feasible_cuts

tree_points_path = os.path.join("/Users", "schriver", "projects", "optimal_cuts_binned", "44120_g2_trees.txt")
road_points_path = os.path.join("/Users", "schriver", "projects", "optimal_cuts_binned", "44120_g2_roads.txt")

#top_left = (1141311.44275, 1374717.3778)
#top_left = (1374717.3778, 1141311.44275)
top_left = (1377133.37353, 1118720.7104)
#top_left = (0, 0)

cut_width, cut_height = (50, 50)

if not os.path.exists("initial_landings.json"):
    initial_landings_list = landings_from_csv(road_points_path)
    initial_landings = Landings(initial_landings_list)

    initial_landings_json = initial_landings.to_json()

    json.dump(initial_landings_json, open("initial_landings.json", "wb"))
else:
    initial_landings_json = json.load(open("initial_landings.json", "rb"))

if not os.path.exists("feasible_cuts.json"):
    initial_cuts_list = binned_cuts_from_csv(tree_points_path, top_left, cut_width, cut_height)
    feasible_cuts_list = binned_get_feasible_cuts(initial_cuts_list, [landing.point for landing in initial_landings_list])
    feasible_cuts = Cuts(feasible_cuts_list)

    starting_cuts_json = feasible_cuts.to_json()
    json.dump(starting_cuts_json, open("feasible_cuts.json", "wb"))
else:
    starting_cuts_json = json.load(open("feasible_cuts.json", "rb"))

num_trials = 100

heuristic_type = "SimulatedAnnealing"

output_dir = heuristic_type
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

for j in range(num_trials):
    print("TRIAL {}".format(j))
    landings = Landings.from_json(initial_landings_json)
    cuts = Cuts.from_json(starting_cuts_json)

    landings.active_change_callbacks.append(cuts.update_landing_points)

    for i in range(40):
        landings.add_random_landing()

    initial_solution = Solution()
    initial_solution.add_component(landings)
    initial_solution.add_component(cuts)

    if heuristic_type is "RecordToRecord":
        heuristic = RecordToRecord()
    elif heuristic_type is "SimulatedAnnealing":
        heuristic = SimulatedAnnealing()
        
    heuristic.configure()
        
    solver = Solver(heuristic, initial_solution)
    final_solution_json = solver.solve()
 
    solution_path = os.path.join(output_dir, "{}_{}.json".format(j, int(final_solution_json["fitness"])))
    json.dump(final_solution_json, open(solution_path, "wb"), indent=2)    
        
        

    