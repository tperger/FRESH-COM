# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 17:07:38 2021

@author: perger
"""

# import packages
import pandas as pd
from datetime import timedelta, datetime
import pyam
import FRESH_clustering


# Model name and version, scenario, region
model_name = 'FRESH:COM v2.0'
scenario_name = 'Default scenario'
region_name = 'Austria'
filename_community = 'Input_data_community_IAMC.xlsx'
filename_grid = 'Input_data_grid_IAMC.xlsx'
filename_output = 'output_iamc.xlsx'

clustering = True

# Aggregation in the time domain: preparation
time_zone = '+01:00' # deviation from UTC (+01:00 is CET)
start_date = '2019-01-01 00:00' # YYYY-MM-DD HH:MM
number_days = 365
delta = timedelta(hours=1) # resolution ... hourly

time_steps = []
for t in range(24*number_days):
    time_steps.append((datetime.fromisoformat(start_date+time_zone)+t*delta))
index_time = list(range(len(time_steps)))

# Read Input Data (from the IAMC Format
file_community = pd.ExcelFile(filename_community)
prosumer = file_community.sheet_names

# Electricity demand, PV generation, and other prosumer data
variable_load = 'Final Energy|Residential and Commercial|Electricity'
variable_PV = 'Secondary Energy|Electricity|Solar|PV'
SoC_max = 'Maximum Storage|Electricity|Energy Storage System'
SoC_min = 'Minimum Storage|Electricity|Energy Storage System'
q_bat_max = 'Maximum Charge|Electricity|Energy Storage System'
q_bat_min = 'Maximum Discharge|Electricity|Energy Storage System'
PV_capacity = 'Maximum Active power|Electricity|Solar'
w = 'Price|Carbon'
_a = [SoC_max, SoC_min, q_bat_max, q_bat_min, PV_capacity, w]

load = pd.DataFrame()
PV = pd.DataFrame()
prosumer_data = pd.DataFrame()

for i in prosumer:
    # read excel sheet and convert to pyam.IamDataFrame
    _df = pd.read_excel(file_community, i)
    _df_pyam = pyam.IamDataFrame(_df)
    
    # filter data (load)
    _data = (_df_pyam
        .filter(variable=variable_load)
        .filter(region=region_name)
        .filter(model=model_name)
        .filter(scenario=scenario_name)
        .filter(time=time_steps))
    _b = _data.as_pandas().set_index('time')
    load = pd.concat([load, _b['value'].reindex(time_steps)], 
                     axis=1).rename(columns={'value':i})
    # filter data (PV)
    _data = (_df_pyam
        .filter(variable=variable_PV)
        .filter(region=region_name)
        .filter(model=model_name)
        .filter(scenario=scenario_name)
        .filter(time=time_steps))
    _b = _data.as_pandas().set_index('time')
    PV = pd.concat([PV, _b['value'].reindex(time_steps)], 
                   axis=1).rename(columns={'value':i})
    # Prosumer data (other)
    _data = (_df_pyam
        .filter(variable=_a)
        .filter(region=region_name)
        .filter(model=model_name)
        .filter(scenario=scenario_name))
    _b = _data.as_pandas().set_index('variable')
    prosumer_data = pd.concat([prosumer_data, _b['value'].reindex(_a)], 
                              axis=1).rename(columns={'value':i})
    
# Prices
_df = pd.read_excel(filename_grid)
_df_pyam = pyam.IamDataFrame(_df)

_data = (_df_pyam
        .filter(variable='Price|Final Energy|Residential|Electricity')
        .filter(region=region_name)
        .filter(model=model_name)
        .filter(scenario=scenario_name))
p_grid_in = _data['value'].values[0]/1000

_data = (_df_pyam
        .filter(variable='Price|Secondary Energy|Electricity')
        .filter(region=region_name)
        .filter(model=model_name)
        .filter(scenario=scenario_name))
p_grid_out = _data['value'].values[0]/1000

# Emissions
emissions = pd.DataFrame()

_data = (_df_pyam
        .filter(variable='Emissions|CO2')
        .filter(region=region_name)
        .filter(model=model_name)
        .filter(scenario=scenario_name)
        .filter(time=time_steps))
_b = _data.as_pandas().set_index('time')
emissions = pd.concat([emissions, _b['value'].reindex(time_steps)], 
                      axis=1).rename(columns={'value':'Emissions'})

# Other values
eta_battery = 0.9
distances = pd.read_excel('Input_data_community_other.xlsx',
                          sheet_name='Distances',
                          header=0, 
                          index_col='Prosumer')
alpha = pd.read_excel('Input_data_community_other.xlsx',
                      sheet_name='Alpha',
                      header=0, 
                      index_col='Prosumer')

if clustering:
    emissions, load, PV, time_steps = FRESH_clustering.cluster_input_data(prosumer, 
                                                                          emissions, 
                                                                          load, 
                                                                          PV, 
                                                                          k=3, 
                                                                          hours=24)
    index_time = list(range(len(time_steps)))
    
    
#import plots
#plots.plot_prosumer(load=load, 
#                    PV=PV, 
#                    w=prosumer_data.loc['Price|Carbon'], 
#                    prosumer=['Prosumer 1', 'Prosumer 2','Prosumer 3', 
#                              'Prosumer 4','Prosumer 5', 'Prosumer 6'],
#                    save=False)