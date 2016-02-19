#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (C) 2011-2015 German Aerospace Center DLR
(Deutsches Zentrum fuer Luft- und Raumfahrt e.V.),
Institute of System Dynamics and Control

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


from PySide import QtGui, QtCore
import os, sys
import numpy
import shutil
import time
import ParallelSimulation
from ... import Simulator


def simulateListMenu(model, gui):

    class SimulateListControl(QtGui.QDialog):
        ''' Class for the SimulateList Control GUI '''

        def __init__(self):
            QtGui.QDialog.__init__(self)
            self.setModal(False)
            self.setWindowTitle("Simulate List of Models")
            self.setWindowIcon(QtGui.QIcon(gui.rootDir + '/Icons/pysimulatorLists.ico'))

            mainGrid = QtGui.QGridLayout(self)

            setupFile = QtGui.QLabel("Setup file:", self)
            mainGrid.addWidget(setupFile, 0, 0, QtCore.Qt.AlignRight)
            browseSetupFile = QtGui.QPushButton("Select", self)
            mainGrid.addWidget(browseSetupFile, 0, 2)
            self.setupFileEdit = QtGui.QLineEdit("", self)
            mainGrid.addWidget(self.setupFileEdit, 0, 1)

            setupFile = QtGui.QLabel("Directory of results:", self)
            mainGrid.addWidget(setupFile, 1, 0, QtCore.Qt.AlignRight)
            browseDirResults = QtGui.QPushButton("Select", self)
            mainGrid.addWidget(browseDirResults, 1, 2)
            self.dirResultsEdit = QtGui.QLineEdit("", self)
            mainGrid.addWidget(self.dirResultsEdit, 1, 1)

            self.deleteDir = QtGui.QCheckBox("Delete existing result directories for selected simulators before simulation", self)
            mainGrid.addWidget(self.deleteDir, 2, 1, 1, 2)

            mainGrid.addWidget(QtGui.QLabel("Simulators:"), 3, 0, QtCore.Qt.AlignRight)
            self.simulator = QtGui.QListWidget(self)
            self.simulator.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
            self.simulator.setFixedHeight(150)
            allSimulatorPlugins = list(gui.simulatorPlugins.keys())
            allSimulatorPlugins.sort()
            for x in allSimulatorPlugins:
                QtGui.QListWidgetItem(x, self.simulator)

            mainGrid.addWidget(self.simulator, 3, 1)


            self.stopButton = QtGui.QPushButton("Stop", self)
            mainGrid.addWidget(self.stopButton, 7, 0)
            self.stopButton.clicked.connect(self.stop)
            self.runButton = QtGui.QPushButton("Run simulations", self)
            mainGrid.addWidget(self.runButton, 7, 1)
            self.runButton.clicked.connect(self.run)
            self.closeButton = QtGui.QPushButton("Close", self)
            mainGrid.addWidget(self.closeButton, 7, 2)
            self.closeButton.clicked.connect(self._close_)
                       
            self.parallelButton = QtGui.QPushButton("Parallel Simulation", self)
            mainGrid.addWidget(self.parallelButton, 8, 1)
            self.parallelButton.clicked.connect(self.parallel)

            def _browseSetupFileDo():
                (fileName, trash) = QtGui.QFileDialog().getOpenFileName(self, 'Open Simulation Setup File', os.getcwd(), '(*.txt);;All Files(*.*)')
                if fileName != '':
                    self.setupFileEdit.setText(fileName)

            def _browseDirResultsDo():
                dirName = QtGui.QFileDialog().getExistingDirectory(self, 'Select Directory of Results', os.getcwd())
                dirName = dirName.replace('\\', '/')
                if dirName != '':
                    self.dirResultsEdit.setText(dirName)

            browseSetupFile.clicked.connect(_browseSetupFileDo)
            browseDirResults.clicked.connect(_browseDirResultsDo)
            self.dirResultsEdit.setText(os.getcwd().replace('\\', '/'))


        def _close_(self):
            self.close()


        def run(self):
            if hasattr(gui, '_simThreadTesting'):
                if gui._simThreadTesting.running:
                    print "A list of simulations is still running."
                    return

            # Get data from GUI
            setupFile = self.setupFileEdit.text()
            resultsDir = self.dirResultsEdit.text()
            simulators = []
            for item in self.simulator.selectedItems():
                simulators.append(gui.simulatorPlugins[item.text()])
            deleteDir = self.deleteDir.isChecked()

            # Run the simulations
            gui._simThreadTesting = runListSimulation(gui.rootDir, setupFile, resultsDir, simulators, deleteDir)

        def parallel(self):
            if hasattr(gui, '_simThreadTesting'):
                if gui._simThreadTesting.running:
                    print "A list of simulations is still running."
                    return

            # Get data from GUI
            setupFile = self.setupFileEdit.text()
            resultsDir = self.dirResultsEdit.text()
            simulators = []
            for item in self.simulator.selectedItems():
                simulators.append(gui.simulatorPlugins[item.text()])
            deleteDir = self.deleteDir.isChecked()
                        
            # Run parallel simulations
            gui._simThreadTesting = ParallelSimulation.runParallelSimulation(gui.rootDir, setupFile, resultsDir, simulators, deleteDir)


        def stop(self):
            if hasattr(gui, '_simThreadTesting'):
                if gui._simThreadTesting.running:
                    gui._simThreadTesting.stopRequest = True
                    print "Try to cancel simulations ..."



    # Code of function
    control = SimulateListControl()
    control.show()

