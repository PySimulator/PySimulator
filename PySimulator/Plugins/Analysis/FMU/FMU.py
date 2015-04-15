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
import ConnectedFMUSimulation
import os
from PySide import QtGui, QtCore
import zipfile
import xml.etree.ElementTree as ET
import codecs
from xml.dom import minidom

class FMU(object):

    def __init__(self, name, location):
        self._name = name
        self._location = location
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

class FMUsListModel(QtCore.QAbstractItemModel):

    fmuRemoved = QtCore.Signal(FMU)

    def __init__(self):
        QtCore.QAbstractItemModel.__init__(self)
        self._fmus = []

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 2

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._fmus)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid() is True:
            column = index.column()
            if column == 0:
                if role == QtCore.Qt.DisplayRole:
                    return self._fmus[index.row()]._name
                elif role == QtCore.Qt.ToolTipRole:
                    return self._fmus[index.row()]._name
            elif column == 1:
                if role == QtCore.Qt.DisplayRole:
                    return self._fmus[index.row()]._location
                elif role == QtCore.Qt.ToolTipRole:
                    return self._fmus[index.row()]._location
        return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if (orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole):
            if section == 0:
                return self.tr("Name")
            elif section == 1:
                return self.tr("Location")

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if self.hasIndex(row, column, parent):
            return self.createIndex(row, column)
        else:
            return QtCore.QModelIndex()

    def parent(self, child=QtCore.QModelIndex()):
        return QtCore.QModelIndex()

    def addFMU(self, fileName, fmuName = None):
        fmuFileInfo = QtCore.QFileInfo(fileName)
        row = self.rowCount()
        if fmuName is None:
            fmuName = self.getUniqueFMUName(fmuFileInfo.completeBaseName())
        fmu = FMU(fmuName, fmuFileInfo.absoluteFilePath())
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        self._fmus.insert(row, fmu)
        self.endInsertRows()

    def removeFMU(self, row):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        fmu = self._fmus.pop(row)
        self.fmuRemoved.emit(fmu)
        del fmu
        self.endRemoveRows()

    def getUniqueFMUName(self, name, number = 1):
      fmuName = name + str(number)
      for fmu in self._fmus:
          if fmu._name == fmuName:
              fmuName = self.getUniqueFMUName(name, number + 1)
              break
      return fmuName

