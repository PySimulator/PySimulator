#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (C) 2014 ITI GmbH
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

# SimulationX constants

# SimWindowStates
simWindowStateNormal = 0
simWindowStateMaximize = 1
simWindowStateMinimize = 2

# SimSpecialToolButtons
simSpecialToolButtonCurve = -1
simSpecialToolButtonOptions = 0
simSpecialToolButtonLast = 1
simSpecialToolButtonNext = 2
simSpecialToolButtonPrev = 3
simSpecialToolButtonFirst = 4

# SimProperty
simIsHidden = 0
simIsSelected = 1
simNoStore = 2
simIsFinal = 3
simIsReplaceable = 4
simIsTypeAssign = 5
simIsBaseClass = 6
simIsToplevel = 7
simIsDisabled = 8
simIsDiscrete = 9
simIsDefaultDiscrete = 10
simIsInput = 11
simIsOutput = 12
simIsFlowVar = 13
simIsPartial = 14
simIsInner = 15
simIsOuter = 16
simIsModified = 17
simIsProtected = 18
simIsDynamic = 19
simValueMark = 20
simIsForCompat = 21
simIsAttribute = 22

# SimEntityClass
simEntity = 0
simNameSpace = 1
simParameter = 2
simRealParameter = 3
simIntParameter = 4
simBoolParameter = 5
simEnumeration = 6
simBoolean = 7
simString = 8
simVariable = 9
simRealVariable = 10
simIntVariable = 11
simBoolVariable = 12
simCurve = 13
simCurveSet = 14
simCurve2D = 15
simCurve3D = 16
simHystereseCurve = 17
simPin = 18
simConservPin = 19
simSignalInputPin = 20
simSignalOutputPin = 21
simPinRef = 22
simTypeAssign = 23
simTypedComponent = 24
simStateReference = 25
simFluidRef = 26
simFluid = 27
simFluidImpl = 28
simFluidMixture = 29
simFluidSet = 30
simAlias = 31
simSimObject = 32
simSimModel = 33
simSimBlock = 34
simFunction = 35
simConnection = 36
simSignalConnection = 37
simConservConnection = 38
simFluidConnection = 39
simActivityGroups = 40
simActivityGroup = 41
simDBGroup = 42
simLibrary = 43
simXSequence = 44
simYSequence = 45
simCurveMap = 46
simCurveAxis = 47
simCurveValues = 48
simGeneralParameter = 49
simGeneralCurve = 50
simSelEnum = 51
simModelicaPin = 52

# SimSolutionStates
simNoSolutionServer = 1
simReady = 2
simInitPrepare = 4
simRunning = 8
simStopped = 16
simFailed = 32
simContinuePrepare = 64
simBlocked = 128

# SimEntityKind
simType = 0
simComponent = 1
simModification = 2
simInstance = 3

# SimModelicaClass
simModClass = 0
simModRecord = 1
simModType = 2
simModConnector = 3
simModModel = 4
simModBlock = 5
simModPackage = 6
simModFunction = 7

# SimInitStates
simUninitialized = 0
simInitBase = 1
simInitAutomatic = 2
simInitManual = 3

# SimSpecialBlock
simSpecialBlockText = 0
simSpecialBlockImage = 1
simSpecialBlockNumber = 2
simSpecialBlockVBar = 3
simSpecialBlockHBar = 0
simSpecialBlockBulb = 4
simSpecialBlockMeter = 5
simSpecialBlockVSlider = 6
simSpecialBlockHSlider = 7
simSpecialBlockSwitch = 8

# SimStringFormat
SimFormatNone = 0
SimFormatDirectory = 1
SimFormatFileName = 2
SimFormatComputer = 3
SimFormatScript = 4
SimFormatExternalProgram = 5
SimFormatInternalModule = 6
SimFormatEvent = 7

# SimVariantsOutputFormat
SimVariantsOutputFormatText = 0
SimVariantsOutputFormatXML = 1
SimVariantsOutputFormatModel = 2

# SimCalculationMode
SimCalculationModeTransient = 0
SimCalculationModeEquilibration = 1

# SimTraceMsgType
SimTraceMsgTypeInfo = 0
SimTraceMsgTypeWarning = 1
SimTraceMsgTypeStop = 2
SimTraceMsgTypeQuestion = 3
SimTraceMsgTypeError = 4
SimTraceMsgTypeDebug = 5
SimTraceMsgTypeNone = 6

# SimTraceMsgLocation
SimTraceMsgCurrent = -1
SimTraceMsgSimulation = 0
SimTraceMsgLocationFile = 1

# SimViewInfoProperty
SimViewInfoPinPosition = 0
SimViewInfoPinDir = 1
SimViewInfoObjSize = 2
SimViewInfoObjImage = 3

# SimStatementKind
simAlgorithm = 0
simEquation = 1

# SimChildFilter
simGetTypes = 0
simGetNoTypes = 1
simGetBases = 2
simGetNoBases = 3
simGetAll = 4

# SimChildFilterFlags
simNoFilterFlags = 0
simResolveAliases = 1
simRecursive = 2

# SimTypeEditableFlags
simTypeNotEditable = 0
simTypeEditable = 1
simTypeDefaultEditable = 2

# SimCodeExportProject
simCodeExportProjectWithoutSolver = 0
simCodeExportProjectEmbeddedSolver = 1
simCodeExportProjectSFunction = 2

# SimCodeExportSaveOutputsApproach
simCodeExportSaveOutputsEqidistant = 0
simCodeExportSaveOutputsAll = 1
simCodeExportSaveOutputsAtleastwithdtProt = 2

# SimCurveMonotony
simDescendMon = -1
simNonMonoton = 0
simAscendMon = 1

# SimCurveInterpolation
simDefaultInterpol = 0
simLinearInterpol = 1
simStairsInterpol = 2
simSplineInterpol = 3
simHyperbolicApprox = 4
simArcApproc = 5

# SimFailureDataModes
simFailurePropagator = 0
simFailureNotRefined = 1
simFailureRefined = 2
simFailureBoth = 3
simFailureConnOr = 4
simFailureConnAnd = 5
