''' 
Copyright (C) 2011-2013 German Aerospace Center DLR
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
This Simulator plugin can load Modelica models (assumed SimulationX is installed),
simulate them by Simulation X and save the results.
***************************
'''

import os
import pythoncom
import win32com.client
import time
import types
import csv

import Plugins.Simulator.SimulatorBase
import Plugins.SimulationResult.SimulationXCsv.SimulationXCsv as SimulationXCsv

iconImage = 'simulatorSimulationX.ico'
modelExtension = ['mo']
simulationXused = False

def closeSimulatorPlugin():
    if simulationXused:
        sim = win32com.client.Dispatch("iti.simx3")
        sim.Quit()
        
def prepareSimulationList(fileName, name, config):
    pass

class Model(Plugins.Simulator.SimulatorBase.Model):   
      
    def __init__(self, modelName, modelFileName, config):             
        
        Plugins.Simulator.SimulatorBase.Model.__init__(self, modelName, modelFileName, 'SimulationX', config)
                            
        # A dummy object to get result properties:
        self.integrationResults = SimulationXCsv.Results('') 
        self.integrationSettings.resultFileExtension = 'csvx'                
        
        self._avilableIntegrationAlgorithms = ["BDF", "MEBDF", "CVODE", "FixedStep"]        
           
        self._IntegrationAlgorithmHasFixedStepSize = [False, False, False, True]
        self._IntegrationAlgorithmCanProvideStepSizeResults = [False, False, False, False]
        
        self.integrationSettings.algorithmName = self._avilableIntegrationAlgorithms[0]

        # Open SimulationX
        self._sim=self._openSimulationX()

        # Open model using Modelica-Identifier
        try:
            for x in self.fileName:
                self._sim.Application.LoadLibrary(x)
        except:
            pass
        self._doc=self._sim.Documents.Open(self.name)

    def _openSimulationX(self):
        # Constants
        simUninitialised = 0
        simInitBase = 1
        simInitAutomatic = 2
        simInitManual = 3
    
        # Start SimulationX/Connection with SimulationX
        pythoncom.CoInitialize()
        sim = win32com.client.Dispatch("iti.simx3")

        # Wait till SimulationX starts and loads Modelica
        if sim.InitState == simUninitialised:
            while sim.InitState != simInitBase:
                time.sleep(0.1)
    
        if sim.InitState == simInitBase:
            # SimulationX in non-interactive mode 
            sim.Interactive = 0
    
            # Open SimulationX window
            sim.Visible = 0
    
            # Others
            sim.InitSimEnvironment() # Necessary when a script is used to start SimulationX

        global simulationXused
        simulationXused = True
        
        return sim
        
    def close(self):
        # Close model
        self._doc.Close()
        
        # Quit SimulationX
        #self._sim.Quit()
        # Close the model
        Plugins.Simulator.SimulatorBase.Model.close(self)
        
        
            
    def setVariableTree(self):
        ''' Generate variable tree from initialization file        
        '''
        # List all parameters
        all_params = self._doc.Parameters
        all_params_length = len(all_params)
        for i in range(all_params_length):
            # Exclude SimulationX internal parameters such as solver settings 
            if (all_params[i].Parent.Type.Ident!="BuiltIn.SimModel"):               
                name = all_params[i].GetRelIdent(self._doc)
                value = self._doc.Parameters(name).Value
                valueEdit = True
                unit = None
                if all_params[i].Unit != '-':
                    unit = all_params[i].Unit
                variability = 'fixed'
                variableAttribute = ''
                if all_params[i].Comment != '' :
                    variableAttribute += 'Description:' + chr(9) + all_params[i].Comment + '\n'
                variableAttribute += 'Causality:' + chr(9) + 'parameter' + '\n'
                variableAttribute += 'Variability:' + chr(9) + variability# + '\n'
                #variableAttribute += 'Type:' + chr(9) + dataType
                self.variableTree.variable[name] = Plugins.Simulator.SimulatorBase.TreeVariable(self.structureVariableName(name), value, valueEdit, unit, variability, variableAttribute)
   
        # List all result variables
        all_results = self._doc.Results
        all_results_length=len(all_results)
        for i in range(all_results_length):
            #interne Variablen for Solver, etc. mit Ausnahme der Simulationszeit nicht protokollieren
            if (all_results[i].Parent.Type.Ident!="BuiltIn.SimModel" or all_results[i].Name=="t"):
                name = all_results[i].GetRelIdent(self._doc)
                value = None            
                valueEdit = False
                unit = None
                if all_results[i].Unit != '-':
                    unit = all_results[i].Unit
                variability = 'continuous'
                variableAttribute = ''
                if all_results[i].Comment != '' :
                    variableAttribute += 'Description:' + chr(9) + all_results[i].Comment + '\n'
                variableAttribute += 'Causality:' + chr(9) + 'state' + '\n'
                variableAttribute += 'Variability:' + chr(9) + variability# + '\n'
                #variableAttribute += 'Type:' + chr(9) + dataType
                self.variableTree.variable[name] = Plugins.Simulator.SimulatorBase.TreeVariable(self.structureVariableName(name), value, valueEdit, unit, variability, variableAttribute)

    def getReachedSimulationTime(self):
        ''' Read the current simulation time during a simulation           
        '''
        rTime = None
        
        return rTime
     
    def simulate(self):
        ''' Simulate a Modelica model by executing SimulationX's simulation.       
        '''
        
        #import pydevd
        #pydevd.connected = True
        #pydevd.settrace(suspend=False)
        
        pythoncom.CoInitialize()
        
        sim = win32com.client.Dispatch("iti.simx3")
        doc = sim.ActiveDocument
        
        
        # Constants
        simSimModel = 33
        # Simulation solution states
        #    2 ... simReady
        #    8 ... simRunning
        #   16 ... simStopped
        #   32 ... simFailed
        simStopped = 16
        #simFailed = 32

        simulation = self.integrationSettings
        
