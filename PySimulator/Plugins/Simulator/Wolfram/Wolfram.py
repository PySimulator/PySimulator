#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (C) 2011-2014
Open Source Modelica Consortium
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

import Plugins.Simulator.SimulatorBase
import os, sys, shutil
from PySide import QtGui
from pythonica import pythonica


iconImage = 'simulatorWolfram.ico'
modelExtension = ['mo']  # e.g. ['mo']
simulationProgressData = 0.0

def closeSimulationPlugin():
    pass

def getNewModel(modelName=None, modelFileName=None, config=None):    
    return Model(modelName, modelFileName, config)

class Model(Plugins.Simulator.SimulatorBase.Model):

    def __init__(self, modelName, modelFileName, config):

        Plugins.Simulator.SimulatorBase.Model.__init__(self, modelName, modelFileName, config)
        self.modelType = 'Modelica model in Wolfram'

        self.onlyResultFile = False
        self.integrationSettings.resultFileExtension = 'mat'

        self._availableIntegrationAlgorithms = ['DASSL', 'CVODES', 'Euler', 'RungeKutta', 'Heun']
        self.integrationSettings.algorithmName = self._availableIntegrationAlgorithms[0]

        self._IntegrationAlgorithmHasFixedStepSize = [False, False, True, True, True]
        self._IntegrationAlgorithmCanProvideStepSizeResults = [False, False, True, True, True]

        if not config['Plugins']['Wolfram'].has_key('mathLinkPath'):
            config['Plugins']['Wolfram']['mathLinkPath'] = ''
        mathLinkPath = config['Plugins']['Wolfram']['mathLinkPath']

        if mathLinkPath == '' or not os.path.exists(mathLinkPath):
            ''' Ask for MathLink executable '''
            print "No MathLink executable (math.exe or MathKernel.exe) found to run Wolfram. Please select one ..."
            (mathLinkPath, trash) = QtGui.QFileDialog().getOpenFileName(None, 'Select MathLink executable file', os.getcwd(), 'Executable file (*.exe)')
        if mathLinkPath == '':
            print "failed. No MathLink executable (math.exe or MathKernel.exe) specified."
            return None
        else:
            config['Plugins']['Wolfram']['mathLinkPath'] = mathLinkPath
            config.write()

        #Creates a link to a Mathematica Kernel and stores information needed for communication
        self.mathLink = pythonica.Pythonica(path= "" + mathLinkPath + "" )
        self.compileModel()

        self._initialResult = loadResultFileInit(os.path.join(os.getcwd(), self.name + ".sim"))

    def compileModel(self):
        """
        Compiles a Modelica model by Loading Wolfram SystemModeler Link.It is just needed to load the data into the VariablesBrowser
        before simulating the model with parameters
        """
        if len(self.fileName) == 1:
            if not os.path.isfile(self.fileName[0]):
                raise FileDoesNotExist("File '" + self.fileName[0] + "' does not exist")

        # Load Wolfram SystemModeler Link and Modelica Model and then compiles a model
        self.mathLink.eval('Needs["WSMLink`"]')
        self.mathLink.eval('Import["' + self.fileName[0].encode('utf8') + '",{"ModelicaModel"}]')
        self.mathLink.eval('sim = WSMSimulate["' + self.name + '",{' + str('0') + str(',') + str('10')+ '} ]')

        # Retrieve the path to the result file and copy the simulation settings result file(.sim) to the current working directory
        simResultFileName = self.mathLink.eval('sim[[1]]')
        resultDirectory = os.path.dirname(simResultFileName)
        fileName =  os.path.splitext(os.path.basename(simResultFileName))[0]

        sourceSettingsFileName = os.path.join(resultDirectory + "\\\\\\\\" , fileName + ".sim"+ '"')
        sourceSettingsFileName = sourceSettingsFileName.replace('"', '')
        sourceSettingsFileName = sourceSettingsFileName.replace(' ', '')

        destinationSettingsFileName = os.path.join(os.getcwd(), self.name + ".sim")

        shutil.copyfile(sourceSettingsFileName, destinationSettingsFileName)

    def getReachedSimulationTime(self):
        '''
        Read the current simulation time during a simulation
        '''
        t = ((simulationProgressData * self.integrationSettings.stopTime) / 100.0)
        return t

    def simulate(self):

        s = self.integrationSettings

        # Set simulation interval
        simInterval = str(s.startTime) + str(',') + str(s.stopTime)

        # Set simulation method
        intAlg = self._availableIntegrationAlgorithms.index(s.algorithmName)
	if self._IntegrationAlgorithmHasFixedStepSize[intAlg]:
            simMethod = str('Method->{"')+ str(s.algorithmName)+ str('","StepSize" ->') + str(s.fixedStepSize)+ str('}')
        else:
           simMethod = str('Method->{"')+ str(s.algorithmName)+ str('","Tolerance" ->') + str(s.errorToleranceRel)+ str('}')

        # Set new parameter and initial values for state variables
        changedParameters = ','.join(['"%s" -> %s' % (name,newValue) for name,newValue in self.changedStartValue.iteritems()])
        ChangedParameters = str('WSMInitialValues->{')+ changedParameters +  str('}')

        # Simulate a model with a new parameter values and simulation interval
        self.mathLink.eval('sim = WSMSimulate["' + self.name + '",{' + simInterval + '}, '+ simMethod +', '+ ChangedParameters +']')

        # Retrieve the path to the result file and copy to the current working directory
        simResultFileName = self.mathLink.eval('sim[[1]]')
        resultDirectory = os.path.dirname(simResultFileName)
        fileName =  os.path.splitext(os.path.basename(simResultFileName))[0]

        sourceResultFileName = os.path.join(resultDirectory + "\\\\\\\\" , fileName + ".mat"+ '"')
        sourceResultFileName = sourceResultFileName.replace('"', '')
        sourceResultFileName = sourceResultFileName.replace(' ', '')

        destinationResultFileName = os.path.join(os.getcwd(), os.path.abspath(self.integrationSettings.resultFileName))

        shutil.copyfile(sourceResultFileName, destinationResultFileName)

        sourceSettingsFileName = os.path.join(resultDirectory + "\\\\\\\\" , fileName + ".sim"+ '"')
        sourceSettingsFileName = sourceSettingsFileName.replace('"', '')
        sourceSettingsFileName = sourceSettingsFileName.replace(' ', '')

        destinationSettingsFileName = os.path.join(os.getcwd(), self.name + ".sim")

        shutil.copyfile(sourceSettingsFileName, destinationSettingsFileName)

        if not os.path.isfile(self.integrationSettings.resultFileName):
           raise FileDoesNotExist(self.integrationSettings.resultFileName)

    def setVariableTree(self):
        #if self.resFile == '""':
            #return
        for v in self._initialResult:
            value = None

            if v['kind'] == 'parameter' or v['direction'] == 'state':
              value = v['value']
            else:
              value = None

            variableAttribute = ''
            if v['description'] != '' :
                variableAttribute += 'Description:' + chr(9) + v['description'] + '\n'
            variableAttribute += 'Causality:' + chr(9) + v['direction'] + '\n'
            variableAttribute += 'Variability:' + chr(9) + v['kind'] + '\n'
            variableAttribute += 'Type:' + chr(9) + v['type']

            self.variableTree.variable[v['name'].replace('[', '.[')] = Plugins.Simulator.SimulatorBase.TreeVariable(self.structureVariableName(v['name'].replace('[', '.[')), value, 'false', v['unit'], v['kind'], variableAttribute)
    def getAvailableIntegrationAlgorithms(self):
        ''' Returns a list of strings with available integration algorithms
        '''
        return self._availableIntegrationAlgorithms

    def getIntegrationAlgorithmHasFixedStepSize(self, algorithmName):
        ''' Returns True or False dependent on the fact,
            if the integration algorithm given by the string algorithmName
            has a fixed step size or not (if not it has a variable step size).
        '''
        return self._IntegrationAlgorithmHasFixedStepSize[self._availableIntegrationAlgorithms.index(algorithmName)]

    def getIntegrationAlgorithmCanProvideStepSizeResults(self, algorithmName):
        ''' Returns True or False dependent on the fact,
            if the integration algorithm given by the string algorithmName
            can provide result points at every integration step.
        '''
        return self._IntegrationAlgorithmCanProvideStepSizeResults[self._availableIntegrationAlgorithms.index(algorithmName)]


