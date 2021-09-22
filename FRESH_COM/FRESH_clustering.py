# -*- coding: utf-8 -*-
"""
Created on Thu Mar 25 19:35:57 2021

@author: perger
"""
import pandas as pd
import numpy as np
from tslearn.clustering import TimeSeriesKMeans

def custom_reshape(timeseries, hours):
    """ Auxilary function for k-means"""
    datapoints = int(len(timeseries)/hours)
    return np.reshape(timeseries[:(datapoints*hours)],
                      (datapoints, hours))

def custom_norm(timeseries):
    """ Auxilary function for k-means"""
    norm = np.amax(timeseries.to_numpy())
    if norm > 0:
        norm_array = timeseries.to_numpy()/norm
    else:
        norm_array = timeseries.to_numpy()
    return norm_array, norm

def cluster_input(prosumer, emissions, load, PV, k, hours):
    """ Clustering of hourly input data into representative time periods using 
    k-means clustering algorithm
    
    Keyword arguments:
        prosumer ... list of prosumer names
        emissions ... marginal emissions (pandas.DataFrame(index=time_steps,
                                                           columns='Emissions')) 
        load ... electricity demand (pandas.DataFrame(index=time_steps,
                                                      columns=prosumer))
        PV ... PV generation (pandas.DataFrame(index=time_steps,
                                                      columns=prosumer))
        k ... number of clusters in the k means algorithm / number of 
              representative time periods (e.g. days, weeks, ...)
        hours ... number of hours in one representative time period
    """
    
    # Normalize and create input matrix (cluster_matrix) for k-means algorithm
    cluster_matrix = []
    norm = []
    
    # emissions
    _input, _norm = custom_norm(emissions)
    cluster_matrix = custom_reshape(_input, hours)
    norm.append(_norm)
    
    # load
    for i in prosumer:
        _input, _norm = custom_norm(load[i])
        cluster_matrix = np.append(cluster_matrix,
                                   custom_reshape(_input, hours), 
                                   axis=1)
        norm.append(_norm)
        
    # PV
    for i in prosumer:
        _input, _norm = custom_norm(PV[i])
        cluster_matrix = np.append(cluster_matrix,
                                   custom_reshape(_input, hours), 
                                   axis=1)
        norm.append(_norm)
    
    # Run k-means algorithm
    kmeans = TimeSeriesKMeans(n_clusters=k).fit(cluster_matrix)
    
    # Results of k-means
    result_kmeans = np.array(kmeans.cluster_centers_)[:,:,0]
    labels = np.array(kmeans.labels_)
    (unique, counts) = np.unique(labels, return_counts=True)
    
    # Scale k-means results according to weights 
    #for i in unique:
    #    result_kmeans[i,:] *= counts[i] / (sum(counts[j] for j in unique))
    
    # Re-scale and create data frames with representative times
    j = 0
    emissions_cluster = pd.DataFrame()
    load_cluster = pd.DataFrame()
    PV_cluster = pd.DataFrame()
    
    emissions_cluster['Emissions'] = np.reshape(result_kmeans[:,(j*hours):((j+1)*hours)],
                                                k*hours) * norm[j]
                                      
    j += 1
        
    for i in prosumer:
        load_cluster[i] = np.reshape(result_kmeans[:,(j*hours):((j+1)*hours)],
                                     k*hours) * norm[j]
        j += 1
            
    for i in prosumer:
        PV_cluster[i] = np.reshape(result_kmeans[:,(j*hours):((j+1)*hours)],
                                   k*hours) * norm[j]
        j += 1
    
    time_clustered = emissions_cluster.index
        
    return emissions_cluster, load_cluster, PV_cluster, time_clustered, counts
