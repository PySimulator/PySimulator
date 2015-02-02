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

import zipfile
import xml.etree.ElementTree as etree
import FMUError


iconImage = 'simulatorFMUSimulator.ico'
modelExtension = ['fmu']

def closeSimulatorPlugin():
    ''' Function is called when closing the plugin (normally when PySimulator is closed).
        It can be used to release resources used by the plugin.
    '''
    pass

def prepareSimulationList(fileName, name, config):
    pass

def getNewModel(modelName=None, modelFileName=None, config=None):  
    
    ''' Open the given fmu-file (read only)'''
    try:
        _file = zipfile.ZipFile(modelFileName[0], 'r')         
    except BaseException as e:
        raise FMUError.FMUError('Error when reading zip-file.\n' + str(e) + '\n')  
        
    ''' Read FMI description file (directly from zip-file)'''
    try:
        xmlFile = _file.open('modelDescription.xml')
    except BaseException as e:
        raise FMUError.FMUError('Error when reading modelDescription.xml\n' + str(e) + '\n')  
            
    try:
        _document = etree.parse(xmlFile)
    except BaseException as e:        
        raise FMUError.FMUError('Error when parsing FMU\'s xml-file.\n' + str(e) + '\n')
    
    _docroot = _document.getroot()           
    fmiVersion = _docroot.get('fmiVersion')        
    if fmiVersion == "1.0":
        import FMUSimulator1        
        return FMUSimulator1.Model(modelName, modelFileName, config)
    elif fmiVersion == "2.0":
        try:
            import FMUSimulator2
        except:
            raise FMUError.FMUError("FMUs 2.0 not yet supported by FMUSimulator.")        
        return FMUSimulator2.Model(modelName, modelFileName, config)

