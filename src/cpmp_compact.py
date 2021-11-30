#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 17:01:57 2020

@author: Elisabeth Rodríguez-Heck, Erik Mühmer
"""

from pyscipopt import Model, quicksum, SCIP_PARAMSETTING
import reader_cpmp


nlocations, nclusters, distances, demands, capacities = reader_cpmp.read_instance('../instances/p550/p550-03.cpmp')

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
for i in range(nlocations):
    y[i] = model_compact.addVar(vtype = 'B', name="y(%s)"%(i)) # y[i] = 1 iff i-th location is median, 0 otherwise
    for j in range(nlocations):
        x[i,j] = model_compact.addVar(vtype = 'B', name="x(%s,%s)"%(i,j)) # x[i,j] = 1 iff location i is assigned to location j, 0 otherwise
    
# Create the objective function: minimize total distances
model_compact.setObjective(quicksum(distances[i,j] * x[i,j] for i in range(nlocations) for j in range(nlocations)), "minimize")

# Create the assignment constraints: a location is assigned to at most one location/median
for i in range(nlocations):
    model_compact.addCons(quicksum(x[i,j] for j in range(nlocations)) == 1)
    
# Create the capacity constraints: demands of assigned locations does not exceed capacity of median
#                                  coupling of assignment and median variable
for j in range(nlocations):
    model_compact.addCons(quicksum(demands[i] * x[i,j] for i in range(nlocations)) <= capacities[j]*y[j])
    
# Create the p-median constraint: nclusters are needed
model_compact.addCons(quicksum(y[j] for j in range(nlocations)) == nclusters)

# optimize
model_compact.optimize()
