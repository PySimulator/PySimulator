#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (C) 2011-2015 German Aerospace Center DLR
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


'''
***************************
This Simulator plugin can load Functional Mockup Units (FMUs) and simulate them
mainly by a solver of the Sundials solver suite. The result file is saved
in the MTSF format in HDF5.
***************************

For documentation of general Simulator plugins, see also SimulatorBase.py
'''


import getpass
from operator import itemgetter
import os
import time
import types

import numpy

import FMIDescription2 as FMIDescription
import FMUInterface2 as FMUInterface
from ...Algorithms.Integrator.Sundials.AssimuloIntegrators import AssimuloCVode, AssimuloIda
from ...SimulationResult import IntegrationResults
from ...SimulationResult.Mtsf import Mtsf
from ...SimulationResult.Mtsf import MtsfFmi2
from ...SimulationResult.Mtsf import pyMtsf
from ...Simulator.FMUSimulator.FMUInterface2 import fmiTrue, fmiFalse
from ...Simulator import SimulatorBase



class Model(SimulatorBase.Model):
    ''' Class to describe a whole "model", including all FMU information
        and some more information that is needed.
    '''
    def __init__(self, modelName=None, modelFileName=None, config=None):
        ''' Opens a given model and sets it up with its default values
            @param modelFileName: fully qualified file name and path of model
        '''

        def updateSettingsByFMI(description):
            '''
                Function to update the settings with the experiment settings
                in the model's FMI description
            '''
            if description is not None:
                if description.defaultStartTime is not None:
                    self.integrationSettings.startTime = float(description.defaultStartTime)
                if description.defaultStopTime is not None:
                    self.integrationSettings.stopTime = float(description.defaultStopTime)
                if description.defaultTolerance is not None:
                    self.integrationSettings.errorToleranceRel = float(description.defaultTolerance)
                if description.defaultStepSize is not None:
                    self.integrationSettings.fixedStepSize = float(description.defaultStepSize)

        
        loggingOn = False
        if modelFileName is None:
            self.interface = None
            self.description = FMIDescription.FMIDescription(None)
        else:
            if not config['Plugins']['FMU'].has_key('importType'):
                config['Plugins']['FMU']['importType'] = 'me'
                config.write()
            preferredFmiType = config['Plugins']['FMU']['importType']
            self.interface = FMUInterface.FMUInterface(modelFileName[0], self, loggingOn, preferredFmiType)
            self.description = self.interface.description
        
        SimulatorBase.Model.__init__(self, modelName, modelFileName, config)
        self.modelType = 'FMU 2.0 ' + ('Model Exchange' if self.interface.activeFmiType == 'me' else 'CoSimulation') + ' in FMUSimulator'

        if self.interface.activeFmiType == 'me':
            # Dummy object to get properties
            self.integrationResults = Mtsf.Results('')
            self.integrationSettings.resultFileExtension = 'mtsf'
            # Default values
            updateSettingsByFMI(self.description)
            self._availableIntegrationAlgorithms = ["BDF (IDA, Dassl like)", "BDF (CVode)", "Adams (CVode)", "Explicit Euler (fixed step size)"]
            self._IntegrationAlgorithmHasFixedStepSize = [False, False, False, True]
            self._IntegrationAlgorithmCanProvideStepSizeResults = [True, True, True, True]
            self._IntegrationAlgorithmSupportsStateEvents = [True, True, True, True]
    
            self.integrationSettings.algorithmName = self._availableIntegrationAlgorithms[0]
            self.simulationStopRequest = False
            
        elif self.interface.activeFmiType == 'cs':
            # Dummy object to get properties
            self.integrationResults = Mtsf.Results('')
            self.integrationSettings.resultFileExtension = 'mtsf'
            # Default values
            updateSettingsByFMI(self.description)
            self._availableIntegrationAlgorithms = ["Integration method by FMU for CoSimulation"]
            self._IntegrationAlgorithmHasFixedStepSize = [False]
            self._IntegrationAlgorithmCanProvideStepSizeResults = [False]
            self._IntegrationAlgorithmSupportsStateEvents = [False]
    
            self.integrationSettings.algorithmName = self._availableIntegrationAlgorithms[0]
            self.simulationStopRequest = False

    def close(self):
        ''' Closing the model, release of resources
        '''
        SimulatorBase.Model.close(self)
        print "Deleting model instance ", self.description.modelName
        self.interface.free()

   
    def initialize(self, tStart, tStop, errorTolerance=1e-9):
        ''' Initializes the model at time = t with
            changed start values given by the dictionary
            self.changedStartValue.
            The function returns a status flag and the next time event.
        '''
        
        self.interface.fmiInstantiate()

        if self.interface.activeFmiType == 'me':    
            # Set start time
            self.interface.fmiSetTime(tStart)
            
        # Set start values
        self._setDefaultStartValues()
        for name in self.changedStartValue.keys():
            self.setValue(name, self.changedStartValue[name])
        # Initialize model
