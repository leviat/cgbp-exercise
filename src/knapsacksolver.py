#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyscipopt import Model, quicksum, SCIP_PARAMSETTING
import reader_cpmp

def solve(profits, weights, capacity):
    model = Model()

    model.hideOutput()

    ##################################################################################
    # Knapsack Model
    ##################################################################################

    # Initizalization of the variables
    x = {} # do we pack item i?
    
    # Create the variables
    nItems = len(profits)
    
    for i in range(nItems):
        x[i] = model.addVar(vtype = 'B', name="x(%s)"%(i)) # x[i] == 1 iff. item i is packed into the knapsack

    # Create the objective function: maximize profits of packed items
    model.setObjective(quicksum(profits[i] * x[i] for i in range(nItems)), "maximize")

    # Create the capacity constraints: we can pack at most [capacity] weight
    for i in range(nItems):
        model.addCons(quicksum(weights[i] * x[i] for i in range(nItems)) <= capacity)

    # optimize
    model.optimize()
    return list([i for i in range(nItems) if not model.isZero(model.getVal(x[i]))])