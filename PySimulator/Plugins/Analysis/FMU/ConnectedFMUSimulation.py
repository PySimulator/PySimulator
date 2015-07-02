import os
import copy
import Plugins.Simulator.FMUSimulator.FMUSimulator2 as FMUSimulator
import Plugins.SimulationResult.IntegrationResults
import Plugins.SimulationResult.Mtsf.Mtsf as Mtsf

import Plugins.Simulator.SimulatorBase
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

    def __init__(self, instancename=None, modelFileName=None, config=None, xml=None, xmlFileName=None, fmiType=None, independentfmus=None, loggingOn=False):
        ''' ModelFilename are list of strings '''
        self._FMUSimulators = []
        self._xml = xml
        self._xmlFileName = xmlFileName
        self._fmiType = fmiType
        for i in xrange(len(modelFileName)):
            FMUSimulatorObj = FMUSimulator.Model(instancename[i], [modelFileName[i]], config)
            self._FMUSimulators.append(FMUSimulatorObj)

        Plugins.Simulator.SimulatorBase.Model.__init__(self, 'ConnectedFMUS', [], config)
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
        for i in xrange(len(self._FMUSimulators)):
            self._FMUSimulators[i].close()

    def closeIntegrationResults(self):
        for i in xrange(len(self._FMUSimulators)):
            self._FMUSimulators[i].integrationResults.close()

    def loadIntegrationResults(self):
        # mark this model integration results as available
        self.integrationResults.isAvailable = True
        for i in xrange(len(self._FMUSimulators)):
            self._FMUSimulators[i].loadResultFile(self._FMUSimulators[i].integrationSettings.resultFileName)

    def simulate(self):
        Tstart = self.integrationSettings.startTime
        Tend = self.integrationSettings.stopTime
        # Initialize integration statistics
        self.integrationStatistics.nTimeEvents = 0
        self.integrationStatistics.nStateEvents = 0
        self.integrationStatistics.nGridPoints = 0
        self.integrationStatistics.reachedTime = Tstart

        for i in xrange(len(self._FMUSimulators)):
            self._FMUSimulators[i].integrationSettings = copy.copy(self.integrationSettings)
            self._FMUSimulators[i].integrationSettings.resultFileName = unicode(self._FMUSimulators[i].name + "_1.mtsf")
            self._FMUSimulators[i].simulate()

        i = 0
        while True:
            if i >= len(self._FMUSimulators):
                self.integrationStatistics.reachedTime = Tend
                break
            if self._FMUSimulators[i].integrationStatistics.reachedTime == Tend:
                i = i + 1
#==============================================================================
#          print "self.integrationStatistics.reachedTime = " + str(self.integrationStatistics.reachedTime)
#         # Initialize integration statistics
#         self.integrationStatistics.nTimeEvents = 4
#         self.integrationStatistics.nStateEvents = 5
#         self.integrationStatistics.nGridPoints = 6
#==============================================================================
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
        for i in xrange(len(self._FMUSimulators)):
            self._FMUSimulators[i].setVariableTree()
            for vName, treeVariable in self._FMUSimulators[i].variableTree.variable.iteritems():
                self.variableTree.variable[self._FMUSimulators[i].name + '.' + vName] = Plugins.Simulator.SimulatorBase.TreeVariable(self._FMUSimulators[i].name + '.' + vName, treeVariable.value, treeVariable.valueEdit, treeVariable.unit, treeVariable.variability, treeVariable.attribute)

    def getFMUSimulator(self, name):
        for i in xrange(len(self._FMUSimulators)):
            if (self._FMUSimulators[i].name == name):
                return self._FMUSimulators[i]
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