#        (eventInfo, status) = self.interface.fmiInitialize(fmiTrue, errorTolerance)
        s1 = self.interface.fmiSetupExperiment(fmiTrue, errorTolerance, tStart, fmiTrue, tStop)
        s2 = self.interface.fmiEnterInitializationMode()
        s3 = self.interface.fmiExitInitializationMode()
        
        status = max(s1,s2,s3)
        nextTimeEvent = None
        
        if self.interface.activeFmiType == 'me':        
            doLoop = True
            while doLoop:
                s4, eventInfo = self.interface.fmiNewDiscreteStates()
                if eventInfo.terminateSimulation or not eventInfo.newDiscreteStatesNeeded or s4>1:
                    doLoop = False
            
            s5 = self.interface.fmiEnterContinuousTimeMode()       
            if eventInfo.terminateSimulation:
                status = max(status, 2)
            status = max(status, s4,s5)        
            
            # Information about next time event
            if eventInfo.nextEventTimeDefined == fmiTrue:
                nextTimeEvent = eventInfo.nextEventTime            
            
        # status > 1 means error during initialization        
        return status, nextTimeEvent


    def simulate(self):
        ''' The main simulation function
        '''

        def prepareResultFile():
            # Prepare result file
            fmi = self.description
            (modelDescription, modelVariables, simpleTypes, units, enumerations) = MtsfFmi2.convertFromFmi('', fmi)
            # Phase 1 of result file generation
            settings = self.integrationSettings
            experimentSetup = pyMtsf.ExperimentSetup(startTime=settings.startTime, stopTime=settings.stopTime,
                                                     algorithm=settings.algorithmName, relativeTolerance=settings.errorToleranceRel,
                                                     author=getpass.getuser(), description="",
                                                     generationDateAndTime=time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()),
                                                     generationTool="PySimulator", machine=os.getenv('COMPUTERNAME'),
                                                     cpuTime="")
            modelVariables.allSeries[0].initialRows = 1  # Fixed
            modelVariables.allSeries[2].initialRows = 10  # Discrete
            if settings.gridPointsMode == 'NumberOf':
                nGridPoints = settings.gridPoints
            elif settings.gridPointsMode == 'Width':
                nGridPoints = 1 + int((settings.stopTime - settings.startTime) / settings.gridWidth)
            else:
                nGridPoints = 1
            modelVariables.allSeries[1].initialRows = max(nGridPoints, modelVariables.allSeries[2].initialRows)  # Continuous

            # Create result object
            mtsf = Mtsf.Results(settings.resultFileName,
                               modelDescription, modelVariables, experimentSetup, simpleTypes, units, enumerations)
            if not mtsf.isAvailable:
                print("Result file " + settings.resultFileName + " cannot be opened for write access.\n")
                self.integrationResults = IntegrationResults.Results()
                return False

            # Create fmi reference lists in categories
            for series in mtsf._mtsf.results.series.values():
                for category in series.category.values():
                    category.references = FMUInterface.createfmiReferenceVector(category.nColumn)
                    category.iReferences = -1
                    dataType = pyMtsf.CategoryReverseMapping[category.name]
                    if dataType == 'Real':
                        category.fmiGetValues = self.interface.fmiGetReal
                    elif dataType == 'Integer':
                        category.fmiGetValues = self.interface.fmiGetInteger
                    elif dataType == 'Boolean':
                        category.fmiGetValues = self.interface.fmiGetBoolean
                    elif dataType == 'String':
                        category.fmiGetValues = self.interface.fmiGetString
            for name, variable in modelVariables.variable.items():
                if variable.aliasName is None:
                    variable.category.iReferences += 1
                    if name in fmi.scalarVariables:
                        #print variable.seriesIndex, variable.category.name, name, variable.category.iReferences, len(variable.category.references)
                        variable.category.references[variable.category.iReferences] = fmi.scalarVariables[name].valueReference
                    else:
                        # e.g. for time variables, that do not exist in fmi-world
                        series = variable.category.series
                        series.independentVariableCategory = variable.category
                        variable.category.independentVariableColumn = variable.columnIndex
                        variable.category.references[variable.category.iReferences] = 0

            for series in mtsf._mtsf.results.series.values():
                if hasattr(series, 'independentVariableCategory'):
                    category = series.independentVariableCategory
                    column = category.independentVariableColumn
                    if column > 0:
                        dummy = 0
                    else:
                        dummy = 1
                    if category.references.shape[0] > dummy:
                        category.references[column] = category.references[dummy]
                    else:
                        category.references = numpy.array([])
                else:
                    series.independentVariableCategory = None
            self.integrationResults = mtsf
            return True

        def writeResults(seriesName, time):
            ''' Writes variable values at time 'time' to result file.
                Only variables of the given series are written.
            '''
            if hasattr(self, 'integrationResultFileSemaphore'):
                self.integrationResultFileSemaphore.acquire()
            series = self.integrationResults._mtsf.results.series[seriesName]
            for category in series.category.values():
                if category.references.shape[0] > 0:
                    status, values = category.fmiGetValues(category.references)
                else:
                    values = numpy.ndarray((1,))
                if category == series.independentVariableCategory:
                    # There is a time
                    index = category.independentVariableColumn
                    values[index] = time
                category.writeData(values)
            if hasattr(self, 'integrationResultFileSemaphore'):
                self.integrationResultFileSemaphore.release()

        def right_hand_side(t, x, xd=None):
            ''' Returns the right hand side (or the delta to xd for implicit solvers)
            '''
            dx = self.getDerivatives(t, x)  # dx is returned as matrix with one row [[ 0.1  0.4]]
            if implicitSolver:
                return dx[0] - xd  # numpy.array(dx - xd)#maybe [dx] #dx - xd
            else:
                return dx[0]  # return dx as vector

        def state_events(t, x, sw):
            ''' Returns event indicator functions at time=t, states=x
            '''
            test = self.getEventIndicators(t, x)
            return numpy.array(test)

        def state_eventsImplicit(t, x, xd, sw):
            ''' Returns event indicator functions at time=t, states=x
            '''
            return state_events(t, x, sw)

        def time_events(t, x, sw):
            ''' Returns the next time event
            '''
            if simulator.nextTimeEvent == None:
                return 1e10
            else:
                return simulator.nextTimeEvent

        def time_eventsImplicit(t, x, xd, sw):
            ''' Returns event indicator functions at time=t, states=x
            '''
            return time_events(t, x, sw)

        def handle_result(solver, t, x=None, xd=None):
            ''' This function is called when new values
                (in time) for variables shall be saved.
            '''

            # Check, if simulation shall be interrupted
            if self.simulationStopRequest:
                finalize(solver)
                raise(SimulatorBase.Stopping)

            # Update integration statistics
            self.integrationStatistics.reachedTime = t

            # Write results
            if self.interface.activeFmiType == 'me':
                self.interface.fmiSetTime(t)
                if not self.description.numberOfContinuousStates == 0:
                    self.interface.fmiSetContinuousStates(x)

            writeResults('Continuous', t)
            self.integrationStatistics.nGridPoints += 1

        def finalize(solver=None):
            ''' Function that is called at the end of the simulation
            '''           
            
            if solver is not None and 'Discrete' in self.integrationResults._mtsf.results.series:
                # Write discrete Variables
                writeResults('Discrete', solver.t)
        
            # Terminate simulation in model
            self.interface.fmiTerminate()
            self.interface.freeModelInstance()

        def handle_event(solver, event_info=None):
            ''' There is an event. Do the re-initialization and prepare
                the simulation to be proceeded.
                event_info[1] = True: Time event

                Returns True,  if simulation shall be continued
                        False, if simulation shall be terminated
            '''

            if event_info[1]:
                self.integrationStatistics.nTimeEvents += 1
                # print "Handle time event at   ", solver.t_cur
            else:
                self.integrationStatistics.nStateEvents += 1

                # print "Handle state event at  ", solver.t_cur

            # To ensure that the current values are set in the model
            self.interface.fmiSetTime(solver.t)
            if not self.description.numberOfContinuousStates == 0:
                self.interface.fmiSetContinuousStates(solver.y)
          
            # handle_result(solver, solver.t, solver.y) here if your solver does not call it by itself(Assimulo does)

            # Do the event updates
            self.interface.fmiEnterEventMode()
            doLoop = True
            while doLoop:
                status, eventInfo = self.interface.fmiNewDiscreteStates()
                if eventInfo.terminateSimulation or not eventInfo.newDiscreteStatesNeeded or status>1:
                    doLoop = False
            
            s1 = self.interface.fmiEnterContinuousTimeMode()
            s2 = 0             
            
            if eventInfo.nextEventTimeDefined == fmiTrue:
                simulator.nextTimeEvent = eventInfo.nextEventTime
            else:
                simulator.nextTimeEvent = 1e10
            if eventInfo.valuesOfContinuousStatesChanged == fmiTrue:
                # The model signals a value change of states, retrieve them
                if not self.description.numberOfContinuousStates == 0:
                    s2, solver.y = self.interface.fmiGetContinuousStates()
            
            if max(status, s1,s2) > 1:
                print("error in event initialization ... ")
                # Raise exception to abort simulation...
                finalize(solver)
                raise(SimulatorBase.Stopping)
            
            if eventInfo.terminateSimulation == fmiTrue:
                handle_result(solver, solver.t, solver.y)
                if 'Discrete' in self.integrationResults._mtsf.results.series:
                    # Write discrete Variables
                    writeResults('Discrete', solver.t)
                print("terminated by model ... ")
                # Raise exception to abort simulation...
                finalize(solver)
                raise(SimulatorBase.Stopping)
            
            # handle_result(solver, solver.t, solver.y) here if your solver does not call it by itself(Assimulo does)

            if 'Discrete' in self.integrationResults._mtsf.results.series:
                # Write discrete Variables
                writeResults('Discrete', solver.t)

            return True




        def completed_step(solver):
            ''' Function that is called after each successful integrator step
                Returns True,  if there was a step event
                        False, if there was no step event
            '''
            return False  # to be done for FMI2.0
            '''
            if self.interface.fmiCompletedIntegratorStep() == fmiTrue:
                solver.handle_event(solver)
                return True
            else:
                return False
            '''
        
        def doStep(t, dt):
            status = self.interface.fmiDoStep(t, dt, fmiTrue)            
            if status > 2:
                print("error in doStep at time = {:.2e}".format(t))
                # Raise exception to abort simulation...
                finalize(None)
                raise(SimulatorBase.Stopping)
            return status
            


        ''' *********************************
            Here the simulate function starts:
            **********************************
        '''

        # Initialize result file
        if not prepareResultFile():
            return

        # Set Simulation options
        Tstart = self.integrationSettings.startTime
        Tend = self.integrationSettings.stopTime
        IntegrationMethod = self.integrationSettings.algorithmName
        if "BDF (CVode)" in IntegrationMethod:
            IntegrationMethod = 'BDF'
        elif 'Adams' in IntegrationMethod:
            IntegrationMethod = 'Adams'
        if self.integrationSettings.gridPointsMode == 'NumberOf':
            nIntervals = self.integrationSettings.gridPoints - 1
            gridWidth = None
        elif self.integrationSettings.gridPointsMode == 'Width':
            nIntervals = None
            gridWidth = self.integrationSettings.gridWidth
        else:
            nIntervals = 0
            gridWidth = None
        ErrorTolerance = self.integrationSettings.errorToleranceRel

        # Initialize integration statistics
        self.integrationStatistics.nTimeEvents = 0
        self.integrationStatistics.nStateEvents = 0
        self.integrationStatistics.nGridPoints = 0
        self.integrationStatistics.reachedTime = Tstart

        # Run the integration
        ######################
        # Initialize model       
        (status, nextTimeEvent) = self.initialize(Tstart, Tend, ErrorTolerance if self.interface.activeFmiType == 'cs' else min(1e-15, ErrorTolerance*1e-5))
        if status > 1:
            print("Model initialization failed. fmiStatus = " + str(status))
            return

        if 'Fixed' in self.integrationResults._mtsf.results.series:
            # Write parameter values
            writeResults('Fixed', Tstart)
            
                    
        if self.interface.activeFmiType == 'me':
            if 'Discrete' in self.integrationResults._mtsf.results.series:
                # Write discrete variables
                writeResults('Discrete', Tstart)            
            
            # Retrieve initial state x
            if self.description.numberOfContinuousStates == 0:
                x0 = numpy.zeros([1, ])
            else:
                status, x0 = self.interface.fmiGetContinuousStates()
            # x_nominal = numpy.array(self.interface.fmiGetNominalContinuousStates())
    
            # Prepare the solver
            implicitSolver = False
            # Set simulator and special parameters. General parameters are added after if-clause
            if "IDA" in IntegrationMethod:
                implicitSolver = True
                # Define the solver object
                simulator = AssimuloIda()
    
                # Retrieve initial derivatives dx
                if self.description.numberOfContinuousStates == 0:
                    dx0 = numpy.zeros([1, ])
                else:
                    status, dx0 = self.interface.fmiGetDerivatives()
    
                simulator.yd0 = dx0
            elif "Adams" in IntegrationMethod or "BDF" in IntegrationMethod:  # Use CVode
                simulator = AssimuloCVode()
                simulator.iter = 'Newton'  # Default 'FixedPoint'
                simulator.discr = IntegrationMethod  # Default 'Adams'
            else:
                simulator = ExplicitEulerSolver()
                simulator.completed_step = completed_step
    
            # Set starting parameters common to all integrators here:
            simulator.t0 = Tstart
            simulator.y0 = x0
            simulator.atol = ErrorTolerance  # Default 1e-6
            simulator.rtol = ErrorTolerance  # Default 1e-6
    
            # Set function pointers called by simulator
            simulator.rhs = right_hand_side
            simulator.handle_result = handle_result
            simulator.handle_event = handle_event
            simulator.finalize = finalize  # should not be called by the solver (needs one argument then) simulator.finalize = finalize
            # simulator.completed_step = completed_step  # is not supported by python-sundials
    
            # These methods can not have xd=None due to its signature... Apply its dummy-Versions here
            if implicitSolver == True:
                simulator.state_events = state_eventsImplicit
                simulator.time_events = time_eventsImplicit
            else:
                simulator.state_events = state_events
                simulator.time_events = time_events
    
    
            # Store information about next time event in solver
            simulator.nextTimeEvent = nextTimeEvent
    
    
            if hasattr(self, 'numberedModelName'):
                print("Start integration of " + self.numberedModelName + " ... ")
            else:
                print("Start integration of " + self.description.modelName + " ... ")
    
            # Simulate until end of integration interval
            if "Euler" in IntegrationMethod:
                if nIntervals == None:
                    nIntervals = (Tend - Tstart) / gridWidth - 1
                simulator.simulate(Tstart, self.integrationSettings.fixedStepSize, Tend, x0, nIntervals, gridWidth)
            else:
                simulator.simulate(Tend, nIntervals, gridWidth)
                
        
        elif self.interface.activeFmiType == 'cs':
            # Do Co-Simulation for one single (self-containing) FMU
            
            if gridWidth is None:
                gridWidth = (Tend-Tstart) / nIntervals
            
            t = Tstart
            lastStep = False            
            doLoop = Tend > Tstart
            if gridWidth <= Tend-t:
                dt = gridWidth
            else:
                dt = Tend - t
                lastStep = True            
            k = 1
            
            writeResults('Continuous', t)
            if 'Discrete' in self.integrationResults._mtsf.results.series:
                # Write discrete Variables
                writeResults('Discrete', t)
                       
            while doLoop:               
                status = doStep(t, dt)
                if status == 2:  # Discard
                    status, info = self.interface.fmiGetBooleanStatus(3) # fmi2Terminated
                    if info == fmiTrue:
                        status, lastTime = self.interface.fmiGetRealStatus(2)       # fmi2LastSuccessfulTime
                        t = lastTime
                        doLoop = False
                    else:
                        print("Not supported status in doStep at time = {:.2e}".format(t))
                        # Raise exception to abort simulation...
                        finalize()
                        raise(SimulatorBase.Stopping)   
                elif status < 2:
                    t = t + dt
                else:
                    # should not occur
                    pass
                
                handle_result(None, t)
                if 'Discrete' in self.integrationResults._mtsf.results.series:
                    # Write discrete Variables
                    writeResults('Discrete', t)                
                
                if lastStep:
                    doLoop = False
                else:                
                    #Compute next communication point                
                    if gridWidth <= Tend-t:
                        k += 1
                        dt = (Tstart + k*gridWidth) - t
                    else:
                        dt = Tend - t
                        lastStep = True
            
            finalize()
            
            


        return

    def duplicate(self):
        # Must be improved, because closing a duplicated model also closes the dll of the original model
        return SimulatorBase.Model.duplicate(self)


    def getAvailableIntegrationAlgorithms(self):
        return self._availableIntegrationAlgorithms

    def getIntegrationAlgorithmHasFixedStepSize(self, algorithmName):
        return self._IntegrationAlgorithmHasFixedStepSize[self._availableIntegrationAlgorithms.index(algorithmName)]

    def getIntegrationAlgorithmCanProvideStepSizeResults(self, algorithmName):
        return self._IntegrationAlgorithmCanProvideStepSizeResults[self._availableIntegrationAlgorithms.index(algorithmName)]

    def getIntegrationAlgorithmSupportsStateEvents(self, algorithmName):
        return self._IntegrationAlgorithmSupportsStateEvents[self._availableIntegrationAlgorithms.index(algorithmName)]

    def _setDefaultStartValues(self):
        ''' Reads given start values from FMI model description and sets variables accordingly
        '''
        for index in self.description.scalarVariables:
            if self.description.scalarVariables[index].type.start != None:
                self.setValue(index, self.description.scalarVariables[index].type.start)

    def setValue(self, valueName, valueValue):
        ''' set the variable valueName to valueValue
            @param valueName: name of variable to be set
            @type valueName: string
            @param valueValue: new value
            @type valueValue: any type castable to the type of the variable valueName
        '''
        ScalarVariableReferenceVector = FMUInterface.createfmiReferenceVector(1)
        ScalarVariableReferenceVector[0] = self.description.scalarVariables[valueName].valueReference
        if self.description.scalarVariables[valueName].type.basicType == 'Real':
            ScalarVariableValueVector = FMUInterface.createfmiRealVector(1)
            ScalarVariableValueVector[0] = float(valueValue)
            self.interface.fmiSetReal(ScalarVariableReferenceVector, ScalarVariableValueVector)
        elif self.description.scalarVariables[valueName].type.basicType in ['Integer', 'Enumeration']:
            ScalarVariableValueVector = FMUInterface.createfmiIntegerVector(1)
            ScalarVariableValueVector[0] = int(valueValue)
            self.interface.fmiSetInteger(ScalarVariableReferenceVector, ScalarVariableValueVector)
        elif self.description.scalarVariables[valueName].type.basicType == 'Boolean':
            ScalarVariableValueVector = FMUInterface.createfmiBooleanVector(1)
            ScalarVariableValueVector[0] = fmiTrue if valueValue == "true" else fmiFalse
            self.interface.fmiSetBoolean(ScalarVariableReferenceVector, ScalarVariableValueVector)
        elif self.description.scalarVariables[valueName].type.basicType == 'String':
            ScalarVariableValueVector = FMUInterface.createfmiStringVector(1)
            ScalarVariableValueVector[0] = unicode(valueValue)
            self.interface.fmiSetString(ScalarVariableReferenceVector, ScalarVariableValueVector)

    def getDerivatives(self, t, x):
        ''' Returns the right hand side of the dynamic system for
            given time t and state vector x.
            #x is 1d numpy array
        '''
        self.interface.fmiSetTime(t)
        if self.description.numberOfContinuousStates == 0:
            dx = numpy.zeros([1, ])
        else:
            self.interface.fmiSetContinuousStates(x)
            status, dx = self.interface.fmiGetDerivatives()

        return numpy.array([dx])  # Note that the return must be numpy array

    def getEventIndicators(self, t, x):
        ''' Returns the event indicator functions for
            given time t and state vector x.
        '''
        self.interface.fmiSetTime(t)
        if not self.description.numberOfContinuousStates == 0:
            self.interface.fmiSetContinuousStates(x)
        status, z = self.interface.fmiGetEventIndicators() 
        return z

    def getValue(self, name):
        ''' Returns the values of the variables given in name;
            name is either a String or a list of Strings.
        '''
        if types.TypeType(name) == types.ListType:
            n = len(name)
            nameList = True
            names = name
        else:
            n = 1
            nameList = False
            names = [name]

        iReal = []
        iInteger = []
        iBoolean = []
        iString = []
        refReal = []
        refInteger = []
        refBoolean = []
        refString = []
        for i, x in enumerate(names):
            dataType = self.description.scalarVariables[x].type.basicType
            if dataType == 'Real':
                refReal.append(self.description.scalarVariables[x].valueReference)
                iReal.append(i)
            elif dataType == 'Integer':
                refInteger.append(self.description.scalarVariables[x].valueReference)
                iInteger.append(i)
            elif dataType == 'Boolean':
                refBoolean.append(self.description.scalarVariables[x].valueReference)
                iBoolean.append(i)
            elif dataType == 'String':
                refString.append(self.description.scalarVariables[x].valueReference)
                iString.append(i)

        retValue = range(n)
        k = len(refReal)
        if k > 0:
            ref = FMUInterface.createfmiReferenceVector(k)
            for i in xrange(k):
                ref[i] = refReal[i]
            status, values = self.interface.fmiGetReal(ref)
            for i in xrange(k):
                retValue[iReal[i]] = values[i]
        k = len(refInteger)
        if k > 0:
            ref = FMUInterface.createfmiReferenceVector(k)
            for i in xrange(k):
                ref[i] = refInteger[i]
            status, values = self.interface.fmiGetInteger(ref)
            for i in xrange(k):
                retValue[iInteger[i]] = values[i]
        k = len(refBoolean)
        if k > 0:
            ref = FMUInterface.createfmiReferenceVector(k)
            for i in xrange(k):
                ref[i] = refBoolean[i]
            status, values = self.interface.fmiGetBoolean(ref)
            for i in xrange(k):
                retValue[iBoolean[i]] = values[i]
        k = len(refString)
        if k > 0:
            ref = FMUInterface.createfmiReferenceVector(k)
            for i in xrange(k):
                ref[i] = refString[i]
            status, values = self.interface.fmiGetString(ref)
            for i in xrange(k):
                retValue[iString[i]] = values[i]

        if nameList:
            return retValue
        else:
            return retValue[0]

    def getStates(self):
        ''' Returns a vector with the values of the states.
        '''
        status, x = self.interface.fmiGetContinuousStates()
        
        return x

    def getStateNames(self):
        ''' Returns a list of Strings: the names of all states in the model.
        '''
        return  # to be done for FMI2.0        
        
        references = self.interface.fmiGetStateValueReferences()
        allVars = self.description.scalarVariables.items()
        referenceListSorted = [(index, var[1].valueReference) for index, var in enumerate(allVars)]
        referenceListSorted.sort(key=itemgetter(1))
        referenceList = [r[1] for r in referenceListSorted]

        names = []
        for ref in references:
            if ref == -1:
                # No reference available -> name is hidden
                names.append('')
            else:
                k = referenceList.count(ref)
                if k > 0:
                    index = -1
                    i = 0
                    while i < k:
                        i += 1
                        index = referenceList.index(ref, index + 1)
                        ok = False
                        if allVars[referenceListSorted[index][0]][1].alias is not None:
                            if allVars[referenceListSorted[index][0]][1].alias.lower() == 'noalias':
                                ok = True
                        else:
                            ok = True
                        if ok:
                            name = allVars[referenceListSorted[index][0]][0]
                            names.append(name)
                            break
                else:
                    # Reference not found. Should not occur.
                    names.append('')
        return names

    def getReachedSimulationTime(self):
        ''' Results are avialable up to the returned time
        '''
        return self.integrationStatistics.reachedTime


    def setVariableTree(self):
        ''' Sets the variable tree to be displayed in the variable browser.
            The data is set in self.variableTree that is an instance of the class SimulatorBase.VariableTree
        '''

        tipText = ''
        tipText += 'FMI Version:       ' + chr(9) + self.description.fmiVersion + '\n'
        tipText += 'Model name:        ' + chr(9) + self.description.modelName + '\n'       
        tipText += 'Guid:                       ' + chr(9) + self.description.guid + '\n'
        if self.description.description is not None:
            tipText += 'Description:           ' + chr(9) + self.description.description + '\n'
        if self.description.author is not None:
            tipText += 'Author:                   ' + chr(9) + self.description.author + '\n'
        if self.description.version is not None:
            tipText += 'Version:                ' + chr(9) + self.description.version + '\n'
        if self.description.copyright is not None:
            tipText += 'Copyright:                ' + chr(9) + self.description.copyright + '\n'
        if self.description.license is not None:
            tipText += 'License:                ' + chr(9) + self.description.license + '\n'
        if self.description.generationTool is not None:
            tipText += 'Generation tool:   ' + chr(9) + self.description.generationTool + '\n'
        if self.description.generationDateAndTime is not None:
            tipText += 'Gen. date and time:' + chr(9) + self.description.generationDateAndTime + '\n'
        if self.description.variableNamingConvention is not None:
            tipText += 'Naming convention: ' + chr(9) + self.description.variableNamingConvention + '\n'
        if self.description.numberOfEventIndicators is not None:
            tipText += 'Event indicators:  ' + chr(9) + self.description.numberOfEventIndicators + '\n'        
                
       

        if self.description.me is not None and self.interface.activeFmiType == 'me':
            tipText += '--------\n' 
            tipText += 'MODEL EXCHANGE\n'
            tipText += 'Model identifier:  ' + chr(9) + self.description.me.modelIdentifier + '\n'
            if self.description.me.needsExecutionTool is not None:
                tipText += 'needsExecutionTool:                    ' + chr(9) + self.description.me.needsExecutionTool + '\n'
            if self.description.me.completedIntegratorStepNotNeeded is not None:
                tipText += 'completedIntegratorStepNotNeeded: ' + chr(9) + self.description.me.completedIntegratorStepNotNeeded + '\n'
            if self.description.me.canBeInstantiatedOnlyOncePerProcess is not None:
                tipText += 'canBeInstantiatedOnlyOncePerProcess:  ' + chr(9) + self.description.me.canBeInstantiatedOnlyOncePerProcess + '\n'
            if self.description.me.canNotUseMemoryManagementFunctions is not None:
                tipText += 'canNotUseMemoryManagementFunctions:  ' + chr(9) + self.description.me.canNotUseMemoryManagementFunctions + '\n'
            if self.description.me.canGetAndSetFMUstate is not None:
                tipText += 'canGetAndSetFMUstate:                ' + chr(9) + self.description.me.canGetAndSetFMUstate + '\n'
            if self.description.me.canSerializeFMUstate is not None:
                tipText += 'canSerializeFMUstate:                 ' + chr(9) + self.description.me.canSerializeFMUstate + '\n'
            if self.description.me.providesDirectionalDerivative is not None:
                tipText += 'providesDirectionalDerivative:        ' + chr(9) + self.description.me.providesDirectionalDerivative + '\n'         
                       
          
        if self.description.cs is not None and self.interface.activeFmiType == 'cs':
            tipText += '--------\n'
            tipText += 'COSIMULATION\n'  
            tipText += 'Model identifier:  ' + chr(9) + self.description.cs.modelIdentifier + '\n'
            if self.description.cs.needsExecutionTool is not None:
                tipText += 'needsExecutionTool:                    ' + chr(9) + self.description.cs.needsExecutionTool + '\n'
            if self.description.cs.canHandleVariableCommunicationStepSize is not None:
                tipText += 'canHandleVariableCommunicationStepSize:  ' + chr(9) + self.description.cs.canHandleVariableCommunicationStepSize + '\n'
            if self.description.cs.canInterpolateInputs is not None:
                tipText += 'canInterpolateInputs:                    ' + chr(9) + self.description.cs.canInterpolateInputs + '\n'
            if self.description.cs.maxOutputDerivativeOrder is not None:
                tipText += 'maxOutputDerivativeOrder:                 ' + chr(9) + self.description.cs.maxOutputDerivativeOrder + '\n'
            if self.description.cs.canRunAsynchronuously is not None:
                tipText += 'canRunAsynchronuously:                   ' + chr(9) + self.description.cs.canRunAsynchronuously + '\n'           
            if self.description.cs.canBeInstantiatedOnlyOncePerProcess is not None:
                tipText += 'canBeInstantiatedOnlyOncePerProcess:  ' + chr(9) + self.description.cs.canBeInstantiatedOnlyOncePerProcess + '\n'
            if self.description.cs.canNotUseMemoryManagementFunctions is not None:
                tipText += 'canNotUseMemoryManagementFunctions:  ' + chr(9) + self.description.cs.canNotUseMemoryManagementFunctions + '\n'
            if self.description.cs.canGetAndSetFMUstate is not None:
                tipText += 'canGetAndSetFMUstate:                ' + chr(9) + self.description.cs.canGetAndSetFMUstate + '\n'
            if self.description.cs.canSerializeFMUstate is not None:
                tipText += 'canSerializeFMUstate:                 ' + chr(9) + self.description.cs.canSerializeFMUstate + '\n'
            if self.description.cs.providesDirectionalDerivative is not None:
                tipText += 'providesDirectionalDerivative:        ' + chr(9) + self.description.cs.providesDirectionalDerivative + '\n'         
            
        tipText += '--------\n'
        if self.description.defaultStartTime is not None:        
            tipText += 'Default start time:' + chr(9) + self.description.defaultStartTime + '\n'
        if self.description.defaultStopTime is not None:
            tipText += 'Default stop time: ' + chr(9) + self.description.defaultStopTime + '\n'
        if self.description.defaultTolerance is not None:
            tipText += 'Default tolerance: ' + chr(9) + self.description.defaultTolerance + '\n'
        if self.description.defaultStepSize is not None:
            tipText += 'Default step size: ' + chr(9) + self.description.defaultStepSize + '\n'
        

        # ----> Here the rootAttribute of self.variableTree is set
        self.variableTree.rootAttribute = tipText

        for vName, v in self.description.scalarVariables.iteritems():
            variableAttribute = ''
            if v.description is not None:
                variableAttribute += 'Description:' + chr(9) + v.description + '\n'
            variableAttribute += 'Reference:' + chr(9) + v.valueReference            
            if v.causality is not None:
                variableAttribute += '\nCausality:' + chr(9) + v.causality    
            if v.variability is not None:
                variableAttribute += '\nVariability:' + chr(9) + v.variability
            if v.initial is not None:
                variableAttribute += '\nInitial:' + chr(9) + v.initial
            if v.canHandleMultipleSetPerTimeInstant is not None:
                variableAttribute += '\nMultipleSet:' + chr(9) + v.canHandleMultipleSetPerTimeInstant
            if v.type is not None:
                variableAttribute += '\nBasic type:' + chr(9) + v.type.basicType
                if v.type.declaredType is not None:
                    variableAttribute += '\nDeclared type:' + chr(9) + v.type.declaredType             
                if v.type.quantity is not None:
                    variableAttribute += '\nQuantity:' + chr(9) + v.type.quantity
                if v.type.unit is not None:
                    variableAttribute += '\nUnit:' + chr(9) + v.type.unit
                if v.type.displayUnit is not None:
                    variableAttribute += '\nDisplay unit:' + chr(9) + v.type.displayUnit
                if v.type.relativeQuantity is not None:
                    variableAttribute += '\nRel. quantity:' + chr(9) + v.type.relativeQuantity
                if v.type.min is not None:
                    variableAttribute += '\nMin:' + chr(9) + v.type.min
                if v.type.max is not None:
                    variableAttribute += '\nMax:' + chr(9) + v.type.max
                if v.type.nominal is not None:
                    variableAttribute += '\nNominal:' + chr(9) + v.type.nominal
                if v.type.unbounded is not None:
                    variableAttribute += '\nUnbounded:' + chr(9) + v.type.unbounded                
                if v.type.start is not None:
                    variableAttribute += '\nStart:' + chr(9) + v.type.start    
                if v.type.derivative is not None:
                    variableAttribute += '\nDerivative:' + chr(9) + v.type.derivative    
                if v.type.reinit is not None:
                    variableAttribute += '\nReinit:' + chr(9) + v.type.reinit    
                 
                                
            valueEdit = True  # for the moment
            # ----> Here variable of self.variableTree is set (one entry of the dictionary)
            self.variableTree.variable[vName] = SimulatorBase.TreeVariable(self.structureVariableName(vName), v.type.start, valueEdit, v.type.unit, v.variability, variableAttribute)


