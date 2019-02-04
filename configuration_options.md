# Algorithm Configurations
## Non-configurable
### harvested_tree_threshold
Weight threshold used by the program to determine harvested vs non-harvested trees
metric tonnes 
default 0.3
## Landing
### clearing_cost
Cost for creating a landing
dollars
default 400
## Cut
### moving_cost_per_foot
Cost for moving equipment. 
dollars per foot
default 0.01
### felling_cost_per_non_harvested_tonne
Cost for felling every non-harvested tree.
dollars per metric tonne
default 12
### felling_cost_per_harvested_tonne
Cost for felling every harvested tree
dollars per metric tonne
default 10
### processing_cost_per_harvested_tonne
Cost for processing every harvested tree
dollars per metric tonne
default 15
### skidding_cost_per_foot
Distance component of skidding cost.
dollars per foot per metric tonne
default 0.061
### skidding_cost_per_tonne
Weight component of skidding cost
dollars per metric tonne
default 20
### felling_value_per_tree
Value of each felled tree. USDA set.
dollars per tree
default 2
### harvest_value_per_tonne
Value from selling each harvested tree
dollars per metric tonne
default 49.60

# Heuristic Configurations
## type
Heuristic type
RecordToRecord
SimulatedAnnealing
## RecordToRecord
### deviation
Maximum allowed normalized deviation from best solution
default 0.1
### max_iterations
Maximum iterations before stopping
default 200000
## SimulatedAnnealing
Typically in simulated annealing the value delta is computed just from the difference 
between the values of the two solutions. For this project, we used the normalized value delta
computed as follows
value_delta = (self.base_value - neighbor_solution_value) / 
(abs(self.base_value) + abs(neighbor_solution_value))

The acceptance probability is computed as follows
accept_probability =  1.0 / math.exp((value_delta / self.temperature))
### temperature
Starting temperature
default 0.25
### min_temperature
Stopping temperature
default 0.00001
### alpha
Change in temperature per step
default 0.99
### repetitions
Number of repetitions at each temperature
default 200