#        self.resultFileName = ''  # e.g. 'Rectifier.mtsf'
#        self.resultFileExtension = ''  # e.g. 'mtsf', 'mat'
#        self.resultFileFormat = ''  # e.g. 'single', 'double', etc.?
#        self.resultFileIncludeInputs = True
#        self.resultFileIncludeOutputs = True
#        self.resultFileIncludeStates = True
#        self.resultFileIncludeDerivatives = True
#        self.resultFileIncludeParameters = True
#        self.resultFileIncludeAuxiliaries = True

        # Integration settings
        doc.Lookup("tStart").Value=simulation.startTime
        doc.Lookup("tStop").Value=simulation.stopTime
        doc.Lookup("relTol").Value=simulation.errorToleranceRel
        if simulation.errorToleranceAbs is None:
            doc.Lookup("absTol").Value=simulation.errorToleranceRel
        else:
            doc.Lookup("absTol").Value=simulation.errorToleranceAbs

        ialg = self._avilableIntegrationAlgorithms.index(simulation.algorithmName)
        if self._IntegrationAlgorithmHasFixedStepSize[ialg]:
            doc.Lookup("dtMin").Value=simulation.fixedStepSize
        else:
            doc.Lookup("dtMin").Value=1e-008    
        #doc.Lookup("dtMax").Value="(tStop-tStart)/10"
        #doc.Lookup("dtDetect").Value="dtMin*1e-5"
        if simulation.gridPointsMode == 'NumberOf':   
            gridWidth = (simulation.stopTime-simulation.startTime)/(simulation.gridPoints-1)
        elif simulation.gridPointsMode == 'Width':
            gridWidth = simulation.gridWidth
        doc.Lookup("dtProtMin").Value=gridWidth
        doc.Lookup("protKind").Value=0 # = "BaseModel.ProtKind.MinTimeStepsPostEvents"
        doc.SolverByName = simulation.algorithmName

        for name,value in self.changedStartValue.iteritems():
            doc.Parameters(name).Value = value

        # Log all variables
        results = doc.Results
        results_length=len(results)
        for i in range(results_length):
            # Ignore logging of internal variables such as solver settings
            # if (results[i].Parent.Type.Ident!="BuiltIn.SimModel"):
            if (results[i].Parent.Class!=simSimModel): 
                results[i].Protocol=1
            else:
                results[i].Protocol=0

       
        # Start simulation
        doc.Reset()
        doc.Start()
    
        # Wait till simulation is finished
        while doc.SolutionState < simStopped:
            time.sleep(0.1)

        # Integration is finished
        # Log all parameters 
        all_params = doc.Parameters
        all_params_length = len(all_params)
        paramName = list()
        paramUnit = list()
        paramValue = list()
        for i in range(all_params_length):
            # Exclude SimulationX internal parameters such as solver settings 
            if (all_params[i].Parent.Type.Ident!="BuiltIn.SimModel"):               
                ignoreParam = False
                if (all_params[i].Class!=1):                   
                    value =  all_params[i].Eval()
                else:
                    #print params[i].GetRelIdent(doc), params[i].Value
                    # Spezialbehandlung for Short Class Definitions
                    try:
                        bc=all_params[i].BaseEntities[0]
                        while bc.Class==1:
                            bc=bc.BaseEntities[0]
                        value = bc.Eval()
                    except:
                        ignoreParam = True
                       
                # print params2[i].Eval()
                if not ignoreParam:
                    if value is None:
                        value = 1e30
                    
                    if type(value) == types.TupleType:
                        if len(value) > 0:
                            if type(value[0]) != types.TupleType: # Currently only vectors
                                n = len(value)
                                name = all_params[i].GetRelIdent(doc)
                                unit = all_params[i].Unit
                                for k in xrange(n):                        
                                    paramName.append(name + '[' + str(k+1) + ']')                            
                                    paramUnit.append(unit)
                                    if type(value[k]) == types.BooleanType:
                                        value_k = int(value[k])
                                    else:
                                        value_k = value[k]    
                                    paramValue.append(value_k)
                    else:
                        paramName.append(all_params[i].GetRelIdent(doc))
                        paramUnit.append(all_params[i].Unit)
                        if type(value) == types.BooleanType:
                            value = int(value)
                        paramValue.append(value)


        if (doc.SolutionState == simStopped):
            res="OK"
            # Save results in CSV-file            
            resultFileName = os.path.abspath(simulation.resultFileName).replace('\\', '/')
            doc.StoreAllResultsAsText(resultFileName)
            # Save parameters in CSV-file
            if len(paramName) > 0:
                with open(resultFileName + 'p', 'wb') as csvfile:
                    csvwriter = csv.writer(csvfile, delimiter=';')                   
                    csvwriter.writerow(paramName)
                    csvwriter.writerow(paramUnit)     
                    csvwriter.writerow(paramValue)
            self.integrationStatistics.reachedTime = simulation.stopTime     
        else:
            res="Error"

    def getAvailableIntegrationAlgorithms(self): 
        ''' Returns a list of strings with available integration algorithms
        '''       
        return self._avilableIntegrationAlgorithms
    
    def getIntegrationAlgorithmHasFixedStepSize(self, algorithmName):
        ''' Returns True or False dependent on the fact, 
            if the integration algorithm given by the string algorithmName
            has a fixed step size or not (if not it has a variable step size).
        '''
        return self._IntegrationAlgorithmHasFixedStepSize[self._avilableIntegrationAlgorithms.index(algorithmName)]
    
    def getIntegrationAlgorithmCanProvideStepSizeResults(self, algorithmName):
        ''' Returns True or False dependent on the fact,
            if the integration algorithm given by the string algorithmName
            can provide result points at every integration step.
        '''
        return self._IntegrationAlgorithmCanProvideStepSizeResults[self._avilableIntegrationAlgorithms.index(algorithmName)]
  
    
