# -*- coding: utf-8 -*-
"""
Created on Wed Mar  3 14:54:50 2021

@author: perger
"""

import numpy as np
from numpy import matlib
import pandas as pd
from pyomo.environ import *


    
def run_KKT(prosumer, prosumer_new, prosumer_old, results_old,
            PV_min, PV_max, load_min, load_max,
            cm, weight, battery, solver_name):
    
    # deactivate BESS
    if battery == False:
        for i in prosumer:
            cm.prosumer_data.loc[cm.SoC_max,i] = 0
            cm.prosumer_data.loc[cm.q_bat_max,i] = 0   
        
    # Define model as concrete model
    model = ConcreteModel()
    
    # Define new variables
    model.PV_new = Var(prosumer_new, 
                       bounds = (0,PV_max)) 
    model.load_new = Var(prosumer_new, 
                         bounds = (0,load_max)) 
    
    model.b = Var(prosumer_new, within=Binary)
    
    # Define optimization variables 
    model.q_G_in = Var(cm.time_steps, 
                       prosumer, 
                       within = NonNegativeReals)
    model.q_G_out = Var(cm.time_steps, 
                        prosumer, 
                        within = NonNegativeReals)
    model.q_share = Var(cm.time_steps, 
                        prosumer, 
                        prosumer, 
                        within = NonNegativeReals)
    model.q_B_in = Var(cm.time_steps, 
                       prosumer, 
                       within = NonNegativeReals)
    model.q_B_out = Var(cm.time_steps, 
                        prosumer, 
                        within = NonNegativeReals)
    model.SoC = Var(cm.time_steps, 
                    prosumer, 
                    within = NonNegativeReals)
    
    model.lambda_load = Var(cm.time_steps, prosumer)
    model.lambda_PV = Var(cm.time_steps, prosumer)
    model.lambda_SoC = Var(cm.time_steps, prosumer)
    
    model.mu_SoC = Var(cm.time_steps, prosumer, within = NonNegativeReals)
    model.mu_B_in = Var(cm.time_steps, prosumer, within = NonNegativeReals)
    model.mu_B_out = Var(cm.time_steps, prosumer, within = NonNegativeReals)
    
    model.u_G_in = Var(cm.time_steps, prosumer, within=Binary)
    model.u_G_out = Var(cm.time_steps, prosumer, within=Binary)
    model.u_share = Var(cm.time_steps, prosumer, prosumer, within=Binary)
    model.u_B_in = Var(cm.time_steps, prosumer, within=Binary)
    model.u_B_out = Var(cm.time_steps, prosumer, within=Binary)
    model.u_SoC = Var(cm.time_steps, prosumer, within=Binary)
    model.u_SoC_max = Var(cm.time_steps, prosumer, within=Binary)
    model.u_B_max_in = Var(cm.time_steps, prosumer, within=Binary)
    model.u_B_max_out = Var(cm.time_steps, prosumer, within=Binary)
    
    
    model.M1 = 5000
    model.M2 = 2000
    
    # binary constraints
    
    model.bin_con = Constraint(expr=sum(model.b[i] for i in prosumer_new) == 1)
    
    def load_max_bin_rule(model, i):
        return (model.load_new[i]  <= model.b[i] * load_max)
    model.load_max_bin_con = Constraint(prosumer_new, 
                                    rule = load_max_bin_rule)
    
    def load_min_bin_rule(model, i):
        return (model.load_new[i]  >= model.b[i] * load_min)
    model.load_min_bin_con = Constraint(prosumer_new, 
                                    rule = load_min_bin_rule)
    
    def PV_max_bin_rule(model, i):
        return (model.PV_new[i]  <= model.b[i] * PV_max)
    model.PV_max_bin_con = Constraint(prosumer_new, 
                                  rule = PV_max_bin_rule)
    
    def PV_min_bin_rule(model, i):
        return (model.PV_new[i]  >= model.b[i] * PV_min)
    model.PV_min_bin_con = Constraint(prosumer_new, 
                                  rule = PV_min_bin_rule)
    
    # From KKT
    def q_G_in_complementarity_rule_1(model, i, t):
        return (cm.p_grid_in * weight[t] + model.lambda_load[t,i] >= 0)
    model.q_G_in_compl_1 = Constraint(prosumer, cm.time_steps, 
                                      rule = q_G_in_complementarity_rule_1)
    
    def q_G_in_complementarity_rule_2(model, i, t):
        return (cm.p_grid_in * weight[t]
                + model.lambda_load[t,i] <= (1-model.u_G_in[t,i])*model.M1)
    model.q_G_in_compl_2 = Constraint(prosumer, cm.time_steps, 
                                      rule = q_G_in_complementarity_rule_2)
    
    def q_G_in_complementarity_rule_3(model, i, t):
        return (model.q_G_in[t,i] <= model.u_G_in[t,i]*model.M2)
    model.q_G_in_compl_3 = Constraint(prosumer, cm.time_steps, 
                                      rule = q_G_in_complementarity_rule_3)
    
    def q_G_out_complementarity_rule_1(model, i, t):
        return (-cm.p_grid_out * weight[t] + model.lambda_PV[t,i] >= 0)
    model.q_G_out_compl_1 = Constraint(prosumer, cm.time_steps, 
                                       rule = q_G_out_complementarity_rule_1)
    
    def q_G_out_complementarity_rule_2(model, i, t):
        return (-cm.p_grid_out * weight[t]
                + model.lambda_PV[t,i] <= (1-model.u_G_out[t,i])*model.M1)
    model.q_G_out_compl_2 = Constraint(prosumer, cm.time_steps, 
                                       rule = q_G_out_complementarity_rule_2)
    
    def q_G_out_complementarity_rule_3(model, i, t):
        return (model.q_G_out[t,i] <= model.u_G_out[t,i]*model.M2)
    model.q_G_out_compl_3 = Constraint(prosumer, cm.time_steps, 
                                       rule = q_G_out_complementarity_rule_3)
    
    def q_share_complementarity_rule_1(model, i, j, t):
        return (-(cm.p_grid_in 
                  + (cm.prosumer_data.loc[cm.w,j]*(1 - cm.distances.loc[i,j]))
                  *cm.emissions.Emissions.loc[t]/1000000) * weight[t] 
                + model.lambda_load[t,j] 
                + model.lambda_PV[t,i] >= 0)
    model.q_share_compl_1 = Constraint(prosumer, prosumer, cm.time_steps, 
                                       rule = q_share_complementarity_rule_1)
    
    def q_share_complementarity_rule_2(model, i, j, t):
        return (-(cm.p_grid_in 
                  + (cm.prosumer_data.loc[cm.w,j]*(1 - cm.distances.loc[i,j]))
                  *cm.emissions.Emissions.loc[t]/1000000) * weight[t]
                + model.lambda_load[t,j] 
                + model.lambda_PV[t,i] <= (1-model.u_share[t,i,j])*model.M1)
    model.q_share_compl_2 = Constraint(prosumer, prosumer, cm.time_steps, 
                                       rule = q_share_complementarity_rule_2)
    
    def q_share_complementarity_rule_3(model, i, j, t):
        return (model.q_share[t,i,j] <= model.u_share[t,i,j]*model.M2)
    model.q_share_compl_3 = Constraint(prosumer, prosumer, cm.time_steps, 
                                       rule = q_share_complementarity_rule_3)
    
    def q_B_in_complementarity_rule_1(model, i, t):
        return (model.lambda_PV[t,i] 
                + model.lambda_SoC[t,i]*cm.eta_battery 
                + model.mu_B_in[t,i] >= 0)
    model.q_B_in_compl_1 = Constraint(prosumer, cm.time_steps, 
                                      rule = q_B_in_complementarity_rule_1)
    
    def q_B_in_complementarity_rule_2(model, i, t):
        return (model.lambda_PV[t,i] 
                + model.lambda_SoC[t,i]*cm.eta_battery 
                + model.mu_B_in[t,i] <= (1-model.u_B_in[t,i])*model.M1)
    model.q_B_in_compl_2 = Constraint(prosumer, cm.time_steps, 
                                      rule = q_B_in_complementarity_rule_2)
    
    def q_B_in_complementarity_rule_3(model, i, t):
        return (model.q_B_in[t,i] <= model.u_B_in[t,i]*model.M2)
    model.q_B_in_compl_3 = Constraint(prosumer, cm.time_steps, 
                                      rule = q_B_in_complementarity_rule_3)
    
    def q_B_out_complementarity_rule_1(model, i, t):
        return (model.lambda_load[t,i] 
                - model.lambda_SoC[t,i]/cm.eta_battery 
                + model.mu_B_out[t,i] >= 0)
    model.q_B_out_compl_1 = Constraint(prosumer, cm.time_steps, 
                                       rule = q_B_out_complementarity_rule_1)
    
    def q_B_out_complementarity_rule_2(model, i, t):
        return (model.lambda_load[t,i] 
                - model.lambda_SoC[t,i]/cm.eta_battery 
                + model.mu_B_out[t,i] <= (1-model.u_B_out[t,i])*model.M1)
    model.q_B_out_compl_2 = Constraint(prosumer, cm.time_steps, 
                                       rule = q_B_out_complementarity_rule_2)
    
    def q_B_out_complementarity_rule_3(model, i, t):
        return (model.q_B_out[t,i] <= model.u_B_out[t,i]*model.M2)
    model.q_B_out_compl_3 = Constraint(prosumer, cm.time_steps, 
                                       rule = q_B_out_complementarity_rule_3)
    
    def SoC_complementarity_rule_1(model, i, t):
        if t < cm.index_time[-1]:
            return (-model.lambda_SoC[cm.time_steps[t],i] 
                    + model.lambda_SoC[cm.time_steps[t+1],i] 
                    + model.mu_SoC[cm.time_steps[t],i] >= 0)
        elif t == cm.index_time[-1]:
            return (-model.lambda_SoC[cm.time_steps[t],i] 
                    + model.lambda_SoC[cm.time_steps[0],i] 
                    + model.mu_SoC[cm.time_steps[t],i] >= 0)
    model.SoC_compl_1 = Constraint(prosumer, cm.index_time, 
                                   rule = SoC_complementarity_rule_1)
    
    def SoC_complementarity_rule_2(model, i, t):
        if t < cm.index_time[-1]:
            return (-model.lambda_SoC[cm.time_steps[t],i] 
                    + model.lambda_SoC[cm.time_steps[t+1],i] 
                    + model.mu_SoC[cm.time_steps[t],i] 
                    <= (1-model.u_SoC[cm.time_steps[t],i])*model.M1)
        elif t == cm.index_time[-1]:
            return (-model.lambda_SoC[cm.time_steps[t],i] 
                    + model.lambda_SoC[cm.time_steps[0],i] 
                    + model.mu_SoC[cm.time_steps[t],i] 
                    <= (1-model.u_SoC[cm.time_steps[t],i])*model.M1)
    model.SoC_compl_2 = Constraint(prosumer, cm.index_time, 
                                   rule = SoC_complementarity_rule_2)
    
    def SoC_complementarity_rule_3(model, i, t):
            return (model.SoC[t,i] <= model.u_SoC[t,i]*model.M2)
    model.SoC_compl_3 = Constraint(prosumer, cm.time_steps, 
                                   rule = SoC_complementarity_rule_3)
    
    # Equality constraints: lambda
    def load_constraint_rule_old(model, i, t):    
        return (model.q_G_in[t,i] 
                + model.q_B_out[t,i] 
                + sum(model.q_share[t,j,i] for j in prosumer) 
                - cm.load.loc[t,i] == 0)
    model.load_con_old = Constraint(prosumer_old, cm.time_steps, 
                                    rule = load_constraint_rule_old)
    
    def load_constraint_rule_new(model, i, t):    
        return (model.q_G_in[t,i] 
                + model.q_B_out[t,i] 
                + sum(model.q_share[t,j,i] for j in prosumer) 
                - model.load_new[i]*cm.load.loc[t,i] == 0)
    model.load_con_new = Constraint(prosumer_new, cm.time_steps, 
                                    rule = load_constraint_rule_new)
    
    def PV_constraint_rule_old(model, i, t):    
        return (model.q_G_out[t,i] 
                + model.q_B_in[t,i] 
                + sum(model.q_share[t,i,j] for j in prosumer) 
                - cm.PV.loc[t,i] == 0)
    model.PV_con_old = Constraint(prosumer_old, cm.time_steps, 
                                  rule = PV_constraint_rule_old)
    
    def PV_constraint_rule_new(model, i, t):    
        return (model.q_G_out[t,i] 
                + model.q_B_in[t,i] 
                + sum(model.q_share[t,i,j] for j in prosumer) 
                - model.PV_new[i]*cm.PV.loc[t,i] == 0)
    model.PV_con_new = Constraint(prosumer_new, cm.time_steps, 
                              rule = PV_constraint_rule_new)
    
    def SoC_constraint_rule(model, i, t):
        if t == 0:
            return (model.SoC[cm.time_steps[-1],i] 
                    + model.q_B_in[cm.time_steps[t],i]*cm.eta_battery 
                    - model.q_B_out[cm.time_steps[t],i]/cm.eta_battery
                    - model.SoC[cm.time_steps[t],i] == 0)
        elif t > 0:
            return (model.SoC[cm.time_steps[t-1],i] 
                    + model.q_B_in[cm.time_steps[t],i]*cm.eta_battery 
                    - model.q_B_out[cm.time_steps[t],i]/cm.eta_battery
                    - model.SoC[cm.time_steps[t],i] == 0)
    model.SoC_con = Constraint(prosumer, cm.index_time, 
                               rule = SoC_constraint_rule)
    
    # Inequality constraints: mu
    
    def mu_SoC_max_complementarity_rule_1(model, i, t):
        return (cm.prosumer_data.loc[cm.SoC_max][i] - model.SoC[t,i] >= 0)
    model.mu_SoC_max_compl_1 = Constraint(prosumer, cm.time_steps, 
                                          rule = mu_SoC_max_complementarity_rule_1)
    
    def mu_SoC_max_complementarity_rule_2(model, i, t):
        return (cm.prosumer_data.loc[cm.SoC_max][i] 
                - model.SoC[t,i] <= (1-model.u_SoC_max[t,i])*model.M1)
    model.mu_SoC_max_compl_2 = Constraint(prosumer, cm.time_steps, 
                                          rule = mu_SoC_max_complementarity_rule_2)
    
    def mu_SoC_max_complementarity_rule_3(model, i, t):
        return (model.mu_SoC[t,i] <= model.u_SoC_max[t,i]*model.M2)
    model.mu_SoC_max_compl_3 = Constraint(prosumer, cm.time_steps, 
                                          rule = mu_SoC_max_complementarity_rule_3)
    
    def mu_q_B_in_complementarity_rule_1(model, i, t):
        return (cm.prosumer_data.loc[cm.q_bat_max][i] - model.q_B_in[t,i] >= 0)
    model.mu_q_B_in_compl_1 = Constraint(prosumer, cm.time_steps, 
                                          rule = mu_q_B_in_complementarity_rule_1)
    
    def mu_q_B_in_complementarity_rule_2(model, i, t):
        return (cm.prosumer_data.loc[cm.q_bat_max][i] 
                - model.q_B_in[t,i] <= (1-model.u_B_max_in[t,i])*model.M1)
    model.mu_q_B_in_compl_2 = Constraint(prosumer, cm.time_steps, 
                                          rule = mu_q_B_in_complementarity_rule_2)
    
    def mu_q_B_in_complementarity_rule_3(model, i, t):
        return (model.mu_B_in[t,i] <= model.u_B_max_in[t,i]*model.M2)
    model.mu_q_B_in_compl_3 = Constraint(prosumer, cm.time_steps, 
                                          rule = mu_q_B_in_complementarity_rule_3)
    
    def mu_q_B_out_complementarity_rule_1(model, i, t):
        return (cm.prosumer_data.loc[cm.q_bat_max][i] - model.q_B_out[t,i] >= 0)
    model.mu_q_B_out_compl_1 = Constraint(prosumer, cm.time_steps, 
                                          rule = mu_q_B_out_complementarity_rule_1)
    
    def mu_q_B_out_complementarity_rule_2(model, i, t):
        return (cm.prosumer_data.loc[cm.q_bat_max][i] 
                - model.q_B_out[t,i] <= (1-model.u_B_max_out[t,i])*model.M1)
    model.mu_q_B_out_compl_2 = Constraint(prosumer, cm.time_steps, 
                                          rule = mu_q_B_out_complementarity_rule_2)
    
    def mu_q_B_out_complementarity_rule_3(model, i, t):
        return (model.mu_B_out[t,i] <= model.u_B_max_out[t,i]*model.M2)
    model.mu_q_B_out_compl_3 = Constraint(prosumer, cm.time_steps, 
                                          rule = mu_q_B_out_complementarity_rule_3)
    
    
    # define welfare (with different parts  for simplification in the code)
    community_welfare = {new_list: [] for new_list in prosumer}
    prosumer_welfare = {new_list: [] for new_list in prosumer}
    prosumer_welfare2 = {new_list: [] for new_list in prosumer}
    
    
    for i in prosumer:
        community_welfare[i] = sum(- cm.p_grid_in*model.q_G_in[t,i]*weight[t]
                                   + cm.p_grid_out*model.q_G_out[t,i]*weight[t] 
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
    
        # prosumer_welfare[i]: prosumer i sells to prosumer j
        # prosumer_welfare2[i]: prosumer i buys from prosumer j
    
    costs = {new_list: [] for new_list in prosumer}    
    for i in prosumer:
        costs[i] = (-community_welfare[i] - prosumer_welfare[i] 
                    + prosumer_welfare2[i])
        
    Delta_costs = {new_list: [] for new_list in prosumer_old}    
    for i in prosumer_old:
        Delta_costs[i] = ((costs[i]-results_old.loc[i,'costs']))
                          #/ abs(results_old.loc[i,'costs']))
    
    emissions = {new_list: [] for new_list in prosumer}
    for i in prosumer:
        emissions[i] = (sum(model.q_G_in[t,i]*weight[t]
                            *cm.emissions.Emissions.loc[t] / 1000000
                            for t in cm.time_steps))
        
    Delta_emissions = {new_list: [] for new_list in prosumer_old}    
    for i in prosumer_old:
        Delta_emissions[i] = ((emissions[i]-results_old.loc[i,'emissions'])*1000)
                              #/ abs(results_old.loc[i,'emissions']))
        
    
    # objective functions
    
    # F1 ... overall emissions
    # F2 ... individual emissions
    # F3 ... individual costs
    # F4 ... individual weights on individual emissions and costs
    
    
    F1 = sum(emissions[i] for i in prosumer_old)
    
    F2 = sum(Delta_emissions[i] for i in prosumer_old)
    
    F3 = sum(Delta_costs[i] for i in prosumer_old)
    
    F4 = sum((cm.alpha.loc[i,'alpha'] * Delta_costs[i])
             +((1-cm.alpha.loc[i,'alpha']) * Delta_emissions[i])
             for i in prosumer_old)
    
    F5 = sum(costs[i] for i in prosumer_old)
    
    # choose one of the objective functions F1, F2, ... defined above
    model.obj = Objective(expr = F2, 
                          sense = minimize)
    
    opt = SolverFactory(solver_name)
    opt_success = opt.solve(model)
    
    # Evaluate the results
    social_welfare = value(sum(community_welfare[i] 
                               + prosumer_welfare[i] for i in prosumer))
    
    q_share = pd.DataFrame(index=prosumer)
    for j in prosumer:
        a = []
        for i in prosumer:
            a.append(value(sum(model.q_share[t,i,j]*weight[t]  
                               for t in cm.time_steps)))
        q_share[j] = a
    
    results = pd.DataFrame(index=prosumer)
    for i in prosumer:
        results.loc[i,'buying grid'] = value(sum(model.q_G_in[t,i]*weight[t]  
                                                 for t in cm.time_steps))
        results.loc[i,'selling grid'] = value(sum(model.q_G_out[t,i]*weight[t]  
                                                  for t in cm.time_steps))
        results.loc[i,'battery charging'] = value(sum(model.q_B_in[t,i]*weight[t]  
                                                      for t in cm.time_steps))
        results.loc[i,'battery discharging'] = value(sum(model.q_B_out[t,i]*weight[t]  
                                                         for t in cm.time_steps))
        results.loc[i,'self-consumption'] = q_share.loc[i,i]
        results.loc[i,'buying community'] = (sum(q_share.loc[j,i] 
                                                 for j in prosumer) 
                                             - q_share.loc[i,i])
        results.loc[i,'selling community'] = (sum(q_share.loc[i,j] 
                                                  for j in prosumer) 
                                              - q_share.loc[i,i])
        results.loc[i,'emissions'] = (value(sum(model.q_G_in[t,i]*weight[t] 
                                                *cm.emissions.Emissions.loc[t]
                                                / 1000000
                                                for t in cm.time_steps)))
        results.loc[i,'costs'] = (value(-community_welfare[i]) 
                                  - value(prosumer_welfare[i]) 
                                  + value(prosumer_welfare2[i])) 
    
    parameter = pd.DataFrame(index=prosumer_new)
    for i in prosumer_new:
        parameter.loc[i, 'PV'] = value(model.PV_new[i])
        parameter.loc[i, 'load'] = value(model.load_new[i])
        
    CE = value(model.obj)

    return results, q_share, social_welfare, parameter, CE