class ConnectFMUsDialog(QtGui.QDialog):

    def __init__(self, gui, fmuType, setupfile=None):
        QtGui.QDialog.__init__(self)
        self.setMinimumWidth(500)        
        
        self._fmuType = fmuType
        self._setupfile = setupfile
        self._gui = gui
        # FMUs model and view
        self._fmusListModel = FMUsListModel()
        self._fmusTableView = QtGui.QTableView()
        self._fmusTableView.verticalHeader().hide();
        self._fmusTableView.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
        self._fmusTableView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self._fmusTableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self._fmusTableView.setModel(self._fmusListModel)
        # add the fmu buttons to button box
        addFmuButton = QtGui.QPushButton(self.tr("Add FMU"))
        addFmuButton.clicked.connect(self.addFMUFile)
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
        # remove fmu button
        removeFmuButton = QtGui.QPushButton(self.tr("Remove FMU(s)"))
        removeFmuButton.clicked.connect(self.removeFmuFiles)
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
        FromToGridLayout.addWidget(QtGui.QLabel(self.tr("List of Connections:")), 0, 0, 1, 2)
        FromToGridLayout.addWidget(QtGui.QLabel(self.tr("From")), 1, 0)
        FromToGridLayout.addWidget(QtGui.QLabel(self.tr("To")), 1, 1)
        FromToGridLayout.addWidget(self._fromFMUsComboBox, 2, 0)
        FromToGridLayout.addWidget(self._toFMUsComboBox, 2, 1)
        FromToGridLayout.addWidget(self._fromComboBox, 3, 0)
        FromToGridLayout.addWidget(self._toComboBox, 3, 1)
        FromToGridLayout.addWidget(addConnectionButton, 4, 0, 1, 2)
        FromToGridLayout.addWidget(self._connectionsTableView, 5, 0, 1, 2)
        FromToGridLayout.addWidget(removeConnectionButton, 6, 0, 1, 2)
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
        mainLayout.addWidget(QtGui.QLabel(self.tr("List of FMUs:")), 0, 0)
        mainLayout.addWidget(addFmuButton, 1, 0)
        mainLayout.addWidget(self._fmusTableView, 2, 0)
        mainLayout.addWidget(removeFmuButton, 3, 0)
        mainLayout.addLayout(FromToGridLayout, 4, 0)
        mainLayout.addLayout(horizontalLayout, 5, 0)
        self.setLayout(mainLayout)

        if self._setupfile is not None:
             self._saveToFile.setEnabled(False)
             tree = ET.parse(self._setupfile)
             root = tree.getroot()

             self._fmuType = int(root.get('type'))
             ## Add fmu's to list with correct instance from xmlsetup
             for fmu in root.iter('fmu'):
                 location = fmu.get('path')
                 fmuName=fmu.get('name')
                 self._fmusListModel.addFMU(location, fmuName)
                 self._fmusTableView.resizeColumnsToContents()

             ## Add connection information to table from xmlsetup
             for connection in root.iter('connection'):
                fromFmuName=connection.get('fromFmuName')
                fromvar=connection.get('fromVariableName')
                toFmuName=connection.get('toFmuName')
                tovar=connection.get('toVariableName')

                for i in xrange(len(self._fmusListModel._fmus)):
                      name = self._fmusListModel._fmus[i]._name

                      if (name==fromFmuName):
                           fromFMU=self._fmusListModel._fmus[i]
                           frominputoutputvar=self._fmusListModel._fmus[i]._inputsOutputs
                           for j in xrange(len(frominputoutputvar)):
                                varname=frominputoutputvar[j]['name']
                                if(fromvar==varname):
                                    inputVar=frominputoutputvar[j]

                      if (name==toFmuName):
                           toFMU=self._fmusListModel._fmus[i]
                           toinputoutputvar=self._fmusListModel._fmus[i]._inputsOutputs
                           for j in xrange(len(toinputoutputvar)):
                                varname=toinputoutputvar[j]['name']
                                if(tovar==varname):
                                    outputVar=toinputoutputvar[j]

                if (fromFMU is None or inputVar is None or toFMU is None or outputVar is None):
                    pass
                else:
                    self._connectionsListModel.addConnection(fromFMU, inputVar, toFMU, outputVar)
                    self._connectionsTableView.resizeColumnsToContents()

        if self._fmuType == 1:
            self.setWindowTitle("Connect FMUs for Model Exchange")
        elif self._fmuType == 2:
            self.setWindowTitle("Connect FMUs for Co-Simulation")
        self.setWindowIcon(QtGui.QIcon(gui.rootDir + '/Icons/pysimulator.ico'))

    def addFMUFile(self):
        (fileNames, trash) = QtGui.QFileDialog().getOpenFileNames(self, 'Open File', os.getcwd(), '(*.fmu)')
        for fileName in fileNames:
            fileName = fileName.replace('\\', '/')
            if fileName != '':
                # add the FMU to FMUsListModel
                self._fmusListModel.addFMU(fileName)
                self._fmusTableView.resizeColumnsToContents()

    def removeFmuFiles(self):
        if len(self._fmusTableView.selectedIndexes()) > 0:
            confirmMsg = self.tr("Removing the FMU(s) will also removes its connections. Are you sure you want to remove?")
            confirm = QtGui.QMessageBox.question(self, self.tr("Question"), confirmMsg,
                                                 QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                 QtGui.QMessageBox.No)
            if confirm == QtGui.QMessageBox.Yes:
                i = 0
                while i < len(self._fmusTableView.selectedIndexes()):
                    row = self._fmusTableView.selectedIndexes()[i].row()
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
        if (self._saveToFile.isChecked() and self._saveToFile.isEnabled()):
            (fileName, trash) = QtGui.QFileDialog().getSaveFileName(self, self.tr("Save file"), os.getcwd(), '(*.xml)')

        else:
            if self._setupfile is not None:
               fileName = self._setupfile
            else:
               fileName = ''

        xmlTemplate = '<?xml version="1.0" encoding="utf-8"?><connectedFmus></connectedFmus>'
        rootElement = ET.fromstring(xmlTemplate)
        rootElement.attrib["type"] = str(self._fmuType)
        # add fmus to file
        fmusElement = ET.SubElement(rootElement, "fmus")
        for fmu in self._fmusListModel._fmus:
            ET.SubElement(fmusElement, "fmu", {"name":fmu._name, "path":fmu._location})

        # add connections to file
        connectionsElement = ET.SubElement(rootElement, "connections")
        for connection in self._connectionsListModel._connections:
            ET.SubElement(connectionsElement, "connection", {"fromFmuName":connection._fromFMU._name, "fromVariableName":connection._inputVar['name'], "toFmuName":connection._toFMU._name, "toVariableName":connection._outputVar['name']})

        # pretty print the xml
        xml = prettify(rootElement)

        if fileName:
          try:
            xmlFile = codecs.open(fileName, "w", "utf-8")
            xmlFile.write(xml)
            xmlFile.close()
            self.accept()
          except IOError, e:
            print "Failed to write the xml file. %s" % e

        StartSimulation(self._gui,xml)

