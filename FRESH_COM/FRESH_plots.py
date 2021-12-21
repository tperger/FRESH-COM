# -*- coding: utf-8 -*-
"""
Created on Tue Apr  6 15:02:38 2021

@author: perger
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme(palette='muted')

def prosumer_data(load, PV, w, prosumer, weight_cluster, save, file):
    
    sns.set_theme(palette='muted')

    sum_load = [sum(load[s]*weight_cluster) for s in prosumer] 
    sum_PV = [sum(PV[s]*weight_cluster) for s in prosumer]
    barWidth = 0.2
    r = np.arange(1,len(sum_load)+1)
    r1 = [x - 1*barWidth for x in r]
    r2 = [x + 1*barWidth for x in r]
    fig, ax1 = plt.subplots()

    ax1.bar(r1, sum_load, width = barWidth, color='g')
    ax1.bar(r, sum_PV, width = barWidth, color='y')
    ax1.bar(r2, [0]*len(sum_load), width = barWidth, color='b')
    lgd = plt.legend(['Total demand', 'Total PV generation','Willingness-to-pay'],
                     loc='upper right', 
                     bbox_to_anchor=(1, 1))
    plt.ylabel('Total demand/generation in kWh')
    plt.xticks(r, np.arange(1,len(prosumer)+1))
    
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    ax2.bar(r2, w[prosumer].tolist(), width = barWidth, color='b')
    #plt.legend(['Willingness-to-pay'])

    plt.grid() 

    plt.xlabel('Prosumer')
    plt.ylabel('Willingness-to-pay in EUR/tCO2')
    
    if save:
        plt.savefig (file, 
                     bbox_extra_artists=(lgd,), 
                     bbox_inches='tight', 
                     format = "pdf", 
                     dpi = 1200)
    else:
        plt.show()
        
def prosumer_data_all(load, PV, PV_max, load_min, load_max, 
                      w, prosumer, weight_cluster, save, file):
    
    sns.set_theme(palette='muted')
    colors_light = sns.hls_palette(8,l=0.8,s=0.9)

    # Prepare data
    sum_load = [sum(load[s]*weight_cluster) for s in prosumer] 
    sum_PV = [sum(PV[s]*weight_cluster) for s in prosumer]
    
    load_H0_norm = sum_load[-1]
    PV_H0_norm = sum_PV[-1]
    
    load_upper = load_max*load_H0_norm
    load_lower = load_min*load_H0_norm
    PV_upper = PV_max*PV_H0_norm
    PV_lower = 0*PV_H0_norm
    
    sum_load[-1] = load_lower
    sum_PV[-1] = PV_lower
    
    sum_load2 = np.append([0]*(len(sum_load)-1),load_upper-load_lower)
    sum_PV2 = np.append([0]*(len(sum_PV)-1),PV_upper)
    
    barWidth = 0.2
    x = np.arange(1,len(sum_load)+1)
    xleft = [r - 1*barWidth for r in x]
    xright = [r + 1*barWidth for r in x]
    fig, ax1 = plt.subplots()

    ax1.bar(xleft, sum_load, width = barWidth, color='g')
    ax1.bar(x, sum_PV, width = barWidth, color='y')
    ax1.bar(xright, [0]*len(sum_load), width = barWidth, color='b')
    lgd = plt.legend(['Total demand', 'Total PV generation','Willingness-to-pay'],
                     loc='upper left', 
                     bbox_to_anchor=(0.4, 1))
    
    ax1.set_ylim(0,8900)
    
    ax1.bar(xleft, sum_load2, bottom = sum_load, width = barWidth, 
            color='g')
    ax1.bar(x, sum_PV2, bottom = sum_PV, width = barWidth, 
            color='y')
    
    plt.ylabel('Total demand/generation in kWh')
    plt.xticks(x, list(x[:-1])+['H0/G0'])
    
    # Draw arrows
    
    plt.arrow(x=xleft[-1], y=load_lower, dx=0, dy=(load_upper-load_lower), 
              head_width=0.6*barWidth, head_length=300, linewidth=1, 
              color='w', length_includes_head=True) 
    plt.arrow(x=xleft[-1], y=load_upper, dx=0, dy=-(load_upper-load_lower), 
              head_width=0.6*barWidth, head_length=300, linewidth=1, 
              color='w', length_includes_head=True) 
    plt.arrow(x=x[-1], y=PV_lower, dx=0, dy=(PV_upper-PV_lower), 
              head_width=0.6*barWidth, head_length=300, linewidth=1, 
              color='w', length_includes_head=True)
    plt.arrow(x=x[-1], y=PV_upper, dx=0, dy=-(PV_upper-PV_lower), 
              head_width=0.6*barWidth, head_length=300, linewidth=1, 
              color='w', length_includes_head=True)

    #plt.annotate(s='', xy=(x[-1],5000), xytext=(x[-1],0), arrowprops=dict(arrowstyle='<->'))
    
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    ax2.bar(xright, w[prosumer].tolist(), width = barWidth, color='b')
    #plt.legend(['Willingness-to-pay'])

    plt.grid() 

    plt.xlabel('Prosumer')
    plt.ylabel('Willingness-to-pay in EUR/tCO2')
    
    if save:
        plt.savefig (file, 
                     bbox_extra_artists=(lgd,), 
                     bbox_inches='tight', 
                     format = "pdf", 
                     dpi = 1200)
    else:
        plt.show()

def KKT_verification(results, results_old, prosumer_new, save, file):
    
    sns.set_theme(palette='muted')
    
    results_a = results.drop(prosumer_new).drop(['battery charging', 'battery discharging'], axis=1)
    results_b = results_old.drop(['battery charging', 'battery discharging'], axis=1)
    df = (results_a-results_b)/abs(results_b)*100
    #df = (results_a-results_b)
    fig, ax = plt.subplots()
    sns.boxplot(data=df, orient="h", dodge=True)
    #sns.stripplot(data=df)
    plt.xticks(fontsize=12)
    #ax.set_xlim(-0.000000001,0.000000001)
    plt.xlabel('Deviation of result in percent')

    if save:
        plt.savefig (file, 
                     bbox_inches='tight',
                     format = "pdf", 
                     dpi = 1200)
    else:
        plt.show()
        
def heatmap(q_share, save, file):
    
    sns.set_theme(palette='muted')   
        
    fig, ax = plt.subplots()
    white = [(0.9764705882352941,0.9764705882352941,0.9764705882352941)]
    cmap = sns.color_palette("RdPu", 15)
    ax = sns.heatmap(q_share.round(decimals=0), 
                     annot=True, 
                     cmap=cmap,  
                     fmt='g')
    sns.heatmap(q_share.round(decimals=0), 
                cmap=white, 
                linewidths=0.5, 
                vmin=0, 
                vmax=2, 
                mask=q_share.round(decimals=0) > 0, 
                cbar=False, 
                ax=ax)
    #heatmap.set_xticklabels(heatmap.get_xticklabels(), rotation=90)
    
    if save:
        plt.savefig (file, 
                 bbox_inches='tight',
                 format = "pdf", 
                 dpi = 1200)
    else:
        plt.show()
        
def PV_bars(results, results_old, prosumer_old, prosumer_new, save, file):
    
    colors = sns.color_palette("muted", 10).as_hex()
    
    bar1 = np.array([sum(results_old.loc[i,'self-consumption'] for i in prosumer_old),
                 sum(results.loc[i,'self-consumption'] for i in prosumer_old)])
    bottom1 = np.array([0, 0])
    new_buy = sum(results.loc[i,'buying community'] for i in prosumer_new)
    bar2 = np.array([sum(results_old.loc[i,'selling community'] for i in prosumer_old),
                     sum(results.loc[i,'selling community'] for i in prosumer_old) - new_buy])
    bottom2 = bottom1 + bar1
    bar3 = np.array([sum(results_old.loc[i,'selling grid'] for i in prosumer_old),
                     sum(results.loc[i,'selling grid'] for i in prosumer_old)])
    bottom3 = bottom2 + bar2
    bar4 = np.array([0, new_buy])
    bottom4 = bottom3 + bar3
    
    x = np.arange(0,2)
    plt.bar(x, bar1, bottom=bottom1, color='y')
    plt.bar(x, bar2, bottom=bottom2, color='g')
    plt.bar(x, bar3, bottom=bottom3, color=colors[1])
    plt.bar(x, bar4, bottom=bottom4, color=colors[4])
    plt.xticks(x, ['Old community', 'New community'])
    plt.ylabel('kWh')
    lgd = plt.legend(['Self-consumption', 
                      'Selling to old community', 
                      'Selling to the grid', 
                      'Selling to new prosumer'], 
                     loc='lower left', 
                     bbox_to_anchor=(1, 0.6))

    if save:
        plt.savefig (file, 
                     bbox_extra_artists=(lgd,), 
                     bbox_inches='tight', 
                     format = "pdf", 
                     dpi = 1200)
    else:
        plt.show()
        
def load_bars(results, results_old, prosumer_old, prosumer_new, save, file):
    
    colors = sns.color_palette("muted", 10).as_hex()
    
    bar1 = np.array([sum(results_old.loc[i,'self-consumption'] for i in prosumer_old),
                 sum(results.loc[i,'self-consumption'] for i in prosumer_old)])
    bottom1 = np.array([0, 0])
    new_sell = sum(results.loc[i,'selling community'] for i in prosumer_new)
    bar2 = np.array([sum(results_old.loc[i,'buying community'] for i in prosumer_old),
                     sum(results.loc[i,'buying community'] for i in prosumer_old) - new_sell])
    bottom2 = bottom1 + bar1
    bar3 = np.array([sum(results_old.loc[i,'buying grid'] for i in prosumer_old),
                     sum(results.loc[i,'buying grid'] for i in prosumer_old)])
    bottom3 = bottom2 + bar2
    bar4 = np.array([0, new_sell])
    bottom4 = bottom3 + bar3
    
    x = np.arange(0,2)
    plt.bar(x, bar1, bottom=bottom1, color='y')
    plt.bar(x, bar2, bottom=bottom2, color='g')
    plt.bar(x, bar3, bottom=bottom3, color=colors[0])
    plt.bar(x, bar4, bottom=bottom4, color=colors[4])
    plt.xticks(x, ['Old community', 'New community'])
    plt.ylabel('kWh')
    lgd = plt.legend(['Self-consumption', 
                      'Buying from old community', 
                      'Buying from the grid', 
                      'Buying from new prosumer'], 
                     loc='lower left', 
                     bbox_to_anchor=(1, 0.6))

    if save:
        plt.savefig (file, 
                     bbox_extra_artists=(lgd,), 
                     bbox_inches='tight', 
                     format = "pdf", 
                     dpi = 1200)
    else:
        plt.show()
        
        
def costs_emissions(results, results_old, prosumer_old, prosumer_new, save, file):
    
    colors = sns.color_palette("muted", 10).as_hex()

    delta_costs = []
    delta_emissions = []
    for i in prosumer_old:
        delta_costs.append((results.loc[i,'costs']
                            -results_old.loc[i,'costs']))
#                           / abs(results_old.loc[i,'costs'])*100)
        delta_emissions.append((results.loc[i,'emissions']
                                -results_old.loc[i,'emissions']))
 #                             / results_old.loc[i,'emissions']*100)

    # Prepare data for bars
    barWidth = 0.3
    x = np.arange(1, len(delta_costs)+1)
    x1 = [_x - 0.5*barWidth for _x in x]
    x2 = [_x + 0.5*barWidth for _x in x]
    
    y1max = max(abs(i) for i in delta_costs)*1.1
    y2max = max(abs(i) for i in delta_emissions)*1.1

    fig, ax1 = plt.subplots()
    
    # Set x-axis 
    plt.xticks(x)
    plt.xlabel('Prosumer')
     
    # Plot left axis
    ax1.bar(x1, delta_costs, width = barWidth, color = colors[3], label='Costs')
    
    # Plot right axis
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    ax2.bar(x2, delta_emissions, width = barWidth, color = colors[2], label='Emissions')
    
    # Adding legend
    ax2.legend(loc='upper right')
    ax1.legend(loc='lower right')
    
    # Adding labels
    ax1.set_ylabel('Increase/decrease in EUR', color = colors[3])
    ax2.set_ylabel('Increase/decrease in tCO2', color = colors[2])
    
    # Color y-axes
    ax1.tick_params(axis='y', labelcolor=colors[3])
    ax2.tick_params(axis='y', labelcolor=colors[2])
    
    # Setting axes limits
    ax1.set_ylim(-y1max,y1max)
    ax2.set_ylim(-y2max,y2max)

    # Setting grid
    ax1.xaxis.grid(True)
    ax2.yaxis.grid(False)
    
    #ax1.set_ylim(-80,40)

    if save:
        plt.savefig (file,  
                     bbox_inches='tight', 
                     format = "pdf", 
                     dpi = 1200)
    else:
        plt.show()
        
### Appendix B

def plot_avg_values(input_df, prosumer, y_label, save, file):

    df_avg = pd.DataFrame(index=range(1,25))
    
    for i in prosumer:
        for h in range(24):
            df_avg.loc[h+1,i]=(sum(input_df[i].to_list()[h+24*t]/365 for t in range(365)))
    
    ax1 = df_avg.plot(figsize=(10, 5))
    ax1.set_xlim(0,25)
    plt.xticks(range(1,25))
    plt.xlabel('hours')
    plt.ylabel(y_label)
    ax1.legend(loc='upper left')
    
    if save:
        plt.savefig (file,  
                     bbox_inches='tight', 
                     format = "pdf", 
                     dpi = 1200)
    else:
        plt.show()