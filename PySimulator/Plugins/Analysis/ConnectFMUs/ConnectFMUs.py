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
            
            self.xmlFile = QtGui.QLabel("Load XML:", self)
            mainGrid.addWidget(self.xmlFile, 0, 0, QtCore.Qt.AlignRight)
            self.xmlFileEdit = QtGui.QLineEdit("", self)
            mainGrid.addWidget(self.xmlFileEdit, 0, 1)
            
            self.xmlSetupFile = QtGui.QPushButton("Select", self)
            mainGrid.addWidget(self.xmlSetupFile, 0, 2)
            self.xmlSetupFile.clicked.connect(self.display)
                        
            self.fmulabel = QtGui.QLabel("List of FMUs:", self)
            mainGrid.addWidget(self.fmulabel, 1, 0, QtCore.Qt.AlignRight)
            self.fmu = QtGui.QListWidget(self)
            self.fmu.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
            #self.fmu.setFixedHeight(100)
            mainGrid.addWidget(self.fmu, 1, 1, 2, 1)
            
            self.browseSetupFile = QtGui.QPushButton("Select", self)
            mainGrid.addWidget(self.browseSetupFile, 1, 2)
            
            
            self.removeButton = QtGui.QPushButton("Remove", self)
            mainGrid.addWidget(self.removeButton, 2, 2)
            self.removeButton.clicked.connect(self.remove)
            
            self.parseButton = QtGui.QPushButton("Next", self)
            mainGrid.addWidget(self.parseButton, 3, 2)
            self.parseButton.clicked.connect(self.next)
                        
            self.variablelist = QtGui.QLabel("Select Connections:", self)
            mainGrid.addWidget(self.variablelist, 4, 0, QtCore.Qt.AlignRight)
            self.variablelist.hide()
            
            self.combo = QtGui.QComboBox()
            self.combo.setFixedSize(240,20)
            mainGrid.addWidget(self.combo, 4, 1)
            self.combo.hide()
            
            self.combo1 = QtGui.QComboBox()
            self.combo1.setFixedSize(240,20)
            mainGrid.addWidget(self.combo1, 4, 2)
            self.combo1.hide()

            self.connectButton = QtGui.QPushButton("Connect", self)
            mainGrid.addWidget(self.connectButton, 4, 3)
            self.connectButton.clicked.connect(self.connect)
            self.connectButton.hide()  
            
            self.connectionlist = QtGui.QLabel("Connection List:", self)
            mainGrid.addWidget(self.connectionlist, 5, 0, QtCore.Qt.AlignRight)
            self.connectionlist.hide()
            
            
            self.table = QtGui.QTableWidget(self)
            self.table.setRowCount(0)
            self.table.setColumnCount(2)
            self.table.setHorizontalHeaderLabels(["From","To"])
            mainGrid.addWidget(self.table, 5, 1, 1, 2)
            #self.table.setFixedSize(250,200)
            self.table.hide() 
            
            self.removeButtonconnect = QtGui.QPushButton("Remove", self)
            #self.removeButtonconnect.setFixedSize(90,25)
            mainGrid.addWidget(self.removeButtonconnect, 5, 3)
            self.removeButtonconnect.clicked.connect(self.connectremove)
            self.removeButtonconnect.hide()
            
            self.paramlist = QtGui.QLabel("Parameter List:", self)
            mainGrid.addWidget(self.paramlist, 6, 0, QtCore.Qt.AlignRight)
            self.paramlist.hide()
                       
            self.paramtable = QtGui.QTableWidget(self)
            self.paramtable.setRowCount(0)
            self.paramtable.setColumnCount(4)
            self.paramtable.setHorizontalHeaderLabels(["FMU","Variable","Type","Value"])
            mainGrid.addWidget(self.paramtable, 6, 1, 1, 2)
            self.paramtable.hide()          
            
            self.SaveFile = QtGui.QLabel("Save File", self)
            mainGrid.addWidget(self.SaveFile, 7, 0, QtCore.Qt.AlignRight)
            self.SaveFileEdit = QtGui.QLineEdit("", self)
            mainGrid.addWidget(self.SaveFileEdit, 7, 1)
            self.SaveFile.hide()
            self.SaveFileEdit.hide()
            
            self.saveButton = QtGui.QPushButton("Select", self)
            #self.saveButton.setFixedSize(90,25)
            mainGrid.addWidget(self.saveButton, 7, 2)
            self.saveButton.hide()
 
            self.step1Button = QtGui.QPushButton("Previous", self)
            #self.step1Button.setFixedSize(90,25)
            mainGrid.addWidget(self.step1Button, 8, 0)
            self.step1Button.clicked.connect(self.previous)
            self.step1Button.hide()  
            
            self.FinishButton = QtGui.QPushButton("Finish", self)
            #self.FinishButton.setFixedSize(90,25)
            mainGrid.addWidget(self.FinishButton, 7, 3)
            self.FinishButton.clicked.connect(self.finish)
            self.FinishButton.hide() 

            
            def browseFile():
                (fileName, trash) = QtGui.QFileDialog().getOpenFileName(self, 'Open File', os.getcwd(), '(*.fmu)')
                fileName = fileName.replace('\\', '/')
                if fileName != '':
                    #self.setupFileEdit.setText(fileName)
                    self.fmu.addItem(fileName)

            
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
       
       
       def remove(self):
           'Remove FMUS from List'                    
           #cur=self.fmu.currentItem().text()
           listItems=self.fmu.selectedItems()
           if not listItems: return        
           for item in listItems:
               self.fmu.takeItem(self.fmu.row(item))
           self.fmu.show() 
           
           
       def connectremove(self):
           'Remove connected FMUS from Qtable'
           row=self.table.currentRow()  
           self.table.removeRow(row)
           
       
       def previous(self):
            ## Show only the widgets of step1 and also delete the contents of widgets for proper update of data if the user adds or removes a FMU ##
            '''' 
            for i in reversed(range(self.table.rowCount())):
                 self.table.removeRow(i)'''
                 
            for j in reversed(range(self.paramtable.rowCount())):
                 self.paramtable.removeRow(j)
                 
            ### Hide the following widgets ###     
            self.combo.clear()
            self.combo1.clear()
            self.combo.hide()
            self.combo1.hide()
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
            self.paramtable.hide()
            self.paramlist.hide()
            
            ### Show the following widgets ###
            
            self.browseSetupFile.show()
            self.fmulabel.show()
            self.fmu.show()
            self.removeButton.show()
            self.parseButton.show()
            self.xmlFileEdit.show()
            self.xmlFile.show()
            self.xmlSetupFile.show()
            
       def finish(self):
           ## Parse the data from the GUI and write to XML ##
           logFile = self.SaveFileEdit.text()
           template='''<?xml version="1.0" encoding="utf-8"?>
<connectedFmus>
<fmus>
</fmus>

<connections>
</connections>
</connectedFmus>'''
           root = ET.fromstring(template)
                      
                      
           list1=self.fmu.count()
           
           ## Parse the data from self.fmu widget and self.paramtable and write to <fmus> tag in xml##
           for i in xrange(list1):
              item=self.fmu.item(i).text()
              name=os.path.basename(item).replace('fmu','').replace('.','')
              fmus = root.find('fmus')
              fmu = ET.SubElement(fmus,'fmu')
              fmu.set("fmuId",str(i))               
              fmu.set("name",os.path.basename(item).replace('.fmu','')) 
              fmu.set("path",item)
              parameters=ET.SubElement(fmu,'parameters')

              for row in range(self.paramtable.rowCount()):
                fmuname = self.paramtable.item(row,0).text()
                if(name==fmuname):
                   parameter=ET.SubElement(parameters,'parameter')                           
                   for column in range(self.paramtable.columnCount()):
                      if(column==1):
                         parname = self.paramtable.item(row,column).text()
                         parameter.set("name",parname)
                      if(column==2):
                         partype = self.paramtable.item(row,column).text()
                         parameter.set("type",partype)                  
                      if(column==3):
                         parvalue = self.paramtable.item(row,column).text()
                         parameter.set("value",parvalue)
                         
           ## Parse the data from self.table widget and write to the <connection> tag in xml ##             
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
             
              
           s=prettify(root)
           xmlstr=s.replace('&quot;','"')
           if(logFile!=''):
             f=open(logFile,'w')
             f.write(xmlstr)
             print 'xml file generated'
           else:
             print 'Select a name to save the xml'
    
            
       def next(self):
       
            #### update the connection table if the user goes for previous step and removes fmus from the list###
            count=self.table.rowCount()            
            if (count!=0):
              x=self.fmu.count()
              checkfmus=[]
              for i in xrange(x):
                 y=self.fmu.item(i).text()
                 modelname=os.path.basename(y).replace('.fmu','').replace('.','')
                 checkfmus.append(modelname)
              rownumbers=[]
              for row in range(self.table.rowCount()):
                  for column in range(self.table.columnCount()):
                       item = self.table.item(row,column).text()
                       y1=item.split(' ')
                       fmuname=y1[1].split(".",1)[0]    
                       if (column==0):
                           col0 = [s for s in checkfmus if fmuname in s]
                       if (column==1):
                           col1 = [s for s in checkfmus if fmuname in s]

                  if(len(col0)==0 or len(col1)==0):
                     #print 'rownumber', row
                     rownumbers.append(row)
                     
              if(len(rownumbers)!=0):
              
                 for i in reversed(range(self.table.rowCount())):
                     if i in rownumbers:
                         self.table.removeRow(i)
                    
            ## hide the following widgets ##
            self.browseSetupFile.hide()
            self.fmulabel.hide()
            self.fmu.hide()
            self.removeButton.hide()
            self.parseButton.hide()
            self.xmlFileEdit.hide()
            self.xmlFile.hide()
            self.xmlSetupFile.hide()
            
            ## show the following widgets ##
            self.table.show()
            self.paramlist.show()
            self.paramtable.show()
            self.variablelist.show()
            self.combo.show()
            self.combo1.show()
            self.connectionlist.show()
            self.connectButton.show()
            self.step1Button.show()  
            self.removeButtonconnect.show()  
            self.FinishButton.show()        
            self.SaveFile.show()
            self.SaveFileEdit.show()            
            self.saveButton.show()

            ## Parse FMUs from the List ##                   
            x=self.fmu.count()
            for i in xrange(x):
               y=self.fmu.item(i).text()
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
                 parname=variable.get('variability')
                 valueref=variable.get('valueReference')
                 if (cname=='input'):
                    s=''.join([str(i),' ',modelname,'.',varname,' ',cname,' ','(',valueref,')'])
                    self.combo.addItem(s)
                    self.combo1.addItem(s)        
                 if (cname=='output'):
                    s=''.join([str(i),' ',modelname,'.',varname,' ',cname,' ','(',valueref,')'])
                    self.combo.addItem(s)
                    self.combo1.addItem(s)
                 if (parname=='parameter'):
                    for x in variable.iter('Real'):
                       #print modelname, varname, x.get('start')
                       row = self.paramtable.rowCount()
                       self.paramtable.insertRow(row)
                       self.paramtable.setItem(row, 0, QtGui.QTableWidgetItem(modelname))
                       self.paramtable.setItem(row, 1, QtGui.QTableWidgetItem(varname))
                       self.paramtable.setItem(row, 2, QtGui.QTableWidgetItem('Real'))  
                       self.paramtable.setItem(row, 3, QtGui.QTableWidgetItem(x.get('start')))
                       self.paramtable.resizeColumnsToContents()
                                    
                                   
       def connect(self):
           ##connect the selected FMU connections##                    
           cur=self.combo.currentText()
           cur1=self.combo1.currentText()
           row = self.table.rowCount()
           self.table.insertRow(row)
           self.table.setItem(row, 0, QtGui.QTableWidgetItem(cur))
           self.table.setItem(row, 1, QtGui.QTableWidgetItem(cur1))
           self.table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
           self.table.resizeColumnsToContents()

           
    # Code of function
    control = ConnectFMU()
    control.show()

    
def prettify(elem):
   """Return a pretty-printed XML string for the Element """
   rough_string = ET.tostring(elem, 'utf-8')
   reparsed = minidom.parseString(rough_string)
   return reparsed.toprettyxml(indent="  ")
                   
