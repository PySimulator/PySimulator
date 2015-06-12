import os
import numpy
import Plugins.Simulator.FMUSimulator.FMUInterface1 as FMUInterface
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

    def __init__(self, instancename=None, modelFileName=None, config=None, xml=None, xmlFileName=None, independentfmus=None, loggingOn=False):
         ''' ModelFilename are list of strings '''
         self._interfaceinstance=[]
         self._descriptioninstance=[]
         self._xml = xml
         self._xmlFileName = xmlFileName
         for i in xrange(len(modelFileName)):
            self.interface = FMUInterface.FMUInterface(modelFileName[i], self, loggingOn, 'ConnectedFmu',instancename[i])
            self.description = self.interface.description
            self._interfaceinstance.append(self.interface)
            self._descriptioninstance.append(self.description)

         Plugins.Simulator.SimulatorBase.Model.__init__(self, 'ConnectedFMUS', [], config)
         self.modelType = 'Connected FMU Simulation'
         self._availableIntegrationAlgorithms = ["BDF (IDA, Dassl like)", "BDF (CVode)", "Adams (CVode)", "Explicit Euler (fixed step size)"]
         self._IntegrationAlgorithmHasFixedStepSize = [False, False, False, True]
         self._IntegrationAlgorithmCanProvideStepSizeResults = [True, True, True, True]
         self._IntegrationAlgorithmSupportsStateEvents = [True, True, True, True]
         self.integrationResults = Mtsf.Results('')
         self.integrationSettings.resultFileExtension = 'mtsf'
         self.integrationSettings.algorithmName = self._availableIntegrationAlgorithms[0]
         self.simulationStopRequest = False

    def close(self):
        ''' Closing the model, release of resources
        '''
        Plugins.Simulator.SimulatorBase.Model.close(self)
        print "Deleting model instance"

    def simulate(self):
        pass

    def getAvailableIntegrationAlgorithms(self):
        return self._availableIntegrationAlgorithms

    def getIntegrationAlgorithmHasFixedStepSize(self, algorithmName):
        return self._IntegrationAlgorithmHasFixedStepSize[self._availableIntegrationAlgorithms.index(algorithmName)]

    def getIntegrationAlgorithmCanProvideStepSizeResults(self, algorithmName):
        return self._IntegrationAlgorithmCanProvideStepSizeResults[self._availableIntegrationAlgorithms.index(algorithmName)]

    def getIntegrationAlgorithmSupportsStateEvents(self, algorithmName):
        return self._IntegrationAlgorithmSupportsStateEvents[self._availableIntegrationAlgorithms.index(algorithmName)]

    def setVariableTree(self):
      #Sets the variable tree to be displayed in the variable browser.
      #The data is set in self.variableTree that is an instance of the class SimulatorBase.VariableTree

      self.description=self._descriptioninstance

      for i in xrange(len(self.description)):
        for vName, v in self.description[i].scalarVariables.iteritems():
            #text=(self.description[i].modelName).split('.')
            #text=(self.description[i].modelName).replace('.','')
            #varname=text+'.'+vName
            variableAttribute = ''
            if v.description is not None:
                variableAttribute += 'Description:' + chr(9) + v.description + '\n'
            variableAttribute += 'Reference:' + chr(9) + str(v.valueReference)
            if v.variability is not None:
                variableAttribute += '\nVariability:' + chr(9) + v.variability
            if v.causality is not None:
                variableAttribute += '\nCausality:' + chr(9) + v.causality
            if v.alias is not None:
                if v.alias.lower() is not 'noalias':
                    variableAttribute += '\nAlias:' + chr(9) + v.alias
            if v.directDependency is not None:
                variableAttribute += '\nDirect dep.:' + chr(9) + str(v.directDependency)
            if v.type is not None:
                variableAttribute += '\nType:' + chr(9) + v.type.type
                if v.type.description is not None:
                    variableAttribute += '\nType info:' + chr(9) + v.type.description
                if v.type.quantity is not None:
                    variableAttribute += '\nQuantity:' + chr(9) + v.type.quantity
                if v.type.unit is not None:
                    variableAttribute += '\nUnit:' + chr(9) + v.type.unit
                if v.type.displayUnit is not None:
                    variableAttribute += '\nDisplay unit:' + chr(9) + v.type.displayUnit
                if v.type.relativeQuantity is not None:
                    variableAttribute += '\nRel. quantity:' + chr(9) + str(v.type.relativeQuantity)
                if v.type.min is not None:
                    variableAttribute += '\nMin:' + chr(9) + v.type.min
                if v.type.max is not None:
                    variableAttribute += '\nMax:' + chr(9) + v.type.max
                if v.type.nominal is not None:
                    variableAttribute += '\nNominal:' + chr(9) + v.type.nominal
                if v.type.start is not None:
                    variableAttribute += '\nStart:' + chr(9) + v.type.start
                if v.type.fixed is not None:
                    variableAttribute += '\nFixed:' + chr(9) + str(v.type.fixed)
            valueEdit = True  # for the moment
            # ----> Here variable of self.variableTree is set (one entry of the dictionary)
            self.variableTree.variable[vName] = Plugins.Simulator.SimulatorBase.TreeVariable(self.structureVariableName(vName), v.type.start, valueEdit, v.type.unit, v.variability, variableAttribute)

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

