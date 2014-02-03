''' 
Copyright (C) 2011-2014 German Aerospace Center DLR
(Deutsches Zentrum fuer Luft- und Raumfahrt e.V.), 
Institute of System Dynamics and Control
All rights reserved.

This file is part of PySimulator.

PySimulator is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

PySimulator is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with PySimulator. If not, see www.gnu.org/licenses.
'''


import numpy as np
from sundials import *

from assimulo.problem import Explicit_Problem, Implicit_Problem
from assimulo.solvers import CVode, IDA, RungeKutta34


class AssimuloRK34():  
    '''Function for using the RK34 solver of Assimulo. 
    Beware: State events not supported
    Usage: 
    1. Set all parameters in the init section
    2. Overwrite dummy methods below
    3. Call the simulate function, results can be saved in the handle_result function (called at output points and events)
    '''
    def __init__(self):
                    
        #Have to be set from outside:
        self.atol = 1e-6                #Default 1e-6. The absulute tolerance
        self.rtol = 1e-6                #Default 1e-6. The relative tolerance
        self.verbosity = 50             #QUIET = 50 WHISPER = 40 NORMAL = 30 LOUD = 20 SCREAM = 10
        self.inith = 0.01              #Default 0.01. The initial step-size to be used in the integration.
        self.t0 = 0          
        self.y0 = None

    #Define dummy functions with warning message:
    def handle_result(self, t, x):
        print 'AssimuloRK34: handle_result has to be overwritten from the outside!'          
           
    def time_events(self, t, x, sw):
        print 'AssimuloRK34: time_events has to be overwritten from the outside!'              
         
    def handle_event(self, solver, event_info):
        print 'AssimuloRK34: handle_event has to be overwritten from the outside!'      
    
    def rhs(self, t, x, xd=None):   ##rhs: explicit, res = implicit, 
        print 'AssimuloRK34: rhs has to be overwritten from the outside!'      

    def finalize(self, solver):
        print 'AssimuloRK34: finalize has to be overwritten from the outside!'  
    
    
    def simulate(self, Tend, nIntervals, gridWidth):   
        
        problem = Explicit_Problem(self.rhs, self.y0)
        problem.name = 'RK34'
        problem.handle_result = self.handle_result
        problem.handle_event = self.handle_event
        problem.time_events = self.time_events   
        problem.finalize = self.finalize 
        
        if hasattr(self, 'state_events'):
            print 'Warning: state_event function in RK34 is not supported and will be ignored!'
        
        simulation = RungeKutta34(problem)
            
        #Sets additional parameters
        simulation.atol=self.atol
        simulation.rtol=self.rtol
        simulation.verbosity = self.verbosity
        simulation.continuous_output = False #default 0, if one step approach should be used
        simulation.inith = self.inith
               
        #Calculate nOutputIntervals:        
        if gridWidth <> None:
            nOutputIntervals = int((Tend - self.t0)/gridWidth)
        else:
            nOutputIntervals = nIntervals
        #Check for feasible input parameters
        if nOutputIntervals == 0:
            print 'Error: gridWidth too high or nIntervals set to 0! Continue with nIntervals=1'
            nOutputIntervals = 1
        #Perform simulation
        simulation.simulate(Tend, nOutputIntervals) #to get the values: t_new, y_new = simulation.simulate

        
