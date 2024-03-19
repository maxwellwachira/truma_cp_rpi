# As Raspberry Pi has no Prefence. We will use a .json file to write, read and update data 
import json

from global_variables import ControlVariables

def read_json(filename):
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}  # If the file doesn't exist, start with an empty dictionary
    return data

def write_json(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

def update_json(filename, updates):
    data = read_json(filename)
    data.update(updates)
    write_json(filename, data)

def update_dict(json_file):
   ControlVariables.set_variable("temp", json_file["temp"])  
   ControlVariables.set_variable("heat", json_file["heat"])
   ControlVariables.set_variable("boil", json_file["boil"] ) 
   ControlVariables.set_variable("boil_mode", json_file["boil_mode"])
   ControlVariables.set_variable("fan", json_file["fan"])  
   ControlVariables.set_variable("rst", json_file["rst"])