def StartSimulation(gui,xml):
   ###  Main function which starts the Simulation of Connected FMUS ###

   ## Parse the xml-setup and find the connection order from the connection tag as defined by the user
   ## create a graph edges information to find strongly connected components
   ## eg: Let us say there are four FMU'S 1)Step.fmu, 2)PI.fmu , 3)gain.fmu and 4) test.fmu
   ## and we define the connection in the following order 1--->2--->3--->4, then we create the edges information like below
   ## { 'step' : ['PI'],
   ##   'PI'   : ['gain'],
   ##   'gain' : ['test'] }

   root = ET.fromstring(xml)
   graph={}
   for connection in root.iter('connection'):
      frominstance=connection.get('fromInstanceName')
      toinstance=connection.get('toInstanceName')
      graph[frominstance] = [toinstance]
 
   ## Provide the the graph edges to find the strongly connected components using tarjan's algorithm
   #print graph
   connected_components = StronglyConnectedComponents(graph)
  
   ## Check for Algebraic loops  ##
   Algebraic_loops=[]
   for i in xrange(len(connected_components)):
        Algebraic_loops.append(len(connected_components[i]))

   True=Algebraic_loops.count(1)==len(Algebraic_loops)

   ## Loop the List FMUs and display in the variable Browser as a SingleComponent
   if True:
      import configobj
      config = configobj.ConfigObj(os.path.join(os.path.expanduser("~"), '.config', 'PySimulator', 'PySimulator.ini'), encoding='utf8')

      modelname=[]
      filename=[]
      for fmu in root.iter('fmu'):
         file=fmu.get('path')
         name=fmu.get('name')
         filename.append(file)
         modelname.append(name)

      model=ConnectedFMUSimulation.Model(modelname, filename, config)
      gui._newModel(model)

   else:
      msg=QtGui.QMessageBox()
      msg.setText("The connections contains Algebraic Loops, Currently PySimulator supports ConnectedFMU Simulation without Algebraic Loops")
      msg.exec_()