def runListSimulation(PySimulatorPath, setupFile, resultDir, allSimulators, deleteDir=False):
    import configobj
    import csv


    print "Start running the list of simulations ..."

    f = open(setupFile, 'rb')

    '''
    # Read the general settings
    general = []
    k = 0
    endLoop = False
    while not endLoop:
        pos = f.tell()
        y = f.readline()
        if y == '': # end of file
            endLoop = True
        else:
            y = y.split('#',1)[0].replace('\n', '').strip()
            if len(y) > 0:
                if not '/' in y: # No Path information
                    f.seek(pos)
                    endLoop = True
                else:
                    k += 1
                    general.append(y)

    # Read the list of models
    modelList = numpy.genfromtxt(f, dtype='S2000, S2000, f8, f8, f8, i4, b1', names=['fileName', 'modelName', 'tStart', 'tStop', 'tol', 'nInterval', 'includeEvents'])
    '''

    line = []
    reader = csv.reader(f, delimiter=' ', skipinitialspace=True)
    for a in reader:
        if len(a) > 0:
            if not (len(a[0]) > 0 and a[0][0] == '#'):
                if a[0] != '':
                    line.append(a)
                
    f.close()

    modelList = numpy.zeros((len(line),), dtype=[('fileName', 'U2000'), ('modelName', 'U2000'), ('subDirectory', 'U2000'), ('tStart', 'f8'), ('tStop', 'f8'), ('tol', 'f8'), ('stepSize', 'f8'), ('nInterval', 'i4'), ('includeEvents', 'b1')])
    for i, x in enumerate(line):
        absPath = x[0].replace('\\', '/')
        if absPath <> "" and not os.path.isabs(absPath):
            absPath = os.path.normpath(os.path.join(os.path.split(setupFile)[0], absPath)).replace('\\', '/')
        if len(x) >= 9:
            modelList[i] = (absPath, x[1], x[2], float(x[3]), float(x[4]), float(x[5]), float(x[6]), int(x[7]), True if x[8].lower() == 'true' else False)
        else:
            modelList['fileName'][i] = absPath

    # packageName = general[0]
    #config = configobj.ConfigObj(PySimulatorPath.replace('\\', '/') + '/PySimulator.ini')
    config = configobj.ConfigObj(os.path.join(os.path.expanduser("~"), '.config', 'PySimulator', 'PySimulator.ini'), encoding='utf8')

    sim = simulationThread(None)
    sim.config = config
    # sim.packageName = packageName
    sim.modelList = modelList
    sim.allSimulators = allSimulators
    sim.resultDir = resultDir
    sim.deleteDir = deleteDir
    sim.stopRequest = False
    sim.running = False
    sim.start()

    return sim

