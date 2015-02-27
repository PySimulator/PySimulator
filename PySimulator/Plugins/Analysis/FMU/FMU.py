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

import os
from PySide import QtGui, QtCore
import zipfile
import xml.etree.ElementTree as ET
import codecs
from xml.dom import minidom
from datetime import datetime

class FMU(object):

    def __init__(self, name, location, instance):
        self._name = name
        self._location = location
        self._instanceName = name + datetime.now().strftime("%Y%m%d%H%M%S")
        #check if an instance exits when loading from xmlsetup
        if(instance):
           self._instanceName=instance
        self._inputsOutputs = []
        
        try:
            self._fmuFile = zipfile.ZipFile(location, 'r')
        except:
            print "Error opening the FMU file %s" % location
            return
        try:
            self._xmlFile = self._fmuFile.open('modelDescription.xml')
        except:
            print "Error opening the modelDescription.xml file of FMU %s" % location
            return

        modelDescriptionTree = ET.parse(self._xmlFile)
        root = modelDescriptionTree.getroot()
        for variable in root.iter('ScalarVariable'):
            varName = variable.get('name')
            varValueReference = variable.get('valueReference')
            varDescription = variable.get('description')
            varCausality = variable.get('causality')
            if (varCausality == 'input' or varCausality == 'output'):
                _inputOutput = {'name':varName, 'valueReference':varValueReference, 'description': varDescription}
                for varType in variable.iter('Real'):
                    _inputOutput['type'] = 'Real'
                    break
                for varType in variable.iter('Integer'):
                    _inputOutput['type'] = 'Integer'
                    break
                for varType in variable.iter('Boolean'):
                    _inputOutput['type'] = 'Boolean'
                    break
                for varType in variable.iter('String'):
                    _inputOutput['type'] = 'String'
                    break
                if (varCausality == 'input'):
                    _inputOutput['causality'] = 'input'
                elif (varCausality == 'output'):
                    _inputOutput['causality'] = 'output'
                self._inputsOutputs.append(_inputOutput)

class Connection:

    def __init__(self, fromFMU, inputVar, toFMU, outputVar):
        self._fromFMU = fromFMU
        self._inputVar = inputVar
        self._toFMU = toFMU
        self._outputVar = outputVar
        

class InputsOutputsListModel(QtCore.QAbstractListModel):

    def __init__(self):
        QtCore.QAbstractListModel.__init__(self)
        self._inputsOutputs = []

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._inputsOutputs)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid() is True:
            if role == QtCore.Qt.DisplayRole:
                return ("%s (%s)"
                        %
                        (self._inputsOutputs[index.row()]['name'],
                        self._inputsOutputs[index.row()]['causality'])
                        )
            elif role == QtCore.Qt.ToolTipRole:
                return ("<b>Type:</b> %s<br />"
                        "<b>Name:</b> %s<br />"
                        "<b>Value Reference:</b> %s<br />"
                        "<b>Description:</b> %s<br />"
                        %
                        (self._inputsOutputs[index.row()]['type'],
                         self._inputsOutputs[index.row()]['name'],
                         self._inputsOutputs[index.row()]['valueReference'],
                         self._inputsOutputs[index.row()]['description'])
                        )
        return None

    def updateInputs(self, inputsOutputs):
        # clear any existing inputs
        if len(self._inputsOutputs) > 0:
            self.beginRemoveRows(QtCore.QModelIndex(), 0, len(self._inputsOutputs) - 1)
            self._inputsOutputs = []
            self.endRemoveRows()

        # add inputs
        if len(inputsOutputs) > 0:
            self.beginInsertRows(QtCore.QModelIndex(), 0, len(inputsOutputs) - 1)
            self._inputsOutputs = inputsOutputs
            self.endInsertRows()

