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
import os
import pythonica
import tempfile
iconImage = 'simulatorWolfram.ico'
modelExtension = ['mo']  # e.g. ['mo']

def closeSimulationPlugin():
    pass

class Model(Plugins.Simulator.SimulatorBase.Model):

    def __init__(self, modelName, modelFileName, config):

        Plugins.Simulator.SimulatorBase.Model.__init__(self, modelName, modelFileName, 'Wolfram', config)

        self.onlyResultFile = False
        self.integrationSettings.resultFileExtension = 'mat'

        self._availableIntegrationAlgorithms = ['DASSL', 'CVODES', 'Explicit Euler', 'Heuns method', 'Runge-Kutta (RK4)']
        self.integrationSettings.algorithmName = self._availableIntegrationAlgorithms[0]

        self._IntegrationAlgorithmHasFixedStepSize = [False, True, False, False, True, False]
        self._IntegrationAlgorithmCanProvideStepSizeResults = [False, True, False, False, True, False]

        self.compileModel()

        if self.resFile != '""':
            self._initialResult = loadResultFileInit(os.path.join(tempfile.gettempdir(), self.name + "_init.sim"))
        else:
            print "The selected model could not be instantiated, check for any dependencies that the model might have"
            return


    def compileModel(self):
        """
        This function is needed to load the data into the VariablesBrowser
        before simulating the model with parameters.
        """
        if len(self.fileName) == 1:
            if not os.path.isfile(self.fileName[0]):
                raise FileDoesNotExist("File '" + self.fileName[0] + "' does not exist")

        # set the working directory in Wolfram
        work_dir = os.getcwd()
        mofile = os.path.join(work_dir,self.name + ".mo")
        mofile = mofile.replace('\\', '/')
        pwd = os.path.abspath('.').replace('\\', '/')


        m = pythonica.Pythonica()
        m.eval('Needs["WSMLink`"]')
        m.eval('Import["' + mofile + '",{"ModelicaModel"}]')

        res = m.eval('WSMSimulate["' + self.name + '",{' + str('0') + str(',') + str('10')+ '} ]')

        # read the result file
        self.resFile = os.path.join(work_dir,self.name + "_res.mat")

    def simulate(self):
        ''' Simulate a Modelica model by executing Wolfram's simulation executable.'''

        def compile_model(simulate_options):

            if self.fileName != None:
                print("okey")

        def precheck_for_set_sim_options():
            s = self.integrationSettings
            settings = s.__dict__

        def precheck_for_model():
            sim_opts = precheck_for_set_sim_options()
            if sim_opts != '':
                compile_model(sim_opts)
            else:
                compile_model('')



    def setVariableTree(self):
        if self.resFile == '""':
            return
        for v in self._initialResult:
            value = None

            if v['kind'] == 'parameter':
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


# Adapted from DymolaMat/DymolaMat.py for OpenModelica #

import scipy.io, string

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
        # fileName = selectResultFile()

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