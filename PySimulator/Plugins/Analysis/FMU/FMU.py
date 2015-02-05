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

from PySide import QtGui, QtCore


def NewConnectME(model, gui):
    print "New connected FMU for Model Exchange"
    pass
    
    
    
def NewConnectCS(model, gui):
    print "New connected FMU for CoSimulation"
    pass     
    

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