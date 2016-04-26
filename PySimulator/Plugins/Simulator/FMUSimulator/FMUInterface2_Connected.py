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

import tempfile
import FMUInterface2
import FMIDescription2_Connected

import numpy
from enum import Enum
import xml.etree.ElementTree as ET

''' Changed from numpy.uint32 to numpy.long to handle connected FMUs value references
    We append the FMU id with the value reference so we need a bigger data structure.
    We convert the value reference back to numpy.uint32 before calling fmiSet*/fmiGet* functions.
'''
def createfmiReferenceVector(n):
    return (numpy.ndarray(n, numpy.long))

class FMUData:
    def __init__(self):
        self.valueReferences = []
        self.values = []

class FMIVarType(Enum):
    Real = 1
    Integer = 2
    Enumeration = 3
    Boolean = 4
    String = 5

class FMUInterface:
    ''' This class encapsulates the FMU C-Interface
        all fmi* functions are a public interface to the FMU-functions        
    '''
    def __init__(self, connectedfmusitems, xml, connectionorder, parent=None, loggingOn=True, preferredFmiType='me'):
        ''' Load an FMU-File and start a new instance
            @param fileName: complete path and name of FMU-file (.fmu)
            @type fileName: string
        '''
        self._connections = []
        self._connectionorder = connectionorder
        self.FMUInterfaces = {}
        self.activeFmiType = preferredFmiType  # 'me' or 'cs'
        self.visible = 0
        
        self._loggingOn = loggingOn
        self._tempDir = tempfile.mkdtemp()
        # create FMUInterface objects
        for i in xrange(len(connectedfmusitems)):
            fileName = connectedfmusitems[i]['filename']
            FMUInterfaceObj = FMUInterface2.FMUInterface(fileName, self, loggingOn, preferredFmiType)
            FMUInterfaceObj.instanceName = connectedfmusitems[i]['instancename']
            # assuming we won't get FMUs more than 999.
            self.FMUInterfaces[str(i+1).ljust(3, '0')] = FMUInterfaceObj
        
        self.description = FMIDescription2_Connected.FMIDescription(self.FMUInterfaces)

                # read the xml to know the connections
        rootElement = ET.fromstring(xml)
        for connection in rootElement.iter('connection'):
            self._connections.append({'fromFmuName':connection.get('fromFmuName'), 'fromVariableName':connection.get('fromVariableName'),
                                      'toFmuName':connection.get('toFmuName'), 'toVariableName':connection.get('toVariableName')})

    def createFmiData(self, valueReference, value):
        fmus = {}
        for i in xrange(len(valueReference)):
            key = str(valueReference[i])[:3]
            if fmus.has_key(key):
                fmu = fmus[key]
            else:
                fmu = FMUData()
                fmus[key] = fmu
            fmu.valueReferences.append(str(valueReference[i])[3:])
            if (value is not None):
                fmu.values.append(value[i])
        return fmus

    def makeFmiGetCall(self, fmus, valueReference, fmiVarType):
        statuses = []
        if fmiVarType == FMIVarType.Real:
            values = FMUInterface2.createfmiRealVector(len(valueReference))
        elif fmiVarType == FMIVarType.Integer or fmiVarType == FMIVarType.Enumeration:
            values = FMUInterface2.createfmiIntegerVector(len(valueReference))
        elif fmiVarType == FMIVarType.Boolean:
            values = FMUInterface2.createfmiBooleanVector(len(valueReference))
        elif fmiVarType == FMIVarType.String:
            values = FMUInterface2.createfmiStringVector(len(valueReference))

        for key, fmuData in fmus.iteritems():
            FMUValueReference = numpy.array(map(numpy.uint32, fmuData.valueReferences))

            if self.FMUInterfaces.has_key(key):
                FMUInterfaceObj = self.FMUInterfaces[key]
                if fmiVarType == FMIVarType.Real:
                    status, value = FMUInterfaceObj.fmiGetReal(FMUValueReference)
                elif fmiVarType == FMIVarType.Integer or fmiVarType == FMIVarType.Enumeration:
                    status, value = FMUInterfaceObj.fmiGetInteger(FMUValueReference)
                elif fmiVarType == FMIVarType.Boolean:
                    status, value = FMUInterfaceObj.fmiGetBoolean(FMUValueReference)
                elif fmiVarType == FMIVarType.String:
                    status, value = FMUInterfaceObj.fmiGetString(FMUValueReference)

                # store the value we get from fmiGet* function against correct value reference
                for i in xrange(len(valueReference)):
                    if key == str(valueReference[i])[:3]:
                        for j in xrange(len(FMUValueReference)):
                            if str(FMUValueReference[j]) == str(valueReference[i])[3:]:
                                values[i] = value[j]
                statuses.append(status)
        return statuses, values

    def makeFmiSetCall(self, fmus, fmiVarType):
        status = []
        for key, fmuData in fmus.iteritems():
            FMUValueReference = numpy.array(map(numpy.uint32, fmuData.valueReferences))

            if self.FMUInterfaces.has_key(key):
                FMUInterfaceObj = self.FMUInterfaces[key]
                if fmiVarType == FMIVarType.Real:
                    FMUValue = numpy.array(map(numpy.float, fmuData.values))
                    status.append(FMUInterfaceObj.fmiSetReal(FMUValueReference, FMUValue))
                elif fmiVarType == FMIVarType.Integer or fmiVarType == FMIVarType.Enumeration:
                    FMUValue = numpy.array(map(numpy.int, fmuData.values))
                    status.append(FMUInterfaceObj.fmiSetInteger(FMUValueReference, FMUValue))
                elif fmiVarType == FMIVarType.Boolean:
                    FMUValue = numpy.array(map(numpy.int, fmuData.values))
                    status.append(FMUInterfaceObj.fmiSetBoolean(FMUValueReference, FMUValue))
                elif fmiVarType == FMIVarType.String:
                    FMUValue = numpy.array(map(numpy.str, fmuData.values))
                    status.append(FMUInterfaceObj.fmiSetString(FMUValueReference, FMUValue))

        return status

    def getValue(self, name):
        ''' Returns the values of the variables given in name;
            name is a String.
        '''
        dataType = self.description.scalarVariables[name].type.basicType
        ScalarVariableReferenceVector = createfmiReferenceVector(1)
        ScalarVariableReferenceVector[0] = self.description.scalarVariables[name].valueReference
        if dataType == 'Real':
            status, values = self.fmiGetReal(ScalarVariableReferenceVector)
            return values[0]
        elif dataType == 'Integer' or dataType == 'Enumeration':
            status, values = self.fmiGetInteger(ScalarVariableReferenceVector)
            return values[0]
        elif dataType == 'Boolean':
            status, values = self.fmiGetBoolean(ScalarVariableReferenceVector)
            return values[0]
        elif dataType == 'String':
            status, values = self.fmiGetString(ScalarVariableReferenceVector)
            return values[0]

    def setValue(self, valueName, valueValue):
        ''' set the variable valueName to valueValue
            @param valueName: name of variable to be set
            @type valueName: string
            @param valueValue: new value
            @type valueValue: any type castable to the type of the variable valueName
        '''
        ScalarVariableReferenceVector = createfmiReferenceVector(1)
        ScalarVariableReferenceVector[0] = self.description.scalarVariables[valueName].valueReference
        if self.description.scalarVariables[valueName].type.basicType == 'Real':
            ScalarVariableValueVector = FMUInterface2.createfmiRealVector(1)
            ScalarVariableValueVector[0] = float(valueValue)
            self.fmiSetReal(ScalarVariableReferenceVector, ScalarVariableValueVector)
        elif self.description.scalarVariables[valueName].type.basicType in ['Integer', 'Enumeration']:
            ScalarVariableValueVector = FMUInterface2.createfmiIntegerVector(1)
            ScalarVariableValueVector[0] = int(valueValue)
            self.fmiSetInteger(ScalarVariableReferenceVector, ScalarVariableValueVector)
        elif self.description.scalarVariables[valueName].type.basicType == 'Boolean':
            ScalarVariableValueVector = FMUInterface2.createfmiBooleanVector(1)
            ScalarVariableValueVector[0] = FMUInterface2.fmiTrue if valueValue == "true" else FMUInterface2.fmiFalse
            self.fmiSetBoolean(ScalarVariableReferenceVector, ScalarVariableValueVector)
        elif self.description.scalarVariables[valueName].type.basicType == 'String':
            ScalarVariableValueVector = FMUInterface2.createfmiStringVector(1)
            ScalarVariableValueVector[0] = unicode(valueValue)
            self.fmiSetString(ScalarVariableReferenceVector, ScalarVariableValueVector)

    def fmiInstantiate(self):
        for key, FMUInterfaceObj in self.FMUInterfaces.iteritems():
            FMUInterfaceObj.fmiInstantiate()

    def free(self):
        for key, FMUInterfaceObj in self.FMUInterfaces.iteritems():
            FMUInterfaceObj.free()

    def freeModelInstance(self):
        ''' Call FMU destructor before being destructed. Just cleaning up. '''
        for key, FMUInterfaceObj in self.FMUInterfaces.iteritems():
            FMUInterfaceObj.freeModelInstance()

    def fmiSetupExperiment(self, toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime):
        status = []
        for key, FMUInterfaceObj in self.FMUInterfaces.iteritems():
            status.append(FMUInterfaceObj.fmiSetupExperiment(toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime))
        return min(status)

    def fmiEnterInitializationMode(self):
        status = []
        for key, FMUInterfaceObj in self.FMUInterfaces.iteritems():
            status.append(FMUInterfaceObj.fmiEnterInitializationMode())
        return min(status)
    
    def fmiExitInitializationMode(self):
        status = []
        for key, FMUInterfaceObj in self.FMUInterfaces.iteritems():
            status.append(FMUInterfaceObj.fmiExitInitializationMode())
        return min(status)

    def fmiTerminate(self):
        status = []
        for key, FMUInterfaceObj in self.FMUInterfaces.iteritems():
            status.append(FMUInterfaceObj.fmiTerminate())
        return min(status)

    def fmiGetReal(self, valueReference):
        fmus = self.createFmiData(valueReference, None)
        statuses, values = self.makeFmiGetCall(fmus, valueReference, FMIVarType.Real)
        return min(statuses), values

    def fmiSetReal(self, valueReference, value):
        fmus = self.createFmiData(valueReference, value)
        status = self.makeFmiSetCall(fmus, FMIVarType.Real)
        return min(status)

    def fmiDoStep(self, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint):
        # resolve connections here
        for i in xrange(len(self._connectionorder)):
            for j in self._connectionorder[i]:
                for ele in xrange(len(self._connections)):
                    if self._connections[ele]['fromFmuName'] == j:
                        fromName = self._connections[ele]['fromFmuName'] + '.' + self._connections[ele]['fromVariableName']
                        fromValue = self.getValue(fromName)
                        toName = self._connections[ele]['toFmuName'] + '.' + self._connections[ele]['toVariableName']
                        self.setValue(toName, fromValue)

        status = []
        for key, FMUInterfaceObj in self.FMUInterfaces.iteritems():
            status.append(FMUInterfaceObj.fmiDoStep(currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint))
        return min(status)
