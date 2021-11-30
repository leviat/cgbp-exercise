#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 17:32:43 2020

@author: Elisabeth Rodríguez-Heck, Erik Mühmer
"""

# Format of the .cpmp instances:
#
# [nlocations] [nclusters]
# [distance_1_1] ... [distance_1_nlocations]
# [distance_2_1] ... [distance_2_nlocations]
# ...            ... ... 
# [distance_nlocations_1] ... [distance_nlocations_nlocations]
# [demand_1] ... [demand_nlocations]
# [capacity_1] ... [capacity_nlocations]

def is_integer(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

""" Method to read the .cpmp instances
:param filename: path to the instance to read
"""
def read_instance(filename):
    with open(filename) as fp:
        line = fp.readline()
        
        # Reading the first line separately to get nlocations and nclusters
        nlocations = 0
        nclusters = 0
        sp = line.split()
        print(line)
        if len(sp) > 0 and sp[0].isnumeric():
            assert len(sp) == 2
            assert is_integer(sp[0]) and is_integer(sp[1])
            nlocations = int(sp[0])
            nclusters = int(sp[1])
        
        # Reading the distance matrix
        nlines = 0                
        distances = {}
        
        ##############################################################################
        # TODO: read in the distance matrix and store the data in distances
        ##############################################################################
        
        for i in range(nlocations):
            line = fp.readline()
            sp = line.split()
            print(line)
            if len(sp) > 0 and sp[0].isnumeric():
                assert len(sp) == nlocations
                is_int = True
                for j in range(nlocations):
                    is_int = is_int and is_integer(sp[j])
                assert is_int
                for j in range(nlocations):
                    distances[i,j] = sp[j]
                
            
        # Reading the demands
        demands = {}
        #############################################################################
        # TODO: read in the demands 
        #############################################################################
        line = fp.readline()
        sp = line.split()
        if len(sp) > 0 and sp[0].isnumeric():
            assert len(sp) == nlocations
            for j in range(nlocations):
                is_int = is_int and is_integer(sp[j])
            assert is_int
            for j in range(nlocations):
                demands[j] = sp[j]

          
        # Reading the capacities
        capacities = {}
        #############################################################################
        # TODO: read in the capacities
        #############################################################################
        line = fp.readline()
        sp = line.split()
        if len(sp) > 0 and sp[0].isnumeric():
            assert len(sp) == nlocations
            for j in range(nlocations):
                is_int = is_int and is_integer(sp[j])
            assert is_int
            for j in range(nlocations):
                capacities[j] = sp[j]
        
    return nlocations, nclusters, distances, demands, capacities
