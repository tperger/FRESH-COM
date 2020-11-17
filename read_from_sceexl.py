import pyam 
# import nomenclature

# 1) Installation process is already accomplished.

# 2) Push results. This step is already completed. Data exists on the scenario explorer.


# 3) Pull results from the scenario explorer

pyam.iiasa.Connection('openentrance')

# read from database
# select model, scenario, regions, variable


df = pyam.read_iiasa(
    'openentrance',
    model = 'HEROSCARS v1.0')

# show data
print(df.head())

# save data as pandas dataframe
data = df.as_pandas()


# 4) Unit conversion using pyam

#%% a. Using units already defined in pyam

# filter Final Energy|Electricity|Profile from dataset obtained in step 3
Filter_A = df.filter(model='HEROSCARS v1.0', variable='Final Energy|Electricity|Profile', level='1-')

# unit conversion from MW to GW
Filter_A = Filter_A.convert_unit('MW', to ='GW')

# save data as pandas dataframe
Filter_A = Filter_A.as_pandas()

#%% b. Using a custom conversion factor defined by the user

# filter Emissions|CO2 from dataset obtained in step 3
Filter_B = df.filter(model='HEROSCARS v1.0', variable='Emissions|CO2', region='Austria', level='1-')

# unit conversion from kg CO2/MWh to t CO2/MWh
Filter_B = Filter_B.convert_unit('kg CO2/MWh', to='my_unit', factor=1e-3)

# save data as pandas dataframe
Filter_B = Filter_B.as_pandas()

#%% c. Using a unit registry defined by the user
import pint
ureg = pint.UnitRegistry()
ureg.define('my_unit_reg = 1000 * MW')

# filter Emissions|CO2 from dataset obtained in step 3
Filter_C = df.filter(model='HEROSCARS v1.0', variable='Final Energy|Electricity|Profile', level='1-')

# # unit conversion from MW to GW
Filter_C = Filter_C.convert_unit('MW', to='my_unit_reg', registry=ureg)

# save data as pandas dataframe
Filter_C = Filter_C.as_pandas()