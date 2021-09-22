# -*- coding: utf-8 -*-
"""
Created on Wed Mar 10 11:51:30 2021

@author: perger
"""

import numpy as np
import pandas as pd
from pyomo.environ import *

def run_LP(prosumer, cm, weight, battery, solver_name):

    # deactivate BESS
    if battery == False:
        for i in prosumer:
            cm.prosumer_data.loc[cm.SoC_max,i] = 0
            cm.prosumer_data.loc[cm.q_bat_max,i] = 0            
    
    # Define model as concrete model
    model = ConcreteModel()
    
    #Define optimization variables 
    model.q_grid_in = Var(cm.time_steps, 
                          prosumer, 
                          within = NonNegativeReals)
    model.q_grid_out = Var(cm.time_steps, 
                           prosumer, 
                           within = NonNegativeReals)
    model.q_share = Var(cm.time_steps, 
                        prosumer, 
                        prosumer, 
                        within = NonNegativeReals)
    model.q_bat_in = Var(cm.time_steps, 
                         prosumer, 
                         within = NonNegativeReals)
    model.q_bat_out = Var(cm.time_steps, 
                          prosumer, 
                          within = NonNegativeReals)
    model.SoC = Var(cm.time_steps, 
                    prosumer, 
                    within = NonNegativeReals)
    
    # Define constraints
    def load_constraint_rule(model, i, t):    
        return (model.q_grid_in[t,i] 
                + model.q_bat_out[t,i] 
                + sum(model.q_share[t,j,i] for j in prosumer)
                - cm.load.loc[t,i] == 0)
    model.load_con = Constraint(prosumer, 
                                cm.time_steps, 
                                rule = load_constraint_rule)
    
    def PV_constraint_rule(model, i, t):    
        return (model.q_grid_out[t,i] 
                + model.q_bat_in[t,i] 
                + sum(model.q_share[t,i,j] for j in prosumer) 
                - cm.PV.loc[t,i] == 0)
    model.PV_con = Constraint(prosumer, 
                              cm.time_steps, 
                              rule = PV_constraint_rule)
    
    def SoC_min_constraint_rule(model, i, t):
        return (model.SoC[t,i] >= cm.prosumer_data.loc[cm.SoC_min][i])
    model.SoC_min_con = Constraint(prosumer, 
                                   cm.time_steps, 
                                   rule = SoC_min_constraint_rule)
    
    def SoC_max_constraint_rule(model, i, t):
        return (model.SoC[t,i] <= cm.prosumer_data.loc[cm.SoC_max][i])
    model.SoC_max_con = Constraint(prosumer, 
                                   cm.time_steps, 
                                   rule = SoC_max_constraint_rule)
    
    def q_bat_in_constraint_rule(model, i, t):
        return (model.q_bat_in[t,i] <= cm.prosumer_data.loc[cm.q_bat_max][i])
    model.q_bat_in_con = Constraint(prosumer, 
                                    cm.time_steps, 
                                    rule = q_bat_in_constraint_rule)
    
    def q_bat_out_constraint_rule(model, i, t):
        return (model.q_bat_out[t,i] <= cm.prosumer_data.loc[cm.q_bat_max][i])
    model.q_bat_out_con = Constraint(prosumer, 
                                     cm.time_steps, 
                                     rule = q_bat_out_constraint_rule)
    
    def SoC_constraint_rule(model, i, t):
        if t == 0:
            return (model.SoC[cm.time_steps[-1],i] 
                    + model.q_bat_in[cm.time_steps[t],i]*cm.eta_battery 
                    - model.q_bat_out[cm.time_steps[t],i]/cm.eta_battery
                    - model.SoC[cm.time_steps[t],i] == 0)
        elif t > 0:
            return (model.SoC[cm.time_steps[t-1],i] 
                    + model.q_bat_in[cm.time_steps[t],i]*cm.eta_battery 
                    - model.q_bat_out[cm.time_steps[t],i]/cm.eta_battery
                    - model.SoC[cm.time_steps[t],i] == 0)
    model.SoC_con = Constraint(prosumer, 
                               cm.index_time, 
                               rule = SoC_constraint_rule)
    
    # Objective function
    community_welfare = {new_list: [] for new_list in prosumer}
    prosumer_welfare = {new_list: [] for new_list in prosumer}
    prosumer_welfare2 = {new_list: [] for new_list in prosumer}
       
    
    for i in prosumer:
        community_welfare[i] = sum(- cm.p_grid_in * model.q_grid_in[t,i]*weight[t]
                                   + cm.p_grid_out * model.q_grid_out[t,i]*weight[t] 
                                   for t in cm.time_steps)
        prosumer_welfare[i] = sum((cm.p_grid_in 
                                   + (cm.prosumer_data.loc[cm.w,j]
                                      * (1 - cm.distances.loc[i,j]))
                                   * cm.emissions.Emissions.loc[t] / 1000000)
                                  * model.q_share[t,i,j]*weight[t] 
                                  for j in prosumer 
                                  for t in cm.time_steps)
        prosumer_welfare2[i] = sum((cm.p_grid_in 
                                    + (cm.prosumer_data.loc[cm.w,i]
                                       * (1 - cm.distances.loc[j,i]))
                                    * cm.emissions.Emissions.loc[t] / 1000000)
                                   * model.q_share[t,j,i]*weight[t] 
                                   for j in prosumer 
                                   for t in cm.time_steps)
    
        # 1. prosumer i sells to prosumer j
        # 2. prosumer i buys from prosumer j
    
    model.obj = Objective(
        expr = sum(community_welfare[i] 
                   + prosumer_welfare2[i] 
                   for i in prosumer), 
        sense = maximize)
    
    opt = SolverFactory(solver_name)
    opt_success = opt.solve(model)
    
    # Evaluate the results
    social_welfare = value(model.obj)
    
    q_share_total = pd.DataFrame(index=prosumer)
    for j in prosumer:
        a = []
        for i in prosumer:
            a.append(value(sum(model.q_share[t,i,j]*weight[t] for t in cm.time_steps)))
        q_share_total[j] = a
    
    results= pd.DataFrame(index=prosumer)
    for i in prosumer:
        results.loc[i,'buying grid'] = value(sum(model.q_grid_in[t,i]*weight[t] 
                                                 for t in cm.time_steps))
        results.loc[i,'selling grid'] = value(sum(model.q_grid_out[t,i]*weight[t] 
                                                  for t in cm.time_steps))
        results.loc[i,'battery charging'] = value(sum(model.q_bat_in[t,i]*weight[t] 
                                                      for t in cm.time_steps))
        results.loc[i,'battery discharging'] = value(sum(model.q_bat_out[t,i]*weight[t] 
                                                         for t in cm.time_steps))
        results.loc[i,'self-consumption'] = q_share_total.loc[i,i]
        results.loc[i,'buying community'] = (sum(q_share_total.loc[j,i] 
                                                 for j in prosumer) 
                                             - q_share_total.loc[i,i])
        results.loc[i,'selling community'] = (sum(q_share_total.loc[i,j] 
                                                  for j in prosumer) 
                                              - q_share_total.loc[i,i])
        results.loc[i,'emissions'] = value(sum(model.q_grid_in[t,i]*weight[t]
                                               * cm.emissions.Emissions.loc[t]
                                               / 1000000 
                                                for t in cm.time_steps))
        results.loc[i,'costs'] = (value(-community_welfare[i]) 
                                      - value(prosumer_welfare[i]) 
                                      + value(prosumer_welfare2[i]))
    
    return results, q_share_total, social_welfare