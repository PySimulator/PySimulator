import os
import copy
import Plugins.Simulator.FMUSimulator.FMUSimulator2 as FMUSimulator
import Plugins.SimulationResult.IntegrationResults
import Plugins.SimulationResult.Mtsf.Mtsf as Mtsf
from Plugins.Simulator.FMUSimulator.FMUInterface2 import fmiTrue
from Plugins.Simulator import SimulatorBase

from PySide import QtGui, QtCore
from datetime import datetime
import codecs
import xml.etree.ElementTree as ET

class ExportConnectFMUsDialog(QtGui.QDialog):

    def __init__(self, xml, gui):
        QtGui.QDialog.__init__(self, gui)
        self.setWindowTitle("Export Connect FMUs")

        self._xml = xml
        # add export directory
        exportDirLabel = QtGui.QLabel(self.tr("Export Directory:"))
        self._exportDirTextBox = QtGui.QLineEdit()
        browseExportDirButton = QtGui.QPushButton(self.tr("Browse"))
        browseExportDirButton.clicked.connect(self.browseExportDirectory)
        # ok and cancel buttons
        okButton = QtGui.QPushButton(self.tr("OK"))
        okButton.clicked.connect(self.exportConnectFMUs)
        cancelButton = QtGui.QPushButton(self.tr("Cancel"))
        cancelButton.clicked.connect(self.reject)
        # add the buttons to button box
        buttonsBox = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal)
        buttonsBox.addButton(okButton, QtGui.QDialogButtonBox.ActionRole)
        buttonsBox.addButton(cancelButton, QtGui.QDialogButtonBox.ActionRole)
        # set the dialog layout
        mainLayout = QtGui.QGridLayout()
        mainLayout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        mainLayout.addWidget(exportDirLabel, 0, 0)
        mainLayout.addWidget(self._exportDirTextBox, 0, 1)
        mainLayout.addWidget(browseExportDirButton, 0, 2)
        mainLayout.addWidget(buttonsBox, 1, 0, 1, 3, QtCore.Qt.AlignRight)
        self.setLayout(mainLayout)

    def browseExportDirectory(self):
        directoryName = QtGui.QFileDialog().getExistingDirectory(self, self.tr("Choose Export Directory"), os.getcwd())
        directoryName = directoryName.replace('\\', '/')
        self._exportDirTextBox.setText(directoryName)

    def exportConnectFMUs(self):
        exportDirectory = self._exportDirTextBox.text() + '/connectedFMUs' + datetime.now().strftime('%Y%m%d%H%M%S')
        if not QtCore.QDir().mkpath(exportDirectory):
            print "Unable to create the path %s" % exportDirectory
            return

        # read the xml to know the FMUs locations and then copy them
        rootElement = ET.fromstring(self._xml)
        for fmu in rootElement.iter('fmu'):
            fmuPath = fmu.get('path')
            fmuFile = QtCore.QFile(fmuPath)
            if fmuFile.exists():
                fmuFileInfo = QtCore.QFileInfo(fmuPath)
                fmuFile.copy(exportDirectory + '/' + fmuFileInfo.fileName())
                fmu.set('path', fmuFileInfo.fileName())

        # pretty print the xml
        xml = ET.tostring(rootElement, "utf-8")
        xml = '<?xml version="1.0" ?>\n' + xml

        # write the updated xml to a file in the new exported directory
        try:
            xmlFile = codecs.open(exportDirectory + '/connectFMUs.xml', "w", "utf-8")
            xmlFile.write(xml)
            xmlFile.close()
        except IOError, e:
            print "Failed to write the xml file. %s" % e
            return

        print 'Files exported to %s' % exportDirectory
        self.accept()

