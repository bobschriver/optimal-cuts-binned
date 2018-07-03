import os
import csv
import random
import sys
import time
import copy
import math

import numpy as np

from cut import Cut
from cuts import Cuts
from landing import Landing
from landings import Landings

from solution import Solution
from heuristic import RecordToRecord,SimulatedAnnealing

class Solver():
    def __init__(self, heuristic, solution):
        self.heuristic = heuristic
        self.solution = solution
            
    def solve(self):
        iterations = 0
        start_time = time.time()
        while self.heuristic.continue_solving(iterations):
            iterations += 1

            self.solution.forward()

            accept_solution = self.heuristic.accept_solution(self.solution)
            if not accept_solution:
                #print("{} Not accepting \t {:03.2f} \t {:03.2f} \t {:03.2f}".format(iterations, self.solution.compute_value(), self.heuristic.base_value, self.heuristic.best_value))
                self.solution.reverse()
            else:
                #print("{} Accepting \t {:03.2f} \t {:03.2f} \t {:03.2f}".format(iterations, self.solution.compute_value(), self.heuristic.base_value, self.heuristic.best_value))
                self.heuristic.set_base_solution(self.solution)

            if iterations % 10000 == 0:
                print("{} Curr Value {} Base Value {} Best Value {} seconds {}".format(iterations, self.solution.compute_value(), self.heuristic.base_value, self.heuristic.best_value, time.time() - start_time))
                print("Curr {}\tFinal {}".format(self.solution, self.heuristic.final_solution))
                start_time = time.time()
            
            #if iterations % 10000 == 0:
            #    if not os.path.exists(str(iterations)):
            #        os.makedirs(str(iterations))
            #    
            #    self.heuristic.final_solution.export(str(iterations))
                

        #self.heuristic.final_solution.export("final")
        return self.heuristic.final_solution

def landings_from_csv(csv_path):
    initial_landings_coordinates = []
    #for i in range(100):
    #    x = random.randint(0, 1000)
    #    y = random.randint(0, 1000)
    #    z = random.randint(0, 1000)
    #    basin = int(x / 100) + int(y / 100)
    #    coordinate = (x, y, z, basin)

    #    initial_landings_coordinates.append(coordinate)

    with open(csv_path) as landing_points_file:
        landing_points_reader = csv.reader(landing_points_file)
        landing_points_header = next(landing_points_reader)
    
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
    with open(csv_path) as tree_points_file:
        tree_points_reader = csv.reader(tree_points_file)
        tree_points_header = next(tree_points_reader)
    
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
    print(all_landing_points)
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
top_left = (1374717.3778, 1141311.44275)
cut_width, cut_height = (50, 50)

initial_landings = landings_from_csv(road_points_path)
initial_cuts = binned_cuts_from_csv(tree_points_path, top_left, cut_width, cut_height)

feasible_cuts = binned_get_feasible_cuts(initial_cuts, [landing.point for landing in initial_landings])

num_trials = 100

if not os.path.exists("RecordToRecord"):
    os.makedirs("RecordToRecord")

for j in range(num_trials):
    landings = Landings(initial_landings)
    cuts = Cuts(feasible_cuts)

    landings.active_change_callbacks.append(cuts.update_landing_points)

    for i in range(20):
        landings.add_random_landing()

    initial_solution = Solution()
    initial_solution.add_component(landings)
    initial_solution.add_component(cuts)

    heuristic = RecordToRecord()
    heuristic.configure()

    solver = Solver(heuristic, initial_solution)

    final_solution = solver.solve()
 
    solution_dir = os.path.join(".", "RecordToRecord", "{}_{}".format(j, int(final_solution.compute_value())))
    
    os.makedirs(solution_dir)
    final_solution.export(solution_dir)    
        
        

    