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


import collections

import FMUError
import xml.etree.ElementTree as etree


def defaultNone(x, default):
    if x is None:
        return default
    else:
        return x
    
def getAttribute(root, attr):
    a = root.get(attr)
    if a is None:
        pass
    return a

class EnumerationItem:
    def __init__(self):
        self.value = None
        self.description = None



class SimpleType:
    ''' Class for description of simple data types in FMI
        Some values are optional, them not being defined is signaled by a value of None
    '''
    def __init__(self, x):
        ''' Populate data from x
            @type x: ElemenTree element holding a type description
        '''
        self.basicType = str(x.tag)
        self.description = x.get('description')
        self.quantity = x.get('quantity')
        self.unit = x.get('unit')
        self.displayUnit = x.get('displayUnit')
        self.relativeQuantity = defaultNone(x.get('relativeQuantity'), 'false')
        self.min = x.get('min')
        self.max = x.get('max')
        self.nominal = x.get('nominal')        
        self.unbounded = defaultNone(x.get('unbounded'), 'false')
        self.item = dict()
        for item in x.findall('Item'):
            name = item.get('name')
            self.item[name] = EnumerationItem()
            self.item[name].value = item.get('value')
            self.item[name].description = item.get('description')
        
        
    

class ScalarVariableType(SimpleType):
    ''' Class for description of data types in FMI scalar variables
        Some values are optional, them not being defined is signaled by a value of None
    '''
    def __init__(self, x):
        ''' Populate data from x
            @type x: ElemenTree element holding a type description
        '''                
        SimpleType.__init__(self, x)
        self.declaredType = x.get('declaredType')       
        self.start = x.get('start')
        self.derivative = x.get('derivative')
        self.reinit = defaultNone(x.get('reinit'), 'false')
        
        
    def updateDefaults(self, defaults):
        ''' Update some elements of the class by default values given in a SimpleType class
            @type defaults: SimpleType class holding a type description
        '''       
        if defaults.quantity is not None:
            self.quantity = defaults.quantity
        if defaults.unit is not None:
            self.unit = defaults.unit
        if defaults.displayUnit is not None:
            self.displayUnit = defaults.displayUnit
        if defaults.relativeQuantity is not None:
            self.relativeQuantity = defaults.relativeQuantity
        if defaults.min is not None:
            self.min = defaults.min
        if defaults.max is not None:
            self.max = defaults.max
        if defaults.nominal is not None:
            self.nominal = defaults.nominal
        if defaults.unbounded is not None:
            self.unbounded = defaults.unbounded
        

class FMIScalarVariable:
    ''' Class for description of Scalar Variables
    '''
    def __init__(self, scalarVariableType=None, reference=None, description=None, causality=None, variability=None, initial=None, canHandleMultipleSetPerTimeInstant=None, annotations=None):
        self.type = scalarVariableType
        self.valueReference = reference
        self.description = description
        self.causality = causality
        self.variability = variability        
        self.initial = initial
        self.canHandleMultipleSetPerTimeInstant = canHandleMultipleSetPerTimeInstant
        self.annotations = annotations


class FMITypeAttributes:
    def __init__(self):
        self.modelIdentifier = None
        self.needsExecutionTool = 'false'       
        self.canBeInstantiatedOnlyOncePerProcess = 'false'
        self.canNotUseMemoryManagementFunctions = 'false'
        self.canGetAndSetFMUstate = 'false'
        self.canSerializeFMUstate = 'false'
        self.providesDirectionalDerivative = 'false'        
        self.sourceFile = []

class ModelExchange(FMITypeAttributes):
    def __init__(self):
        FMITypeAttributes.__init__(self)
        self. completedIntegratorStepNotNeeded = 'false'        

    
class CoSimulation(FMITypeAttributes):
    def __init__(self):
        FMITypeAttributes.__init__(self)
        self.canHandleVariableCommunicationStepSize = 'false'
        self.canInterpolateInputs = 'false'
        self.maxOutputDerivativeOrder = '0'
        self.canRunAsynchronuously = 'false'  
        

class Unit:
    def __init__(self):
        self.kg = 0
        self.m = 0
        self.s = 0
        self.A = 0
        self.K = 0
        self.mol = 0
        self.cd = 0
        self.rad = 0
        self.factor = 0
        self.offset = 0        
        self.displayUnit = dict()        
    def update(self, member, value):
        if value is not None:
            if member in ['factor', 'offset']:
                setattr(self, member, float(value))
            else:
                setattr(self, member, int(value))
        
