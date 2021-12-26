#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  9 13:52:43 2020

@author: Elisabeth Rodríguez-Heck, Erik Mühmer
"""

from __future__ import print_function
from ortools.algorithms import pywrapknapsack_solver

from pyscipopt import Model, Pricer, SCIP_RESULT, SCIP_PARAMSETTING
from pyscipopt.scip import quicksum

from dataclasses import dataclass
from typing import List

import math
import knapsacksolver

EPS = 1.e-10
LONG_INT_MAX = 9223372036854775807
#
# Data structures
#

# variable pricer data
@dataclass
class PatternVarData:
    median: int
    locations: List[int]


class PricerCPMP(Pricer):       
    def __init__(self, solveinteger, use_mip):
        self.nlocations = 0
        self.nclusters = 0
        self.distances = {}
        self.demands = {}
        self.capacities = {}
    
        # Master Vardata
        self.patternVars = []
        self.nvars = 0
        self.nVarsMedian = {}
        
        # Master Constraints
        self.assignmentConss = []
        self.convexityConss = []
        self.pmedianCons = None
        
        # Forbiddenassignments used to communicate between branching and pricer
        self.forbiddenassignments = {}
        
        # Solving LP relaxation or IP? 
        # If True, in addColumn variables are added as 'B' 
        # If False, in addColumn variables are added as 'C' 
        self.solveinteger = solveinteger
        
        self.use_mip = use_mip # if true we use the mip solver instead of the google knapsack solver

    # 
    # Local methods
    #    

    def isLocationInCluster(self, var, targetlocation):
        for location in var.data.locations:
            if location == targetlocation:
                return True
            
        return False


    """Add a new column to the master problem
     
    :param median: median for which the pricing problem has been solved
    :param sollocations: locations contained in the new cluster
    :param nsollocations: number of locations contained in the new cluser
    :param score: score for the column: either its reduced cost or Farkas value
    :return: SCIP status
    """
    def addColumn(self, median, sollocations):
        ###########################################################################################
        # TODO: compute the total service costs of the new cluster, to be stored in 'cost' 
        ###########################################################################################
        cost = sum([self.distances[location, median] for location in sollocations]) # total distances of new generated cluster
        
        
        # create a new variable representing the newly found cluster, add the corresponding data and add it to the master problem 
        varName = "Pattern_"+str(median)+"_"+str(self.nVarsMedian[median])
        self.nVarsMedian[median] = self.nVarsMedian[median]+1

        if self.solveinteger:
            newVar = self.model.addVar(varName, vtype = 'B', obj=cost, lb = 0.0, ub=1.0, pricedVar = True)
        else:
            newVar = self.model.addVar(varName, vtype = 'C', obj=cost, lb = 0.0, ub=1.0, pricedVar = True)
    
        ###########################################################################################
        # TODO: add the variable newVar to the master constraints:
        #   * to each service constraints whose location is contained in the cluster;
        #   * to the convexity constraint of the median
        #   * to the p-median constraint
        ###########################################################################################
        # p-median constraint
        self.model.addConsCoeff(self.pmedianCons, newVar, 1)
        # convexity constraint
        cons = self.convexityConss[median]
        self.model.addConsCoeff(cons, newVar, 1)
        # assignment constraint
        for location in sollocations:
            cons = self.assignmentConss[location]
            self.model.addConsCoeff(cons, newVar, -1)
        

        newVar.data = PatternVarData(median, sollocations)
        self.patternVars.append(newVar)
        self.nvars += 1
        
        return {'result':SCIP_RESULT.SUCCESS}
    
    
    """Call the pricing routine
    
    Method called by the callback methods pricerredcost and pricerfarkas 
    with appropriate value of the redcostpricing flag
    
    :param redcostpricing: True (resp. False) if method is called by the pricerredcost (resp. pricerfarkas) callback 
    """
    def performPricing(self, redcostpricing = False):
        for median in range(self.nlocations):           
            # Array of items in the knapsack problem
            items = []
            # Array of item profits
            profits = []
            # Array of item demands
            itemDemands = []
            
            ################################################################################################
            # TODO: prepare the knapsack problem for the current pricing problem:
            # store the possible locations as items, get their demands and calculate their profits;
            #
            # NOTE: Due to branching restrictions, not all locations are added as items, so you
            # need to check the forbiddenassignments data structure here. Have a look at the methods at 
            # the end of this file.
            #
            # NOTE: The profits depend on whether you do reduced cost pricing or Farkas pricing!!
            ################################################################################################
            
            for location in range(self.nlocations):
                if not self.isAssignmentForbidden(median, location):
                    items.append(location)
                    itemDemands.append(self.demands[location])

                    if redcostpricing == True: # reduced cost pricing
                        profits.append(-self.model.getDualsolLinear(self.assignmentConss[location]) - self.distances[(location, median)])
                    else: # Farkas
                        profits.append(-self.model.getDualfarkasLinear(self.assignmentConss[location]))

            
            
            ####################################################################################################
            # TODO: Prepare the data for the ortools knapsack solver. You have to consider the following points:
            # * The expected data format is as in the following artificialexample: 
            #      profits = [7 5 2 5 2 3]  -> a vector containing the profits of the items
            #      weights = [[10 12 13 15 16]] -> a vector containing the weights of the items
            #      capacities = [[23]]-> a vector with just one entry, the capacity of the knapsack
            # (See also description here: https://developers.google.com/optimization/bin/knapsack)
            # * The ortools solver can only handle integer profits and weights. Are your profits and weights 
            #   always integer? If not, how can you handle this?
            ####################################################################################################
            
            # These are the names of the variables used in knapsackSolver.Init() below, feel free to remove 
            # this initialization if necessary
            myItems = []
            profitsSolver = []
            weightsSolver = [[]]
            capacitiesSolver = [self.capacities[median]]
            
            if self.use_mip:
                packed_items = knapsacksolver.solve(profits, itemDemands, self.capacities[median])
                packed_items = [items[i] for i in packed_items] # re-project to original item / location ids
            else:
                for i in range(len(items)):
                    if profits[i] > EPS:
                        profitsSolver.append(int(math.ceil(profits[i] / EPS))) # divide by eps to get eps precision as integer
                        weightsSolver[0].append(itemDemands[i])
                        myItems.append(items[i]) # add the associated location for reprojection

                # initialize the ortools Knapsack solver
                knapsackSolver = pywrapknapsack_solver.KnapsackSolver(pywrapknapsack_solver.KnapsackSolver.KNAPSACK_DYNAMIC_PROGRAMMING_SOLVER, 'KnapsackExample')
                knapsackSolver.Init(profitsSolver,weightsSolver,capacitiesSolver)
                # solve the subproblem
                computed_value = knapsackSolver.Solve()

                # gather the results from the ortools Knapsack solver
                packed_items = [myItems[i] for i in range(len(profitsSolver)) if knapsackSolver.BestSolutionContains(i)]

            ####################################################################################################
            # TODO: now that a column has been calculated, 
            # 1) calculate its reduced cost or Farkas coefficient (to be stored in 'score'); 
            # 2) check whether it can be added (i.e., replace the "True" in the "if" below by an appropriate condition) 
            # 3) if the column can be added use the addColumn()
            # method to add it to the master problem (this point is implemented already.)
            ####################################################################################################
            
            score = 0

            if redcostpricing == True: # reduced cost pricing
                score += sum([self.model.getDualsolLinear(self.assignmentConss[location]) for location in packed_items])
                score += sum([self.distances[location, median] for location in packed_items])
                score -= self.model.getDualsolLinear(self.pmedianCons)
                score -= self.model.getDualsolLinear(self.convexityConss[median])
            else: # farkas 
                score += sum([self.model.getDualfarkasLinear(self.assignmentConss[location]) for location in packed_items])
                score -= self.model.getDualfarkasLinear(self.pmedianCons)
                score -= self.model.getDualfarkasLinear(self.convexityConss[median])
                
            if score < 0 - EPS:
                self.addColumn(median, packed_items)
            
            #print("{0} of {1} have been priced.".format(median + 1, self.nlocations))
            
            ####################################################################################################
            # TODO: (AT THE END OF THE EXERCISE, FOR THE ANALYSIS PART OF THE REPORT)
            # -> We have solved the subproblem using an efficient Knapsack solver from ortools. 
            #    Implement a different approach to solve the subproblems. What happens if you solve the 
            #    subproblems for example as a MIP? Is the performance better, worse, or maybe it does not change?
            ####################################################################################################
            
            
                
        return {'result':SCIP_RESULT.SUCCESS}
    
    #
    # Callback methods of variable pricer
    #  
    
    """Reduced cost pricing method of variable pricer for feasible LPs"""
    def pricerredcost(self):
        self.performPricing(redcostpricing = True)                
        return {'result':SCIP_RESULT.SUCCESS}
    
    """Farkas pricing method of variable pricer for infeasible LPs"""
    def pricerfarkas(self):        
        self.performPricing(redcostpricing = False)        
        return {'result':SCIP_RESULT.SUCCESS}
    
    """Solving process initialization method of variable pricer (called when branch and bound process is about to begin)"""
    def pricerinit(self):
        for i, c in enumerate(self.assignmentConss):
            self.assignmentConss[i] = self.model.getTransformedCons(c)
        for i, c in enumerate(self.convexityConss):
            self.convexityConss[i] = self.model.getTransformedCons(c)
        
        self.pmedianCons = self.model.getTransformedCons(self.pmedianCons)
     
    #
    # Variable pricer specific interface methods
    #  
    
    """forbid assignments for a certain location"""
    def forbidAssignments(self, location, forbidden):
        assert location >= 0 and location < self.nlocations
        for median in range(self.nlocations):
            if (forbidden[median]):
                assert forbidden[median] >= 0 and forbidden[median] < self.nlocations
                self.forbiddenassignments[median,location] = True
    
    """forbid assignments of a certain location to a certain median"""
    def forbidAssignment(self,median,location):
        assert median >= 0 and median < self.nlocations
        assert location >= 0 and location < self.nlocations
        self.forbiddenassignments[median,location] = True
        
    """allow previously forbidden assignments for a certain location"""
    def allowAssignments(self, location, forbidden):
        assert location >= 0 and location < self.nlocations
        for median in range(self.nlocations):
            if (forbidden[median]):
                assert forbidden[median] >= 0 and forbidden[median] < self.nlocations
                self.forbiddenassignments[median,location] = False
    
    """allow assignments for a certain location"""
    def allowAssignment(self,median,location):
        assert median >= 0 and median < self.nlocations
        assert location >= 0 and location < self.nlocations
        self.forbiddenassignments[median,location] = False
        
    """check whether a certain assignment is currently forbidden"""
    def isAssignmentForbidden(self,median,location):
        assert median >= 0 and median < self.nlocations
        assert location >= 0 and location < self.nlocations
        
        return self.forbiddenassignments[median,location]
