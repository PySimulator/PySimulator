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

class FMU(object):

    def __init__(self, name, location):
        self._name = name
        self._location = location
        self._inputs = []
        self._outputs = []
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
            if (varCausality == 'input'):
                _input = {'name':varName, 'valueReference':varValueReference, 'description': varDescription}
                for varType in variable.iter('Real'):
                    _input['type'] = 'Real'
                    break
                for varType in variable.iter('Integer'):
                    _input['type'] = 'Integer'
                    break
                for varType in variable.iter('Boolean'):
                    _input['type'] = 'Boolean'
                    break
                for varType in variable.iter('String'):
                    _input['type'] = 'String'
                    break
                self._inputs.append(_input)
            elif (varCausality == 'output'):
                _output = {'name':varName, 'valueReference':varValueReference, 'description': varDescription}
                for varType in variable.iter('Real'):
                    _output['type'] = 'Real'
                    break
                for varType in variable.iter('Integer'):
                    _output['type'] = 'Integer'
                    break
                for varType in variable.iter('Boolean'):
                    _output['type'] = 'Boolean'
                    break
                for varType in variable.iter('String'):
                    _output['type'] = 'String'
                    break
                self._outputs.append(_output)

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
                return self._inputsOutputs[index.row()]['name']
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
                        "<b>Input Variable:</b> %s<br />"
                        "<b>To FMU:</b> %s<br />"
                        "<b>Output Variable:</b> %s<br />"
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

    def addFMU(self, fileName):
        if not self.containsFMU(fileName):
            fmuFileInfo = QtCore.QFileInfo(fileName)
            fmu = FMU(fmuFileInfo.baseName(), fmuFileInfo.absoluteFilePath())
            row = self.rowCount()
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
        xmlFileLabel = QtGui.QLabel(self.tr("Load XML:"))
        xmlFileTextBox = QtGui.QLineEdit()
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
        self._inputFMUsComboBox = QtGui.QComboBox()
        self._inputFMUsComboBox.setModel(self._fmusListModel)
        self._inputFMUsComboBox.currentIndexChanged.connect(self.inputFMUChanged)
        self._inputsListModel = InputsOutputsListModel()
        self._inputsComboBox = QtGui.QComboBox()
        self._inputsComboBox.setModel(self._inputsListModel)
        self._outputFMUsComboBox = QtGui.QComboBox()
        self._outputFMUsComboBox.setModel(self._fmusListModel)
        self._outputFMUsComboBox.currentIndexChanged.connect(self.outputFMUChanged)
        self._outputsListModel = InputsOutputsListModel()
        self._outputsComboBox = QtGui.QComboBox()
        self._outputsComboBox.setModel(self._outputsListModel)
        # add connection button
        addConnectionButton = QtGui.QPushButton(self.tr("Add Connection"))
        addConnectionButton.clicked.connect(self.addInputOutputConnection)
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
        removeConnectionButton.clicked.connect(self.removeInputOutputConnection)
        # layout for inputs & outputs
        inputsOutputsGridLayout = QtGui.QGridLayout()
        inputsOutputsGridLayout.addWidget(QtGui.QLabel(self.tr("Inputs")), 0, 0)
        inputsOutputsGridLayout.addWidget(QtGui.QLabel(self.tr("Outputs")), 0, 1)
        inputsOutputsGridLayout.addWidget(self._inputFMUsComboBox, 1, 0)
        inputsOutputsGridLayout.addWidget(self._outputFMUsComboBox, 1, 1)
        inputsOutputsGridLayout.addWidget(self._inputsComboBox, 2, 0)
        inputsOutputsGridLayout.addWidget(self._outputsComboBox, 2, 1)
        inputsOutputsGridLayout.addWidget(addConnectionButton, 3, 0, 1, 2)
        inputsOutputsGridLayout.addWidget(self._connectionsTableView, 4, 0, 1, 2)
        inputsOutputsGridLayout.addWidget(removeConnectionButton, 5, 0, 1, 2)
        # ok and cancel buttons
        okButton = QtGui.QPushButton(self.tr("OK"))
        okButton.clicked.connect(self.accept)
        cancelButton = QtGui.QPushButton(self.tr("Cancel"))
        cancelButton.clicked.connect(self.reject)
        # add the buttons to button box
        navigationButtonBox = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal)
        navigationButtonBox.addButton(okButton, QtGui.QDialogButtonBox.ActionRole)
        navigationButtonBox.addButton(cancelButton, QtGui.QDialogButtonBox.ActionRole)
        # save to file
        saveToFile = QtGui.QCheckBox(self.tr("Save to file"))
        saveToFile.setChecked(True)
        # horizontal layout for saveToFile and buttons
        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.addWidget(saveToFile, 0, QtCore.Qt.AlignLeft)
        horizontalLayout.addWidget(navigationButtonBox, 0, QtCore.Qt.AlignRight)
        # set the widget layout
        mainLayout = QtGui.QGridLayout()
        mainLayout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        mainLayout.addWidget(xmlFileLabel, 0, 0)
        mainLayout.addWidget(xmlFileTextBox, 0, 1)
        mainLayout.addWidget(browseXmlSetupFileButton, 0, 2)
        mainLayout.addWidget(fmuLabel, 1, 0, 1, 1, QtCore.Qt.AlignTop)
        mainLayout.addWidget(self._fmusListView, 1, 1)
        mainLayout.addWidget(FmuButtonBox, 1, 2)
        mainLayout.addLayout(inputsOutputsGridLayout, 2, 0, 1, 3)
        mainLayout.addLayout(horizontalLayout, 3, 0, 1, 3)
        self.setLayout(mainLayout)

    def browseXmlSetupFile(self):
        (fileName, trash) = QtGui.QFileDialog().getOpenFileName(self, 'Open File', os.getcwd(), '(*.xml)')
        if fileName != '':
             self.xmlFileEdit.setText(fileName)
             setupfile=self.xmlFileEdit.text()
             tree = ET.parse(setupfile)
             root = tree.getroot()
             for fmu in root.iter('fmu'):
                 name = fmu.get('path')
                 self.fmu.addItem(name)
             
             for connection in root.iter('connection'):
                fid=connection.get('fromFmuId')
                fvar=connection.get('fromFmuvar')
                fvarcon=connection.get('fromFmuvarconnection')
                fval=connection.get('fromValueReference')
                fromtable=''.join([fid,' ',fvar,' ',fvarcon,' ','(',fval,')'])
                tid=connection.get('toFmuId')
                tvar=connection.get('toFmuvar')
                tvarcon=connection.get('toFmuvarconnection')
                tval=connection.get('toValueReference') 
                totable=''.join([tid,' ',tvar,' ',tvarcon,' ','(',tval,')'])
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QtGui.QTableWidgetItem(fromtable))    
                self.table.setItem(row, 1, QtGui.QTableWidgetItem(totable))                    
                self.table.resizeColumnsToContents()

    def browseFmuFile(self):
        (fileNames, trash) = QtGui.QFileDialog().getOpenFileNames(self, 'Open File', os.getcwd(), '(*.fmu)')
        for fileName in fileNames:
            fileName = fileName.replace('\\', '/')
            if fileName != '':
                # add the FMU to FMUsListModel
                if not self._fmusListModel.addFMU(fileName):
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

    def inputFMUChanged(self, index):
        if len(self._fmusListModel._fmus) > index and index != -1:
            self._inputsListModel.updateInputs(self._fmusListModel._fmus[index]._inputs)
        else:
            self._inputsListModel.updateInputs([])

    def outputFMUChanged(self, index):
        if len(self._fmusListModel._fmus) > index and index != -1:
            self._outputsListModel.updateInputs(self._fmusListModel._fmus[index]._outputs)
        else:
            self._outputsListModel.updateInputs([])

    def addInputOutputConnection(self):
        fromFMU = inputVar = toFMU = outputVar = None
        if len(self._fmusListModel._fmus) > self._inputFMUsComboBox.currentIndex() and self._inputFMUsComboBox.currentIndex() != -1:
            fromFMU = self._fmusListModel._fmus[self._inputFMUsComboBox.currentIndex()]
        if len(self._inputsListModel._inputsOutputs) > self._inputsComboBox.currentIndex() and self._inputsComboBox.currentIndex() != -1:
            inputVar = self._inputsListModel._inputsOutputs[self._inputsComboBox.currentIndex()]
        if len(self._fmusListModel._fmus) > self._outputFMUsComboBox.currentIndex() and self._outputFMUsComboBox.currentIndex() != -1:
            toFMU = self._fmusListModel._fmus[self._outputFMUsComboBox.currentIndex()]
        if len(self._outputsListModel._inputsOutputs) > self._outputsComboBox.currentIndex() and self._outputsComboBox.currentIndex() != -1:
            outputVar = self._outputsListModel._inputsOutputs[self._outputsComboBox.currentIndex()]
        if (fromFMU is None or inputVar is None or toFMU is None or outputVar is None):
            pass
        else:
            if self._connectionsListModel.addConnection(fromFMU, inputVar, toFMU, outputVar):
                self._connectionsTableView.resizeColumnsToContents()
            else:
                QtGui.QMessageBox().information(self, self.tr("Information"),
                              self.tr("This connection already exists."), QtGui.QMessageBox.Ok)

    def removeInputOutputConnection(self):
        i = 0
        while i < len(self._connectionsTableView.selectedIndexes()):
            row = self._connectionsTableView.selectedIndexes()[i].row()
            self._connectionsListModel.removeConnection(row)
            # restart iteration
            i = 0

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