class AssimuloCVode():  
    '''Function for using the CVode solver of Assimulo. 
    Usage: 
    1. Set all parameters in the init section
    2. Overwrite dummy methods below
    3. Call the simulate function, results can be saved in the handle_result function (called at output points and events)
    '''
    def __init__(self):
                    
        #Have to be set from outside:
        self.iter = 'FixedPoint'    #Default FixedPoint: The iteration method used by the solver('Newton' or 'FixedPoint')
        self.discr = 'Adams'        #Default 'Adams'. The discretization method
        self.atol = 1e-6            #Default 1e-6. The absulute tolerance
        self.rtol = 1e-6            #Default 1e-6. The relative tolerance
        self.verbosity = 50         #QUIET = 50 WHISPER = 40 NORMAL = 30 LOUD = 20 SCREAM = 10
     
        self.t0 = 0          
        self.y0 = None

    #Define dummy functions with warning message:
    def handle_result(self, t, x):
        print 'AssimuloCVode: handle_result has to be overwritten from the outside!'          
           
    def time_events(self, t, x, sw):
        print 'AssimuloCVode: time_events has to be overwritten from the outside!'  

    def state_events(self, t, x, sw):
        print 'AssimuloCVode: time_events has to be overwritten from the outside!'              
         
    def handle_event(self, solver, event_info):
        print 'AssimuloCVode: handle_event has to be overwritten from the outside!'      
    
    def rhs(self, t, x, xd=None):   ##rhs: explicit, res = implicit, 
        print 'AssimuloCVode: rhs has to be overwritten from the outside!'      

    def finalize(self, solver):
        print 'AssimuloCVode: finalize has to be overwritten from the outside!'  
    
    
    def simulate(self, Tend, nIntervals, gridWidth):   
        
        problem = Explicit_Problem(self.rhs, self.y0)
        problem.name = 'CVode'
        #solver.rhs = self.right_hand_side
        problem.handle_result = self.handle_result
        problem.state_events = self.state_events
        problem.handle_event = self.handle_event
        problem.time_events = self.time_events   
        problem.finalize = self.finalize  

        simulation = CVode(problem)
        
        #Change multistep method: 'adams' or 'VDF'
        if self.discr == 'Adams':
            simulation.discr = 'Adams'
            simulation.maxord = 12
        else:
            simulation.discr = 'BDF'    
            simulation.maxord = 5
        #Change iteration algorithm: functional(FixedPoint) or newton
        if self.iter == 'FixedPoint':
            simulation.iter = 'FixedPoint'  
        else:
            simulation.iter = 'Newton'
            
        #Sets additional parameters
        simulation.atol=self.atol
        simulation.rtol=self.rtol
        simulation.verbosity = self.verbosity
        simulation.continuous_output = False #default 0, if one step approach should be used
   
        #'''Initialize problem '''        
        #self.t_cur = self.t0
        #self.y_cur = self.y0
               
        #Calculate nOutputIntervals:        
        if gridWidth <> None:
            nOutputIntervals = int((Tend - self.t0)/gridWidth)
        else:
            nOutputIntervals = nIntervals
        #Check for feasible input parameters
        if nOutputIntervals == 0:
            print 'Error: gridWidth too high or nIntervals set to 0! Continue with nIntervals=1'
            nOutputIntervals = 1
        #Perform simulation
        simulation.simulate(Tend, nOutputIntervals) #to get the values: t_new, y_new = simulation.simulate