class ExplicitEulerSolver():
    '''
        Integration method: Explicit Euler with event handling (without rootfinding)
    '''
    def simulate(self, Tstart, dt, Tend, y0, nOutputIntervals, gridWidth):
        ''' Simulates an ODE-system defined by different functions
            from Tstart to Tend by the explicit Euler method with the fixed step size dt.
            The initial start values of the states are given by the vector y0.
            Time or state events are handled after a successful step if necessary.
            Result points are defined by the number of output intervals 'nOutputIntervals'
            that define a time grid between Tstart and Tend with constant width.
            The grid width can be equal to dt or less or greater than dt.
        '''

        # euler_basic.run_example()

        self.t_cur = Tstart
        self.y_cur = y0.copy()
        y_cur0 = y0.copy()
        # Define vectors for crossing and indicator functions
        z = self.state_events(self.t_cur, self.y_cur, None)
        zb = numpy.empty(len(z))
        zb_new = zb.copy()
        for i in xrange(len(z)):
            zb[i] = (z[i] > 0.0)
        nextTimeEvent = self.time_events(self.t_cur, self.y_cur, None)
        # Write initial values to results
        self.handle_result(None, self.t_cur, self.y_cur)
        # Define next step point and next output point
        stepCounter = 1
        nextStepPoint = min(Tstart + dt, Tend)
        if nOutputIntervals > 0:
            dOutput = (Tend - Tstart) / nOutputIntervals
        else:
            dOutput = dt
        outputStepCounter = 1
        nextOutputPoint = min(Tstart + dOutput, Tend)

        # Start the integration loop
        while self.t_cur < Tend:
            # Define stepsize h, next step point, t_new and time_event
            if nextTimeEvent is None or nextStepPoint < nextTimeEvent:
                time_event = False
                h = min(dt, Tend - self.t_cur)
                stepCounter += 1
                t_new = nextStepPoint
                nextStepPoint = min(Tstart + stepCounter * dt, Tend)
            else:
                time_event = True
                h = nextTimeEvent - self.t_cur
                t_new = nextTimeEvent
                if nextStepPoint == nextTimeEvent:
                    stepCounter += 1
                    nextStepPoint = min(Tstart + stepCounter * dt, Tend)

            # Do the explicit Euler step
            temp = self.y_cur
            self.y_cur = y_cur0
            self.y_cur[:] = temp[:]
            y_cur0 = temp
            t_cur0 = self.t_cur
            self.y_cur = self.y_cur + h * self.rhs(self.t_cur, self.y_cur)
            self.t_cur = t_new

            # Check for state events
            z = self.state_events(self.t_cur, self.y_cur, None)
            for i in xrange(len(z)):
                zb_new[i] = (z[i] > 0.0)
            state_event = (zb_new != zb)
            temp = zb
            zb = zb_new
            zb_new = temp

            # Inform about completed step
            self.completed_step(self)

            def interpolateLinear(a1, b1, a2, b2, t):
                return (b2 - b1) / (a2 - a1) * (t - a1) + b1

            # Write output points until the current time
            while nextOutputPoint < self.t_cur:
                y_Output = interpolateLinear(t_cur0, y_cur0, self.t_cur, self.y_cur, nextOutputPoint)
                self.handle_result(None, nextOutputPoint, y_Output)
                outputStepCounter += 1
                nextOutputPoint = min(Tstart + outputStepCounter * dOutput, Tend)

            # Depending on events have been detected do different tasks
            if state_event.any() or time_event:
                # Event handling
                event_info = [state_event, time_event]
                self.t = self.t_cur
                self.y = self.y_cur
                if not self.handle_event(self, event_info):
                    break
                z = self.state_events(self.t_cur, self.y_cur, None)
                for i in xrange(len(z)):
                    zb[i] = (z[i] > 0.0)
                nextTimeEvent = self.time_events(self.t_cur, self.y_cur, None)
            elif nextOutputPoint == self.t_cur:
                y_Output = interpolateLinear(t_cur0, y_cur0, self.t_cur, self.y_cur, nextOutputPoint)
                self.handle_result(self, nextOutputPoint, y_Output)
                outputStepCounter += 1
                nextOutputPoint = min(Tstart + outputStepCounter * dOutput, Tend)

        self.finalize(None)