class ConnectionsListModel(QtCore.QAbstractItemModel):

    def __init__(self):
        QtCore.QAbstractItemModel.__init__(self)
        self._connections = []

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 2

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._connections)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid() is True:
            column = index.column()
            toolTip = ("<b>Connection</b><br />"
                        "<b>From FMU:</b> %s<br />"
                        "<b>Variable:</b> %s<br />"
                        "<b>To FMU:</b> %s<br />"
                        "<b>Variable:</b> %s<br />"
                        %
                        (self._connections[index.row()]._fromFMU._name,
                         self._connections[index.row()]._inputVar['name'],
                         self._connections[index.row()]._toFMU._name,
                         self._connections[index.row()]._outputVar['name'])
                        )
            if column == 0:
                if role == QtCore.Qt.DisplayRole:
                    return ("%s.%s"
                            %
                            (self._connections[index.row()]._fromFMU._name,
                             self._connections[index.row()]._inputVar['name'])
                            )
                elif role == QtCore.Qt.ToolTipRole:
                    return toolTip
            elif column == 1:
                if role == QtCore.Qt.DisplayRole:
                    return ("%s.%s"
                            %
                            (self._connections[index.row()]._toFMU._name,
                             self._connections[index.row()]._outputVar['name'])
                            )
                elif role == QtCore.Qt.ToolTipRole:
                    return toolTip
        return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if (orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole):
            if section == 0:
                return self.tr("From")
            elif section == 1:
                return self.tr("To")

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if self.hasIndex(row, column, parent):
            return self.createIndex(row, column)
        else:
            return QtCore.QModelIndex()

    def parent(self, child=QtCore.QModelIndex()):
        return QtCore.QModelIndex()

    def addConnection(self, fromFMU, inputVar, toFMU, outputVar):
        if not self.containsConnection(fromFMU, inputVar, toFMU, outputVar):
            connection = Connection(fromFMU, inputVar, toFMU, outputVar)
            row = self.rowCount()
            self.beginInsertRows(QtCore.QModelIndex(), row, row)
            self._connections.insert(row, connection)
            self.endInsertRows()
            return True
        else:
            return False

    def removeConnection(self, row):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        connection = self._connections.pop(row)
        del connection
        self.endRemoveRows()

    def containsConnection(self, fromFMU, inputVar, toFMU, outputVar):
        for connection in self._connections:
            if (connection._fromFMU == fromFMU and connection._inputVar == inputVar and
                connection._toFMU == toFMU and connection._outputVar == outputVar):
                return True
        return False

    def handleFMURemoved(self, fmu):
        if len(self._connections) > 0:
            i = 0
            while i < len(self._connections):
                if (self._connections[i]._fromFMU == fmu or self._connections[i]._toFMU == fmu):
                    self.removeConnection(i)
                    # restart iteration
                    i = 0
                else:
                    i += 1

class FMUsListModel(QtCore.QAbstractListModel):

    fmuRemoved = QtCore.Signal(FMU)

    def __init__(self):
        QtCore.QAbstractListModel.__init__(self)
        self._fmus = []

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._fmus)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid() is True:
            if role == QtCore.Qt.DisplayRole:
                return self._fmus[index.row()]._name
            elif role == QtCore.Qt.ToolTipRole:
                return self._fmus[index.row()]._location
        return None

    def addFMU(self, fileName, fmuinstance):
        if not self.containsFMU(fileName):
            fmuFileInfo = QtCore.QFileInfo(fileName)
            row = self.rowCount()
            fmu = FMU(fmuFileInfo.baseName(), fmuFileInfo.absoluteFilePath(), fmuinstance)
            self.beginInsertRows(QtCore.QModelIndex(), row, row)
            self._fmus.insert(row, fmu)
            self.endInsertRows()
            return True
        else:
            return False

    def removeFMU(self, row):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        fmu = self._fmus.pop(row)
        self.fmuRemoved.emit(fmu)
        del fmu
        self.endRemoveRows()

    def containsFMU(self, fileName):
        for fmu in self._fmus:
            if fmu._location == fileName:
                return True
        return False

