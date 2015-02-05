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


import _ctypes
import ctypes
from ctypes.util import find_library
import platform
import tempfile
import zipfile
import shutil
import os

import numpy

from FMIDescription2 import FMIDescription
import FMUError


''' Declaration of file-type correspondents between Modelica/C and Python
    The mapping is done according to file: fmi2TypesPlatform.h
'''
fmiFalse = 0
fmiTrue = 1
fmiReal = ctypes.c_double
fmiInteger = ctypes.c_int
fmiBoolean = ctypes.c_int
fmiString = ctypes.c_char_p
fmiRealVector = ctypes.POINTER(fmiReal)
fmiIntegerVector = ctypes.POINTER(fmiInteger)
fmiBooleanVector = ctypes.POINTER(fmiBoolean)
fmiStringVector = ctypes.POINTER(fmiString)
fmiBooleanPtr = ctypes.POINTER(fmiBoolean)
fmiComponent = ctypes.c_void_p
fmiComponentEnvironment = ctypes.c_void_p
fmiStatus = ctypes.c_int
fmiValueReference = ctypes.c_uint
fmiValueReferenceVector = ctypes.POINTER(fmiValueReference)
fmiType = ctypes.c_uint
fmiFMUstate = ctypes.c_void_p
fmiFMUstatePtr = ctypes.POINTER(fmiFMUstate)
fmiByte = ctypes.c_char
fmiByteVector = ctypes.POINTER(fmiByte)
fmiStatusKind = ctypes.c_uint



def createfmiRealVector(n):
    return (numpy.ndarray(n, numpy.float))


def createfmiIntegerVector(n):
    return (numpy.ndarray(n, numpy.int))


def createfmiBooleanVector(n):
    return (numpy.ndarray(n, numpy.int))


def createfmiStringVector(n):
    return (fmiString * n)()


def createfmiReferenceVector(n):
    return (numpy.ndarray(n, numpy.uint32))



class fmiEventInfo(ctypes.Structure):
    _fields_ = [('newDiscreteStatesNeeded', fmiBoolean),
                ('terminateSimulation', fmiBoolean),
                ('nominalsOfContinuousStatesChanged', fmiBoolean),
                ('valuesOfContinuousStatesChanged', fmiBoolean),
                ('nextEventTimeDefined', fmiBoolean),
                ('nextEventTime', fmiReal)]


''' C-interface for system functions '''
Logger = ctypes.CFUNCTYPE(None, fmiComponentEnvironment, fmiString, fmiStatus, fmiString, fmiString)
AllocateMemory = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t)
FreeMemory = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
StepFinished = ctypes.CFUNCTYPE(None, ctypes.c_void_p, fmiStatus)
class _fmiCallbackFunctions(ctypes.Structure):
    _fields_ = [('logger', Logger), ('allocateMemory', AllocateMemory), ('freeMemory', FreeMemory), ('stepFinished', StepFinished), ('componentEnvironment', fmiComponentEnvironment)]



