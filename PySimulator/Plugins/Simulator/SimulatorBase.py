#!/usr/bin/env python
# -*- coding: utf-8 -*-

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


'''
***************************
This module provides the basic classes and functions for a Simulator plugin.

The main part of a simulator plugin is the Model class. It holds all the information
of a loaded model and provides functions to simulate it, write and read results, etc.
***************************
'''


import copy
import os
import string
import Plugins.SimulationResult.IntegrationResults as IntegrationResults


'''
modelExtension is a list of file name extension that can be loaded by the Simulator plugin
'''
modelExtension = ['']  # e.g. ['mo', 'moe', 'exe']


def closeSimulatorPlugin():
    ''' Function is called when closing the plugin (normally when PySimulator is closed).
        It can be used to release resources used by the plugin.
    '''
    pass


class Stopping(Exception):
    ''' Own exception class for stopping the numerical integration '''
    pass


class IntegrationSettings():
    ''' Provides default values for Integration settings
    '''
    def __init__(self):
        self.startTime = 0.0
        self.stopTime = 1.0
        self.algorithmName = ''  # e.g. 'Euler'
        self.errorToleranceRel = 1.0e-4
        self.errorToleranceAbs = None  # None means equal to ToleranceRel
        self.fixedStepSize = 1.0e-3
        self.gridPoints = 1001
        self.gridWidth = 1.0e-3
        self.gridPointsMode = 'NumberOf'  # or 'Width'  or  'Integrator'
        self.resultFileName = ''  # e.g. 'Rectifier.mtsf'
        self.resultFileExtension = ''  # e.g. 'mtsf', 'mat'
        self.resultFileFormat = ''  # e.g. 'single', 'double', etc.?
        self.resultFileIncludeInputs = True
        self.resultFileIncludeOutputs = True
        self.resultFileIncludeStates = True
        self.resultFileIncludeDerivatives = True
        self.resultFileIncludeParameters = True
        self.resultFileIncludeAuxiliaries = True
        self.resultFileIncludeEvents = True


class IntegrationStatistics():
    ''' Holds the Integration statistics
    '''
    def __init__(self):
        self.reset()

    def reset(self):
        #                         Types:
        self.reachedTime = None  # Real
        self.nTimeEvents = None  # Integer
        self.nStateEvents = None  # Integer
        self.nGridPoints = None  # Integer
        self.cpuTime = None  # Real
        self.finished = None  # Boolean


class VariableTree():
    ''' Holds the information for the variable tree of a model in the variables browser
    '''
    def __init__(self):
        self.rootAttribute = ''  # Tip text for the root of the tree
        self.variable = {}  # dictionary of TreeVariable instances; key is name of variable



class TreeVariable():
    ''' Holds information (necessary to build a variable tree) for a single variable
    '''
    def __init__(self, browserName, value, valueEdit, unit, variability, attribute):
        #                                Types:
        self.browserName = browserName  # String
        self.value = value  # Different types, e.g. Real, Integer, Boolean, String
        self.valueEdit = valueEdit  # Boolean
        self.unit = unit  # String
        self.variability = variability  # String
        self.attribute = attribute  # String



