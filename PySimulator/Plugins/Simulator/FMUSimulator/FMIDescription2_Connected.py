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

import collections

class FMIDescription:
    ''' This object holds the description of an Functional Mock-up Interface for Model Exchange
        It parses an XML-file description as defined by FMI Version 2.0
        The model description (FMI) is usually part of a Functional Mock-Up Unit (FMU)
    '''
    def __init__(self, FMUInterfaces):
        ''' Create FMIDescription from XML-file
            @param xmlFile: File object of the describing XML-Document
        '''
        self.FMUInterfaces = FMUInterfaces
        ''' initialization of variables and more visible public interface '''
        self.me = None
        self.cs = None
        self.defaultStartTime = None
        self.defaultStopTime = None
        self.defaultTolerance = None
        self.defaultStepSize = None
        self.scalarVariables = collections.OrderedDict()

        self.fmiVersion = None
        self.modelName = None
        self.guid = None
        self.description = None
        self.author = None
        self.version = None
        self.copyright = None
        self.license = None
        self.generationTool = None
        self.generationDateAndTime = None
        self.variableNamingConvention = 'flat'
        #self.numberOfEventIndicators = None
        ## not sure 
        self.numberOfEventIndicators = 0
        self.numberOfContinuousStates = 0
        
        for key, FMUInterfaceObj in self.FMUInterfaces.iteritems():
            description = FMUInterfaceObj.description

            self.me = description.me
            self.cs = description.cs
            self.defaultStartTime = description.defaultStartTime
            self.defaultStopTime = description.defaultStopTime
            self.defaultTolerance = description.defaultTolerance
            self.defaultStepSize = description.defaultStepSize

            self.fmiVersion = description.fmiVersion
            self.modelName = description.modelName
            self.guid = description.guid
            self.description = description.description
            self.author = description.author
            self.version = description.version
            self.copyright = description.copyright
            self.license = description.license
            self.generationTool = description.generationTool
            self.generationDateAndTime = description.generationDateAndTime
            self.variableNamingConvention = description.variableNamingConvention
            self.numberOfEventIndicators += int(description.numberOfEventIndicators)
            self.numberOfContinuousStates += description.numberOfContinuousStates
            
            for scalarName, var in description.scalarVariables.iteritems():
                if (scalarName.startswith("der(")):
                    scalarName = "der(" + FMUInterfaceObj.instanceName + '.' + scalarName[4:]
                else:
                    scalarName = FMUInterfaceObj.instanceName + '.' + scalarName
                var.valueReference = key + var.valueReference
                self.scalarVariables[scalarName] = var
