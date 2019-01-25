import os
import json
import csv
import sys
import math
import random

from cut import Cut
from cuts import Cuts

from landing import Landing
from landings import Landings

from solution import Solution
from heuristic import RecordToRecord, SimulatedAnnealing


class Preprocessor:
    def __init__(self, status, progress_bar):
        self.status = status
        self.progress_bar = progress_bar

    def landings_from_csv(self, csv_path):
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

    def binned_cuts_from_csv(self, csv_path, global_top_left, cut_width, cut_height):
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

    def binned_get_feasible_cuts(self, initial_cuts, all_landing_points):
        maximal_fitness = 0
        feasible_cuts = set()
        self.status.set("Finding feasible cuts")
        self.progress_bar.start()
        for i, cut in enumerate(initial_cuts):       
            cut.find_closest_active_landing_point(all_landing_points)
            value = cut.compute_value()

            cut.closest_landing_point_distance = sys.maxsize
            cut.update_cached = True

            if value > 1:
                maximal_fitness += value
                feasible_cuts.add(cut)
        self.progress_bar.stop()

        return feasible_cuts


    def preprocess(self, trees_path, landings_path, output_dir):
        top_left = (0, 0)
        cut_width, cut_height = (50, 50)

        tile_initial_landings_filename = os.path.join(output_dir, "initial_landings.json")
        if not os.path.exists(tile_initial_landings_filename):
            self.status.set("Loading landings from CSV")
            self.progress_bar.start()
            initial_landings_list = self.landings_from_csv(landings_path)

            active_landings_list = []
            inactive_landings_list = initial_landings_list
            initial_landings = Landings(active_landings_list, inactive_landings_list)

            initial_landings_json = initial_landings.to_json()

            json.dump(initial_landings_json, open(tile_initial_landings_filename, "w"))
            self.progress_bar.stop()
        else:
            self.status.set("Loading landings from JSON")
            self.progress_bar.start()
            initial_landings_json = json.load(open(tile_initial_landings_filename, "rb"))
            self.progress_bar.stop()


        tile_feasible_cuts_filename = os.path.join(output_dir, "feasible_cuts.json")
        if not os.path.exists(tile_feasible_cuts_filename):
            self.status.set("Loading trees from CSV")
            self.progress_bar.start()
            initial_cuts_list = self.binned_cuts_from_csv(trees_path, top_left, cut_width, cut_height)
            initial_landings_list = Landings.from_json(initial_landings_json).inactive_landings
            self.progress_bar.stop()

            feasible_cuts_set = self.binned_get_feasible_cuts(
                initial_cuts_list, 
                [landing.point for landing in initial_landings_list]
                )

            active_cuts_set = set()
            inactive_cuts_set = feasible_cuts_set
            feasible_cuts = Cuts(active_cuts_set, inactive_cuts_set)

            starting_cuts_json = feasible_cuts.to_json()
            json.dump(starting_cuts_json, open(tile_feasible_cuts_filename, "w"))
        else:
            self.status.set("Loading trees from JSON")
            self.progress_bar.start()
            starting_cuts_json = json.load(open(tile_feasible_cuts_filename, "rb"))
            self.progress_bar.stop()

        return initial_landings_json, starting_cuts_json

class Solver():
    def __init__(self, heuristic, status, progress_bar, current_value, best_value):
        self.heuristic = heuristic
        self.status = status
        self.progress_bar = progress_bar

        self.current_value = current_value
        self.best_value = best_value
            
    def solve(self, solution, output_dirname):
        iterations = 0

        iteration_fitnesses = {}
        iteration_fitnesses["current_value"] = {}
        iteration_fitnesses["best_value"] = {}

        self.progress_bar.start()
        self.status.set("Solution Iteration {}".format(0))

        while self.heuristic.continue_solving(iterations):
            iterations += 1

            solution.forward()

            accept_solution = self.heuristic.accept_solution(solution)
            if not accept_solution:
                solution.reverse()
            else:
                self.heuristic.set_base_solution(solution)

            
            if iterations % 100 == 0:
                self.status.set("Solution Iteration {}".format(iterations))
                self.current_value.set(solution.compute_value())
                self.best_value.set(self.heuristic.best_value)
            
            if iterations % 1000 == 0:
                iteration_fitnesses["current_value"][iterations] = self.heuristic.base_value
                iteration_fitnesses["best_value"][iterations] = self.heuristic.best_value
            
            """
            if iterations % 10000 == 0:
                current_solution_json = self.solution.to_json()
                current_solution_path = os.path.join(bucket_dirname, "{}.json".format(int(current_solution_json["fitness"])))
                current_solution_object = s3.Object("optimal-cuts", current_solution_path)
                current_solution_object.put(Body=json.dumps(current_solution_json, indent=2))
                #json.dump(current_solution_json, open(current_solution_path, "w"))
                print("Wrote current solution to {}".format(current_solution_path))
            """
        self.progress_bar.stop()
        return (self.heuristic.final_solution_json, iteration_fitnesses)


