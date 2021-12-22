#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  9 13:43:18 2020

@author: Elisabeth Rodríguez-Heck, Erik Mühmer
"""

from pyscipopt import Branchrule, SCIP_RESULT
import numpy

EPS = 1.e-10

class BranchruleSemiassign(Branchrule):
    def __init__(self, pricer, conshdlr):
        super().__init__()
        self.pricer = pricer
        self.conshdlr = conshdlr
        
    #
    # Local methods
    #
    
    """ for each pair of locations, compute the (possibly fractional) assignment value
        :param sol: solution to be checked, or NULL for LP solution
        :param assignments: dictionary of lists of location-median assignments
    """
    def computeAssignments(self, sol, assignments):
        nlocations = self.pricer.nlocations
        
        for i in range(nlocations):
            for j in range(nlocations):
                assignments[i][j] = 0.0
                
        ########################################################################################
        # TODO: calculate the assignment value for each location-median pair.
        # i.e., assignments[i][j] should describe the (possible fractional) assignment value of
        # median j to location i.
        # This is done by looping over the master variables.
        #
        # NOTE: For implementational reasons reasons, the location is the *first* index here
        # and the median the *second*!
        ########################################################################################
        master_vars = self.pricer.patternVars

        for master_var in self.pricer.patternVars:
            median = master_var.data.median
            locations = master_var.data.locations
            for location in locations:
                assignments[location][median] += self.model.getVal(master_var) # why is sol none?
        
        
        return {'result':SCIP_RESULT.SUCCESS}
    
    """for each location, sort the potential medians by nonincreasing value of fractional assignment
       :param sortedids: for each location, the array of medians sorted by fractional assignment
       :param assignments: dictionary of lists of location-median assignments
    """
    def sortMedians(self, sortedids, assignments):
        nlocations = self.pricer.nlocations
        
        for i in range(nlocations):
            # argsort cannot be applied in reverse order
            sortedidstemp = numpy.argsort(assignments[i])
            # we reverse the array afterwards
            sortedids[i] = sortedidstemp[::-1]
            # finally, sort also the assignments array inplace
            assignments[i].sort(reverse = True)
        
        return {'result':SCIP_RESULT.SUCCESS}
    
    """choose a location to branch on, or find out that the given assignments are feasible:
     we choose a location for which the number of fractionally assigned medians is maximal;
     in case of ties, we choose the location for which the total fractional assignment value
     of every second median is closest to half the total fractional assignment value of all medians.
     :param assignments: dictionary of lists of location-median assignments
     :returns: a location to branch on, or -1 in case of feasibility
    """
    def chooseLocation(self, assignments):
        nlocations = self.pricer.nlocations
        
        # variable for the location that will be returned by this method
        location = -1
        maxnfracmedians = 0
        
        
        for i in range(nlocations):
            nfracmedians = 0
            totfrac = 0.0
            halffrac = 0.0
            
            ##########################################################################################
            # TODO: for each location, calculate
            #   * to how many medians it is assigned fractionally (nfracmedians)
            #   * the sum of all fractional assignments (totfrac)
            #   * the sum of all fractional assignments to an even median (halffrac)
            ##########################################################################################
            for j in range(nlocations):
                fractional = self.model.frac(assignments[i][j])
                
                if fractional > EPS:
                    nfracmedians += 1
                    totfrac += assignments[i][j]
                    if (j % 2 == 0): # check if median is even
                        halffrac += assignments[i][j]
            
                
            minfracdiff = self.model.infinity()
            if (nfracmedians > maxnfracmedians) or (nfracmedians > 0 and nfracmedians == maxnfracmedians and self.model.isLE(abs(halffrac-0.5*totfrac),minfracdiff)):
                location = i
                maxnfracmedians = nfracmedians
                minfracdiff = abs(halffrac-0.5*totfrac)
                
        return location
    

 
 
    """ branch on a location: create two child nodes and forbid assigning them to the medians alternately in the two nodes
        :param sortedids: array of medians sorted by fractional assignment
        :param assignments: array of median assignments
        :param location: the location to branch on
    """
    def performBranching(self, sortedids, assignments, location):
        nlocations = self.pricer.nlocations
        # leftforbidden will contain the forbidden medians for the left child in tree
        leftforbidden = []
        # rightforbidden will contain the forbidden medians for the right child in tree
        rightforbidden = []
        
        for i in range(nlocations):
            leftforbidden.append(False)
            rightforbidden.append(False)
        
        # loop over all potential medians
        for i in range(nlocations):
            assert((not self.model.isFeasIntegral(assignments[sortedids[i]])) or self.model.isFeasZero(assignments[sortedids[i]]))
        
            # ignore already forbidden assignments, such that the child constraints only store newly forbidden assignments;
            # otherwise, this could lead to an error when deactivating a constraint
            if self.pricer.isAssignmentForbidden(sortedids[i], location):
                continue
            
            ##############################################################################################
            # TODO: fill the 'leftforbidden' and 'rightforbidden' arrays which describe which medians
            # cannot be assigned to the location in the left and right node, respectively;
            # note that the medians are forbidden alternately
            ##############################################################################################
            if i % 2:
                leftforbidden[sortedids[i]] = True
            else:
                rightforbidden[sortedids[i]] = True
            
            
        ##############################################################################################
        # TODO: create the two child nodes as well as a semiassignment constraint 
        # for each of them. The constraint must be specifically added to the node. 
        ##############################################################################################
            
        # create left child and add constraint
        leftChild = self.model.createChild(-self.model.getDualbound(), self.model.getLocalEstimate())
        cons = self.conshdlr.createConsSemiassign("forbid_{0}_{1}".format(location, leftforbidden), location, leftforbidden, leftChild)
        self.model.addConsNode(leftChild, cons)

        # create right child and add constraint
        rightChild = self.model.createChild(-self.model.getDualbound(),self.model.getLocalEstimate())
        cons = self.conshdlr.createConsSemiassign("forbid_{0}_{1}".format(location, rightforbidden), location, rightforbidden, rightChild)
        self.model.addConsNode(rightChild, cons)
        
        return {'result':SCIP_RESULT.SUCCESS}
    
    #
    # CALLBACK METHODS
    #
    
    """branching execution method for fractional LP solutions"""
    def branchexeclp(self, allowadcons):
        # dictionary of lists: for each location, list of sorted medians
        sortedids = {}
        # double-entry dictionary, first index is location, second index is median
        assignments = {}
        
        nlocations = self.pricer.nlocations
        
        for i in range(nlocations):
            sortedids[i] = []
            assignments[i] = []
            for j in range(nlocations):
                sortedids[i].append(j)
                assignments[i].append(None)
                
        self.computeAssignments(None, assignments)
        self.sortMedians(sortedids,assignments)
        
        location = self.chooseLocation(assignments)
        
        if location == -1: 
            return {"result": SCIP_RESULT.DIDNOTFIND}
        else: 
            self.performBranching(sortedids[location], assignments[location], location)
            return{"result": SCIP_RESULT.BRANCHED}
