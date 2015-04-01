import getpass
from operator import itemgetter
import os
import time
import types
import numpy
import FMU
import Plugins.Simulator.FMUSimulator.FMIDescription1 as FMIDescription
import Plugins.Simulator.FMUSimulator.FMUInterface1 as FMUInterface
from Plugins.Algorithms.Integrator.Sundials.AssimuloIntegrators import AssimuloCVode, AssimuloIda
import Plugins.SimulationResult.IntegrationResults
import Plugins.SimulationResult.Mtsf.Mtsf as Mtsf
import Plugins.SimulationResult.Mtsf.MtsfFmi as MtsfFmi
import Plugins.SimulationResult.Mtsf.pyMtsf as pyMtsf
from Plugins.Simulator.FMUSimulator.FMUInterface1 import fmiTrue, fmiFalse
import Plugins.Simulator.SimulatorBase


class Model(Plugins.Simulator.SimulatorBase.Model):
    
    def __init__(self, modelName=None, modelFileName=None, config=None, loggingOn=False):
         ''' Modelname and ModelFilename are list of strings '''
         
         self._descriptioninstance=[]
         for i in xrange(len(modelFileName)):
            self.interface = FMUInterface.FMUInterface(modelFileName[i], self, loggingOn)
            self.description = self.interface.description
            self._descriptioninstance.append(self.description)
            
         Plugins.Simulator.SimulatorBase.Model.__init__(self, 'ConnectedFMUS', modelFileName[0], config)
         self.modelType = 'Connected FMU Simulation ' + ' in FMUSimulator'
         self._availableIntegrationAlgorithms = ["BDF (IDA, Dassl like)", "BDF (CVode)", "Adams (CVode)", "Explicit Euler (fixed step size)"]
         self._IntegrationAlgorithmHasFixedStepSize = [False, False, False, True]
         self._IntegrationAlgorithmCanProvideStepSizeResults = [True, True, True, True]
         self._IntegrationAlgorithmSupportsStateEvents = [True, True, True, True]
         self.integrationResults = Mtsf.Results('')
         self.integrationSettings.resultFileExtension = 'mtsf'
         self.integrationSettings.algorithmName = self._availableIntegrationAlgorithms[0]
         self.simulationStopRequest = False
    
    def close(self):
        ''' Closing the model, release of resources
        '''
        Plugins.Simulator.SimulatorBase.Model.close(self)
        print "Deleting model instance"
        self.interface.free()
       
    
    def getAvailableIntegrationAlgorithms(self):
        return self._availableIntegrationAlgorithms

    def getIntegrationAlgorithmHasFixedStepSize(self, algorithmName):
        return self._IntegrationAlgorithmHasFixedStepSize[self._availableIntegrationAlgorithms.index(algorithmName)]

    def getIntegrationAlgorithmCanProvideStepSizeResults(self, algorithmName):
        return self._IntegrationAlgorithmCanProvideStepSizeResults[self._availableIntegrationAlgorithms.index(algorithmName)]

    def getIntegrationAlgorithmSupportsStateEvents(self, algorithmName):
        return self._IntegrationAlgorithmSupportsStateEvents[self._availableIntegrationAlgorithms.index(algorithmName)]    
        
    def setVariableTree(self):
      #Sets the variable tree to be displayed in the variable browser.
      #The data is set in self.variableTree that is an instance of the class SimulatorBase.VariableTree

      self.description=self._descriptioninstance
      
      for i in xrange(len(self.description)):
        for vName, v in self.description[i].scalarVariables.iteritems():
            #text=(self.description[i].modelName).split('.')
            text=(self.description[i].modelName).replace('.','')                      
            varname=text+'.'+vName
            variableAttribute = ''
            if v.description is not None:
                variableAttribute += 'Description:' + chr(9) + v.description + '\n'
            variableAttribute += 'Reference:' + chr(9) + str(v.valueReference)
            if v.variability is not None:
                variableAttribute += '\nVariability:' + chr(9) + v.variability
            if v.causality is not None:
                variableAttribute += '\nCausality:' + chr(9) + v.causality
            if v.alias is not None:
                if v.alias.lower() is not 'noalias':
                    variableAttribute += '\nAlias:' + chr(9) + v.alias
            if v.directDependency is not None:
                variableAttribute += '\nDirect dep.:' + chr(9) + str(v.directDependency)
            if v.type is not None:
                variableAttribute += '\nType:' + chr(9) + v.type.type
                if v.type.description is not None:
                    variableAttribute += '\nType info:' + chr(9) + v.type.description
                if v.type.quantity is not None:
                    variableAttribute += '\nQuantity:' + chr(9) + v.type.quantity
                if v.type.unit is not None:
                    variableAttribute += '\nUnit:' + chr(9) + v.type.unit
                if v.type.displayUnit is not None:
                    variableAttribute += '\nDisplay unit:' + chr(9) + v.type.displayUnit
                if v.type.relativeQuantity is not None:
                    variableAttribute += '\nRel. quantity:' + chr(9) + str(v.type.relativeQuantity)
                if v.type.min is not None:
                    variableAttribute += '\nMin:' + chr(9) + v.type.min
                if v.type.max is not None:
                    variableAttribute += '\nMax:' + chr(9) + v.type.max
                if v.type.nominal is not None:
                    variableAttribute += '\nNominal:' + chr(9) + v.type.nominal
                if v.type.start is not None:
                    variableAttribute += '\nStart:' + chr(9) + v.type.start
                if v.type.fixed is not None:
                    variableAttribute += '\nFixed:' + chr(9) + str(v.type.fixed)
            valueEdit = True  # for the moment
            # ----> Here variable of self.variableTree is set (one entry of the dictionary)
            self.variableTree.variable[varname] = Plugins.Simulator.SimulatorBase.TreeVariable(self.structureVariableName(varname), v.type.start, valueEdit, v.type.unit, v.variability, variableAttribute)
        

