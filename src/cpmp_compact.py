#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 17:01:57 2020

@author: Elisabeth Rodríguez-Heck, Erik Mühmer
"""

from pyscipopt import Model, quicksum, SCIP_PARAMSETTING
import reader_cpmp


nlocations, nclusters, distances, demands, capacities = reader_cpmp.read_instance('../instances/p550/p550-3.cpmp')

model_compact = Model()

# By default, SCIPs output is printed in the std output, not visible here. To have visible output:
model_compact.redirectOutput()
# Print SCIP version
model_compact.printVersion()

# Set solver parameters
model_compact.setPresolve(SCIP_PARAMSETTING.OFF)    
model_compact.setIntParam("presolving/maxrestarts", 0)    
model_compact.setSeparating(SCIP_PARAMSETTING.OFF)

model_compact.setMinimize()

##################################################################################
# TODO: Create the variables, constraints and objective function for 
# model_compact and optimize it
##################################################################################

# Initizalization of the variables
x = {}
y = {}



# Create the variables

    
# Create the objective function


# Create the assignment constraints

    
# Create the capacity constraints

    
# Create the p-median constraint


# optimize
model_compact.optimize()