class ConnectFMUsDialog(QtGui.QDialog):

    def __init__(self, gui, fmuType):
        QtGui.QDialog.__init__(self)

        self._fmuType = fmuType
        if self._fmuType == 1:
            self.setWindowTitle("Connect FMUs for Model Exchange")
        elif self._fmuType == 2:
            self.setWindowTitle("Connect FMUs for Co-Simulation")
        self.setWindowIcon(QtGui.QIcon(gui.rootDir + '/Icons/pysimulator.ico'))
        
        # xml setup file
        self.xmlFileLabel = QtGui.QLabel(self.tr("Load XML:"))
        self.xmlFileTextBox = QtGui.QLineEdit()
        browseXmlSetupFileButton = QtGui.QPushButton(self.tr("Browse"))
        browseXmlSetupFileButton.clicked.connect(self.browseXmlSetupFile)
        # list of FMUs
        fmuLabel = QtGui.QLabel(self.tr("List of FMUs:"))
        self._fmusListModel = FMUsListModel()
        self._fmusListView = QtGui.QListView()
        self._fmusListView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self._fmusListView.setModel(self._fmusListModel)
        # add the fmu buttons to button box
        browseFmuFileButton = QtGui.QPushButton(self.tr("Browse"))
        browseFmuFileButton.clicked.connect(self.browseFmuFile)
        removeFmuButton = QtGui.QPushButton(self.tr("Remove"))
        removeFmuButton.clicked.connect(self.removeFmuFiles)
        FmuButtonBox = QtGui.QDialogButtonBox(QtCore.Qt.Vertical)
        FmuButtonBox.addButton(browseFmuFileButton, QtGui.QDialogButtonBox.ActionRole)
        FmuButtonBox.addButton(removeFmuButton, QtGui.QDialogButtonBox.ActionRole)
        # input & output comboboxes
        self._fromFMUsComboBox = QtGui.QComboBox()
        self._fromFMUsComboBox.setModel(self._fmusListModel)
        self._fromFMUsComboBox.currentIndexChanged.connect(self.fromFMUChanged)
        self._fromListModel = InputsOutputsListModel()
        self._fromComboBox = QtGui.QComboBox()
        self._fromComboBox.setModel(self._fromListModel)
        self._toFMUsComboBox = QtGui.QComboBox()
        self._toFMUsComboBox.setModel(self._fmusListModel)
        self._toFMUsComboBox.currentIndexChanged.connect(self.toFMUChanged)
        self._toListModel = InputsOutputsListModel()
        self._toComboBox = QtGui.QComboBox()
        self._toComboBox.setModel(self._toListModel)
        # add connection button
        addConnectionButton = QtGui.QPushButton(self.tr("Add Connection"))
        addConnectionButton.clicked.connect(self.addFromToConnection)
        # connections list view
        self._connectionsListModel = ConnectionsListModel()
        self._fmusListModel.fmuRemoved.connect(self._connectionsListModel.handleFMURemoved)
        self._connectionsTableView = QtGui.QTableView()
        self._connectionsTableView.verticalHeader().hide();
        self._connectionsTableView.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
        self._connectionsTableView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self._connectionsTableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self._connectionsTableView.setModel(self._connectionsListModel)
        # remove connection button
        removeConnectionButton = QtGui.QPushButton(self.tr("Remove Connection(s)"))
        removeConnectionButton.clicked.connect(self.removeFromToConnection)
        # layout for inputs & outputs
        FromToGridLayout = QtGui.QGridLayout()
        FromToGridLayout.addWidget(QtGui.QLabel(self.tr("From")), 0, 0)
        FromToGridLayout.addWidget(QtGui.QLabel(self.tr("To")), 0, 1)
        FromToGridLayout.addWidget(self._fromFMUsComboBox, 1, 0)
        FromToGridLayout.addWidget(self._toFMUsComboBox, 1, 1)
        FromToGridLayout.addWidget(self._fromComboBox, 2, 0)
        FromToGridLayout.addWidget(self._toComboBox, 2, 1)
        FromToGridLayout.addWidget(addConnectionButton, 3, 0, 1, 2)
        FromToGridLayout.addWidget(self._connectionsTableView, 4, 0, 1, 2)
        FromToGridLayout.addWidget(removeConnectionButton, 5, 0, 1, 2)
        # ok and cancel buttons
        okButton = QtGui.QPushButton(self.tr("OK"))
        okButton.clicked.connect(self.saveConnectionsXML)
        cancelButton = QtGui.QPushButton(self.tr("Cancel"))
        cancelButton.clicked.connect(self.reject)
        # add the buttons to button box
        navigationButtonBox = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal)
        navigationButtonBox.addButton(okButton, QtGui.QDialogButtonBox.ActionRole)
        navigationButtonBox.addButton(cancelButton, QtGui.QDialogButtonBox.ActionRole)
        # save to file
        self._saveToFile = QtGui.QCheckBox(self.tr("Save to file"))
        self._saveToFile.setChecked(True)
        # horizontal layout for saveToFile and buttons
        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.addWidget(self._saveToFile, 0, QtCore.Qt.AlignLeft)
        horizontalLayout.addWidget(navigationButtonBox, 0, QtCore.Qt.AlignRight)
        # set the widget layout
        mainLayout = QtGui.QGridLayout()
        mainLayout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        mainLayout.addWidget(self.xmlFileLabel, 0, 0)
        mainLayout.addWidget(self.xmlFileTextBox, 0, 1)
        mainLayout.addWidget(browseXmlSetupFileButton, 0, 2)
        mainLayout.addWidget(fmuLabel, 1, 0, 1, 1, QtCore.Qt.AlignTop)
        mainLayout.addWidget(self._fmusListView, 1, 1)
        mainLayout.addWidget(FmuButtonBox, 1, 2)
        mainLayout.addLayout(FromToGridLayout, 2, 0, 1, 3)
        mainLayout.addLayout(horizontalLayout, 3, 0, 1, 3)
        self.setLayout(mainLayout)

    def browseXmlSetupFile(self):
        (setupfile, trash) = QtGui.QFileDialog().getOpenFileName(self, 'Open File', os.getcwd(), '(*.xml)')
        if setupfile != '':
             self.xmlFileTextBox.setText(setupfile)
             tree = ET.parse(setupfile)
             root = tree.getroot()
             
             ## Add fmu's to list with correct instance from xmlsetup
             for fmu in root.iter('fmu'):
                 name = fmu.get('path')
                 fmuinstance=fmu.get('instanceName')
                 self._fmusListModel.addFMU(name, fmuinstance)
                     
             ## Add connection information to table from xmlsetup 
             for connection in root.iter('connection'):
                frominstance=connection.get('fromInstanceName')
                fromvar=connection.get('fromVariableName')
                toinstance=connection.get('toInstanceName')
                tovar=connection.get('toVariableName')
                
                for i in xrange(len(self._fmusListModel._fmus)):
                      instance=self._fmusListModel._fmus[i]._instanceName
                      
                      if (instance==frominstance):
                           fromFMU=self._fmusListModel._fmus[i]
                           frominputoutputvar=self._fmusListModel._fmus[i]._inputsOutputs
                           for j in xrange(len(frominputoutputvar)):
                                varname=frominputoutputvar[j]['name']
                                if(fromvar==varname):
                                      inputVar=frominputoutputvar[j]  
                                      
                      if (instance==toinstance):
                           toFMU=self._fmusListModel._fmus[i]
                           toinputoutputvar=self._fmusListModel._fmus[i]._inputsOutputs
                           for j in xrange(len(toinputoutputvar)):
                                varname=toinputoutputvar[j]['name']                               
                                if(tovar==varname):
                                      outputVar=toinputoutputvar[j]                                    
                              
                self._connectionsListModel.addConnection(fromFMU, inputVar, toFMU, outputVar)
                self._connectionsTableView.resizeColumnsToContents()

    def browseFmuFile(self):
        (fileNames, trash) = QtGui.QFileDialog().getOpenFileNames(self, 'Open File', os.getcwd(), '(*.fmu)')
        for fileName in fileNames:
            fileName = fileName.replace('\\', '/')
            if fileName != '':
                # add the FMU to FMUsListModel
                if not self._fmusListModel.addFMU(fileName, ""):
                    QtGui.QMessageBox().information(self, self.tr("Information"),
                                      self.tr("The FMU {0} already exists.").format(fileName),
                                      QtGui.QMessageBox.Ok)

    def removeFmuFiles(self):
        if len(self._fmusListView.selectedIndexes()) > 0:
            confirmMsg = self.tr("Removing the FMU will also remove the connection associated with it. Are you sure you want to remove?")
            confirm = QtGui.QMessageBox.question(self, self.tr("Question"), confirmMsg,
                                                 QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                 QtGui.QMessageBox.No)
            if confirm == QtGui.QMessageBox.Yes:
                i = 0
                while i < len(self._fmusListView.selectedIndexes()):
                    row = self._fmusListView.selectedIndexes()[i].row()
                    self._fmusListModel.removeFMU(row)
                    # restart iteration
                    i = 0

    def fromFMUChanged(self, index):
        if len(self._fmusListModel._fmus) > index and index != -1:
            self._fromListModel.updateInputs(self._fmusListModel._fmus[index]._inputsOutputs)
        else:
            self._fromListModel.updateInputs([])

    def toFMUChanged(self, index):
        if len(self._fmusListModel._fmus) > index and index != -1:
            self._toListModel.updateInputs(self._fmusListModel._fmus[index]._inputsOutputs)
        else:
            self._toListModel.updateInputs([])

    def addFromToConnection(self):
        fromFMU = inputVar = toFMU = outputVar = None
        if len(self._fmusListModel._fmus) > self._fromFMUsComboBox.currentIndex() and self._fromFMUsComboBox.currentIndex() != -1:
            fromFMU = self._fmusListModel._fmus[self._fromFMUsComboBox.currentIndex()]
        if len(self._fromListModel._inputsOutputs) > self._fromComboBox.currentIndex() and self._fromComboBox.currentIndex() != -1:
            inputVar = self._fromListModel._inputsOutputs[self._fromComboBox.currentIndex()]
        if len(self._fmusListModel._fmus) > self._toFMUsComboBox.currentIndex() and self._toFMUsComboBox.currentIndex() != -1:
            toFMU = self._fmusListModel._fmus[self._toFMUsComboBox.currentIndex()]
        if len(self._toListModel._inputsOutputs) > self._toComboBox.currentIndex() and self._toComboBox.currentIndex() != -1:
            outputVar = self._toListModel._inputsOutputs[self._toComboBox.currentIndex()]
        if (fromFMU is None or inputVar is None or toFMU is None or outputVar is None):
            pass
        else:
            if self._connectionsListModel.addConnection(fromFMU, inputVar, toFMU, outputVar):
                self._connectionsTableView.resizeColumnsToContents()
            else:
                QtGui.QMessageBox().information(self, self.tr("Information"),
                              self.tr("This connection already exists."), QtGui.QMessageBox.Ok)

    def removeFromToConnection(self):
        i = 0
        while i < len(self._connectionsTableView.selectedIndexes()):
            row = self._connectionsTableView.selectedIndexes()[i].row()
            self._connectionsListModel.removeConnection(row)
            # restart iteration
            i = 0

    def saveConnectionsXML(self):
        if self._saveToFile.isChecked():
            (fileName, trash) = QtGui.QFileDialog().getSaveFileName(self, self.tr("Save file"), os.getcwd(), '(*.xml)')
            if fileName == '':
                return
    
            xmlTemplate = '<?xml version="1.0" encoding="utf-8"?><connectedFmus></connectedFmus>'
            rootElement = ET.fromstring(xmlTemplate)
            # add fmus to file
            fmusElement = ET.SubElement(rootElement, "fmus")
            for fmu in self._fmusListModel._fmus:
                ET.SubElement(fmusElement, "fmu", {"name":fmu._name, "instanceName":fmu._instanceName, "path":fmu._location})
    
            # add connections to file
            connectionsElement = ET.SubElement(rootElement, "connections")
            for connection in self._connectionsListModel._connections:
                ET.SubElement(connectionsElement, "connection", {"fromInstanceName":connection._fromFMU._instanceName, "fromVariableName":connection._inputVar['name'], "toInstanceName":connection._toFMU._instanceName, "toVariableName":connection._outputVar['name']})
    
            # pretty print the xml
            xml = prettify(rootElement)
            try:
                xmlFile = codecs.open(fileName, "w", "utf-8")
                xmlFile.write(xml)
                xmlFile.close()
                self.accept()
            except IOError, e:
                print "Failed to write the xml file. %s" % e
        else:
            self.accept()

