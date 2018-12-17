import os
import csv
import random
import sys
import time
import copy
import math
import json
import argparse
import uuid

from cut import Cut
from cuts import Cuts
from landing import Landing
from landings import Landings

from solution import Solution
from heuristic import RecordToRecord, SimulatedAnnealing

import boto3

s3 = boto3.resource('s3')

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
    def __init__(self, heuristic, solution, output_dirname):
        self.heuristic = heuristic
        self.solution = solution
        self.output_dirname = output_dirname
            
    def solve(self):
        iterations = 0
        start_time = time.time()

        iteration_fitnesses = {}
        iteration_fitnesses["current_value"] = {}
        iteration_fitnesses["best_value"] = {}
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


            if iterations % 1000 == 0:
                print("{} Curr Value {} Base Value {} Best Value {} seconds {}".format(iterations, self.solution.compute_value(), self.heuristic.base_value, self.heuristic.best_value, time.time() - start_time))
                print("Curr\t{}".format(self.solution))
                print("Final\t{}".format(solution_json_to_str(self.heuristic.final_solution_json)))
                start_time = time.time()
            
            if iterations % 1000 == 0:
                iteration_fitnesses["current_value"][iterations] = self.heuristic.base_value
                iteration_fitnesses["best_value"][iterations] = self.heuristic.best_value
                
            if iterations % 10000 == 0:
                current_solution_json = self.solution.to_json()
                current_solution_path = os.path.join(bucket_dirname, "{}.json".format(int(current_solution_json["fitness"])))
                current_solution_object = s3.Object("optimal-cuts", current_solution_path)
                current_solution_object.put(Body=json.dumps(current_solution_json, indent=2))
                #json.dump(current_solution_json, open(current_solution_path, "w"))
                print("Wrote current solution to {}".format(current_solution_path))

        return (self.heuristic.final_solution_json, iteration_fitnesses)

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
        header = next(landing_points_reader)
    
        x_index = header.index("x")
        y_index = header.index("y")
        elevation_index = header.index("elevation")
        basin_index = header.index("basin")

        for landing_point_line in landing_points_reader:
            x = float(landing_point_line[x_index])
            y = float(landing_point_line[y_index])

            elevation = float(landing_point_line[elevation_index])
            basin = int(landing_point_line[basin_index])

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
        header = next(tree_points_reader)
    
        x_index = header.index("x")
        y_index = header.index("y")
        elevation_index = header.index("elevation")
        basin_index = header.index("basin")
        height_index = header.index("height")

        for tree_point_line in tree_points_reader:
            x = float(tree_point_line[x_index])
            y = float(tree_point_line[y_index])

            elevation = float(tree_point_line[elevation_index])
            basin = int(tree_point_line[basin_index])
   
            height = float(tree_point_line[height_index])
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
    feasible_cuts = set()
    for cut in initial_cuts:
        cut.find_closest_active_landing_point(all_landing_points)
        value = cut.compute_value()

        cut.closest_landing_point_distance = sys.maxsize
        cut.update_cached = True

        if value > 1:
            maximal_fitness += value
            feasible_cuts.add(cut)

    print("Max Fitness {}".format(maximal_fitness))
    return feasible_cuts

# CONFIGURATION
parser = argparse.ArgumentParser()
parser.add_argument("--tile_name", dest="tile_name")       
parser.add_argument("--heuristic", dest="heuristic")
parser.add_argument("--num_trials", dest="num_trials", default=100, type=int)
parser.add_argument("--top_left", dest="top_left", default=(0, 0), type=tuple)
parser.add_argument("--cut_size", dest="cut_size", default=(50, 50), type=tuple)

args = parser.parse_args()

tile_name = args.tile_name
tree_points_path = "{}-trees.txt".format(tile_name)
landing_points_path = "{}-landings.txt".format(tile_name)
heuristic_type = args.heuristic
num_trials = args.num_trials
top_left = args.top_left
cut_width, cut_height = args.cut_size
min_basin = 0
algorithm_name = "grid_cell"

tile_initial_landings_filename = "{}_initial_landings.json".format(tile_name)
if not os.path.exists(tile_initial_landings_filename):
    initial_landings_list = landings_from_csv(landing_points_path)

    active_landings_list = []
    inactive_landings_list = initial_landings_list
    initial_landings = Landings(active_landings_list, inactive_landings_list)

    initial_landings_json = initial_landings.to_json()

    json.dump(initial_landings_json, open(tile_initial_landings_filename, "w"))
else:
    initial_landings_json = json.load(open(tile_initial_landings_filename, "rb"))

tile_feasible_cuts_filename = "{}_feasible_cuts.json".format(tile_name)
if not os.path.exists(tile_feasible_cuts_filename):
    initial_cuts_list = binned_cuts_from_csv(tree_points_path, top_left, cut_width, cut_height)
    initial_landings_list = Landings.from_json(initial_landings_json).inactive_landings
    feasible_cuts_set = binned_get_feasible_cuts(initial_cuts_list, [landing.point for landing in initial_landings_list])
    exit()

    active_cuts_set = set()
    inactive_cuts_set = feasible_cuts_set
    feasible_cuts = Cuts(active_cuts_set, inactive_cuts_set)

    starting_cuts_json = feasible_cuts.to_json()
    json.dump(starting_cuts_json, open(tile_feasible_cuts_filename, "w"))
else:
    starting_cuts_json = json.load(open(tile_feasible_cuts_filename, "rb"))


for j in range(num_trials):
    print("TRIAL {}".format(j))
    trial_uuid = str(uuid.uuid4())

    bucket_dirname = os.path.join("output", algorithm_name, heuristic_type, tile_name, trial_uuid)
    os.makedirs(bucket_dirname)

    landings = Landings.from_json(initial_landings_json)
    cuts = Cuts.from_json(starting_cuts_json)

    landings.active_change_callbacks.append(cuts.update_landing_points)

    for i in range(40):
        landings.add_random_landing()

    initial_solution = Solution()
    initial_solution.add_component(landings)
    initial_solution.add_component(cuts)

    if heuristic_type == "RecordToRecord":
        heuristic = RecordToRecord()
    elif heuristic_type == "SimulatedAnnealing":
        heuristic = SimulatedAnnealing()
        
    heuristic.configure()
        
    solver = Solver(heuristic, initial_solution, bucket_dirname)
    final_solution_json, iteration_fitnesses = solver.solve()

    final_solution_path = os.path.join(bucket_dirname, "{}_final.json".format(int(final_solution_json["fitness"])))
    final_solution_object = s3.Object("optimal-cuts", final_solution_path)
    #json.dump(final_solution_json, open(final_solution_path, "w"))
    final_solution_object.put(Body=json.dumps(final_solution_json, indent=2))    

    
    final_solution_fitnesses_path = os.path.join(bucket_dirname, "iteration_fitnesses.json")
    #json.dump(iteration_fitnesses, open(final_solution_fitnesses_path, "w"))
    final_solution_fitnesses_object = s3.Object("optimal-cuts", final_solution_fitnesses_path)
    final_solution_fitnesses_object.put(Body=json.dumps(iteration_fitnesses, indent=2))
        

    