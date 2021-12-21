# -*- coding: utf-8 -*-
"""
Created on Thu May 27 16:59:44 2021

@author: perger
"""

import numpy as np
from numpy import matlib
import pandas as pd
from pyomo.environ import *
from pathlib import Path

import FRESH_define_community as cm
import FRESH_LP
import FRESH_KKT
import FRESH_plots

solver_name = 'gurobi'
battery = True

prosumer_old = (['Prosumer 1',
                 'Prosumer 2',
                 'Prosumer 3',
                 'Prosumer 4', 
                 'Prosumer 5', 
                 'Prosumer 6'])
prosumer_new = (['Prosumer H0'])
prosumer = prosumer_old + prosumer_new

PV_min = 0
PV_max = 5 # kWpeakp
load_min = 2 # 1000kWh/year
load_max = 8 # 1000kWh/year

#cm.prosumer_data.loc[cm.w, 'Prosumer G0'] = 100
#cm.prosumer_data.loc[cm.w, 'Prosumer H0'] = 100

if cm.clustering == True:
    hours = len(cm.time_steps) / len(cm.counts)
    weight = np.matlib.repmat(cm.counts,int(hours),1).transpose().reshape(len(cm.time_steps),1)[:,0]

results_old, q_share_old, social_welfare_old = FRESH_LP.run_LP(prosumer_old, 
                                                               cm, 
                                                               weight,
                                                               battery, 
                                                               solver_name)

results, q_share, social_welfare, parameter, CE = FRESH_KKT.run_KKT(prosumer, 
                                                                prosumer_new,
                                                                prosumer_old,
                                                                results_old,
                                                                PV_min,
                                                                PV_max, 
                                                                load_min, 
                                                                load_max,
                                                                cm, 
                                                                weight,
                                                                battery, 
                                                                solver_name)
    

# plot results

path_to_graphics = ('')

FRESH_plots.prosumer_data(load=cm.load, 
                          PV=cm.PV, 
                          w=cm.prosumer_data.loc['Price|Carbon'], 
                          prosumer=prosumer_old,
                          weight_cluster=weight,
                          save=False,
                          file=Path(path_to_graphics+'prosumer_data.pdf'))

FRESH_plots.heatmap(q_share,
                    save=False, 
                    file=Path(path_to_graphics+"heatmap_alpha_1.pdf"))

FRESH_plots.PV_bars(results, 
                    results_old, 
                    prosumer_old,
                    prosumer_new,
                    save=False,
                    file=Path(path_to_graphics+'bar_stacked_PV.pdf'))

FRESH_plots.load_bars(results, 
                      results_old, 
                      prosumer_old,
                      prosumer_new,
                      save=False,
                      file=Path(path_to_graphics+'bar_stacked_load.pdf'))

FRESH_plots.costs_emissions(results, 
                      results_old, 
                      prosumer_old,
                      prosumer_new,
                      save=False,
                      file=Path(path_to_graphics+'costs_emissions.pdf'))

FRESH_plots.prosumer_data_all(load=cm.load, 
                          PV=cm.PV,
                          PV_max=PV_max, 
                          load_min=load_min, 
                          load_max=load_max, 
                          w=cm.prosumer_data.loc['Price|Carbon'], 
                          prosumer=prosumer,
                          weight_cluster=weight,
                          save=False,
                          file=Path(path_to_graphics+'prosumer_data_all.pdf'))
