This set of scripts provides a method of generating a harvest plan given a set of individual tree locations and potential landing sites.

The only external requirement other than python is scipy. To install scipy, run `pip install scipy` 

There are a few manual parameters which must be configured before running. These parameters will eventually be converted into command line arguments

All parameters are located within the `find_optimal_cuts.py` file. 

First are the csv file locations
```
tree_points_path = "[TREE POINTS CSV]"
road_points_path = "[LANDING POINTS CSV]"
```

The tree point csv file is expected to contain the following columns:
`x y elevation basin height`

The landing point csv file is expected to contain the following columns:
`x y elevation basin`

The order of these columns in the csv file is unimportant.

Next are the grid parameters
```
top_left = ([TOP LEFT X], [TOP LEFT Y])
cut_width, cut_height = ([GRID CELL WIDTH], [GRID CELL HEIGHT])
```

These define the offset and scale of the grid

Finally is the heuristic
```
heuristic_type = "[HEURISTIC TYPE]"
```

Currently two heuristics are supported, RecordToRecord and SimulatedAnnealing.

The first run will generate a list of feasible harvest units from the input tree point set, and output to a json file. This file will subsequently be used instead of the csv files.
Solutions will be output to a folder with the heuristic name, with the filename containing the trial number and objective value

After configuration, to run use `python find_optimal_cuts.py`

