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
This Simulator plugin can load Modelica models (assumed Dymola is installed)
and simulation executable of Dymola. It runs the executable and loads the result file.
***************************
'''


import os, sys, string
import subprocess
from PySide import QtGui

import Plugins.Simulator.SimulatorBase
import Plugins.SimulationResult.DymolaMat.DymolaMat as DymolaMat

iconImage = 'simulatorDymola.ico'
modelExtension = ['mo', 'moe', 'exe']
def closeSimulatorPlugin():
    pass

class Model(Plugins.Simulator.SimulatorBase.Model):

    def __init__(self, modelName, modelFileName, config):

        Plugins.Simulator.SimulatorBase.Model.__init__(self, modelName, modelFileName, 'Dymola', config)

        # A dummy object to get result properties:
        self.integrationResults = DymolaMat.Results('')
        self.integrationSettings.resultFileExtension = 'mat'

        self._availableIntegrationAlgorithms = ["Dassl", "Explicit Euler", "Lsodar", "Rkfix2", "Rkfix3", "Rkfix4"]
        '''
        ,"Radau IIa","Esdirk23a","Esdirk34a","Esdirk45a",
        "Dopri45","Dopri853","Sdirk34hw","Cerk23","Cerk34","Cerk45"]
        '''
        self._IntegrationAlgorithmHasFixedStepSize = [False, True, False, True, True, True] #, False, False, False, False, False, False, False, False, False, False]
        self._IntegrationAlgorithmCanProvideStepSizeResults = [False, False, False, False, False, False] #, False, False, False, False, False, False, False, False, False, False]

        self.integrationSettings.algorithmName = self._availableIntegrationAlgorithms[0]

        # Compile model, generate initialization file (including all variable names) and read this file
        self._compileModel()        
        subprocess.call((self.fileNameExec + ' -ib dsin.mat').encode(sys.getfilesystemencoding()))
        self._initialResult = DymolaMat.loadDymolaInit(os.path.abspath('.') + '/dsin.mat')


    def setVariableTree(self):
        ''' Generate variable tree from initialization file
        '''
        for i in xrange(len(self._initialResult.name)):
            if   self._initialResult.value[i,4] == 1:
                causality = 'parameter'
            elif self._initialResult.value[i,4] == 2:
                causality = 'state'
            elif self._initialResult.value[i,4] == 3:
                causality = 'stateDerivative'
            elif self._initialResult.value[i,4] == 4:
                causality = 'output'
            elif self._initialResult.value[i,4] == 5:
                causality = 'input'
            else:
                causality = 'local'

            # De-chiffre of Dymola's initialValue matrix, see also Dymola/source/adymosim.h
            # Set variable properties accordingly.
            binStr = bin(int(self._initialResult.value[i,5]))[2:]
            binStr = '0'*(15-len(binStr)) + binStr
            variability = 'continuous'
            if causality == 'parameter':
                variability = 'fixed'
            elif binStr[-7] == '1': # 64
                variability = 'discrete'

            valueEdit = False
            if int(self._initialResult.value[i,0]) == -1:
                if binStr[-4] == '1' or binStr[-6] == '1': # 8 or 32
                    valueEdit = True

            dataType = 'Real'
            if binStr[-2:] == '01': # 1
                dataType = 'Boolean'
            elif binStr[-2:] == '10': # 2
                dataType = 'Integer'

            value = None
            if variability == 'fixed' or valueEdit:
                value = self._initialResult.value[i,1]

            unit = self._initialResult.unit[i]
            variableAttribute = ''
            if self._initialResult.description[i] != '' :
                variableAttribute += 'Description:' + chr(9) + self._initialResult.description[i] + '\n'
            variableAttribute += 'Causality:' + chr(9) + causality + '\n'
            variableAttribute += 'Variability:' + chr(9) + variability + '\n'
            variableAttribute += 'Type:' + chr(9) + dataType
            self.variableTree.variable[self._initialResult.name[i]] = Plugins.Simulator.SimulatorBase.TreeVariable(self.structureVariableName(self._initialResult.name[i]), value, valueEdit, unit, variability, variableAttribute)


    def _compileModel(self):
        ''' Compiles a Modelica model by calling Dymola and running a mos-file
            If there is already a simulation executable in the working directory
            that is newer than the Modelica model file, then this executable is used.
        '''
        if len(self.fileName) == 1:
            sp = string.rsplit(self.fileName[0], '.', 1)
            suffix = sp[1]
            if suffix not in ['mo', 'moe']:
                # Can only compile *.mo and *.moe files
                self.fileNameExec = self.fileName[0]
                return

        fileNameExec = prepareSimulationList(self.fileName, [self.name], self.config)
        if fileNameExec is not None:
            self.fileNameExec = fileNameExec[0]


    def getReachedSimulationTime(self):
        ''' Read the current simulation time during a simulation
            from the file "status"
        '''
        rTime = None
        # Read current time from file "status"
        try:
            f = open('status.', 'r')
            s = f.readline()
            if 'Time' in s:
                rTime = float(s.rsplit('=',1)[1])
            f.close()
        except:
            pass
        return rTime

    def simulate(self):
        ''' Simulate a Modelica model by executing Dymola's simulation executable.
        '''

        # First, define some functions:

        def writeDsin(changedStartValue):
            ''' Write input file for Dymola's simulation executable
            '''
            s = self.integrationSettings

            if s.gridPointsMode == 'NumberOf':
                nGridPoints = s.gridPoints
                gridWidth = 0
                method1 = 1
            elif s.gridPointsMode == 'Width':
                nGridPoints = 1
                gridWidth = s.gridWidth
                method1 = 1
            else:
                nGridPoints = 2
                gridWidth = 0
                method1 = 3
            nGridPoints = max(1,nGridPoints)

            includeEvents = 1 if s.resultFileIncludeEvents else 0

            algorithm = dict()
            algorithm['Explicit Euler'] = 11
            algorithm['Dassl'] = 8
            algorithm['Lsodar'] = 4
            algorithm['Rkfix2'] = 12
            algorithm['Rkfix3'] = 13
            algorithm['Rkfix4'] = 14
            algorithm['Radau IIa'] = 15
            algorithm['Esdirk23a'] = 16
            algorithm['Esdirk34a'] = 17
            algorithm['Esdirk45a'] = 18
            algorithm['Dopri45'] = 19
            algorithm['Dopri853'] = 21
            algorithm['Sdirk34hw'] = 24
            algorithm['Cerk23'] = 26
            algorithm['Cerk34'] = 27
            algorithm['Cerk45'] = 28

            experiment = [s.startTime,s.stopTime, gridWidth, nGridPoints-1, s.errorToleranceRel, s.fixedStepSize, algorithm[s.algorithmName]]
            # DYMOLA Method tuning parameters
            method = [method1,
                      1,     # nt       Use every NT time instant, if grid = 3
                      3,     # dense    1/2/3 restart/step/interpolate GRID points
          includeEvents,     # evgrid   0/1 do not/save event points in comm. time grid
                      1,     # evu      0/1 U-discontinuity does not/trigger events
                      0,     # evuord       U-discontinuity order to consider (0,1,...)
                      0,     # error    0/1/2 One message/warning/error messages
                      0,     # jac      0/1 Compute jacobian numerically/by BLOCKJ
                      0,     # xd0c     0/1 Compute/set XD0
                      0,     # f3       0/1 Ignore/use F3 of HDAE (= index 1)
                      0,     # f4       0/1 Ignore/use F4 of HDAE (= index 2)
                      0,     # f5       0/1 Ignore/use F5 of HDAE (= invar.)
                      0,     # debug    flags for debug information (1<<0 uses pdebug)
                      100,   # pdebug   priority of debug information (1...100)
                      0,     # fmax     Maximum number of evaluations of BLOCKF, if > 0
                      0,     # ordmax   Maximum allowed integration order, if > 0
                      0,     # hmax     Maximum absolute stepsize, if > 0
                      0,     # hmin     Minimum absolute stepsize, if > 0 (use with care!)
                      0,     # h0       Stepsize to be attempted on first step, if > 0
                      1e-12, # teps     Bound to check, if 2 equal time instants
                      1e-10, # eveps    Hysteresis epsilon at event points
                      20,    # eviter   Maximum number of event iterations
                      0,     # delaym   Minimum time increment in delay buffers
                      1,     # fexcep   0/1 floating exception crashes/stops dymosim
                      1,     # tscale   clock-time = tscale*simulation-time, if grid = 5
                      1,     # shared   (not used)
                      2473]  # memkey   (not used)
            # DYMOLA Output parameters
            settings = [1,   # lprec    0/1 do not/store result data in double
                        1,   # lx       0/1 do not/store x  (state variables)
                        1,   # lxd      0/1 do not/store xd (derivative of states)
                        1,   # lu       0/1 do not/store u  (input     signals)
                        1,   # ly       0/1 do not/store y  (output    signals)
                        1,   # lz       0/1 do not/store z  (indicator signals)
                        1,   # lw       0/1 do not/store w  (auxiliary signals)
                        1,   # la       0/1 do not/store a  (alias     signals)
                        0,   # lperf    0/1 do not/store performance indicators
                        0,   # levent   0/1 do not/store event point
                        1,   # lres     0/1 do not/store results on result file
                        0,   # lshare   0/1 do not/store info data for shared memory on dsshare.txt
                        1]   # lform    0/1 ASCII/Matlab-binary storage format of results
            initialName = changedStartValue.keys()
            initialValue = [float(x) for x in changedStartValue.values()]


            f = open('dsin.txt', "w")
            f.write('#1\n')
            f.write('char Aclass(3,36)\n')
            f.write('Adymosim\n')
            f.write('1.4\n')
            f.write('Input file generated by PySimulator\n')
            f.write('\n\n')

            f.write('#    Experiment parameters\n')
            f.write('double experiment(7,1)\n')
            for value in experiment:
                f.write('{0:0.16e}'.format(value) + '\n')
            f.write('\n\n')

            f.write('#    Method tuning parameters\n')
            f.write('double method(27,1)\n')
            for value in method:
                f.write('{0:0.16e}'.format(value) + '\n')
            f.write('\n\n')

            f.write('#    Output parameters\n')
            f.write('int settings(13,1)\n')
            for value in settings:
                f.write(str(value) + '\n')

            f.write('\n\n')

            nVariables = len(initialName)
            if nVariables != len(initialValue):
                print("Length of initialValues and initialNames is not identical ... ")
                raise(Exception)
            if nVariables > 0:
                maxLength = max([len(x) for x in initialName])
                f.write('#    Names of initial variables\n')
                f.write('char initialName(' + str(nVariables) + ',' + str(maxLength) + ')\n')
                for value in initialName:
                    f.write(value + '\n')
                f.write('\n\n')

                f.write('#    Values of initial variables\n')
                f.write('double initialValue(' + str(nVariables) + ',6)\n')
                for value in initialValue:
                    f.write('-1  ' + '{0:0.16e}'.format(value) + '  0  0  1  0' + '\n')
                f.write('\n\n')

            f.close()

        def readStatistics():
            ''' Reads some integration statistics from the file "dslog.txt"
            '''

            f = open('dslog.txt', "r")

            content = f.readlines()

            nTimeEvents = 0
            nStateEvents = 0
            currentGridPoints = 0
            currentTime = self.integrationSettings.startTime
            endCondition = False
            for c in content:
                if 'Number of result points' in c:
                    currentGridPoints = int(c.split(':',1)[1])
                if 'Number of state    events' in c:
                    nStateEvents = int(c.split(':',1)[1])
                if 'Number of (model) time events' in c:
                    nTimeEvents = nTimeEvents + int(c.split(':',1)[1])
                if 'Number of (U) time events' in c:
                    nTimeEvents = nTimeEvents + int(c.split(':',1)[1])
                if 'Integration terminated' in c:
                    if 'Integration terminated successfully' in c and not endCondition:
                        # Time in dslog.txt is not accurate enough
                        currentTime = self.integrationSettings.stopTime
                    else:
                        currentTime = float(c.rsplit('T =',1)[1])
                if 'End condition reached' in c:
                    endCondition = True


            self.integrationStatistics.nTimeEvents = nTimeEvents
            self.integrationStatistics.nStateEvents = nStateEvents
            self.integrationStatistics.nGridPoints = currentGridPoints
            self.integrationStatistics.reachedTime = currentTime

            f.close()

        # End of defining functions in simulate


        # Compile the model if necessary:
        self._compileModel()

        # Write input file and start simulation
        writeDsin(self.changedStartValue)      
        subprocess.call((self.fileNameExec + ' -s dsin.txt ' + self.integrationSettings.resultFileName).encode(sys.getfilesystemencoding()))
        
        # Simulation statistics from dslog.txt
        readStatistics()

        # Integration is finished


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




def prepareSimulationList(fileName, name, config):
    ''' Compiles a Modelica model by calling Dymola and running a mos-file
        If there is already a simulation executable in the working directory
        that is newer than the Modelica model file, then this executable is used.
    '''


    # Check whether a up-to-date executable is available
    if 'win' in sys.platform:
        suffix = '.exe'
    else:
        suffix = ''

    pwd = os.path.abspath('.').replace('\\','/')

    fileNameExec = []
    timeStampModel = 0
    translateModel = []
    for x in name:
        translateModel.append(True)         
        fileNameExec.append(pwd.decode(sys.getfilesystemencoding()) + '/' + x + suffix)
        if os.path.exists(fileNameExec[-1]):
            if timeStampModel == 0:
                for x in fileName:
                    timeStampModel = max(timeStampModel, os.path.getmtime(x))
            timeStampExec  = os.path.getmtime(fileNameExec[-1])
            if timeStampModel < timeStampExec:
                translateModel[-1] = False

    for i, x in enumerate(name):
        if translateModel[i]:
            print "Translate Modelica model ", x, " by Dymola ... "

    if not any(translateModel):
        return fileNameExec



    if not config['Plugins']['Dymola'].has_key('dymolaPath'):
        config['Plugins']['Dymola']['dymolaPath'] = ''
    dymolaPath = config['Plugins']['Dymola']['dymolaPath']

    if dymolaPath == '':
        ''' Ask for Dymola executable '''
        print "No Dymola executable (Dymola.exe) found to run Dymola. Please select one ..."
        (dymolaPath, trash) = QtGui.QFileDialog().getOpenFileName(None, 'Select Dymola executable file', os.getcwd(), 'Executation file (*.exe)')
        #dymolaPath = str(dymolaPath)
        if dymolaPath == '':
            print "failed. No Dymola executable (Dymola.exe) specified."
            return None
        else:
            config['Plugins']['Dymola']['dymolaPath'] = dymolaPath
            config.write()

    if not os.path.exists(dymolaPath):
        print "failed. Dymola executable " + dymolaPath + " not found."
        return None



    mosFileName = 'openTranslate.mos'
    mosFile = open(mosFileName, "w")
    for x in fileName:
        if x != '':
            mosFile.write("openModel(\"" + x.encode(sys.getfilesystemencoding()) + "\");\n")
    mosFile.write("cd(\"" + pwd + "\");\n")
    mosFile.write("Modelica.Utilities.Files.remove(\"dymosim.exe\");\n")
    for x in name:        
        mosFile.write("ok := translateModel(\"" + x + "\");\n")
        mosFile.write("if ok then\n");
        mosFile.write("  Modelica.Utilities.Files.move(\"" + "dymosim" + suffix +"\", \"" + x + suffix + "\", true);\n")
        mosFile.write("end if;\n");
    mosFile.write("exit();\n")
    mosFile.close()

    subprocess.call((dymolaPath + ' /nowindow ' + pwd.decode(sys.getfilesystemencoding()) + '/' + mosFileName).encode(sys.getfilesystemencoding()))

    for i, x in enumerate(fileNameExec):
        if os.path.exists(x):
            print "... translation done for " + name[i] + ".\n"
        else:
            print "... translation failed for " + name[i] + ".\n"

    return fileNameExec