class AssimuloIda():  
    '''Function for using the Ida solver of Assimulo. 
    Usage: 
    1. Set all parameters in the init section
    2. Overwrite dummy methods below
    3. Call the simulate function, results can be saved in the handle_result function (called at output points and events)
    '''
    def __init__(self):
                    
        #Have to be set from outside:
        self.atol = 1e-6            #Default 1e-6. The absulute tolerance
        self.rtol = 1e-6            #Default 1e-6. The relative tolerance
        self.verbosity = 50         #QUIET = 50 WHISPER = 40 NORMAL = 30 LOUD = 20 SCREAM = 10
        self.tout1 = 0.001          #Default 0.001. The value used in the internal Sundials function for determine init. cond.
        #self.suppress_alg = False   #Default False. Indicates that the error-tests are suppressed on algebraic variables
        self.lsoff = False          #Default False. Value to turn OFF Sundials LineSearch when calculating initial conditions.
        
        self.t0 = 0          
        self.y0 = None
        self.yd0 = None

    #Define dummy functions with warning message:
    def handle_result(self, t, x, xd):
        print 'AssimuloIda: handle_result has to be overwritten from the outside!'          
           
    def time_events(self, t, x, xd, sw):
        print 'AssimuloIda: time_events has to be overwritten from the outside!'  

    def state_events(self, t, x, xd, sw):
        print 'AssimuloIda: time_events has to be overwritten from the outside!'              
         
    def handle_event(self, solver, event_info):
        print 'AssimuloIda: handle_event has to be overwritten from the outside!'      
    
    def rhs(self, t, x, xd):   ##rhs: explicit, res = implicit, 
        print 'AssimuloIda: rhs has to be overwritten from the outside!'      

    def finalize(self, solver):
        print 'AssimuloIda: finalize has to be overwritten from the outside!'  
    
    
    def simulate(self, Tend, nIntervals, gridWidth):   
        
        problem = Implicit_Problem(self.rhs, self.y0, self.yd0)
        problem.name = 'IDA'
        #solver.rhs = self.right_hand_side
        problem.handle_result = self.handle_result
        problem.state_events = self.state_events
        problem.handle_event = self.handle_event
        problem.time_events = self.time_events   
        problem.finalize = self.finalize  
        #Create IDA object and set additional parameters
        simulation = IDA(problem)
        simulation.atol=self.atol
        simulation.rtol=self.rtol
        simulation.verbosity = self.verbosity
        simulation.continuous_output = False #default 0, if one step approach should be used
        simulation.tout1 = self.tout1
        simulation.lsoff = self.lsoff
   
        #Calculate nOutputIntervals:        
        if gridWidth <> None:
            nOutputIntervals = int((Tend - self.t0)/gridWidth)
        else:
            nOutputIntervals = nIntervals
        #Check for feasible input parameters
        if nOutputIntervals == 0:
            print 'Error: gridWidth too high or nIntervals set to 0! Continue with nIntervals=1'
            nOutputIntervals = 1
        #Perform simulation
        simulation.simulate(Tend, nOutputIntervals) #to get the values: t_new, y_new,  yd_new = simulation.simulate


class AssimuloRK():  
    '''Not working yet'''
    def __init__(self):
                       
        #Have to be set from outside:
        self.iter = 'FixedPoint'
        self.discr = 'Adams'
        self.atol = 1e-6 
        self.rtol = 1e-6
        self.verbosity = 50             #QUIET = 50 WHISPER = 40 NORMAL = 30 LOUD = 20 SCREAM = 10

        self.rhs = None                 #rhs: explicit, res = implicit, 
        self.handle_result = None
        self.state_events = None
        self.handle_event = None
        self.time_events = None
        self.finalize = None
        self.completed_step = None      # NOT supported
        self.t0 = 0           
        self.y0 = None
        self.yd0 = None
        



    def f(self, t, y, sw):
        yarray = np.array(y)    
        return self.rhs(t,yarray)

    def rootf(self, t, y, sw):
        yarray = np.array(y)       
        rootfunctions = self.state_events(t, yarray)
        return rootfunctions

    
    def handle_result(self, t, x):
        ''' This function is called when new values
            (in time) for variables shall be saved.
        '''
        print 'handle_result_AssimuloIntegratros'          
        
    
    
    def simulate(self, Tend, nIntervals, gridWidth):   
       
        #define assimulo problem:(has to be done here because of the starting value in Explicit_Problem
        solver = Explicit_Problem(self.rhs, self.y0)
        ''' *******DELETE LATER '''''''''
#        problem.handle_event = handle_event
#        problem.state_events = state_events
#        problem.init_mode = init_mode
        
        solver.handle_result= self.handle_result
        
        
        solver.name = 'Simple Explicit Example'
        simulation = CVode(solver) #Create a RungeKutta34 solver
        #simulation.inith = 0.1 #Sets the initial step, default = 0.01
        
        #Change multistep method: 'adams' or 'VDF'
        if self.discr == 'Adams':
            simulation.discr = 'Adams'
            simulation.maxord = 12
        else:
            simulation.discr = 'BDF'    
            simulation.maxord = 5

        #Change iteration algorithm: functional(FixedPoint) or newton
        if self.iter == 'FixedPoint':
            simulation.iter = 'FixedPoint'  
        else:
            simulation.iter = 'Newton'
            
        #Sets additional parameters
        simulation.atol=self.atol
        simulation.rtol=self.rtol
        simulation.verbosity = 0
        simulation.continuous_output = False #default 0, if one step approach should be used
                
        # Create Solver and set settings 
        noRootFunctions = np.size(self.state_events(self.t0, np.array(self.y0) )) 
          