class OptimalCuts:
    def __init__(self, status, progress_bar, current_value, best_value):
        self.status = status
        self.progress_bar = progress_bar

        self.current_value = current_value
        self.best_value = best_value
    
    
    def configure(self, configuration):
        print(configuration)
        if "cut" in configuration:
            cut_configuration = configuration["cut"]
            Cut.configure(**cut_configuration)
            """
            if "moving_cost_per_foot" in cut_configuration:
                Cut.moving_cost_per_foot = cut_configuration["moving_cost_per_foot"]
            
            if "felling_cost_per_non_harvested_tree" in cut_configuration:
                Cut.felling_cost_per_non_harvested_tree = cut_configuration["felling_cost_per_non_harvested_tree"]

            if "felling_cost_per_harvested_tree" in cut_configuration:
                Cut.felling_cost_per_harvested_tree = cut_configuration["felling_cost_per_harvested_tree"]
    
            if "processing_cost_per_harvested_tree" in cut_configuration:
                Cut.processing_cost_per_harvested_tree = cut_configuration["processing_cost_per_harvested_tree"]

            if "skidding_cost_per_foot" in cut_configuration:
                Cut.skidding_cost_per_foot = cut_configuration["skidding_cost_per_foot"]

            if "skidding_cost_per_tonne" in cut_configuration:
                Cut.skidding_cost_per_tonne = cut_configuration["skidding_cost_per_tonne"]

            if "felling_value_per_tree" in cut_configuration:
                Cut.felling_value_per_tree = cut_configuration["felling_value_per_tree"]

            if "harvest_value_per_tonne" in cut_configuration:
                Cut.harvest_value_per_tonne = cut_configuration["harvest_value_per_tonne"]
            """

        if "landing" in configuration:
            landing_configuration = configuration["landing"]
            Landing.configure(**landing_configuration)
    

    def find(self, trees_path, landings_path, configuration_path, output_dir):
        configuration = json.load(open(configuration_path, 'r'))
        self.configure(configuration)

        preprocessor = Preprocessor(self.status, self.progress_bar)
        initial_landings_json, initial_cuts_json = preprocessor.preprocess(
            trees_path, 
            landings_path, 
            output_dir)

        landings = Landings.from_json(initial_landings_json)
        cuts = Cuts.from_json(initial_cuts_json)

        landings.active_change_callbacks.append(cuts.update_landing_points)

        for i in range(40):
            landings.add_random_landing()

        initial_solution = Solution()
        initial_solution.add_component(landings)
        initial_solution.add_component(cuts)

        heuristic_configuration = configuration["heuristic"]
        heuristic_type = heuristic_configuration["type"]

        if heuristic_type == "RecordToRecord":
            heuristic = RecordToRecord()
        elif heuristic_type == "SimulatedAnnealing":
            heuristic = SimulatedAnnealing()
            
        heuristic.configure(**heuristic_configuration["parameters"])

        solver = Solver(heuristic, self.status, self.progress_bar, self.current_value, self.best_value)
        final_solution_json, iteration_fitnesses = solver.solve(initial_solution, output_dir)

        final_solution_path = os.path.join(output_dir, "final_solution.json")
        json.dump(final_solution_json, open(final_solution_path, "w"), indent=2)
        
        final_solution_fitnesses_path = os.path.join(output_dir, "iteration_fitnesses.json")
        json.dump(iteration_fitnesses, open(final_solution_fitnesses_path, "w"), indent=2)