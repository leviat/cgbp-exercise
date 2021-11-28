#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 17:39:18 2020

@author: Elisabeth Rodríguez-Heck, Erik Mühmer
"""


from pyscipopt import Model, SCIP_PARAMSETTING, scip
from pyscipopt.scip import quicksum

import reader_cpmp
import branch_semiassign
import cons_semiassign
import pricer_cpmp

EPS = 1.e-10


    
def test_cpmp(nlocations, nclusters, distances, demands, capacities, solveinteger, semiassignmentbranching):
    # Create solver instance
    master = Model("CPMP")
    
    # By default, SCIPs output is printed in the std output, not visible here. To have visible output:
    master.redirectOutput()
    # Print SCIP version
    master.printVersion()
    
    # Set solver parameters
    master.setPresolve(SCIP_PARAMSETTING.OFF)
    master.setIntParam("presolving/maxrestarts", 0)
    master.setSeparating(SCIP_PARAMSETTING.OFF)

    
    master.setMinimize()
    
    # Creating a pricer
    pricer = pricer_cpmp.PricerCPMP(solveinteger)
    master.includePricer(pricer, "PricerCPMP", "Pricer to identify new CPMP assignment patterns")
    
    if solveinteger and semiassignmentbranching:
        conshdlr = cons_semiassign.ConshdlrSemiassign(pricer)
        master.includeConshdlr(conshdlr, name = "semiassign", desc = "constraint handler for branching decisions in capacitated p-median problems", enfopriority = 0, chckpriority=0, propfreq = 1, eagerfreq = 100, needscons = True, delayprop = False, proptiming = scip.PY_SCIP_PROPTIMING.BEFORELP)
        branchrule = branch_semiassign.BranchruleSemiassign(pricer,conshdlr)
        master.includeBranchrule(branchrule, name = "Semiassign", desc = "semi assignment branching rule", priority=50000, maxdepth = -1, maxbounddist = 1)


    # Initialize containers for the master constraints
    assignmentConss = []
    convexityConss = []
    pmedianCons = None
    
    #############################################################################################################
    # TODO: create the master constraints; you need to consider the following aspects:
    #   * The master constraints should not contain any variable yet 
    #   * The constraints should not be separated
    #   * What should the value of the parameter **modifiable** be?
    #   * You must store the constraints in the containers above: assignmentConss, convexityConss and pmedianCons
    #
    # NOTE: Due to performance issues and to PySCIPOpt implementation issues, we strongly recommend to write  
    # all constraints in the form "<=". How can you achieve this without losing correctness of the model?
    #############################################################################################################
    
    # Create the assignment constraints
        
    
    # Create the convexity constraints
     
    
    # Create the p-median constraint
       
    
    #
    # Prepare the pricer data
    #
    
    # Dictionary of pattern variables, keys are the medians, value is an array of pattern variables
    patternVars = []
    # Dictionary of counters, for each median we count how many variables we have generated. 
    nVarsMedian = {}
    for median in range(nlocations):
        nVarsMedian[median] = 0
    
    
    # Input data
    pricer.nlocations = nlocations
    pricer.nclusters = nclusters
    pricer.distances = distances
    pricer.demands = demands
    pricer.capacities = capacities
    
    # Master Variables
    pricer.patternVars = patternVars
    pricer.nVarsMedian = nVarsMedian
    
    # Master Constraints
    pricer.assignmentConss = assignmentConss
    pricer.convexityConss = convexityConss
    pricer.pmedianCons = pmedianCons
    
    #
    # Data structure to facilitate communcation between branching rule and pricer
    #
    
    # In this problem we also have to create the forbiddenassignments matrix, in order to communicate 
    # to the pricer which assignments cannot take place due to branching decisions
    
    # IMPORTANT: In this dictionary, first index is always the median, second index the location
    forbiddenassignments = {}
    # Initialize it to false everywehere: initially every assignment is possible
    for median in range(nlocations):
        for location in range(nlocations):
            forbiddenassignments[median,location] = False
    pricer.forbiddenassignments = forbiddenassignments
    
    
    master.optimize()
    
if __name__ == '__main__':
    # Change the name of the instance to test different instances
    nlocations, nclusters, distances, demands, capacities = reader_cpmp.read_instance('../instances/p25/p25-01.cpmp')
    
    # If solveinteger is True, we will solve the problem as an Integer Program, i.e., variables will be added as binary 'B' variables.
    # If solveinteger is False, we will solve the LP-relaxation, i.e., variables will be added as continuous 'C' variables.
    solveinteger = True
    
    # If semiassignmentbranching is True, we will use semiassignment branching. 
    # If semiassignmentbranching is False, we will not use semiassignment branching. 
    
    ############################################################################################################
    # TODO QUESTION - to answer in your report at the end of the exercise: 
    # If semiassignment = False, and solveinteger = True, what will the branching 
    # behaviour of the program be? Would it be correct? Justify your answer.
    ############################################################################################################
    semiassignmentbranching = True

    test_cpmp(nlocations, nclusters, distances, demands, capacities, solveinteger, semiassignmentbranching)
    