#        solver = CVodeSolver(RHS = self.f, ROOT = self.rootf, SW = [False]*noRootFunctions,
#                       abstol = self.atol, reltol = self.rtol)  
        #solver.settings.JAC = None   #Add user-dependent jacobian here        
        
        '''Initialize problem '''        
#        solver.init(self.t0, self.y0)
        self.handle_result(self.t0, self.y0) 
        nextTimeEvent = self.time_events(self.t0, self.y0)   
        self.t_cur = self.t0
        self.y_cur = self.y0
        state_event = False
#               
#               
        if gridWidth <> None:
            nOutputIntervals = int((Tend - self.t0)/gridWidth)
        else:
            nOutputIntervals = nIntervals
        #Define step length depending on if gridWidth or nIntervals has been chosen
        if nOutputIntervals > 0:
            #Last point on grid (does not have to be Tend:)
            if(gridWidth <> None):
                dOutput = gridWidth
            else:
                dOutput = (Tend - self.t0) / nIntervals
        else:
            dOutput = Tend
        
        outputStepCounter = long(1)        
        nextOutputPoint = min(self.t0 + dOutput, Tend)        
               
        while self.t_cur < Tend:
            
            #Time-Event detection and step time adjustment
            if nextTimeEvent is None or nextOutputPoint < nextTimeEvent:
                time_event = False
                self.t_cur = nextOutputPoint
            else:
                time_event = True             
                self.t_cur = nextTimeEvent                       
            

            
            try:
#                #Integrator step
#                self.y_cur = solver.step(self.t_cur) 
#                self.y_cur = np.array(self.y_cur)                
#                state_event = False         
                #Simulate
                
                
                
                
                #take a step to next output point:
                t_new, y_new = simulation.simulate(self.t_cur)#5, 10) #5, 10  self.t_cur self.t_cur  2. argument nsteps Simulate 5 seconds
                #t_new, y_new are both vectors of the time and states at t_cur and all intermediate
                #points before it! So take last values:
                self.t_cur = t_new[-1]
                self.y_cur = y_new[-1]
                state_event = False 
   
                a=2;
           
            except:
                import sys
                print "Unexpected error:", sys.exc_info()[0]   
#            except CVodeRootException, info:
#                self.t_cur = info.t
#                self.y_cur = info.y
#                self.y_cur = np.array(self.y_cur)
#                time_event = False             
#                state_event = True
#                
#            
            # Depending on events have been detected do different tasks  
            if time_event or state_event:
                event_info = [state_event, time_event]
                if not self.handle_event(self, event_info):
                    break          
                solver.init(self.t_cur, self.y_cur)                   
                
                nextTimeEvent = self.time_events(self.t_cur, self.y_cur) 
                #If no timeEvent happens:
                if nextTimeEvent<=self.t_cur:
                    nextTimeEvent = None
            
            if self.t_cur == nextOutputPoint:           
                #Write output if not happened before:
                if not time_event and not state_event:
                    self.handle_result(nextOutputPoint, self.y_cur)                
                outputStepCounter += 1
                nextOutputPoint = min(self.t0 + outputStepCounter * dOutput, Tend)  
                            
        self.finalize()    


