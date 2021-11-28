#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  9 13:51:05 2020

@author: Elisabeth Rodríguez-Heck, Erik Mühmer
"""

from pyscipopt import Conshdlr, SCIP_RESULT
from pyscipopt.scip import Node

from dataclasses import dataclass
from typing import List

##### There are no TODOs in this file #####

#
# Data structures
#

# Constraint data for semiassign constraints
@dataclass
class ConsData:
    location: int            # location for which certain medians are forbidden
    forbidden: List[bool]    # for each median, the information whether the location may not be assigned to it
    node: Node = None        # node for which the constraint is valid
    propagate: bool = True   # should the constraint be propagated? TRUE if the subtree below the node is entered 
                             # and new variables have been created since the last propagation
    npropvars: int = 0       # number of variables present in the problem the last time the constraint was propagated
  

class ConshdlrSemiassign(Conshdlr):
    def __init__(self, pricer):
        super().__init__()
        self.pricer = pricer
    

    #
    # Callback methods
    #

    """Domain propagation method of constraint handler
    
    Fixes to zero those variables whose represented clusters assign a location to a forbidden median
    
    :param constraints: constraints to be propagated
    :param nfixedvars: 
    :param fixed: 
    :param infeasible:
    """
    def consprop(self, constraints, nusefulconss, nmarkedconss, proptiming):
        result = SCIP_RESULT.DIDNOTFIND
        for c in constraints:
            if result == SCIP_RESULT.CUTOFF:
                break
            else:
                assert c.isActive()
            
                if c.data.propagate:
                    i = c.data.npropvars - 1
                    for i in range(c.data.npropvars, self.pricer.nvars):
                        var = self.pricer.patternVars[i]
                        median = var.data.median
                        if not self.model.isFeasZero(var.getUbLocal()) and c.data.forbidden[median] and self.pricer.isLocationInCluster(var, c.data.location):
                            infeasible, fixed = self.model.fixVar(var, 0.0)

                            if infeasible:
                                result = SCIP_RESULT.CUTOFF
                                break
                            else:
                                result = SCIP_RESULT.REDUCEDDOM
                                assert(fixed)
                            
                    c.data.propagate = False
                    c.data.npropvars = i + 1
             
        return {'result': result}

    """constraint activation notification method of constraint handler"""
    def consactive(self, constraint):
        assert(constraint.data.npropvars <= self.pricer.nvars)
        
        # notify SCIP that the branching decision has to be propagated to the newly created master variables
        if constraint.data.npropvars < self.pricer.nvars:
            constraint.data.propagate = True
            self.model.repropagateNode(constraint.data.node)
        
        # notify the pricer about the forbidden assignments
        self.pricer.forbidAssignments(constraint.data.location, constraint.data.forbidden)
        
        return {'result':SCIP_RESULT.SUCCESS}
 
    """constraint deactivation notification method of constraint handler"""
    def consdeactive(self, constraint):
        self.pricer.allowAssignments(constraint.data.location, constraint.data.forbidden)
        constraint.data.propagate = False
        
        return {'result':SCIP_RESULT.SUCCESS}
    
    """Constraint display method of constraint handler"""
    def consprint(self, constraint):
        nlocations = self.pricer.nlocations
        
        print("Semiassignment Constraint:")
        print("   Location "+str(constraint.data.location))
        print("   Forbidden medians: ", end = '')
        for i in range(nlocations):
            if constraint.data.forbidden[i]:
                print(str(i)+" ", end = '')
        print("\n")
        
        return {'result':SCIP_RESULT.SUCCESS}
    
    def conscheck(self, constraints, solution, checkintegrality, checklprows, printreason, completely):
        return {"result": SCIP_RESULT.FEASIBLE}

    
    #
    # Constraint specific interface methods
    #

    """Creates a semi-assignment constraint
    
    :param name: name of constraint
    :param location: location for which certain medians are forbidden
    :param forbidden: for each median, the information of whether the location in the previous parameter
                may NOT be assigned to the median
    :param node: node for which the constraint is valid
    :return: returns the newly created constraint
    """
    def createConsSemiassign(self, name, location, forbidden, node):
        cons = self.model.createCons(self, name, initial = False, separate = False, enforce = True, check = True, propagate = True, local = True, modifiable = False, dynamic = False, removable = False, stickingatnode = True)
        cons.data = ConsData(location, forbidden, node)
        return cons