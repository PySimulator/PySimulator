import numpy
import os
import sys
from PySide import QtGui, QtCore
import Plugins.Simulator
import Plugins.Simulator.SimulatorBase as SimulatorBase
import Plugins.SimulationResult as SimulationResult
import zipfile
import xml.etree.ElementTree as ET
from xml.dom import minidom
 

def getModelCallbacks():
    return [["Select list of FMUS...", ConnectFMUMenu]]


def getModelMenuCallbacks():
    return []


def getPlotCallbacks():
    ''' see getModelCallbacks
    '''
    return []
    
def ConnectFMUMenu(model, gui):

    class ConnectFMU(QtGui.QDialog):

       def __init__(self):
            QtGui.QDialog.__init__(self)
            self.setModal(False)
            self.setWindowTitle("Connect List of FMUS")
            self.setWindowIcon(QtGui.QIcon(gui.rootDir + '/Icons/pysimulatorLists.ico'))
           
            mainGrid = QtGui.QGridLayout(self)
            
            self.xmlFile = QtGui.QLabel("Load XML", self)
            mainGrid.addWidget(self.xmlFile, 0, 0, QtCore.Qt.AlignRight)
            self.xmlFileEdit = QtGui.QLineEdit("", self)
            mainGrid.addWidget(self.xmlFileEdit, 0, 1)
            
            self.xmlSetupFile = QtGui.QPushButton("Select", self)
            mainGrid.addWidget(self.xmlSetupFile, 0, 2)
            self.xmlSetupFile.clicked.connect(self.display)

            
            self.File = QtGui.QLabel("Load file", self)
            mainGrid.addWidget(self.File, 1, 0, QtCore.Qt.AlignRight)
            self.setupFileEdit = QtGui.QLineEdit("", self)
            mainGrid.addWidget(self.setupFileEdit, 1, 1)
            
            self.browseSetupFile = QtGui.QPushButton("Select", self)
            mainGrid.addWidget(self.browseSetupFile, 1, 2)
            
            
            self.addButton = QtGui.QPushButton("Add", self)
            mainGrid.addWidget(self.addButton, 1, 3)
            self.addButton.clicked.connect(self.add)
            
            self.fmulabel = QtGui.QLabel("FMUs", self)
            mainGrid.addWidget(self.fmulabel, 2, 0, QtCore.Qt.AlignRight)
            self.simulator = QtGui.QListWidget(self)
            self.simulator.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
            self.simulator.setFixedHeight(70)
            mainGrid.addWidget(self.simulator, 2, 1)
            
            self.removeButton = QtGui.QPushButton("Remove", self)
            mainGrid.addWidget(self.removeButton, 2, 2)
            self.removeButton.clicked.connect(self.remove)
            
            self.parseButton = QtGui.QPushButton("Next", self)
            mainGrid.addWidget(self.parseButton, 3, 2)
            self.parseButton.clicked.connect(self.next)
                    
            self.variablelist = QtGui.QLabel("Select Variables", self)
            mainGrid.addWidget(self.variablelist, 4, 0, QtCore.Qt.AlignRight)
            self.variablelist.hide()
            
            self.combo = QtGui.QComboBox()
            self.combo.setFixedSize(250,20)
            mainGrid.addWidget(self.combo, 4, 1)
            self.combo.hide()
            
            self.combo1 = QtGui.QComboBox()
            self.combo1.setFixedSize(250,20)
            mainGrid.addWidget(self.combo1, 4, 2)
            self.combo1.hide()

            self.connectButton = QtGui.QPushButton("Connect", self)
            mainGrid.addWidget(self.connectButton, 4, 3)
            self.connectButton.clicked.connect(self.connect)
            self.connectButton.hide()  
            
            self.connectionlist = QtGui.QLabel("Connection List", self)
            mainGrid.addWidget(self.connectionlist, 5, 0, QtCore.Qt.AlignRight)
            self.connectionlist.hide()
            '''
            self.componentConnect = QtGui.QListWidget(self)
            self.componentConnect.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
            self.componentConnect.setFixedHeight(200)
            mainGrid.addWidget(self.componentConnect, 5, 1)
            self.componentConnect.hide() 
            '''
            self.table = QtGui.QTableWidget(self)
            self.table.setRowCount(0)
            self.table.setColumnCount(2)
            self.table.setFixedSize(300,200)
            self.table.setHorizontalHeaderLabels(["From","To"])

            mainGrid.addWidget(self.table, 5, 1)
            self.table.hide() 
            
            self.removeButtonconnect = QtGui.QPushButton("Remove", self)
            self.removeButtonconnect.setFixedSize(90,25)
            mainGrid.addWidget(self.removeButtonconnect, 5, 2)
            self.removeButtonconnect.clicked.connect(self.connectremove)
            self.removeButtonconnect.hide()
            
            self.SaveFile = QtGui.QLabel("Save File", self)
            mainGrid.addWidget(self.SaveFile, 6, 0, QtCore.Qt.AlignRight)
            self.SaveFileEdit = QtGui.QLineEdit("", self)
            mainGrid.addWidget(self.SaveFileEdit, 6, 1)
            self.SaveFile.hide()
            self.SaveFileEdit.hide()
            
            self.saveButton = QtGui.QPushButton("Select", self)
            self.saveButton.setFixedSize(90,25)
            mainGrid.addWidget(self.saveButton, 6, 2)
            self.saveButton.hide()
 
            self.step1Button = QtGui.QPushButton("Previous", self)
            self.step1Button.setFixedSize(90,25)
            mainGrid.addWidget(self.step1Button, 7, 1)
            self.step1Button.clicked.connect(self.previous)
            self.step1Button.hide()  
            
            self.FinishButton = QtGui.QPushButton("Finish", self)
            self.FinishButton.setFixedSize(90,25)
            mainGrid.addWidget(self.FinishButton, 7, 2)
            self.FinishButton.clicked.connect(self.finish)
            self.FinishButton.hide() 

            
            def browseFile():
                (fileName, trash) = QtGui.QFileDialog().getOpenFileName(self, 'Open File', os.getcwd(), '(*.fmu)')
                if fileName != '':
                    self.setupFileEdit.setText(fileName)
            
            self.browseSetupFile.clicked.connect(browseFile)
            
            def browseResultFile():
                (fileName, trash) = QtGui.QFileDialog().getSaveFileName(self, 'Define fileName', os.getcwd(), '(*.xml)')
                if fileName != '':
                    self.SaveFileEdit.setText(fileName)

            self.saveButton.clicked.connect(browseResultFile)
       
       def display(self):
            (fileName, trash) = QtGui.QFileDialog().getOpenFileName(self, 'Open File', os.getcwd(), '(*.xml)')
            if fileName != '':
                 self.xmlFileEdit.setText(fileName)
                 setupfile=self.xmlFileEdit.text()
                 tree = ET.parse(setupfile)
                 root = tree.getroot()
                 for fmu in root.iter('fmu'):
                     name = fmu.get('path')
                     self.simulator.addItem(name)
                     
                 '''
                 for connection in root.iter('connection'):
                    fid=connection.get('fromFmuId')
                    fvar=connection.get('fromFmuvar')
                    fvarcon=connection.get('fromFmuvarconnection')
                    fval=connection.get('fromValueReference')                     
                    tid=connection.get('toFmuId')
                    tvar=connection.get('toFmuvar')
                    tvarcon=connection.get('toFmuvarconnection')
                    tval=connection.get('toValueReference') 
                    
                    s=''.join([fid,' ',fvar,' ',fvarcon,' ','(',fval,')','--->',tid,' ',tvar,' ',tvarcon,' ','(',tval,')'])
                    self.componentConnect.addItem(s)'''
        
                
       def add(self):
            'Get data from GUI'                    
            self.setupFile = self.setupFileEdit.text() 
            item =QtGui.QListWidgetItem(self.setupFile)
            self.simulator.addItem(item)
            self.simulator.show() 
       
       def remove(self):
           'Remove FMUS from List'                    
           #cur=self.simulator.currentItem().text()
           listItems=self.simulator.selectedItems()
           if not listItems: return        
           for item in listItems:
               self.simulator.takeItem(self.simulator.row(item))
           self.simulator.show() 
           
           
       def connectremove(self):
           'Remove connected FMUS from Qtable'
           row=self.table.currentRow()  
           self.table.removeRow(row)
           
       
       def previous(self):
            self.combo.clear()
            #self.componentConnect.clear()
            self.combo1.clear()
            self.combo.hide()
            self.combo1.hide()
            #self.componentConnect.hide() 
            self.connectButton.hide() 
            self.removeButtonconnect.hide()  
            self.step1Button.hide()  
            self.FinishButton.hide()            
            self.variablelist.hide()
            self.connectionlist.hide()
            self.SaveFile.hide()
            self.SaveFileEdit.hide()
            self.saveButton.hide()
            self.table.hide()
            
            self.File.show()
            self.setupFileEdit.show()
            self.browseSetupFile.show()
            self.addButton.show()
            self.fmulabel.show()
            self.simulator.show()
            self.removeButton.show()
            self.parseButton.show()
            self.xmlFileEdit.show()
            self.xmlFile.show()
            self.xmlSetupFile.show()
            
       def finish(self):
           logFile = self.SaveFileEdit.text()
           template='''<?xml version="1.0" encoding="utf-8"?>
<connectedFmus>
<fmus>
</fmus>
<connections>
</connections>
</connectedFmus>'''
           root = ET.fromstring(template)
                      
                      
           list1=self.simulator.count()
           for i in xrange(list1):
              item=self.simulator.item(i).text()
              fmus = root.find('fmus')
              fmu = ET.SubElement(fmus,'fmu')
              fmu.set("fmuId",str(i))               
              fmu.set("name",os.path.basename(item).replace('.fmu','')) 
              fmu.set("path",item)
              
           for row in range(self.table.rowCount()):
             connections = root.find('connections')
             connection = ET.SubElement(connections, 'connection')
             for column in range(self.table.columnCount()):
                                   
                  if (column%2==0):
                     item = self.table.item(row,column).text()
                     y1=item.split(' ')
                     
                  if (column%2!=0):
                     item = self.table.item(row,column).text()
                     y2=item.split(' ')
                     
             connection.set("fromFmuId",str(y1[0]))
             connection.set("fromFmuvar",str(y1[1]))
             connection.set("fromFmuvarconnection",str(y1[2]))
             connection.set("fromValueReference",str(y1[3]).replace('(','').replace(')','')) 
             connection.set("toFmuId",str(y2[0]))
             connection.set("toFmuvar",str(y2[1]))
             connection.set("toFmuvarconnection",str(y2[2]))
             connection.set("toValueReference",str(y2[3]).replace('(','').replace(')',''))             
             
           '''     
           list2=self.componentConnect.count()
           for i in xrange(list2):
              item=self.componentConnect.item(i).text()
              connections = root.find('connections')
              connection = ET.SubElement(connections, 'connection')
              h=item.split('--->',1)
              x1=h[0]
              x2=h[1]
              y1=x1.split(' ')
              y2=x2.split(' ')
              connection.set("fromFmuId",str(y1[0]))
              connection.set("fromFmuvar",str(y1[1]))
              connection.set("fromFmuvarconnection",str(y1[2]))
              connection.set("fromValueReference",str(y1[3]).replace('(','').replace(')',''))
              connection.set("toFmuId",str(y2[0]))
              connection.set("toFmuvar",str(y2[1]))
              connection.set("toFmuvarconnection",str(y2[2]))
              connection.set("toValueReference",str(y2[3]).replace('(','').replace(')',''))'''
              
           s=prettify(root)
           xmlstr=s.replace('&quot;','"')
           if(logFile!=''):
             f=open(logFile,'w')
             f.write(xmlstr)
             print 'xml file generated'
           else:
             print 'Select a name to save the xml'
    
            
       def next(self):
            self.File.hide()
            self.setupFileEdit.hide()
            self.browseSetupFile.hide()
            self.addButton.hide()
            self.fmulabel.hide()
            self.simulator.hide()
            self.removeButton.hide()
            self.parseButton.hide()
            self.xmlFileEdit.hide()
            self.xmlFile.hide()
            self.xmlSetupFile.hide()
            
            self.table.show()
            self.variablelist.show()
            self.combo.show()
            self.combo1.show()
            self.connectionlist.show()
            #self.componentConnect.show() 
            self.connectButton.show()
            self.step1Button.show()  
            self.removeButtonconnect.show()  
            self.FinishButton.show()        
            self.SaveFile.show()
            self.SaveFileEdit.show()            
            self.saveButton.show()

            'Parse FMUs from the List'                    
            x=self.simulator.count()
            for i in xrange(x):
               y=self.simulator.item(i).text()
               modelname=os.path.basename(y).replace('.fmu','')
               try:
                  file = zipfile.ZipFile(y, 'r')
               except:
                  print 'Error when reading zip-file' 
               
               try:
                  xmlFileName = file.open('modelDescription.xml')
               except:
                  print 'Error when reading modelDescription.xml'
                            
               tree = ET.parse(xmlFileName)
               root = tree.getroot()
               for variable in root.iter('ScalarVariable'):
                 cname = variable.get('causality')
                 varname = variable.get('name')
                 valueref=variable.get('valueReference')
                 if (cname=='input'):
                    s=''.join([str(i),' ',modelname,'.',varname,' ',cname,' ','(',valueref,')'])
                    self.combo.addItem(s)
                    self.combo1.addItem(s)        
                 if (cname=='output'):
                    s=''.join([str(i),' ',modelname,'.',varname,' ',cname,' ','(',valueref,')'])
                    self.combo.addItem(s)
                    self.combo1.addItem(s)
                                 
            
       def connect(self):
           'connect the selected FMU connections'                    
           cur=self.combo.currentText()
           cur1=self.combo1.currentText()
           #s=''.join([cur,'--->',cur1])
           row = self.table.rowCount()
           self.table.insertRow(row)
           self.table.setItem(row, 0, QtGui.QTableWidgetItem(cur))
           self.table.setItem(row, 1, QtGui.QTableWidgetItem(cur1))

           #item =QtGui.QListWidgetItem(s)
           #self.componentConnect.addItem(item)
     
    # Code of function
    control = ConnectFMU()
    control.show()

    
def prettify(elem):
   """Return a pretty-printed XML string for the Element """
   rough_string = ET.tostring(elem, 'utf-8')
   reparsed = minidom.parseString(rough_string)
   return reparsed.toprettyxml(indent="  ")
                   