class SundialsIDA():  
    
    def __init__(self):
        
        #Have to be set from outside:
        self.iter = 'FixedPoint'
        self.discr = 'Adams'
        self.atol = 1e-6 
        self.rtol = 1e-6
        self.verbosity = 0

        self.rhs = None
        self.handle_result = None
        self.state_events = None
        self.handle_event = None
        self.time_events = None
        self.finalize = None
        self.completed_step = None # NOT supported
        self.t0 = 0           
        self.y0 = None
        self.yd0 = None


    def f(self, t, y, yd, sw):
        yarray = np.array(y)
        ydarray = np.array(yd)   
        return self.rhs(t,yarray, ydarray)

    def rootf(self, t, y, yd, sw):
        yarray = np.array(y)                 
        rootfunctions = self.state_events(t, yarray)
        return rootfunctions
    
        
    def simulate(self, Tend, nIntervals, gridWidth):   

        ''' Create Solver and set settings '''
        noRootFunctions = np.size(self.state_events(self.t0, np.array(self.y0) ))          
        solver = IDASolver(RES = self.f, ROOT = self.rootf, SW = [False]*noRootFunctions,       
                       abstol = self.atol, reltol = self.rtol)
   
        solver.settings.maxord = 5          #default 5, Maximum order
        solver.settings.mxsteps = 5000      #default 500, Maximum steps allowed to reach next output time
        solver.settings.hmax = 1e37         #default inf, Maximum step size allowed         
        solver.settings.suppressalg = False #default False, indicates if algebraic var. should be suppressed in error testing
        solver.settings.lsoff = False       #default False, flag to turn off(True) or keep(False) linesearch algorithm
        
        solver.settings.JAC = None          #Add user-dependent jacobian here

        
        
        '''Initialize problem '''
        solver.init(self.t0, self.y0, self.yd0)
        self.handle_result(self.t0, self.y0) 
        nextTimeEvent = self.time_events(self.t0, self.y0)   
        self.t_cur = self.t0
        self.y_cur = self.y0
        self.yd_cur = self.yd0
        state_event = False
               
               
        if gridWidth <> None:
            nOutputIntervals = int((Tend - self.t0)/gridWidth)
        else:
            nOutputIntervals = nIntervals
        #Define step length depending on if gridWidth or nIntervals has been chosen
        if nOutputIntervals > 0:
            #Last point on grid does not have to be Tend:
            if(gridWidth <> None):
                dOutput = gridWidth
            else:
                dOutput = (Tend - self.t0) / nIntervals
        else:
            dOutput = Tend
        
        outputStepCounter = long(1)        
        nextOutputPoint = min(self.t0 + dOutput, Tend)        
               
        
        while self.t_cur < Tend:
            
            
            
            
            
            
            #Time-Event detection and step time adjustment
            if nextTimeEvent is None or nextOutputPoint < nextTimeEvent:
                time_event = False
                self.t_cur = nextOutputPoint
            else:
                time_event = True             
                self.t_cur = nextTimeEvent                  

   
            try:
                #Integrator step                
                self.y_cur, self.yd_cur = solver.step(self.t_cur)
                self.y_cur = np.array(self.y_cur)
                self.yd_cur = np.array(self.yd_cur)                                
                state_event = False                       
                
            except IDARootException, info:
                self.t_cur = info.t
                self.y_cur = info.y
                self.y_cur = np.array(self.y_cur)
                self.yd_cur = info.ydot
                self.yd_cur = np.array(self.yd_cur)   
                time_event = False             
                state_event = True
                
            
            # Depending on events have been detected do different tasks  
            if time_event or state_event:
                event_info = [state_event, time_event]
                                
                if not self.handle_event(self, event_info):                    
                    break          
                solver.init(self.t_cur, self.y_cur, self.yd_cur)
               
                nextTimeEvent = self.time_events(self.t_cur, self.y_cur) 
                #If no timeEvent happens:
                if nextTimeEvent<=self.t_cur:
                    nextTimeEvent = None
                
            if self.t_cur == nextOutputPoint:           
                #Write output if not happened before:
                if not time_event and not state_event:
                    self.handle_result(nextOutputPoint, self.y_cur)                
                outputStepCounter += 1
                nextOutputPoint = min(self.t0 + outputStepCounter * dOutput, Tend)  
                              
        self.finalize()    

        