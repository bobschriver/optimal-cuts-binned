import tkinter
import os
import time
import threading

from tkinter import filedialog
from tkinter.ttk import Progressbar

from find_optimal_cuts import OptimalCuts

root = tkinter.Tk()
root.title("Grid Cell Harvest Scheduler for Individual trees")
root.geometry("500x200")

trees_path = tkinter.StringVar()
landings_path = tkinter.StringVar()
configuration_path = tkinter.StringVar()
output_dir = tkinter.StringVar()

status = tkinter.StringVar()
progress_bar = Progressbar(root, length=100, mode="indeterminate")

current_value = tkinter.IntVar()
best_value = tkinter.IntVar()

def start_optimization():
    optimal_cuts = OptimalCuts(status, progress_bar, current_value, best_value)

    status.set("Starting optimization")
    optimal_cuts_task = threading.Thread(
        target=optimal_cuts.find, 
        args=(trees_path.get(), landings_path.get(), configuration_path.get(), output_dir.get())
        )
    optimal_cuts_task.start()


status_label = tkinter.Label(root, text="Status: Waiting for file input")
status_label.grid(column=0, row=5, sticky="w")

def update_status(*args):
    status_label.configure(text="Status: {}".format(status.get()))

status.trace("w", update_status)

progress_bar.grid(column=1, row=5)

start_button = tkinter.Button(
    root, 
    text="Start Optimization", 
    state="disabled",
    command=start_optimization)
start_button.grid(column=0, row=4, sticky="w")

def set_enabled_state(*args):
    if (os.path.exists(trees_path.get()) and   
        os.path.exists(landings_path.get()) and
        os.path.exists(configuration_path.get()) and
        os.path.exists(output_dir.get())):
        start_button.configure(state="normal")

trees_path.trace("w", set_enabled_state)
landings_path.trace("w", set_enabled_state)  
configuration_path.trace("w", set_enabled_state)  
output_dir.trace("w", set_enabled_state)    

tkinter.Label(root, text="Trees CSV file").grid(column=0, row=0, sticky="w")
trees_file_label = tkinter.Label(root, text="")
trees_file_label.grid(column=2, row=0, sticky="w")
def set_trees_file():
    trees_path.set(filedialog.askopenfilename(
        title="Trees Path",
        filetypes=[("text files", "*.txt")]
    ))

    trees_file_label.configure(text=os.path.basename(trees_path.get()))

trees_file_button = tkinter.Button(root, text="Choose File", command=set_trees_file)
trees_file_button.grid(column=1, row=0, sticky="w")


tkinter.Label(root, text="Landings CSV file").grid(column=0, row=1, sticky="w")
landings_file_label = tkinter.Label(root, text="")
landings_file_label.grid(column=2, row=1, sticky="w")
def set_landings_file():
    landings_path.set(filedialog.askopenfilename(
        title="Landings Path",
        filetypes=[("text files", "*.txt")]
    ))

    landings_file_label.configure(text=os.path.basename(landings_path.get()))

landings_file_button = tkinter.Button(root, text="Choose File", command=set_landings_file)
landings_file_button.grid(column=1, row=1, sticky="w")

tkinter.Label(root, text="Configuration JSON file").grid(column=0, row=2, sticky="w")
configuration_file_label = tkinter.Label(root, text="")
configuration_file_label.grid(column=2, row=2, sticky="w")
def set_configuration_file():
    configuration_path.set(filedialog.askopenfilename(
        title="Configuration Path",
        filetypes=[("json files", "*.json")]
    ))

    configuration_file_label.configure(text=os.path.basename(configuration_path.get()))

configuration_file_button = tkinter.Button(root, text="Choose File", command=set_configuration_file)
configuration_file_button.grid(column=1, row=2, sticky="w")


tkinter.Label(root, text="Output Directory").grid(column=0, row=3, sticky="w")
output_file_label = tkinter.Label(root, text="")
output_file_label.grid(column=2, row=3)
def set_output_dir():
    output_dir.set(filedialog.askdirectory(
        title="Output Directory"
    ))

    output_file_label.configure(text=os.path.basename(output_dir.get()))

output_dir_button = tkinter.Button(root, text="Choose Directory", command=set_output_dir)
output_dir_button.grid(column=1, row=3, sticky="w")

current_value_label = tkinter.Label(root, text="")
current_value_label.grid(row=6, column=0, sticky="w")

def update_current_value(*args):
    current_value_label.configure(text="Current Value: {}".format(current_value.get()))

current_value.trace("w", update_current_value)

best_value_label = tkinter.Label(root, text="")
best_value_label.grid(row=6, column=1, sticky="w")

def update_best_value(*args):
    best_value_label.configure(text="Best Value: {}".format(best_value.get()))

best_value.trace("w", update_best_value)

root.mainloop()