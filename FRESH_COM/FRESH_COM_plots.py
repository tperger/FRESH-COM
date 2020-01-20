# -*- coding: utf-8 -*-
"""
Created on Fri Dec 27 18:17:41 2019

@author: perger

This module provides functions to plot the results of FRESH:COM
"""

# libraries
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

def q_bar_2D_prosumer(Q, N, myxlabel, myylabel, mytitle):
    """ Show the power flow of each prosumer
    
    Keyword arguments:
        Q -- (DataFrame) power flow (rows: time steps, columns: prosumer)
        N -- (int) number of prosumer
        myxlabel, mylabel, mytitle -- (str)
    """
    # Prepare the  dataset:
    height = np.array(Q.sum(axis=0))
    bars = np.arange(1,N+1)
    y_pos = np.arange(len(bars))
    
    # Create bars
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.bar(y_pos, height, color = (0.5,0.1,0.5,0.6))
    
    # Create names on the x-axis
    plt.xticks(y_pos, bars)
    plt.ylabel(myylabel)
    plt.xlabel(myxlabel)
    plt.title(mytitle)
    # Show graphic
    plt.show()

    return fig

def q_bar_3D_total(Q, N, mytitle):
    """ Show the power flow of each prosumer
    
    Keyword arguments:
        Q -- (DataFrame) power flow (rows: prosumer selling, columns: prosumer buying)
        N -- (int) number of prosumer
        myxlabel, mylabel, myzlabel, mytitle -- (str)
    """ 
  
    # thickness of the bars
    dx, dy = .6, .4
    
    # prepare 3d axes
    fig = plt.figure(figsize=(10,6))
    ax = Axes3D(fig)
    
    # set up positions for the bars 
    xpos=np.arange(Q.shape[0])
    ypos=np.arange(Q.shape[1])
    
    # set the ticks in the middle of the bars
    ax.set_xticks(xpos + dx/2)
    ax.set_yticks(ypos + dy/2)
    
    # create meshgrid 
    # print xpos before and after this block if not clear
    ypos, xpos = np.meshgrid(ypos, xpos)
    xpos = xpos.flatten()
    ypos = ypos.flatten()
    
    # the bars starts from 0 attitude
    zpos=np.zeros(Q.shape).flatten()
    
    # the bars' heights
    dz = Q.values.ravel()
    
    # plot 
    ax.bar3d(xpos,ypos,zpos,dx,dy,dz, color = (0.5,0.1,0.5,0.5))
    
    # put the column / index labels
    ax.w_yaxis.set_ticklabels(Q.columns)
    ax.w_xaxis.set_ticklabels(Q.index)
    
    # name the axes
    ax.set_xlabel('Prosumer selling')
    ax.set_ylabel('Prosumer buying')
    ax.set_zlabel('kWh')
    # Show graphic
    #plt.show()

    return fig

def pie_chart_total(Q_total, legend, mytitle):
    """ Pie chart 
    
    Keyword arguments:
        Q_total -- (DataFrame) 
        legend -- (list)
    """
    return None