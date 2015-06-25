#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (C) 2011-2015 German Aerospace Center DLR
(Deutsches Zentrum fuer Luft- und Raumfahrt e.V.),
Institute of System Dynamics and Control
All rights reserved.

This file is licensed under the "BSD New" license
(see also http://opensource.org/licenses/BSD-3-Clause):

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:
   - Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.
   - Redistributions in binary form must reproduce the above copyright notice,
     this list of conditions and the following disclaimer in the documentation
     and/or other materials provided with the distribution.
   - Neither the name of the German Aerospace Center nor the names of its contributors
     may be used to endorse or promote products derived from this software
     without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import zipfile
import collections
import os
from operator import itemgetter

import pyMtsf
from ...Simulator.FMUSimulator.FMIDescription2 import FMIDescription



StandardSeriesForFmi = [pyMtsf.Series('Fixed', None, 'constant', 1), pyMtsf.Series('Continuous', 'Time', 'linear', 100), pyMtsf.Series('Discrete', 'TimeDiscrete', 'constant', 10)]

def convertFromFmi(fmuFilename, fmis=None, ConnectedFmu=None):
  ''' Returns data to initialize an MTSF result file from an FMU.
        The call to initialize an MTSF result file is
            pyMtsf.MTSF(resultFileName, modelDescription, modelVariables, experimentSetup, simpleTypes, units, enumerationsMatrix)
        The missing data is resultFileName and experimentSetup to be specified before initializing the MTSF object.

        Inputs                       Type:
            fmuFilename              String
            fmi                      FMIDescription      [optional]
            if fmi is given, then fmuFilename is ignored. Otherwise the FMI description is loaded from the given file.

        Outputs
           modelDescription          pyMtsf.ModelDescription
           modelVariables            pyMtsf.ModelVariables
           simpleTypes               list of pyMtsf.SimpleType
           units                     list of pyMtsf.Unit
           enumerationsMatrix        list of pyMtsf.Enumeration
  '''

  def _None2Str(x):
     if x is None:
        return ''
     else:
        return x

  '''
  # Load FMIDescription if necessary
  if fmi is None:
        fmuFile = zipfile.ZipFile(os.path.join(os.getcwd(), fmuFilename + u'.fmu'), 'r')
        fmi = FMIDescription(fmuFile.open('modelDescription.xml'))'''
  if ConnectedFmu is None:
      fmis=[fmis]

  # Prepare some variables
  allSeriesNames = [x.name for x in StandardSeriesForFmi]
  variable = collections.OrderedDict()
  simpleTypes = []
  units = []
  enumerationsMatrix = []
  variable['Time'] = pyMtsf.ScalarModelVariable('Continuous Time', 'input', 0, 'continuous', allSeriesNames.index('Continuous'), pyMtsf.StandardCategoryNames.index(pyMtsf.CategoryMapping['Real']), None, 0)
  variable['TimeDiscrete'] = pyMtsf.ScalarModelVariable('Discrete Time at events', 'input', 0, 'discrete', allSeriesNames.index('Discrete'), pyMtsf.StandardCategoryNames.index(pyMtsf.CategoryMapping['Real']), None, 0)
    
  for i in xrange(len(fmis)):  
    fmi=fmis[i]  
    # Searching aliases
    referenceList = [(x, fmi.scalarVariables[x].valueReference) for x in fmi.scalarVariables.keys()]
    referenceList.sort(key = itemgetter(1))
    alias = dict()    
    if len(referenceList) > 1:
        origin = None
        alias[referenceList[0][0]] = None
        for index in xrange(len(referenceList)-1):
            variableName = referenceList[index][0]
            valueReference = referenceList[index][1]
            nextVariableName = referenceList[index+1][0]
            nextValueReference = referenceList[index+1][1]
            if valueReference == nextValueReference:
                if origin is None:
                    origin = variableName
                alias[nextVariableName] = origin 
            else:
                origin = None
                alias[nextVariableName] = None
        
    '''
    # Types and display units
    uniqueSimpleType = []
    for fmiVariableName, fmiVariable in fmi.scalarVariables.iteritems():
        type = fmiVariable.type
        unitList = [_None2Str(type.unit) + _None2Str(type.displayUnit)]
        if fmi.units.has_key(type.unit):
            for displayUnitName, displayUnit in fmi.units[type.unit].iteritems():
                if displayUnitName != type.unit:
                    unitList.append(displayUnitName + '{:.16e}'.format(displayUnit.factor) + '{:.16e}'.format(displayUnit.offset))
            # unitList.sort()
        dataType = type.basicType
        enumerations = ''
        if dataType == 'Enumeration':
            enumerations = ''.join([_None2Str(x[0]) + _None2Str(x[1]) for x in type.item])
        uniqueSimpleType.append((fmiVariableName, type, _None2Str(type.name) + str(pyMtsf.DataType[dataType]) + _None2Str(type.quantity) + str(type.relativeQuantity), ''.join(unitList), enumerations))
    
   
    
    # Simple Types
    uniqueSimpleType.sort(key=itemgetter(3))
    uniqueSimpleType.sort(key=itemgetter(2))
    lastUniqueStr = ''
    rowIndex = dict()
    lastIndex = -1
    uniqueDisplayUnit = []
    uniqueEnumerations = []
    for s in uniqueSimpleType:
        fmiVariableName = s[0]
        type = s[1]
        uniqueStr = s[2] + s[3] + s[4]
        if uniqueStr == lastUniqueStr:
            rowIndex[fmiVariableName] = lastIndex
        else:
            lastUniqueStr = uniqueStr
            lastIndex += 1
            rowIndex[fmiVariableName] = lastIndex
            uniqueDisplayUnit.append((type, lastIndex, s[3]))
            uniqueEnumerations.append((type, lastIndex, s[4]))
            dataType = type.type
            simpleTypes.append(pyMtsf.SimpleType(type.name, pyMtsf.DataType[dataType], type.quantity, type.relativeQuantity, -1, type.description))

    # Units
    uniqueDisplayUnit.sort(key=itemgetter(2))
    lastUniqueStr = ''
    startRow = -1
    for s in uniqueDisplayUnit:
        type = s[0]
        k = s[1]
        uniqueStr = s[2]
        if uniqueStr == lastUniqueStr:
            simpleTypes[k].unitOrEnumerationRow = startRow
        else:
            lastUniqueStr = uniqueStr
            if uniqueStr != '':  # There is a unit definition
                startRow = len(units)
                units.append(pyMtsf.Unit(type.unit, 1.0, 0.0, 0))
                if fmi.units.has_key(type.unit):
                    for displayUnitName, displayUnit in fmi.units[type.unit].iteritems():
                        if displayUnitName != type.unit:
                            if type.displayUnit is not None and type.displayUnit != '' and type.displayUnit == displayUnitName:
                                mode = 2  # DefaultDisplayUnit
                            else:
                                mode = 1  # DisplayUnit
                            units.append(pyMtsf.Unit(displayUnitName, displayUnit.gain, displayUnit.offset, mode))

                simpleTypes[k].unitOrEnumerationRow = startRow
            else:
                startRow = -1

    # Enumerations
    uniqueEnumerations.sort(key=itemgetter(2))
    lastUniqueStr = ''
    startRow = -1
    for s in uniqueEnumerations:
        type = s[0]
        k = s[1]
        uniqueStr = s[2]
        if uniqueStr != '':
            if uniqueStr == lastUniqueStr:
                simpleTypes[k].unitOrEnumerationRow = startRow
            else:
                lastUniqueStr = uniqueStr
                startRow = len(enumerationsMatrix)
                j = 0
                for enum in type.item:
                    j += 1
                    if j == 1:
                        firstEntry = 1
                    else:
                        firstEntry = 0
                    enumerationsMatrix.append(pyMtsf.Enumeration(enum[0], j, enum[1], firstEntry))
                simpleTypes[k].unitOrEnumerationRow = startRow

    '''
    
    simpleTypes.append(pyMtsf.SimpleType('Real', pyMtsf.DataType['Real'], 'Real', False, -1, ''))
    simpleTypes.append(pyMtsf.SimpleType('Integer', pyMtsf.DataType['Integer'], 'Integer', False, -1, ''))
    simpleTypes.append(pyMtsf.SimpleType('Boolean', pyMtsf.DataType['Boolean'], 'Boolean', False, -1, ''))
    

    # Iterate over all fmi-variables
    for fmiVariableName, fmiVariable in fmi.scalarVariables.iteritems():
        variableType = fmiVariable.type.basicType
        if variableType != "String":  # Do not support strings
            aliasNegated = 0 # Not supported in FMI 2.0            
            aliasName = alias[fmiVariableName]           
                        
            categoryIndex = pyMtsf.StandardCategoryNames.index(pyMtsf.CategoryMapping[variableType])
            
            variability = fmiVariable.variability
            if variability == 'tunable':
                variability = 'fixed'
            if variability in ['constant', 'fixed']:
                seriesIndex = allSeriesNames.index('Fixed')                
            elif variability in ['discrete']:
                seriesIndex = allSeriesNames.index('Discrete')
            else:
                seriesIndex = allSeriesNames.index('Continuous')

            causality = fmiVariable.causality
            if causality == 'calculatedParameter':
                causality = 'parameter'
            if causality == 'independent':
                causality = 'option'
                       
            if variableType == 'Real':
                simpleTypeRow = 0
            elif variableType == 'Integer':
                simpleTypeRow = 1
            elif variableType == 'Boolean':
                simpleTypeRow = 2
            elif variableType == 'Enumeration':
                simpleTypeRow = 1  # Integer
            
            variable[fmiVariableName] = pyMtsf.ScalarModelVariable(fmiVariable.description,
                                                    causality,
                                                    simpleTypeRow,
                                                    variability,
                                                    seriesIndex, categoryIndex,
                                                    aliasName, aliasNegated)

    # Some basics for independent time variables
    startRow = len(units)
    units.append(pyMtsf.Unit('s', 1.0, 0.0, 0))
    units.append(pyMtsf.Unit('ms', 0.001, 0.0, 1))
    units.append(pyMtsf.Unit('min', 60.0, 0.0, 1))
    units.append(pyMtsf.Unit('h', 3600.0, 0.0, 1))
    units.append(pyMtsf.Unit('d', 86400.0, 0.0, 1))

    simpleTypes.append(pyMtsf.SimpleType('Time', pyMtsf.DataType["Real"], 'Time', False, startRow, ''))
    variable['Time'].simpleTypeRow = len(simpleTypes) - 1
    variable['TimeDiscrete'].simpleTypeRow = len(simpleTypes) - 1

    modelDescription = pyMtsf.ModelDescription(_None2Str(fmi.modelName), _None2Str(fmi.description), _None2Str(fmi.author), _None2Str(fmi.version), _None2Str(fmi.generationTool), _None2Str(fmi.generationDateAndTime), fmi.variableNamingConvention)
    modelVariables = pyMtsf.ModelVariables(variable, StandardSeriesForFmi, pyMtsf.StandardCategoryNames)

  return modelDescription, modelVariables, simpleTypes, units, enumerationsMatrix