def prettify(elem):
   """Return a pretty-printed XML string for the Element """
   rough_string = ET.tostring(elem, "utf-8")
   reparsed = minidom.parseString(rough_string)
   return reparsed.toprettyxml(indent="  ")

def NewConnectME(model, gui):
    print "New connected FMU for Model Exchange"
    pass
    
def NewConnectCS(model, gui):
    connectFMUsDialog = ConnectFMUsDialog(gui, 2)
    connectFMUsDialog.exec_()

def Settings(model, gui):    

    class SettingsControl(QtGui.QDialog):
        ''' Class for the Settings Control GUI '''

        def __init__(self):
            QtGui.QDialog.__init__(self)
            self.setModal(False)
            self.setWindowTitle("FMU Settings")            
                        
            _mainGrid = QtGui.QGridLayout(self)

            _ImportFMU = QtGui.QGroupBox("Importing FMUs", self)
            _mainGrid.addWidget(_ImportFMU, 0, 0, 1, 3)
            _ImportFMULayout = QtGui.QGridLayout()
            _ImportFMU.setLayout(_ImportFMULayout)
            _ImportFMULayout.addWidget(QtGui.QLabel("Default FMI type:"), 0, 0)
            
            self.me = QtGui.QRadioButton("Model Exchange", self)            
            _ImportFMULayout.addWidget(self.me, 0, 1)
            self.me.toggled.connect(self.changeToME)
            self.cs = QtGui.QRadioButton("CoSimulation", self)
            _ImportFMULayout.addWidget(self.cs, 0, 2)
            self.cs.toggled.connect(self.changeToCS)
            
            _ImportFMULayout.addWidget(QtGui.QLabel("The default FMI type will be used, if an FMU containing"), 1, 0, 1, 3)
            _ImportFMULayout.addWidget(QtGui.QLabel("both Model Exchange and CoSimulation models is opened."), 2, 0, 1, 3)

            self.closeButton = QtGui.QPushButton("Close", self)
            _mainGrid.addWidget(self.closeButton, 1, 1)
            self.closeButton.clicked.connect(self.close)
            
            if not gui.config['Plugins']['FMU'].has_key('importType'):
                gui.config['Plugins']['FMU']['importType'] = 'me'
                gui.config.write() 
                
            if gui.config['Plugins']['FMU']['importType'] == 'me':
                self.me.setChecked(True)
            else:
                self.cs.setChecked(True)
           
        def changeToCS(self):
            gui.config['Plugins']['FMU']['importType'] = 'cs'
            gui.config.write()
        
        def changeToME(self):
            gui.config['Plugins']['FMU']['importType'] = 'me'
            gui.config.write()

    # Code of function
    gui.FMUSettingscontrol = SettingsControl()
    gui.FMUSettingscontrol.show()

def getModelCallbacks():
    ''' Registers model callbacks with main application
        return a list of lists, one list for each callback, each sublist
        containing a name for the function and a function pointer
    '''
    return [["New connected FMU for Model Exchange...", NewConnectME], ["New connected FMU for CoSimulation...", NewConnectCS], ["Settings...", Settings]]