def StronglyConnectedComponents(graph):
    ## For each node in the graph the following two information must be set namely index and lowlinks according to tarjan algorithm
    ## eg: If there is node 'A' then Node A should contain A(index,lowlink)
    index_counter =[0]
    stack = []
    lowlinks = {}
    index = {}
    result = []
    def strongconnect(node):
        ## set the index and lowlink of starting Node to be 0
        ## eg: if A is the starting node in the graph then set A(0,0) and increment the index and lowlink for each successor of a node

        index[node] = index_counter[0]
        lowlinks[node] = index_counter[0]
        index_counter[0] += 1
        stack.append(node)

        # Get successors of 'node'
        try:
            successors = graph[node]
        except:
            successors = []

        for successor in successors:
            if successor not in lowlinks:
                # Successor has not yet been visited;
                strongconnect(successor)
                lowlinks[node] = min(lowlinks[node],lowlinks[successor])
            elif successor in stack:
                # the successor is in the stack and hence in the current strongly connected component (SCC)
                lowlinks[node] = min(lowlinks[node],index[successor])

        # If `node` is a root node, pop the stack and generate an SCC
        if lowlinks[node] == index[node]:
            connected_component = []
            while True:
                successor = stack.pop()
                connected_component.append(successor)
                if successor == node:
                    break
            component = tuple(connected_component)
            # storing the result
            result.append(component)

    for node in graph:
        if node not in lowlinks:
            strongconnect(node)

    ## End of the Algorithm, get the Strongly connected component list and pass it to Topological Sort function to get the order of execution
    orderedlist=GetNodeComponentOrder(result,graph)
    return orderedlist

def GetNodeComponentOrder(result,graph):
    ## This Function is used to get Strongly connected Components list from Tarjan algorithm and create a New Graph components information
    ## to find the order of execution of a Directed Graph using Topological Sort Algorithm

    components = result

    node_component = {}
    for component in components:
        for node in component:
            node_component[node] = component

    component_graph = {}
    for component in components:
        component_graph[component] = []

    for node in graph:
        node_c = node_component[node]
        for successor in graph[node]:
            successor_c = node_component[successor]
            if node_c != successor_c:
                component_graph[node_c].append(successor_c)

    return topological_sort(component_graph)

def topological_sort(graph):
    ### Find the order of execution from the Connected Graph components ###

    ## As a first step, Assign each node in Graph with number of incoming edges set to 0
    count = { }
    for node in graph:
        count[node] = 0

    ## For each node in the graph determine the number of incoming edges and set the count,
    ## In this phase we determine the root node, A node with no incoming edge will be the start node
    for node in graph:
        for successor in graph[node]:
            count[successor] += 1

    startnode = [ node for node in graph if count[node] == 0 ]

    ## After finding the start node, append it to list until all the successor of graph is completed which gives the order of execution
    result = [ ]
    while startnode:
        node = startnode.pop(-1)
        result.append(node)

        for successor in graph[node]:
            count[successor] -= 1
            if count[successor] == 0:
                startnode.append(successor)

    return result


def prettify(elem):
   """Return a pretty-printed XML string for the Element """
   rough_string = ET.tostring(elem, "utf-8")
   reparsed = minidom.parseString(rough_string)
   return reparsed.toprettyxml(indent="  ")

def NewConnectME(model, gui):
    print "New connected FMU for Model Exchange"
    pass

def NewConnectCS(model, gui):
    connectFMUsDialog = ConnectFMUsDialog(gui, 2, None)
    connectFMUsDialog.exec_()

def OpenConnectFMU(model, gui):
    (fileName, trash) = QtGui.QFileDialog().getOpenFileName(gui, 'Open Connected FMU', os.getcwd(), '(*.xml)')
    if fileName == '':
        pass
    else:
        fileName = fileName.replace('\\', '/')
        connectFMUsDialog = ConnectFMUsDialog(gui, 0, fileName)
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
    return [["New connected FMU for Model Exchange...", NewConnectME], ["New connected FMU for CoSimulation...", NewConnectCS], ["Open connected FMU...", OpenConnectFMU],["Settings...", Settings]]