import sys
import math
import random

class SimulatedAnnealing():
    def __init__(self):
        self.base_value = -1000000.0
        self.best_value = -1000000.0
        self.final_value = -1000000.0

        self.iterations_since_improvement = 0
         
    def configure(self, temperature=0.25, min_temperature=0.00001, alpha=0.99, repetitions=200):
        self.temperature = temperature
        self.repetitions = repetitions
        self.alpha = alpha
        self.min_temperature = min_temperature    
        
    def set_base_solution(self, solution):
        solution_value = solution.compute_value()
        
        self.base_value = solution_value
        self.base_solution_json = solution.to_json()

        if self.base_value > self.best_value:
            self.final_value = self.base_value
            self.final_solution_json = self.base_solution_json

            self.best_value = self.base_value
            self.iterations_since_improvement = 0
        else:
            self.iterations_since_improvement += 1

    def continue_solving(self, iterations):
        if iterations % self.repetitions == 0:
            self.temperature = self.temperature * self.alpha
        
        continue_solving = True

        if self.temperature < self.min_temperature:
            print("Reached minimum temperature {}".format(iterations))
            continue_solving = False
        elif iterations > 150000 and self.iterations_since_improvement >= 10000:
            print("Have not improved in 10000 iterations {}".format(iterations))
            continue_solving = False

        return continue_solving
    
    def accept_solution(self, neighbor_solution):
        neighbor_solution_value = neighbor_solution.compute_value()
        
        value_delta = (self.base_value - neighbor_solution_value) / (abs(self.base_value) + abs(neighbor_solution_value))

        try:
            accept_probability =  1.0 / math.exp((value_delta / self.temperature))
        except OverflowError:
            accept_probability = 0
        except ZeroDivisionError:
            accept_probability = 1
            

        return random.random() < accept_probability
        
class RecordToRecord():
    def __init__(self):
        self.base_value = -1000000.0
        self.best_value = -1000000.0
        self.final_value = -1000000.0

        self.iterations_since_improvement = 0

    def configure(self, deviation=0.1, max_iterations=200000):           
        self.deviation = deviation
        self.max_iterations = max_iterations        
    
    def set_base_solution(self, solution):
        solution_value = solution.compute_value()
        self.base_value = solution_value
        
        if solution_value > self.best_value:
            self.best_value = solution_value
            self.best_solution_json = solution.to_json()

            self.final_value = self.best_value
            self.final_solution_json = self.best_solution_json

            self.iterations_since_improvement = 0
        else:
            self.iterations_since_improvement += 1

    def continue_solving(self, iterations):
        continue_solving = True

        if iterations > self.max_iterations:
            print("Reached maximum iterations {}".format(iterations))
            continue_solving = False
        elif iterations > 150000 and self.iterations_since_improvement >= 10000:
            print("Have not improved in 10000 iterations {}".format(iterations))
            continue_solving = False

        return continue_solving
        
    def accept_solution(self, solution):
        solution_value = solution.compute_value()

        return solution_value > self.best_value - abs(self.best_value * self.deviation)
