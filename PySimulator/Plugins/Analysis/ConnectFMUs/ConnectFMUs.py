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
            self.File = QtGui.QLabel("Load file", self)
            mainGrid.addWidget(self.File, 0, 0, QtCore.Qt.AlignRight)
            self.setupFileEdit = QtGui.QLineEdit("", self)
            mainGrid.addWidget(self.setupFileEdit, 0, 1)
            
            self.browseSetupFile = QtGui.QPushButton("Select", self)
            mainGrid.addWidget(self.browseSetupFile, 0, 2)
            
            
            self.addButton = QtGui.QPushButton("Add", self)
            mainGrid.addWidget(self.addButton, 0, 3)
            self.addButton.clicked.connect(self.add)
            
            self.fmulabel = QtGui.QLabel("FMUs", self)
            mainGrid.addWidget(self.fmulabel, 1, 0, QtCore.Qt.AlignRight)
            self.simulator = QtGui.QListWidget(self)
            self.simulator.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
            self.simulator.setFixedHeight(70)
            mainGrid.addWidget(self.simulator, 1, 1)
            
            self.removeButton = QtGui.QPushButton("Remove", self)
            mainGrid.addWidget(self.removeButton, 1, 2)
            self.removeButton.clicked.connect(self.remove)
            
            self.parseButton = QtGui.QPushButton("Next", self)
            mainGrid.addWidget(self.parseButton, 2, 2)
            self.parseButton.clicked.connect(self.next)
                    
            self.variablelist = QtGui.QLabel("Select Variables", self)
            mainGrid.addWidget(self.variablelist, 3, 0, QtCore.Qt.AlignRight)
            self.variablelist.hide()
            
            self.combo = QtGui.QComboBox()
            self.combo.setFixedSize(250,20)
            mainGrid.addWidget(self.combo, 3, 1)
            self.combo.hide()
            
            self.combo1 = QtGui.QComboBox()
            self.combo1.setFixedSize(250,20)
            mainGrid.addWidget(self.combo1, 3, 2)
            self.combo1.hide()

            self.connectButton = QtGui.QPushButton("Connect", self)
            mainGrid.addWidget(self.connectButton, 3, 3)
            self.connectButton.clicked.connect(self.connect)
            self.connectButton.hide()  
            
            self.connectionlist = QtGui.QLabel("Connection List", self)
            mainGrid.addWidget(self.connectionlist, 4, 0, QtCore.Qt.AlignRight)
            self.connectionlist.hide()
            
            self.componentConnect = QtGui.QListWidget(self)
            self.componentConnect.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
            self.componentConnect.setFixedHeight(70)
            mainGrid.addWidget(self.componentConnect, 4, 1)
            self.componentConnect.hide() 
            
            self.removeButtonconnect = QtGui.QPushButton("Remove", self)
            self.removeButtonconnect.setFixedSize(90,25)
            mainGrid.addWidget(self.removeButtonconnect, 4, 2)
            self.removeButtonconnect.clicked.connect(self.connectremove)
            self.removeButtonconnect.hide()
 
            self.step1Button = QtGui.QPushButton("Previous", self)
            self.step1Button.setFixedSize(90,25)
            mainGrid.addWidget(self.step1Button, 5, 1)
            self.step1Button.clicked.connect(self.previous)
            self.step1Button.hide()  
            
            self.FinishButton = QtGui.QPushButton("Finish", self)
            self.FinishButton.setFixedSize(90,25)
            mainGrid.addWidget(self.FinishButton, 5, 2)
            self.FinishButton.clicked.connect(self.finish)
            self.FinishButton.hide()            
           

            def _browseSetupFileDo():
                (fileName, trash) = QtGui.QFileDialog().getOpenFileName(self, 'Open File', os.getcwd(), '(*.fmu*)')
                if fileName != '':
                    self.setupFileEdit.setText(fileName)
            
            self.browseSetupFile.clicked.connect(_browseSetupFileDo)
       
       
            
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
           listItems=self.componentConnect.selectedItems()                      
           if not listItems: return        
           for item in listItems:
               self.componentConnect.takeItem(self.componentConnect.row(item))
           self.componentConnect.show() 
       
      
       
       def previous(self):
            self.combo.clear()
            self.componentConnect.clear()
            self.combo1.clear()
            self.combo.hide()
            self.combo1.hide()
            self.componentConnect.hide() 
            self.connectButton.hide() 
            self.removeButtonconnect.hide()  
            self.step1Button.hide()  
            self.FinishButton.hide()            
            self.variablelist.hide()
            self.connectionlist.hide()

            self.File.show()
            self.setupFileEdit.show()
            self.browseSetupFile.show()
            self.addButton.show()
            self.fmulabel.show()
            self.simulator.show()
            self.removeButton.show()
            self.parseButton.show()
       
       def finish(self):
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
              subtag =''.join(['fmuId=','"',str(i),'"',' ','name=','"',os.path.basename(item).replace('.fmu',''),'"',' ','path=','"',item,'"'])
              fmu.text = subtag
           
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
              subtag=''.join(['fromFmuId=','"',str(y1[0]),'"',' ','fromValueReference=','"',str(y1[3]).replace('(','').replace(')',''),'"',' ','toFmuId=','"',str(y2[0]),'"',
                             ' ','toValueReference=','"',str(y2[3]).replace('(','').replace(')',''),'"'])
              connection.text=subtag
           
           s=prettify(root)
           xmlstr=s.replace('&quot;','"')
           f=open('connect.xml','w')
           f.write(xmlstr)
           print 'xml file generated'
    
            
       def next(self):
            self.File.hide()
            self.setupFileEdit.hide()
            self.browseSetupFile.hide()
            self.addButton.hide()
            self.fmulabel.hide()
            self.simulator.hide()
            self.removeButton.hide()
            self.parseButton.hide()
            
            self.variablelist.show()
            self.combo.show()
            self.combo1.show()
            self.connectionlist.show()
            self.componentConnect.show() 
            self.connectButton.show()
            self.step1Button.show()  
            self.removeButtonconnect.show()  
            self.FinishButton.show()        
            
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
           s=''.join([cur,'--->',cur1])

           item =QtGui.QListWidgetItem(s)
           self.componentConnect.addItem(item)
           self.componentConnect.show() 
     
    # Code of function
    control = ConnectFMU()
    control.show()

    
def prettify(elem):
   """Return a pretty-printed XML string for the Element """
   rough_string = ET.tostring(elem, 'utf-8')
   reparsed = minidom.parseString(rough_string)
   return reparsed.toprettyxml(indent="  ")
                   