class DisplayUnit:
    def __init__(self):
        self.factor = 1.0
        self.offset = 0.0
    def update(self, member, value):
        if value is not None:
            setattr(self, member, float(value))
      
      
class DependencyStructure:
    def __init__(self, index=None, dependencies=None, dependenciesKind=None):
        self.index = index
        self.dependencies = dependencies
        self.dependenciesKind = dependenciesKind
          
class ModelStructure:
    def __init__(self):
        self.outputs = []
        self.derivatives = []
        self.initialUnknowns = []


class FMIDescription:
    ''' This object holds the description of an Functional Mock-up Interface for Model Exchange
        It parses an XML-file description as defined by FMI Version 2.0
        The model description (FMI) is usually part of a Functional Mock-Up Unit (FMU)
    '''
    def __init__(self, xmlFile):
        ''' Create FMIDescription from XML-file
            @param xmlFile: File object of the describing XML-Document
        '''

        ''' initialization of variables and more visible public interface '''
        self.me = None
        self.cs = None        
        self.units = {}
        self.types = {}
        self.logCategories = {}
        self.defaultStartTime = None
        self.defaultStopTime = None
        self.defaultTolerance = None
        self.defaultStepSize = None
        self.vendorAnnotations = []
        self.scalarVariables = collections.OrderedDict()
        self.modelStructure = None        
        
        
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
        self.numberOfEventIndicators = None
        
        
        if xmlFile is None:
            return

        ''' Parse the file '''
        try:
            _document = etree.parse(xmlFile)
        except BaseException as e:
            print 'Error when parsing FMU\'s xml-file. Error: ', e
            raise FMUError.FMUError('Error when parsing FMU\'s xml-file.\n' + str(e) + '\n')
        _docroot = _document.getroot()
        if _docroot.tag != 'fmiModelDescription':
            raise FMUError.FMUError('XML-File type not recognized!\n')        
        
        ''' Parse the global FMI Model Description Attributes '''
        self.fmiVersion = _docroot.get('fmiVersion')
        self.modelName = _docroot.get('modelName')       
        self.guid = _docroot.get('guid')
        self.description = _docroot.get('description')
        self.author = _docroot.get('author')
        self.version = _docroot.get('version')
        self.copyright = _docroot.get('copyright')
        self.license = _docroot.get('license')            
        self.generationTool = _docroot.get('generationTool')
        self.generationDateAndTime = _docroot.get('generationDateAndTime')
        self.variableNamingConvention = _docroot.get('variableNamingConvention')           
        self.numberOfEventIndicators = _docroot.get('numberOfEventIndicators')
      
        
        ''' Child nodes are each parsed by their own subroutine '''
        for child in _docroot:
            if child.tag == 'ModelExchange':
                self._parseModelExchange(child)
            elif child.tag == 'CoSimulation':
                self._parseCoSimulation(child)            
            elif child.tag == 'UnitDefinitions':
                self._parseUnitDefinitions(child)
            elif child.tag == 'TypeDefinitions':
                self._parseTypeDefinitions(child)
            elif child.tag == 'LogCategories':
                self._parseLogCategories(child)
            elif child.tag == 'DefaultExperiment':
                self._parseDefaultExperiment(child)            
            elif child.tag == 'VendorAnnotations':
                self._parseVendorAnnotations(child)        
            elif child.tag == 'ModelVariables':
                self._parseModelVariables(child)
            elif child.tag == 'ModelStructure':
                self._parseModelStructure(child)
            else:
                print('Unknown tag in FMI Model: %s\n' % child.tag)
        
        ''' Update type values in scalar variables - use defaults from simple type definitions '''
        for var in self.scalarVariables.itervalues():
            if var.type.declaredType is not None:
                var.type.updateDefaults(self.types[var.type.declaredType])
                
        self.numberOfContinuousStates = len(self.modelStructure.derivatives) if self.modelStructure is not None else 0 

    def _parseMEandCS(self, root, output):        
        output.modelIdentifier = getAttribute(root, 'modelIdentifier')
        output.needsExecutionTool = defaultNone(getAttribute(root, 'needsExecutionTool'), 'false')
        output.canBeInstantiatedOnlyOncePerProcess = defaultNone(getAttribute(root, 'canBeInstantiatedOnlyOncePerProcess'), 'false')
        output.canNotUseMemoryManagementFunctions = defaultNone(getAttribute(root,'canNotUseMemoryManagementFunctions'), 'false')
        output.canGetAndSetFMUstate = defaultNone(getAttribute(root,'canGetAndSetFMUstate'), 'false')
        output.canSerializeFMUstate = defaultNone(getAttribute(root,'canSerializeFMUstate'), 'false')
        output.providesDirectionalDerivative = defaultNone(getAttribute(root,'providesDirectionalDerivative'), 'false')
        
        output.sourceFile = []
        children = root._children
        for child in children:
            if child.tag == 'SourceFiles':
                allFiles = child._children
                for x in allFiles:                    
                    output.sourceFile.append(x.get('name'))
            else:
                print('Unknown tag in FMI model: %s\n' % child.tag)
        
    def _parseModelExchange(self, root):
        self.me = ModelExchange()
        self._parseMEandCS(root, self.me)
        self.me.completedIntegratorStepNotNeeded = defaultNone(getAttribute(root,'completedIntegratorStepNotNeeded'), 'false')
    
    def _parseCoSimulation(self, root):
        self.cs = CoSimulation()
        self._parseMEandCS(root, self.cs)        
        self.cs.canHandleVariableCommunicationStepSize = defaultNone(getAttribute(root,'canHandleVariableCommunicationStepSize'), 'false')
        self.cs.canInterpolateInputs = defaultNone(getAttribute(root,'canInterpolateInputs'), 'false')
        self.cs.maxOutputDerivativeOrder = defaultNone(getAttribute(root,'maxOutputDerivativeOrder'), '0')
        self.cs.canRunAsynchronuously = defaultNone(getAttribute(root,'canRunAsynchronuously'), 'false')

    def _parseUnitDefinitions(self, root):
        ''' Parse Unit definitions.
            @param root: ElemenTree element holding unit definitions
        '''
        for unit in root:
            if unit.tag != 'Unit':
                print('Unknown tag in unit definitions of FMI Model: %s\n' % unit.tag)
            else:
                unitName = unit.get('name')
                self.units[unitName] = Unit()                
                children = unit._children
                for child in children:
                    if child.tag == 'BaseUnit':
                        self.units[unitName].update('kg', child.get('kg'))
                        self.units[unitName].update('m', child.get('m'))
                        self.units[unitName].update('s', child.get('s'))
                        self.units[unitName].update('A', child.get('A'))
                        self.units[unitName].update('K', child.get('K'))
                        self.units[unitName].update('mol', child.get('mol'))
                        self.units[unitName].update('cd', child.get('cd'))
                        self.units[unitName].update('rad', child.get('rad'))                 
                        self.units[unitName].update('factor', child.get('factor'))                        
                        self.units[unitName].update('offset', child.get('offset'))                        
                    elif child.tag == 'DisplayUnit':
                        dUnitName =  child.get('name')
                        self.units[unitName].displayUnit[dUnitName] = DisplayUnit()
                        self.units[unitName].displayUnit[dUnitName].update('factor', child.get('factor'))
                        self.units[unitName].displayUnit[dUnitName].update('offset', child.get('offset'))                        
                    else:
                        print('Unknown tag in unit definitions of FMI Model: %s\n' % child.tag)         
            
            
    
    def _parseTypeDefinitions(self, root):
        ''' Parse Type descriptions.
            @type root: ElemenTree element holding type definitions
        '''
        ''' Most functionality has be encapsulated in FMIType for Scalar Variables use a similar definition of types.
            According to standard, type has one and only one child. It can therefore be accessed safely by type[0]
        '''
        for x in root:
            if x.tag != 'SimpleType':
                ''' The current FMI definition only knows type SimpleType '''
                raise FMUError.FMUError('TypeDefinitions defining non-type.\n')
            if len(x) != 1:
                raise FMUError.FMUError('Bad type description for: ' + x + '\n')
            self.types[x.get('name')] = SimpleType(x[0])    
    
    
    def _parseLogCategories(self, root):
        for child in root:
            if child.tag == 'Category':
                self.logCategories[child.get('name')] = child.get('description')
            else:
                print('Unknown tag in logCategories for FMI model: %s\n' % child.tag)
                
    
    def _parseDefaultExperiment(self, child):
        self.defaultStartTime = child.get('startTime')
        self.defaultStopTime = child.get('stopTime')
        self.defaultTolerance = child.get('tolerance')
        self.defaultStepSize = child.get('stepSize')
    
    def _parseVendorAnnotations(self, root):
        # Only the tool names are read
        for child in root:
            if child.tag == 'Tool':
                self.vendorAnnotations.append(child.get('name'))
            else:
                print('Unknown tag in VendorAnnotations for FMI model: %s\n' % child.tag)
       
    def _parseModelVariables(self, root):
        ''' Parse Model Variables
            @type root: ElemenTree element holding Model Variable definitions
        '''
        ''' See documentation for: '_parseTypes' '''
        for scalar in root:
            if scalar.tag != 'ScalarVariable':
                ''' The current FMI definition only knows scalar values '''
                raise FMUError.FMUError('ModelVariables definition unknown.\n')
            annotations = []
            for x in scalar:
                if x.tag == 'Annotations':
                    # Only name of tools are read
                    for y in x:
                        annotations.append(y.get('name'))                    
                else:
                    scalarVariableType = ScalarVariableType(x)            
            
            scalarName = scalar.get('name')
            reference = scalar.get('valueReference')
            description = scalar.get('description')
            causality = defaultNone(scalar.get('causality'), 'local')
            variability = defaultNone(scalar.get('variability'), 'continuous')            
            initial = scalar.get('initial')
            canHandleMultipleSetPerTimeInstant = scalar.get('canHandleMultipleSetPerTimeInstant')            
            annotations = annotations
            self.scalarVariables[scalarName] = FMIScalarVariable(scalarVariableType, reference, description, causality, variability, initial, canHandleMultipleSetPerTimeInstant, annotations)

    
    def _parseModelStructure(self, root):
        self.modelStructure = ModelStructure()        
        for child in root:
            if child.tag == 'Outputs':
                for x in child:
                    if x.tag == 'Unknown':
                        self.modelStructure.outputs.append(DependencyStructure(x.get('index'), x.get('dependencies'), x.get('dependenciesKind')))                        
                    else:
                        print('Unknown tag in ModelStructure for FMI model: %s\n' % x.tag)                        
                
            elif child.tag == 'Derivatives':
                for x in child:
                    if x.tag == 'Unknown':
                        self.modelStructure.derivatives.append(DependencyStructure(x.get('index'), x.get('dependencies'), x.get('dependenciesKind')))                        
                    else:
                        print('Unknown tag in ModelStructure for FMI model: %s\n' % x.tag)
                
            elif child.tag == 'InitialUnknowns':
                for x in child:
                    if x.tag == 'Unknown':
                        self.modelStructure.initialUnknowns.append(DependencyStructure(x.get('index'), x.get('dependencies'), x.get('dependenciesKind')))                        
                    else:
                        print('Unknown tag in ModelStructure for FMI model: %s\n' % x.tag)                
            else:
                print('Unknown tag in ModelStructure for FMI model: %s\n' % child.tag)
                
                
                
                
    
     

    


