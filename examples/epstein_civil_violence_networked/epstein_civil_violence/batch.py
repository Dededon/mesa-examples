from model import EpsteinCivilViolence
from mesa.batchrunner import FixedBatchRunner
import json

import numpy as np
import pandas as pd

from itertools import product

# parameters that will remain constant
fixed_parameters = {
    'width':40,
    'height':40,
    'citizen_density':0.7,
    'cop_density':0.074,
    'citizen_vision':7,
    'cop_vision':7,
    'legitimacy':0.8,
    # 'citizen_network_size':20,
    'max_jail_term':1000,
    'active_threshold':0.1,
    'arrest_prob_constant':2.3,
    # 'network_discount_factor':0.5,
    'movement':True,
    'max_iters':1000,
    # 'seed':None
}

# parameters you want to vary
# can also include combinations here
params = {
    'citizen_network_size': [*range(1,30+1,10)],
    'network_discount_factor': [0,0.33,.5,0.66,1],
    'seed': [*range(1,10+1,1)]
}

def dict_product(dicts): #could just use the below but it's cleaner this way
    """
    >>> list(dict_product(dict(number=[1,2], character='ab')))
    [{'character': 'a', 'number': 1},
     {'character': 'a', 'number': 2},
     {'character': 'b', 'number': 1},
     {'character': 'b', 'number': 2}]
    """
    return (dict(zip(dicts, x)) for x in product(*dicts.values()))

parameters_list = [*dict_product(params)]
# print(parameters_list)

# what to run and what to collect
# iterations is how many runs per parameter value
# max_steps is how long to run the model
max_steps = 500
batch_run = FixedBatchRunner(EpsteinCivilViolence, parameters_list,
                             fixed_parameters,
                             model_reporters={
                                "Quiescent": lambda m: m.count_quiescent(m),
                                "Active": lambda m: m.count_active(m),
                                "Jailed": lambda m: m.count_jailed(m),
                                "Speed of Rebellion Transmission": lambda m: m.speed_of_rebellion_calculation(m),
                                "Seed": lambda m: m.report_seed(m)
                             },
                             max_steps=max_steps)

# run the batches of your model with the specified variations
batch_run.run_all()


## NOTE: to do data collection, you need to be sure your pathway is correct to save this!
# Data collection
# extract data as a pandas Data Frame
batch_end = batch_run.get_model_vars_dataframe()
batch_step_raw = batch_run.get_collector_model()
# print(batch_step_raw)
# batch_step = {f'size{key[0]}_discount{key[1]}_run{key[2]}':list(value['Cooperating_Agents']) for key,value in batch_step_raw.items()}
# batch_df_a = batch_run.get_agent_vars_dataframe()

# export the data to a csv file for graphing/analysis
path = 'C:\\Users\\grace\\Desktop\\macs_abm\\mesa-examples\\examples\\epstein_civil_violence_networked\\data'
batch_end.to_csv(path+"\\model_batch.csv")

for key,df in batch_step_raw.items():
    df.to_csv(f'{path}\\step\\size{key[0]}_discount{key[1]}_{key[2]}.csv')

# batch_save = {f'{key[0]}_{key[1]}':list(value['Cooperating_Agents']) for key,value in batch_dict.items()}
# json.dump(batch_save, open("C:\\Users\\grace\\Desktop\\macs_abm\\5_Sheduling\\PD_Grid\\pd_grid\\data\\batch_list.json", 'w'), indent = 4)
# batch_df_a.to_csv("../data/agent_batch.csv")