# Exception classes
class FileDoesNotExist (Exception): pass
class WrongResultFile (Exception): pass
class BuildModelFail (Exception): pass
class OMInitXMLParseException (Exception): pass

def loadResultFileInit(fileName):
    """ Load Wolfram initial data in an object.

    """
    # Correct file path if needed
    if os.name == "nt":
      fileName = fileName.replace("/", "\\")

    # If no fileName given, inquire it interactively
    if fileName == None:
        return

    # Check if fileName exists
    if not os.path.isfile(fileName):
        raise FileDoesNotExist("File '" + fileName + "' does not exist")

    # Determine complete file name
    fullFileName = os.path.abspath(fileName)

    from xml.parsers import expat

    p = expat.ParserCreate()
    def start(name,attr):
      if name == "variable" and attr['name'] != '$dummy' and attr['name'] != 'der($dummy)':
        start.cname = attr['name']
        start.cdesc = attr.get('description') or ''
        start.cvalue = attr.get('value') or ''
        start.cunit =  attr.get('unit') or ''
        start.ctype = attr.get('type')

        if attr.get('direction') == 'BIDIR':
            start.ccausality = 'internal'
        elif attr.get('direction') == 'INDIR':
            start.ccausality = 'input'
        elif attr.get('direction') == 'OUTDIR':
            start.ccausality = 'output'
        else:
            start.ccausality = ''

        if attr.get('kind') == 'STATE':
            start.ccausality = 'state'

        if attr.get('kind') == 'DISCRETE':
            start.cvar = 'discrete'
        elif attr.get('kind') =='PARAM':
            start.cvar = 'parameter'
        elif attr.get('kind') == 'CONSTANT':
            start.cvar = 'constant'
        else:
            start.cvar = 'continuous'

    def end(name):
      if name == "variable":
        end.result += [{'name':start.cname, 'value':start.cvalue, 'unit':start.cunit, 'direction':start.ccausality, 'kind':start.cvar,'description':start.cdesc,'type':start.ctype}]
    end.result = []
    p.StartElementHandler = start
    p.EndElementHandler = end
    f = open(fullFileName,"r")
    try:
      p.ParseFile(f)
    except:
      raise OMInitXMLParseException("Failed to parse " + fullFileName)
    return end.result

def prepareSimulationList(fileName, names, config):
  pass