class simulationThread(QtCore.QThread):
    ''' Class for the simulation thread '''
    def __init__(self, parent):
        super(simulationThread, self).__init__(parent)

    def run(self):
        self.running = True
        
        try:
            import pydevd
            pydevd.connected = True
            pydevd.settrace(suspend=False)
        except:
            # do nothing, since error message only indicates we are not in debug mode
            pass
        
        #startTime=time.time() 
        for simulator in self.allSimulators:
            simulatorName = simulator.__name__.rsplit('.', 1)[-1]
            fullSimulatorResultPath = self.resultDir + '/' + simulatorName
            if os.path.isdir(fullSimulatorResultPath) and self.deleteDir:
                for file_object in os.listdir(fullSimulatorResultPath):
                    file_object_path = os.path.join(fullSimulatorResultPath, file_object)
                    if os.path.isfile(file_object_path):
                        os.unlink(file_object_path)
                    else:
                        shutil.rmtree(file_object_path)

            packageName = []
            globalModelList = []
            globalPackageList = []
            for i in xrange(len(self.modelList['fileName'])):
                modelName = self.modelList['modelName'][i]
                packageName.append(self.modelList['fileName'][i])
                if modelName != '':
                    canLoadAllPackages = True
                    for j in xrange(len(packageName)):
                        sp = packageName[j].rsplit('.', 1)
                        if len(sp) > 1:
                            if not sp[1] in simulator.modelExtension:
                                canLoadAllPackages = False
                                break
                        else:
                            canLoadAllPackages = False
                            break

                    if canLoadAllPackages:
                        globalModelList.append(modelName)
                        for x in packageName:
                            if x not in globalPackageList:
                                globalPackageList.append(x)

                    packageName = []
            simulator.prepareSimulationList(globalPackageList, globalModelList, self.config)
            haveCOM = False

            try:
                try:
                    import pythoncom
                    pythoncom.CoInitialize()  # Initialize the COM library on the current thread
                    haveCOM = True
                except:
                    pass
                
                for i in xrange(len(self.modelList['fileName'])):
                    if self.stopRequest:
                        print "... Simulations canceled."
                        self.running = False
                        return
                    modelName = self.modelList['modelName'][i]
                    packageName.append(self.modelList['fileName'][i])
                    if modelName != '':
                        canLoadAllPackages = True
                        for j in xrange(len(packageName)):
                            if packageName[j] == '':
                                continue
                            sp = packageName[j].rsplit('.', 1)
                            if len(sp) > 1:
                                if not sp[1] in simulator.modelExtension:
                                    canLoadAllPackages = False
                                    break
                            else:
                                canLoadAllPackages = False
                                break
                        if canLoadAllPackages:
                            try:
                                '''
                                Do the numerical integration in a try branch
                                to avoid losing the thread when an intended exception is raised

                                Also guard against compilation failures when loading the model
                                '''
                                model = simulator.getNewModel(modelName, packageName, self.config)

                                if self.modelList['subDirectory'][i] is not '':
                                    resultDir = fullSimulatorResultPath + '/' + self.modelList['subDirectory'][i]
                                    if not os.path.isdir(resultDir):
                                        os.makedirs(resultDir)
                                else:
                                    resultDir = fullSimulatorResultPath

                                resultFileName = resultDir + '/' + modelName + '.' + model.integrationSettings.resultFileExtension
                                model.integrationSettings.startTime = self.modelList['tStart'][i]
                                model.integrationSettings.stopTime = self.modelList['tStop'][i]
                                model.integrationSettings.errorToleranceRel = self.modelList['tol'][i]
                                model.integrationSettings.fixedStepSize = self.modelList['stepSize'][i]
                                model.integrationSettings.gridPoints = self.modelList['nInterval'][i] + 1
                                model.integrationSettings.gridPointsMode = 'NumberOf'
                                model.integrationSettings.resultFileIncludeEvents = self.modelList['includeEvents'][i]
                                model.integrationSettings.resultFileName = resultFileName
                                print "Simulating %s by %s (result in %s)..." % (modelName,simulatorName,resultFileName)
                                model.simulate()

                            except Simulator.SimulatorBase.Stopping:
                                print("Solver cancelled ... ")
                            except Exception as e:
                                import traceback
                                traceback.print_exc(e,file=sys.stderr)
                                print e
                            finally:
                                model.close()
                        else:
                            print "WARNING: Simulator " + simulatorName + " cannot handle files ", packageName, " due to unknown file type(s)."

                        packageName = []
            except:
                pass
            finally:
                if haveCOM:
                    try:
                        pythoncom.CoUninitialize()  # Close the COM library on the current thread
                    except:
                        pass
        #elapsedTime = time.time() - startTime
        #print elapsedTime   
        print "... running the list of simulations done."
        self.running = False
        