if __name__ == '__main__':
    ''' This is for testing and development only! '''

    ''' Read FMI description file (directly from zip-file)'''    
    fmi = FMIDescription(open('d:/modelDescription_Rectifier.xml'))

    print "Attributes"
    print "*************"
    print fmi.fmiVersion
    print fmi.guid
    print fmi.generationTool

    print "Units"
    print "*************"
    print fmi.units.keys()
    print fmi.units['K'].K, fmi.units['K'].A
    print fmi.units['K'].displayUnit['degC'].factor, fmi.units['K'].displayUnit['degC'].offset
  

    print "Types"
    print "*************"
    print fmi.types.keys()
    print fmi.types['Modelica.SIunits.Voltage'].basicType
    print fmi.types['Modelica.SIunits.Voltage'].description

    print "Vendor Annotations"
    print "*************"
    print fmi.vendorAnnotations

    print "ScalarVariables"
    print "***************"
    print fmi.scalarVariables.keys()
    print fmi.scalarVariables['Capacitor1.p.v'].type
    print fmi.scalarVariables['Capacitor1.p.v'].type.unit
    print fmi.scalarVariables['Capacitor1.p.v'].valueReference
    print fmi.scalarVariables['Capacitor1.p.v'].variability
    
    
    print "ModelStructure"
    print "***************"
    print fmi.modelStructure.outputs[0].index
    print fmi.modelStructure.outputs[0].dependencies 
    print fmi.modelStructure.outputs[0].dependenciesKind