class ExplicitEulerSolver():
    '''
        Integration method: Explicit Euler with event handling (without rootfinding)
    '''
    def simulate(self, Tstart, dt, Tend, y0, nOutputIntervals, gridWidth):
        ''' Simulates an ODE-system defined by different functions
            from Tstart to Tend by the explicit Euler method with the fixed step size dt.
            The initial start values of the states are given by the vector y0.
            Time or state events are handled after a successful step if necessary.
            Result points are defined by the number of output intervals 'nOutputIntervals'
            that define a time grid between Tstart and Tend with constant width.
            The grid width can be equal to dt or less or greater than dt.
        '''

        # euler_basic.run_example()

        self.t_cur = Tstart
        self.y_cur = y0.copy()
        y_cur0 = y0.copy()
        # Define vectors for crossing and indicator functions
        z = self.state_events(self.t_cur, self.y_cur, None)
        zb = numpy.empty(len(z))
        zb_new = zb.copy()
        for i in xrange(len(z)):
            zb[i] = (z[i] > 0.0)
        nextTimeEvent = self.time_events(self.t_cur, self.y_cur, None)
        # Write initial values to results
        self.handle_result(None, self.t_cur, self.y_cur)
        # Define next step point and next output point
        stepCounter = 1
        nextStepPoint = min(Tstart + dt, Tend)
        if nOutputIntervals > 0:
            dOutput = (Tend - Tstart) / nOutputIntervals
        else:
            dOutput = dt
        outputStepCounter = 1
        nextOutputPoint = min(Tstart + dOutput, Tend)

        # Start the integration loop
        while self.t_cur < Tend:
            # Define stepsize h, next step point, t_new and time_event
            if nextTimeEvent is None or nextStepPoint < nextTimeEvent:
                time_event = False
                h = min(dt, Tend - self.t_cur)
                stepCounter += 1
                t_new = nextStepPoint
                nextStepPoint = min(Tstart + stepCounter * dt, Tend)
            else:
                time_event = True
                h = nextTimeEvent - self.t_cur
                t_new = nextTimeEvent
                if nextStepPoint == nextTimeEvent:
                    stepCounter += 1
                    nextStepPoint = min(Tstart + stepCounter * dt, Tend)

            # Do the explicit Euler step
            temp = self.y_cur
            self.y_cur = y_cur0
            self.y_cur[:] = temp[:]
            y_cur0 = temp
            t_cur0 = self.t_cur
            self.y_cur = self.y_cur + h * self.rhs(self.t_cur, self.y_cur)
            self.t_cur = t_new

            # Check for state events
            z = self.state_events(self.t_cur, self.y_cur, None)
            for i in xrange(len(z)):
                zb_new[i] = (z[i] > 0.0)
            state_event = (zb_new != zb)
            temp = zb
            zb = zb_new
            zb_new = temp

            # Inform about completed step
            self.completed_step(self)

            def interpolateLinear(a1, b1, a2, b2, t):
                return (b2 - b1) / (a2 - a1) * (t - a1) + b1

            # Write output points until the current time
            while nextOutputPoint < self.t_cur:
                y_Output = interpolateLinear(t_cur0, y_cur0, self.t_cur, self.y_cur, nextOutputPoint)
                self.handle_result(None, nextOutputPoint, y_Output)
                outputStepCounter += 1
                nextOutputPoint = min(Tstart + outputStepCounter * dOutput, Tend)

            # Depending on events have been detected do different tasks
            if state_event.any() or time_event:
                # Event handling
                event_info = [state_event, time_event]
                self.t = self.t_cur
                self.y = self.y_cur
                if not self.handle_event(self, event_info):
                    break
                z = self.state_events(self.t_cur, self.y_cur, None)
                for i in xrange(len(z)):
                    zb[i] = (z[i] > 0.0)
                nextTimeEvent = self.time_events(self.t_cur, self.y_cur, None)
            elif nextOutputPoint == self.t_cur:
                y_Output = interpolateLinear(t_cur0, y_cur0, self.t_cur, self.y_cur, nextOutputPoint)
                self.handle_result(self, nextOutputPoint, y_Output)
                outputStepCounter += 1
                nextOutputPoint = min(Tstart + outputStepCounter * dOutput, Tend)

        self.finalize(None)