class Model(Plugins.Simulator.SimulatorBase.Model):

    def __init__(self, connectedfmusitems=None, config=None, xml=None, xmlFileName=None, fmiType=None, connectionorder=None, loggingOn=False):
        ''' ModelFilename are list of strings '''
        self._FMUSimulators = {}
        self._connections = []
        self._xml = xml
        self._xmlFileName = xmlFileName
        self._fmiType = fmiType
        self._connectionorder = connectionorder
        # create FMUSimulator objects
        for i in xrange(len(connectedfmusitems)):
            instancename = connectedfmusitems[i]['instancename']
            modelfilename = connectedfmusitems[i]['filename']
            FMUSimulatorObj = FMUSimulator.Model(instancename, [modelfilename], config)
            self._FMUSimulators[instancename] = FMUSimulatorObj

        Plugins.Simulator.SimulatorBase.Model.__init__(self, 'ConnectedFMUS', [], config)
        # read the xml to know the connections
        rootElement = ET.fromstring(self._xml)
        for connection in rootElement.iter('connection'):
            self._connections.append({'fromFmuName':connection.get('fromFmuName'), 'fromVariableName':connection.get('fromVariableName'),
                                      'toFmuName':connection.get('toFmuName'), 'toVariableName':connection.get('toVariableName')})
        # do not change the following line. It is used in FMU.py functions export & save.
        self.modelType = 'Connected FMU Simulation'
        self.integrationResults = Mtsf.Results('')
        self.integrationSettings.resultFileExtension = 'mtsf'
        if self._fmiType == 'me':
            self._availableIntegrationAlgorithms = ["BDF (IDA, Dassl like)", "BDF (CVode)", "Adams (CVode)", "Explicit Euler (fixed step size)"]
            self._IntegrationAlgorithmHasFixedStepSize = [False, False, False, True]
            self._IntegrationAlgorithmCanProvideStepSizeResults = [True, True, True, True]
            self._IntegrationAlgorithmSupportsStateEvents = [True, True, True, True]
        elif self._fmiType == 'cs':
            self._availableIntegrationAlgorithms = ["Integration method by FMU for CoSimulation"]
            self._IntegrationAlgorithmHasFixedStepSize = [False]
            self._IntegrationAlgorithmCanProvideStepSizeResults = [False]
            self._IntegrationAlgorithmSupportsStateEvents = [False]

            self.integrationSettings.algorithmName = self._availableIntegrationAlgorithms[0]
            self.simulationStopRequest = False

    def close(self):
        ''' Closing the model, release of resources
        '''
        Plugins.Simulator.SimulatorBase.Model.close(self)
        for key, FMUSimulatorObj in self._FMUSimulators.iteritems():
            FMUSimulatorObj.close()

    def closeIntegrationResults(self):
        for key, FMUSimulatorObj in self._FMUSimulators.iteritems():
            FMUSimulatorObj.integrationResults.close()

    def loadIntegrationResults(self):
        # mark this model integration results as available
        self.integrationResults.isAvailable = True
        for key, FMUSimulatorObj in self._FMUSimulators.iteritems():
            FMUSimulatorObj.loadResultFile(FMUSimulatorObj.integrationSettings.resultFileName)

    def simulate(self):

        def finalize():
            for key, FMUSimulatorObj in self._FMUSimulators.iteritems():
                FMUSimulatorObj.finalize()

        # Set Simulation options
        Tstart = self.integrationSettings.startTime
        Tend = self.integrationSettings.stopTime
        IntegrationMethod = self.integrationSettings.algorithmName
        if "BDF (CVode)" in IntegrationMethod:
            IntegrationMethod = 'BDF'
        elif 'Adams' in IntegrationMethod:
            IntegrationMethod = 'Adams'
        if self.integrationSettings.gridPointsMode == 'NumberOf':
            nIntervals = self.integrationSettings.gridPoints - 1
            gridWidth = None
        elif self.integrationSettings.gridPointsMode == 'Width':
            nIntervals = None
            gridWidth = self.integrationSettings.gridWidth
        else:
            nIntervals = 0
            gridWidth = None
        ErrorTolerance = self.integrationSettings.errorToleranceRel

        # Initialize integration statistics
        self.integrationStatistics.nTimeEvents = 0
        self.integrationStatistics.nStateEvents = 0
        self.integrationStatistics.nGridPoints = 0
        self.integrationStatistics.reachedTime = Tstart

        # prepare result files for each FMU
        for key, FMUSimulatorObj in self._FMUSimulators.iteritems():
            FMUSimulatorObj.integrationSettings = copy.copy(self.integrationSettings)
            fileName = FMUSimulatorObj.name + "_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".mtsf"
            FMUSimulatorObj.integrationSettings.resultFileName = unicode(fileName)
            if not FMUSimulatorObj.prepareResultFile():
                return
            # set simulation options
            FMUSimulatorObj.setSimulationOptions()
            # Initialize model
            (status, nextTimeEvent) = FMUSimulatorObj.initialize(Tstart, Tend, ErrorTolerance if self._fmiType == 'cs' else min(1e-15, ErrorTolerance*1e-5))
            if status > 1:
                print("Instance %s initialization failed with fmiStatus %s" % (FMUSimulatorObj.name, str(status)))
                return
            if 'Fixed' in FMUSimulatorObj.integrationResults._mtsf.results.series:
                # Write parameter values
                FMUSimulatorObj.writeResults('Fixed', Tstart)
            FMUSimulatorObj.writeResults('Continuous', Tstart)

        # Run the integration
        if self._fmiType == 'me':
            return
        elif self._fmiType == 'cs':
            if gridWidth is None:
                gridWidth = (Tend-Tstart) / nIntervals

            t = Tstart
            lastStep = False
            doLoop = Tend > Tstart
            if gridWidth <= Tend-t:
                dt = gridWidth
            else:
                dt = Tend - t
                lastStep = True
            k = 1

            while doLoop:
                for i in xrange(len(self._connectionorder)):
                    for j in self._connectionorder[i]:
                        FMUSimulatorObj = self.getFMUSimulator(j)
                        # handle result
                        FMUSimulatorObj.handle_result(None, t)
                        if 'Discrete' in FMUSimulatorObj.integrationResults._mtsf.results.series:
                            # Write discrete Variables
                            FMUSimulatorObj.writeResults('Discrete', t)

                        # resolve connections here
                        for ele in xrange(len(self._connections)):
                            if self._connections[ele]['fromFmuName'] == j:
                                fromValue = FMUSimulatorObj.getValue(self._connections[ele]['fromVariableName'])
                                toFMUSimulatorObj = self.getFMUSimulator(self._connections[ele]['toFmuName'])
                                if toFMUSimulatorObj is not None:
                                    toFMUSimulatorObj.setValue(self._connections[ele]['toVariableName'], fromValue)

                        status = FMUSimulatorObj.doStep(t, dt)
                        if status == 2:  # Discard
                            status, info = FMUSimulatorObj.interface.fmiGetBooleanStatus(3) # fmi2Terminated
                            if info == fmiTrue:
                                status, lastTime = FMUSimulatorObj.interface.fmiGetRealStatus(2)       # fmi2LastSuccessfulTime
                                t = lastTime
                                doLoop = False
                            else:
                                print("Not supported status in doStep at time = {:.2e}".format(t))
                                # Raise exception to abort simulation...
                                finalize()
                                raise(SimulatorBase.Stopping)

                # increment the loop
                t = t + dt

                if lastStep:
                    doLoop = False
                else:
                    #Compute next communication point
                    if gridWidth <= Tend-t:
                        k += 1
                        dt = (Tstart + k*gridWidth) - t
                    else:
                        dt = Tend - t
                        lastStep = True

            finalize()

        print 'Result files generated'
        return

    def getAvailableIntegrationAlgorithms(self):
        return self._availableIntegrationAlgorithms

    def getIntegrationAlgorithmHasFixedStepSize(self, algorithmName):
        return self._IntegrationAlgorithmHasFixedStepSize[self._availableIntegrationAlgorithms.index(algorithmName)]

    def getIntegrationAlgorithmCanProvideStepSizeResults(self, algorithmName):
        return self._IntegrationAlgorithmCanProvideStepSizeResults[self._availableIntegrationAlgorithms.index(algorithmName)]

    def getIntegrationAlgorithmSupportsStateEvents(self, algorithmName):
        return self._IntegrationAlgorithmSupportsStateEvents[self._availableIntegrationAlgorithms.index(algorithmName)]

    def getReachedSimulationTime(self):
        ''' Results are avialable up to the returned time
        '''
        return self.integrationStatistics.reachedTime

    def setVariableTree(self):
        #Sets the variable tree to be displayed in the variable browser.
        #The data is set in self.variableTree that is an instance of the class SimulatorBase.VariableTree
        for key, FMUSimulatorObj in self._FMUSimulators.iteritems():
            FMUSimulatorObj.setVariableTree()
            for vName, treeVariable in FMUSimulatorObj.variableTree.variable.iteritems():
                self.variableTree.variable[FMUSimulatorObj.name + '.' + vName] = Plugins.Simulator.SimulatorBase.TreeVariable(FMUSimulatorObj.name + '.' + vName, treeVariable.value, treeVariable.valueEdit, treeVariable.unit, treeVariable.variability, treeVariable.attribute)

    def getFMUSimulator(self, name):
        for key, FMUSimulatorObj in self._FMUSimulators.iteritems():
            if (FMUSimulatorObj.name == name):
                return FMUSimulatorObj
        return None

    def export(self, gui):
        exportconnectedFMUsDialog = ExportConnectFMUsDialog(self._xml, gui)
        exportconnectedFMUsDialog.exec_()

    def save(self, gui):
        if self._xmlFileName is None:
            (fileName, trash) = QtGui.QFileDialog().getSaveFileName(gui, gui.tr("Save file"), os.getcwd(), '(*.xml)')
            if fileName == '':
                return
            self._xmlFileName = fileName
        else:
            fileName = self._xmlFileName

        if fileName is not None:
            try:
                xmlFile = codecs.open(fileName, "w", "utf-8")
                xmlFile.write(self._xml)
                xmlFile.close()
            except IOError, e:
                print "Failed to write the xml file. %s" % e