class Model():
    ''' This is the base class for a model of a Simulator plugin
    '''

    def __init__(self, modelName, modelFileName, modelType, config):
        ''' Constructor initializes some class variables.
            Type of modelName, modelType:  String;     modelFileName: List of Strings
        '''
        self.fileName = modelFileName
        self.name = modelName
        self.modelType = modelType  # e.g. 'None', 'FMI1.0', 'FMI2.0', 'Dymola', 'OpenModelica'
        self.integrationSettings = IntegrationSettings()
        self.integrationStatistics = IntegrationStatistics()
        self.integrationResults = IntegrationResults.Results()
        self.variableTree = VariableTree()
        self.changedStartValue = dict()
        self.pluginData = dict()
        self.config = config

    def close(self):
        ''' Function is called when closing the model.
            Resources used by the model instance should be released.
        '''
        # Close the result file (if any)
        try:
            self.integrationResults.close()
        except:
            pass

    def duplicate(self):
        '''  Function is called when duplicating a model in the Variables Browser
        '''
        theCopy = copy.copy(self)
        theCopy.integrationSettings = copy.copy(self.integrationSettings)  # new instance of integration settings
        theCopy.integrationStatistics = copy.copy(self.integrationStatistics)  # new instance of integrationStatistics
        theCopy.integrationStatistics.reset()
        theCopy.integrationResults = IntegrationResults.Results()  # new instance of integration results (empty)
        theCopy.variableTree = VariableTree()  # new instance of variable tree (empty)
        theCopy.changedStartValue = copy.copy(self.changedStartValue)  # new instance of changedStartValue dictionary
        theCopy.pluginData = dict()  # new instance of pluginData dictionary
        return theCopy

    def loadResultFile(self, fileName):
        ''' Loads a result file (format must be known by a SimulationResult plugin) with file name fileName
            The results are available in the class self.integrationResults
        '''
        if os.path.exists(fileName):
            sp = unicode.rsplit(fileName, '.', 1)
            suffix = sp[1]
            import Plugins.SimulationResult as SimulationResult
            if suffix in SimulationResult.fileExtension:
                i = SimulationResult.fileExtension.index(suffix)
                self.integrationResults = SimulationResult.plugin[i].Results(fileName)
            else:
                # Dummy object
                self.integrationResults = IntegrationResults.Results()

    def simulate(self):
        ''' This function starts a model simulation with
            the settings stored in the model class, especially
            in self.integrationSettings. During simulation
            (or at least after simulation) the information
            in self.integrationStatistics is updated.
            Also, a result file is generated during simulation.
        '''

        raise NameError('Not implemented.')

    def getAvailableIntegrationAlgorithms(self):
        ''' Returns a list of strings with available integration algorithms
        '''
        raise NameError('Not implemented.')

    def getIntegrationAlgorithmHasFixedStepSize(self, algorithmName):
        ''' Returns True or False dependent on the fact,
            if the integration algorithm given by the string algorithmName
            has a fixed step size or not (if not it has a variable step size).
        '''
        raise NameError('Not implemented.')

    def getIntegrationAlgorithmCanProvideStepSizeResults(self, algorithmName):
        ''' Returns True or False dependent on the fact,
            if the integration algorithm given by the string algorithmName
            can provide result points at every integration step.
        '''
        raise NameError('Not implemented.')


    def setVariableTree(self):
        ''' This implementation uses the integration result to generate a variable tree.
            It is the default implementation for generating the variable tree when loading only a result file (not a model) into PySimulator.
            Normally, Simulator plugins overload this function and provide their own functions for variable trees of MODELS.

            The function generates an instance of the class VariableTree and stores it in self.variableTree.
            It transforms ResultVariables to TreeVariables.
        '''
        # Generate variable tree from result file information
        variables = self.integrationResults.getVariables()
        fileInfos = self.integrationResults.getFileInfos()
        fileInfosList = [(x, y) for x, y in fileInfos.iteritems()]
        fileInfosList.sort()
        lenList = [len(x) for x in fileInfos.keys()]
        if len(lenList) > 0:
            maxLength = max(lenList)
        else:
            maxLength = 0
        tipText = ''
        for x in fileInfosList:
            group = x[0]
            info = x[1]
            tipText = tipText + group + ":" + ' ' * (maxLength - len(group)) + chr(9) + info + '\n'
        if len(tipText) > 0:
            tipText = tipText[:-1]  # Delete last \n
        self.variableTree.rootAttribute = tipText
        valueEdit = False  # No editing for result files
        for vName, v in variables.iteritems():
            vinfos = ''
            for group, info in v.infos.iteritems():
                vinfos = vinfos + group + ":" + chr(9) + info + '\n'
            if len(vinfos) > 0:
                vinfos = vinfos[:-1]  # Delete last \n
            if len(vinfos) == 0:
                vinfos = None
            self.variableTree.variable[vName] = TreeVariable(self.structureVariableName(vName), v.value, valueEdit, v.unit, v.variability, vinfos)


    def structureVariableName(self, name):
        name2 = name

        ''' der '''
        nDer = name2.count('der(')
        if nDer > 0:
            a = []

            c = name2.rsplit(',', 1)  # Check for der(a.b.c.d, 3) or a.b.c.der(d, 3)
            if len(c) > 1:
                d = c[1].replace(' ', '')
                if len(d) > 1:
                    if d[-1] == ')' and d[:-1].isdigit():
                        p1 = 'der('
                        p2 = ',' + c[1]
                        i = name2.find('der(')
                        if i > -1:
                            if i == 0:  # der(a.b.c.d, 3)
                                a = c[0][4:].rsplit('.', 1)
                            else:  # a.b.c.der(d, 3)
                                a = c[0].split('der(')
                                if a[0][-1] == '.':
                                    a[0] = a[0][:-1]
                                else:
                                    a = []

            if len(a) == 0 and name2[-nDer:] == ')' * nDer:  # Plausibility check for der(der(der(Variablename))) or a.b.c.der(der(der(d)))
                i = name2.find('der(' * nDer)
                if i > -1:
                    p1 = 'der(' * nDer
                    p2 = ')' * nDer
                    if i == 0:  # der(der(der(...)))
                        a = name2[4 * nDer:-nDer].rsplit('.', 1)
                    else:  # a.b.c.der(der(der(...)))
                        a = name2[:-nDer].split('der(' * nDer)
                        if a[0][-1] == '.':
                            a[0] = a[0][:-1]
                        else:
                            a = []

            if len(a) > 0:
                if len(a) == 1:
                    p0 = ''
                    p12 = a[0]
                else:
                    p0 = a[0] + '.'
                    p12 = a[1]
                if '[' in p12:  # p12 = d[4,6,8,9]
                    b = p12.split('[', 1)
                    name2 = p0 + p1 + b[0] + p2 + '[' + b[1]
                else:  # p12 = d
                    name2 = p0 + p1 + p12 + p2


        '''  Arrays '''
        a = name2.split('.')
        name2 = ''
        for k, b in enumerate(a):
            part = b
            i1 = b.find('[')
            if i1 > -1:
                i2 = b.rfind(']')
                if i2 > i1:
                    c = b[i1:i2 + 1]
                    c = c.replace(' ', '')
                    c = c.replace(',', '][')
                    part = b[:i1] + c + b[i2 + 1:]
            if k > 0:
                name2 = name2 + '.'
            name2 = name2 + part
        name2 = name2.replace('[', '.[')

        return name2



    def getReachedSimulationTime(self):
        ''' Results are available up to the returned time
        '''
        raise NameError('Not implemented.')
        # return simulationTime


    ''' **************************************************************************************
        The following functions are optional.
        They are necessary, if detailed
        access to the model equations
        shall be supported (e.g. to be used
        by some Analysis plugins). For simple
        simulation they are not necessary.
    '''

    def getDerivatives(self, t, x):
        ''' Returns the right hand side of the dynamic system for
            given time t and state vector x.
        '''
        raise NameError('Not implemented.')
        # return derivativeValues

    def getEventIndicators(self, t, x):
        ''' Returns the event indicator functions for
            given time t and state vector x.
        '''
        raise NameError('Not implemented.')
        # return indicatorValues

    def getStates(self):
        ''' Returns a vector with the values of the states.
        '''
        raise NameError('Not implemented.')
        # return stateValues

    def getStateNames(self):
        ''' Returns a list of Strings: the names of all states in the model.
        '''
        raise NameError('Not implemented.')
        # return listOfNames

    def getValue(self, name):
        ''' Returns the values of the variables given in name;
            name is either a String or a list of Strings.
        '''
        raise NameError('Not implemented.')
        # return value

    def setValue(self, name, value):
        ''' Set the variable name (a String) to value in the model
        '''
        raise NameError('Not implemented.')

    def initialize(self, t, errorTolerance):
        ''' Initializes the model at time = t with
            changed start values given by the dictionary
            self.changedStartValue.
            The function returns a status flag and the next time event.
        '''
        raise NameError('Not implemented.')
        # return status, nextTimeEvent


def prepareSimulationList(fileName, name, config):
    pass