class FMUInterface:
    ''' This class encapsulates the FMU C-Interface
        all fmi* functions are a public interface to the FMU-functions        
    '''
    def __init__(self, fileName, parent=None, loggingOn=True, preferredFmiType='me'):
        ''' Load an FMU-File and start a new instance
            @param fileName: complete path and name of FMU-file (.fmu)
            @type fileName: string
        '''
        self.activeFmiType = preferredFmiType  # 'me' or 'cs'
        self.visible = fmiFalse
        
        self._loggingOn = loggingOn
        self._tempDir = tempfile.mkdtemp()     

        ''' Open the given fmu-file (read only)'''
        try:
            self._file = zipfile.ZipFile(fileName, 'r')                  
            self._file.extractall(self._tempDir)
            self._file.close()
            
        except BaseException as e:
            raise FMUError.FMUError('Error when reading zip-file.\n' + str(e) + '\n')

        ''' C requires the unique identification of every FMU instance. Python may just use class intances.
            Still the C functions require an ID. Python associates an ID with every instance of an object.
            We just use this ID for communication with the C-Functions.
        '''
        self.instanceID = str(id(self))
        self.log = []

        ''' Read FMI description file (directly from zip-file)'''
        try:
            xmlFileHandle = open(os.path.join(self._tempDir,'modelDescription.xml'))
        except BaseException as e:
            raise FMUError.FMUError('Error when reading modelDescription.xml\n' + str(e) + '\n')
        
        self.description = FMIDescription(xmlFileHandle)
        if self.description.me is None:
            self.activeFmiType = 'cs'
        elif self.description.cs is None:
            self.activeFmiType = 'me'      
        self._InstantiateModel()
        self._createCInterface()

    def _assembleBinaryName(self, modelName):
        ''' Creates the path within the fmu-file for the binary according to current architecture
            @param modelName: name of model
        '''
        binaryName = 'binaries/'
        if platform.system() == 'Linux':
            binaryName += 'linux'
        elif platform.system() == 'Windows':
            binaryName += 'win'
        else:
            raise FMUError.FMUError('Unable to detect system architecture or architecture not supported.\n')
        if platform.architecture()[0] == '32bit':
            binaryName += '32/'
        elif platform.architecture()[0] == '64bit':
            binaryName += '64/'
        else:
            raise FMUError.FMUError('Unable to detect system architecture or architecture not supported.\n')
        binaryName += modelName
        if platform.system() == 'Linux':
            binaryName += '.so'
        elif platform.system() == 'Windows':
            binaryName += '.dll'
        return binaryName

    def _InstantiateModel(self):
        ''' unpacks the model binary and loads it into memory
        '''
        self._binaryName = os.path.join(self._tempDir, self._assembleBinaryName(self.description.me.modelIdentifier if self.activeFmiType=='me' else self.description.cs.modelIdentifier))       

        def _Logger(c, instanceName, status, category, message):
            if self._loggingOn:
                #f = open("Info.txt", "a")
                #f.write(str(status) + " " + str(category) + " " + message + "\n")
                #f.close()
                print(message)
                
                # self.log.append( (c, instanceName, status, category, message) )        

        
        ''' mapping of memory management functions for FMU to operating system functions, depending on OS.
            For Linux it refers to the std-C library - this should always be present
        '''
        if platform.system() == 'Linux':
            c_lib = ctypes.cdll.LoadLibrary('libc.so.6')
        elif platform.system() == 'Windows':
            c_lib = ctypes.CDLL(find_library('c'))
        else:
            raise FMUError.FMUError('Unknown platform: %s\n' % platform.system())
        c_lib.calloc.restype = ctypes.c_void_p
        c_lib.calloc.argtypes = [ctypes.c_size_t, ctypes.c_size_t]
        c_lib.free.restype = None
        c_lib.free.argtypes = [ctypes.c_void_p]    
        self._fmiCallbackFunctions = _fmiCallbackFunctions(
                                 logger=Logger(_Logger),
                                 allocateMemory=AllocateMemory(c_lib.calloc),
                                 freeMemory=FreeMemory(c_lib.free),
                                 stepFinished=StepFinished(0),
                                 componentEnvironment=0)

        ''' Load instance of library into memory '''
        try:
            self._libraryHandle = ctypes.cdll.LoadLibrary(self._binaryName)._handle
            self._library = ctypes.CDLL(self._binaryName, handle=self._libraryHandle)
        except BaseException as e:
            raise FMUError.FMUError('Error when loading binary from FMU.\n' + str(e) + '\n')


    def fmiInstantiate(self):
        Instantiate = getattr(self._library, 'fmi2Instantiate')
        Instantiate.argtypes = [fmiString, fmiType, fmiString, fmiString, ctypes.POINTER(_fmiCallbackFunctions), fmiBoolean, fmiBoolean]
        Instantiate.restype = fmiComponent
        self._fmiComponent = Instantiate(self.instanceID, 0 if self.activeFmiType=='me' else 1, self.description.guid, 'file:/' + self._tempDir, self._fmiCallbackFunctions, self.visible, fmiTrue if self._loggingOn else fmiFalse)
        if self._fmiComponent == None:
            raise FMUError.FMUError('Instantiation of FMU failed.\n')

    def freeLibrary(self):
        ''' Call FMU destructor before being destructed. Just cleaning up. '''
        if hasattr(self, '_library'):
            self.freeModelInstance()            
            _ctypes.FreeLibrary(self._libraryHandle)        

    def free(self):        
        self.freeLibrary()
        shutil.rmtree(self._tempDir)

    def freeModelInstance(self):
        ''' Call FMU destructor before being destructed. Just cleaning up. '''
        if hasattr(self, '_library') and hasattr(self, '_fmiComponent'):
            if self._fmiComponent is not None:
                FreeModelInstance = getattr(self._library, 'fmi2FreeInstance')
                FreeModelInstance.argtypes = [fmiComponent]
                FreeModelInstance.restype = None
                FreeModelInstance(self._fmiComponent)
                self._fmiComponent = None

    def _createCInterface(self):
        ''' Create interfaces to C-function calls.
            The functions are created locally, exposed by a public afterwards, to simplify later customizations
            for error handling etc.
            The mapping is done according to file: fmi2FunctionTypes.h
        '''
        self._fmiGetTypesPlatform = getattr(self._library, 'fmi2GetTypesPlatform')
        self._fmiGetTypesPlatform.argtypes = None
        self._fmiGetTypesPlatform.restype = fmiString

        self._fmiGetVersion = getattr(self._library, 'fmi2GetVersion')
        self._fmiGetVersion.argtypes = None
        self._fmiGetVersion.restype = fmiString

        self._fmiSetDebugLogging = getattr(self._library, 'fmi2SetDebugLogging')
        self._fmiSetDebugLogging.argtypes = [fmiComponent, fmiBoolean, ctypes.c_size_t, fmiStringVector]
        self._fmiSetDebugLogging.restype = fmiStatus

        self._fmiSetupExperiment = getattr(self._library, 'fmi2SetupExperiment')
        self._fmiSetupExperiment.argtypes = [fmiComponent, fmiBoolean, fmiReal, fmiReal, fmiBoolean, fmiReal]
        self._fmiSetupExperiment.restype = fmiStatus
        
        self._fmiEnterInitializationMode = getattr(self._library, 'fmi2EnterInitializationMode')
        self._fmiEnterInitializationMode.argtypes = [fmiComponent]
        self._fmiEnterInitializationMode.restype = fmiStatus
        
        self._fmiExitInitializationMode = getattr(self._library, 'fmi2ExitInitializationMode')
        self._fmiExitInitializationMode.argtypes = [fmiComponent]
        self._fmiExitInitializationMode.restype = fmiStatus
        
        self._fmiTerminate = getattr(self._library, 'fmi2Terminate')
        self._fmiTerminate.argtypes = [fmiComponent]
        self._fmiTerminate.restype = fmiStatus

        self._fmiReset = getattr(self._library, 'fmi2Reset')
        self._fmiReset.argtypes = [fmiComponent]
        self._fmiReset.restype = fmiStatus
        
        self._fmiGetReal = getattr(self._library, 'fmi2GetReal')
        self._fmiGetReal.argtypes = [fmiComponent, fmiValueReferenceVector, ctypes.c_size_t, fmiRealVector]
        self._fmiGetReal.restype = fmiStatus

        self._fmiGetInteger = getattr(self._library, 'fmi2GetInteger')
        self._fmiGetInteger.argtypes = [fmiComponent, fmiValueReferenceVector, ctypes.c_size_t, fmiIntegerVector]
        self._fmiGetInteger.restype = fmiStatus

        self._fmiGetBoolean = getattr(self._library, 'fmi2GetBoolean')
        self._fmiGetBoolean.argtypes = [fmiComponent, fmiValueReferenceVector, ctypes.c_size_t, fmiBooleanVector]
        self._fmiGetBoolean.restype = fmiStatus

        self._fmiGetString = getattr(self._library, 'fmi2GetString')
        self._fmiGetString.argtypes = [fmiComponent, fmiValueReferenceVector, ctypes.c_size_t, fmiStringVector]
        self._fmiGetString.restype = fmiStatus
        
        self._fmiSetReal = getattr(self._library, 'fmi2SetReal')
        self._fmiSetReal.argtypes = [fmiComponent, fmiValueReferenceVector, ctypes.c_size_t, fmiRealVector]
        self._fmiSetReal.restype = fmiStatus

        self._fmiSetInteger = getattr(self._library, 'fmi2SetInteger')
        self._fmiSetInteger.argtypes = [fmiComponent, fmiValueReferenceVector, ctypes.c_size_t, fmiIntegerVector]
        self._fmiSetInteger.restype = fmiStatus

        self._fmiSetBoolean = getattr(self._library, 'fmi2SetBoolean')
        self._fmiSetBoolean.argtypes = [fmiComponent, fmiValueReferenceVector, ctypes.c_size_t, fmiBooleanVector]
        self._fmiSetBoolean.restype = fmiStatus

        self._fmiSetString = getattr(self._library, 'fmi2SetString')
        self._fmiSetString.argtypes = [fmiComponent, fmiValueReferenceVector, ctypes.c_size_t, fmiStringVector]
        self._fmiSetString.restype = fmiStatus
        
        self._fmiGetFMUstate = getattr(self._library, 'fmi2GetFMUstate')
        self._fmiGetFMUstate.argtypes = [fmiComponent, fmiFMUstatePtr]
        self._fmiGetFMUstate.restype = fmiStatus
        
        self._fmiSetFMUstate = getattr(self._library, 'fmi2SetFMUstate')
        self._fmiSetFMUstate.argtypes = [fmiComponent, fmiFMUstate]
        self._fmiSetFMUstate.restype = fmiStatus
        
        self._fmiFreeFMUstate = getattr(self._library, 'fmi2FreeFMUstate')
        self._fmiFreeFMUstate.argtypes = [fmiComponent, fmiFMUstatePtr]
        self._fmiFreeFMUstate.restype = fmiStatus
        
        self._fmiSerializedFMUstateSize = getattr(self._library, 'fmi2SerializedFMUstateSize')
        self._fmiSerializedFMUstateSize.argtypes = [fmiComponent, fmiFMUstate, ctypes.POINTER(ctypes.c_size_t)]
        self._fmiSerializedFMUstateSize.restype = fmiStatus
        
        self._fmiSerializeFMUstate = getattr(self._library, 'fmi2SerializeFMUstate')
        self._fmiSerializeFMUstate.argtypes = [fmiComponent, fmiFMUstate, fmiByteVector, ctypes.c_size_t]
        self._fmiSerializeFMUstate.restype = fmiStatus
        
        self._fmiDeSerializeFMUstate = getattr(self._library, 'fmi2DeSerializeFMUstate')
        self._fmiDeSerializeFMUstate.argtypes = [fmiComponent, fmiByteVector, ctypes.c_size_t, fmiFMUstatePtr]
        self._fmiDeSerializeFMUstate.restype = fmiStatus
        
        self._fmiGetDirectionalDerivative = getattr(self._library, 'fmi2GetDirectionalDerivative')
        self._fmiGetDirectionalDerivative.argtypes = [fmiComponent, fmiValueReferenceVector, ctypes.c_size_t, fmiValueReferenceVector, ctypes.c_size_t, fmiRealVector, fmiRealVector]
        self._fmiGetDirectionalDerivative.restype = fmiStatus
        
        
        if self.activeFmiType == 'me':
        
            self._fmiEnterEventMode = getattr(self._library, 'fmi2EnterEventMode')
            self._fmiEnterEventMode.argtypes = [fmiComponent]
            self._fmiEnterEventMode.restype = fmiStatus
            
            self._fmiNewDiscreteStates = getattr(self._library, 'fmi2NewDiscreteStates')
            self._fmiNewDiscreteStates.argtypes = [fmiComponent, ctypes.POINTER(fmiEventInfo)]
            self._fmiNewDiscreteStates.restype = fmiStatus
            
            self._fmiEnterContinuousTimeMode = getattr(self._library, 'fmi2EnterContinuousTimeMode')
            self._fmiEnterContinuousTimeMode.argtypes = [fmiComponent]
            self._fmiEnterContinuousTimeMode.restype = fmiStatus
            
            self._fmiCompletedIntegratorStep = getattr(self._library, 'fmi2CompletedIntegratorStep')
            self._fmiCompletedIntegratorStep.argtypes = [fmiComponent, fmiBoolean, fmiBooleanPtr, fmiBooleanPtr]
            self._fmiCompletedIntegratorStep.restype = fmiStatus
            
            self._fmiSetTime = getattr(self._library, 'fmi2SetTime')
            self._fmiSetTime.argtypes = [fmiComponent, fmiReal]
            self._fmiSetTime.restype = fmiStatus
    
            self._fmiSetContinuousStates = getattr(self._library, 'fmi2SetContinuousStates')
            self._fmiSetContinuousStates.argtypes = [fmiComponent, fmiRealVector, ctypes.c_size_t]
            self._fmiSetContinuousStates.restype = fmiStatus
            
            self._fmiGetDerivatives = getattr(self._library, 'fmi2GetDerivatives')
            self._fmiGetDerivatives.argtypes = [fmiComponent, fmiRealVector, ctypes.c_size_t]
            self._fmiGetDerivatives.restype = fmiStatus
    
            self._fmiGetEventIndicators = getattr(self._library, 'fmi2GetEventIndicators')
            self._fmiGetEventIndicators.argtypes = [fmiComponent, fmiRealVector, ctypes.c_size_t]
            self._fmiGetEventIndicators.restype = fmiStatus
            
            self._fmiGetContinuousStates = getattr(self._library, 'fmi2GetContinuousStates')
            self._fmiGetContinuousStates.argtypes = [fmiComponent, fmiRealVector, ctypes.c_size_t]
            self._fmiGetContinuousStates.restype = fmiStatus
    
            self._fmiGetNominalsOfContinuousStates = getattr(self._library, 'fmi2GetNominalsOfContinuousStates')
            self._fmiGetNominalsOfContinuousStates.argtypes = [fmiComponent, fmiRealVector, ctypes.c_size_t]
            self._fmiGetNominalsOfContinuousStates.restype = fmiStatus
            
        elif self.activeFmiType == 'cs':       
        
            self._fmiSetRealInputDerivatives = getattr(self._library, 'fmi2SetRealInputDerivatives')
            self._fmiSetRealInputDerivatives.argtypes = [fmiComponent, fmiValueReferenceVector, ctypes.c_size_t, fmiIntegerVector, fmiRealVector]
            self._fmiSetRealInputDerivatives.restype = fmiStatus
            
            self._fmiGetRealOutputDerivatives = getattr(self._library, 'fmi2GetRealOutputDerivatives')
            self._fmiGetRealOutputDerivatives.argtypes = [fmiComponent, fmiValueReferenceVector, ctypes.c_size_t, fmiIntegerVector, fmiRealVector]
            self._fmiGetRealOutputDerivatives.restype = fmiStatus
            
            self._fmiDoStep = getattr(self._library, 'fmi2DoStep')
            self._fmiDoStep.argtypes = [fmiComponent, fmiReal, fmiReal, fmiBoolean]
            self._fmiDoStep.restype = fmiStatus
            
            self._fmiCancelStep = getattr(self._library, 'fmi2CancelStep')
            self._fmiCancelStep.argtypes = [fmiComponent]
            self._fmiCancelStep.restype = fmiStatus
            
            self._fmiGetStatus = getattr(self._library, 'fmi2GetStatus')
            self._fmiGetStatus.argtypes = [fmiComponent, fmiStatusKind, ctypes.POINTER(fmiStatus)]
            self._fmiGetStatus.restype = fmiStatus
            
            self._fmiGetRealStatus = getattr(self._library, 'fmi2GetRealStatus')
            self._fmiGetRealStatus.argtypes = [fmiComponent, fmiStatusKind, ctypes.POINTER(fmiReal)]
            self._fmiGetRealStatus.restype = fmiStatus
            
            self._fmiGetIntegerStatus = getattr(self._library, 'fmi2GetIntegerStatus')
            self._fmiGetIntegerStatus.argtypes = [fmiComponent, fmiStatusKind, ctypes.POINTER(fmiInteger)]
            self._fmiGetIntegerStatus.restype = fmiStatus
     
            self._fmiGetBooleanStatus = getattr(self._library, 'fmi2GetBooleanStatus')
            self._fmiGetBooleanStatus.argtypes = [fmiComponent, fmiStatusKind, ctypes.POINTER(fmiBoolean)]
            self._fmiGetBooleanStatus.restype = fmiStatus
     
            self._fmiGetStringStatus = getattr(self._library, 'fmi2GetStringStatus')
            self._fmiGetStringStatus.argtypes = [fmiComponent, fmiStatusKind, ctypes.POINTER(fmiString)]
            self._fmiGetStringStatus.restype = fmiStatus
 
              
    def fmiGetTypesPlatform(self):
        return self._fmiGetTypesPlatform()

    def fmiGetVersion(self):
        return self._fmiGetVersion()

    def fmiSetDebugLogging(self, onOff, nCategories=0, categories=[]):
        return self._fmiSetDebugLogging(self._fmiComponent, fmiTrue if onOff else fmiFalse, nCategories, categories.ctypes.data_as(fmiStringVector))

    def fmiSetupExperiment(self, toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime):
        return self._fmiSetupExperiment(self._fmiComponent, toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime)
    
    def fmiEnterInitializationMode(self):
        return self._fmiEnterInitializationMode(self._fmiComponent)
    
    def fmiExitInitializationMode(self):
        return self._fmiExitInitializationMode(self._fmiComponent)
    
    def fmiTerminate(self):
        return self._fmiTerminate(self._fmiComponent)
    
    def fmiReset(self):
        return self._fmiReset(self._fmiComponent)
    
    def fmiGetReal(self, valueReference):
        value = createfmiRealVector(len(valueReference))
        status = self._fmiGetReal(self._fmiComponent, valueReference.ctypes.data_as(fmiValueReferenceVector), len(valueReference), value.ctypes.data_as(fmiRealVector))
        return status, value

    def fmiGetInteger(self, valueReference):
        value = createfmiIntegerVector(len(valueReference))
        status = self._fmiGetInteger(self._fmiComponent, valueReference.ctypes.data_as(fmiValueReferenceVector), len(valueReference), value.ctypes.data_as(fmiIntegerVector))
        return status, value

    def fmiGetBoolean(self, valueReference):
        value = createfmiBooleanVector(len(valueReference))
        status = self._fmiGetBoolean(self._fmiComponent, valueReference.ctypes.data_as(fmiValueReferenceVector), len(valueReference), value.ctypes.data_as(fmiBooleanVector))
        return status, value

    def fmiGetString(self, valueReference):
        value = createfmiStringVector(len(valueReference))
        status = self._fmiGetString(self._fmiComponent, valueReference.ctypes.data_as(fmiValueReferenceVector), len(valueReference), value)
        return status, value
   
    def fmiSetReal(self, valueReference, value):
        if len(valueReference) != len(value):
            raise IndexError('length of valueReference not corresponding to length of value')
        return self._fmiSetReal(self._fmiComponent, valueReference.ctypes.data_as(fmiValueReferenceVector), len(valueReference), value.ctypes.data_as(fmiRealVector))

    def fmiSetInteger(self, valueReference, value):
        if len(valueReference) != len(value):
            raise IndexError('length of valueReference not corresponding to length of value')
        return self._fmiSetInteger(self._fmiComponent, valueReference.ctypes.data_as(fmiValueReferenceVector), len(valueReference), value.ctypes.data_as(fmiIntegerVector))

    def fmiSetBoolean(self, valueReference, value):
        if len(valueReference) != len(value):
            raise IndexError('length of valueReference not corresponding to length of value')
        return self._fmiSetBoolean(self._fmiComponent, valueReference.ctypes.data_as(fmiValueReferenceVector), len(valueReference), value.ctypes.data_as(fmiBooleanVector))

    def fmiSetString(self, valueReference, value):
        if len(valueReference) != len(value):
            raise IndexError('length of valueReference not corresponding to length of value')
        return self._fmiSetString(self._fmiComponent, valueReference.ctypes.data_as(fmiValueReferenceVector), len(valueReference), value.ctypes.data_as(fmiStringVector))

    def fmiGetFMUstate(self):              
        FMUstate = ctypes.c_void_p()        
        status = self._fmiGetFMUstate(self._fmiComponent, ctypes.byref(FMUstate))        
        return status, FMUstate
 
    def fmiSetFMUstate(self, FMUstate):
        status = self._fmiSetFMUstate(self._fmiComponent, FMUstate)
        return status
   
    def fmiFreeFMUstate(self, FMUstate):
        status = self._fmiFreeFMUstate(self._fmiComponent, ctypes.byref(FMUstate))
        return status, FMUstate
   
    def fmiSerializedFMUstateSize(self, FMUstate):
        size = ctypes.c_size_t()
        status = self._fmiSerializedFMUstateSize(self._fmiComponent, FMUstate, ctypes.byref(size))
        return status, size
    
    def fmiSerializeFMUstate(self, FMUstate, size):        
        byteVector = (fmiByte*size.value)()        
        status = self._fmiSerializeFMUstate(self._fmiComponent, FMUstate, byteVector, size)
        return status, byteVector
   
    def fmiDeSerializeFMUstate(self, byteVector):
        FMUstate = ctypes.c_void_p()
        size = ctypes.c_size_t(len(byteVector))
        status = self._fmiDeSerializeFMUstate(self._fmiComponent, byteVector, size, ctypes.byref(FMUstate))
        return status, FMUstate
    
    def fmiGetDirectionalDerivative(self, vUnknown_ref, vKnown_ref, dvKnown):
        dvUnknown = createfmiRealVector(len(vUnknown_ref))
        status = self._fmiGetDirectionalDerivative(self._fmiComponent, vUnknown_ref.ctypes.data_as(fmiValueReferenceVector), len(vUnknown_ref), 
                                                   vKnown_ref.ctypes.data_as(fmiValueReferenceVector), len(vKnown_ref), dvKnown.ctypes.data_as(fmiRealVector), dvUnknown)
        return status, dvUnknown
    
    def fmiEnterEventMode(self):
        status = self._fmiEnterEventMode(self._fmiComponent)
        return status
    
    def fmiNewDiscreteStates(self):
        eventInfo = fmiEventInfo()
        status = self._fmiNewDiscreteStates(self._fmiComponent, eventInfo)
        return status, eventInfo
    
    def fmiEnterContinuousTimeMode(self):
        status = self._fmiEnterContinuousTimeMode(self._fmiComponent)
        return status
    
    def fmiCompletedIntegratorStep(self, noSetFMUStatePriorToCurrentPoint):
        enterEventMode = fmiBoolean()
        terminateSimulation = fmiBoolean()        
        status = self._fmiCompletedIntegratorStep(self._fmiComponent, fmiTrue if noSetFMUStatePriorToCurrentPoint else fmiFalse, 
                                                  ctypes.byref(enterEventMode), ctypes.byref(terminateSimulation))
        return status, enterEventMode.value==fmiTrue, terminateSimulation.value==fmiTrue

    def fmiSetTime(self, time):
        return self._fmiSetTime(self._fmiComponent, time)

    def fmiSetContinuousStates(self, vector):
        if len(vector) != self.description.numberOfContinuousStates:
            raise IndexError('length of vector not corresponding to length of models continuous states vector')
        status = self._fmiSetContinuousStates(self._fmiComponent, vector.ctypes.data_as(fmiRealVector), len(vector))
        return status

    def fmiGetDerivatives(self):
        ret = createfmiRealVector(self.description.numberOfContinuousStates)
        status = self._fmiGetDerivatives(self._fmiComponent, ret.ctypes.data_as(fmiRealVector), self.description.numberOfContinuousStates)
        return status, ret

    def fmiGetEventIndicators(self):
        ret = createfmiRealVector(int(self.description.numberOfEventIndicators))
        status = self._fmiGetEventIndicators(self._fmiComponent, ret.ctypes.data_as(fmiRealVector), int(self.description.numberOfEventIndicators))
        return status, ret
   
    def fmiGetContinuousStates(self):
        value = createfmiRealVector(self.description.numberOfContinuousStates)
        status = self._fmiGetContinuousStates(self._fmiComponent, value.ctypes.data_as(fmiRealVector), self.description.numberOfContinuousStates)
        return status, value

    def fmiGetNominalsOfContinuousStates(self):
        value = createfmiRealVector(self.description.numberOfContinuousStates)
        status = self._fmiGetNominalsOfContinuousStates(self._fmiComponent, value.ctypes.data_as(fmiRealVector), self.description.numberOfContinuousStates)
        return status, value
    
    def fmiSetRealInputDerivatives(self, valueReference, order, value):
        status = self._fmiSetRealInputDerivatives(self._fmiComponent, valueReference.ctypes.data_as(fmiValueReferenceVector), len(valueReference), 
                                                  order.ctypes.data_as(fmiIntegerVector), value.ctypes.data_as(fmiRealVector))
        return status
    
    def fmiGetRealOutputDerivatives(self, valueReference, order):
        value = createfmiRealVector(len(valueReference))
        status = self._fmiGetRealOutputDerivatives(self._fmiComponent, valueReference.ctypes.data_as(fmiValueReferenceVector), len(valueReference), 
                                                  order.ctypes.data_as(fmiIntegerVector), value.ctypes.data_as(fmiRealVector))
        return status, value
    
    def fmiDoStep(self, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint):
        status = self._fmiDoStep(self._fmiComponent, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint)
        return status
        
    def fmiCancelStep(self):
        status = self._fmiCancelStep(self._fmiComponent)
        return status
    
    def fmiGetStatus(self, kind):
        value = fmiStatus()        
        status = self._fmiGetStatus(self._fmiComponent, kind, ctypes.byref(value))
        return status, value.value
    
    def fmiGetRealStatus(self, kind):
        value = fmiReal()
        status = self._fmiGetRealStatus(self._fmiComponent, kind, ctypes.byref(value))
        return status, value.value 

    def fmiGetIntegerStatus(self, kind):
        value = fmiInteger()
        status = self._fmiGetIntegerStatus(self._fmiComponent, kind, ctypes.byref(value))
        return status, value.value
    
    def fmiGetBooleanStatus(self, kind):
        value = fmiBoolean()
        status = self._fmiGetBooleanStatus(self._fmiComponent, kind, ctypes.byref(value))
        return status, value.value
    
    def fmiGetStringStatus(self, kind):
        value = fmiString()
        status = self._fmiGetStringStatus(self._fmiComponent, kind, ctypes.byref(value))
        return status, value.value
        



if __name__ == '__main__':
    fmu = FMUInterface('d:/Rectifier.fmu')
    fmu.fmiInstantiate()
    fmu.fmiSetupExperiment(fmiTrue, 1e-6, 0.0, fmiTrue, 1.0)
    fmu.fmiEnterInitializationMode()
    fmu.fmiExitInitializationMode()   
    status, state = fmu.fmiGetFMUstate()
    print status, state
    
    fmu.fmiSetFMUstate(state)
    
    
    status, size = fmu.fmiSerializedFMUstateSize(state)
    status, vec = fmu.fmiSerializeFMUstate(state, size)
    
    status, state = fmu.fmiFreeFMUstate(state)
    print status, state  
    
    
    fmu.free()

