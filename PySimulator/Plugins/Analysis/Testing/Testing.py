#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (C) 2011-2014 German Aerospace Center DLR
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


import Compare
import numpy
import os
import sys
import shutil
from bs4 import BeautifulSoup
import webbrowser
from PySide import QtGui, QtCore
import Plugins.Simulator
import Plugins.Simulator.SimulatorBase as SimulatorBase
import Plugins.SimulationResult as SimulationResult


def compareResults(filewritehtml,resultfile,htmlfile,model1, model2, tol=1e-3, fileOutput=sys.stdout):
    def prepareMatrix(t, y):
        if t is None or y is None:
            print "Not supported to prepare None-vector/matrix."
            return None, None

        if len(t) <> y.shape[0]:
            print "prepareMatrix: Length of time vector and number of rows of y have to be identical."
            return None, None
        yNew = numpy.ndarray((y.shape[0] * 2, y.shape[1]))
        tNew = numpy.ndarray((t.shape[0] * 2,))
        yNew[0, :] = y[0, :]
        tNew[0] = t[0]
        for i in xrange(y.shape[0] - 1):
            yNew[2 * i + 1, :] = y[i, :]
            yNew[2 * i + 2, :] = y[i + 1, :]
            tNew[2 * i + 1] = t[i + 1]
            tNew[2 * i + 2] = t[i + 1]
        yNew[-1, :] = y[-1, :]
        tNew[-1] = t[-1] + 1
        return tNew, yNew
    var1 = model1.integrationResults.getVariables()
    var1Name = var1.keys()
    var2 = model2.integrationResults.getVariables()
    var2Name = var2.keys()

    print "Start of comparing results ..."

    allIdentical = True
    maxEstTol = 0.0

    allNamesBoth = set(var1Name) & set(var2Name)
    allNamesOnce1 = set(var1Name) - set(var2Name)
    allNamesOnce2 = set(var2Name) - set(var1Name)

    nPos = 0
    nNeg = 0

    pMatrix2 = [None] * model2.integrationResults.nTimeSeries
    timeSeries1Names = []
    timeSeries2Names = []
    
    for i in xrange(model1.integrationResults.nTimeSeries):
        timeSeries1Names.append([])
    
    for i in xrange(model2.integrationResults.nTimeSeries):
        timeSeries2Names.append([])


    for name in allNamesBoth:
        timeSeries1Names[var1[name].seriesIndex].append(name)
        timeSeries2Names[var2[name].seriesIndex].append(name)
    

    for i in xrange(model1.integrationResults.nTimeSeries):
        if len(timeSeries1Names[i]) > 0:
            t1 = model1.integrationResults.timeSeries[i].independentVariable
            f1 = model1.integrationResults.timeSeries[i].data

            numpy.set_printoptions(threshold='nan')
            if model1.integrationResults.timeSeries[i].interpolationMethod == "constant" and t1 is not None:
                t1, f1 = prepareMatrix(t1, f1)
            for j in xrange(model2.integrationResults.nTimeSeries):
                if len(timeSeries2Names[j]) > 0:
                    check1= set(timeSeries1Names[i])
                    check2= set(timeSeries2Names[j])
                    namesBothSub = list(set(timeSeries1Names[i]) & set(timeSeries2Names[j]))
    
                    # These variable names are considered in the following:
                    if len(namesBothSub) > 0:
                        k = 0
                        i1 = numpy.ones((len(namesBothSub),), dtype=int) * (-1)
                        i2 = numpy.ones((len(namesBothSub),), dtype=int) * (-1)
                        s1 = numpy.ones((len(namesBothSub),), dtype=int)
                        s2 = numpy.ones((len(namesBothSub),), dtype=int)
                        
                        for variableName in namesBothSub:
                            i1[k] = var1[variableName].column
                            i2[k] = var2[variableName].column
                            s1[k] = var1[variableName].sign
                            s2[k] = var2[variableName].sign
                            k = k + 1
                                          
                        t2 = model2.integrationResults.timeSeries[j].independentVariable
                        f2 = model2.integrationResults.timeSeries[i].data
                        
                        if model2.integrationResults.timeSeries[j].interpolationMethod == "constant" and t2 is not None:
                            if pMatrix2[j] is None:
                                t2, f2 = prepareMatrix(t2, f2)
                                pMatrix2[j] = (t2, f2)
                            else:
                                t2 = pMatrix2[j][0]
                                f2 = pMatrix2[j][1]
                        result = [var for var in namesBothSub if 'Time' in var] 
                        
                        identical, estTol, error = Compare.Compare(t1, f1, i1, s1, t2, f2, i2, s2, tol)
                                  
                        if error:
                            message = u"Error during comparison of results."
                            fileOutput.write(message + u"\n")
                            return
                    
                        maxEstTol = max(maxEstTol, estTol.max())
 
                        allIdentical = allIdentical and all(identical)
                        s = sum(identical)
                        nNeg = nNeg + (len(identical) - s)
                        nPos = nPos + s
                        '''Get the differed variables after comparison'''
                        diff=[]               
                        for m in xrange(len(identical)):
                            if not identical[m]:
                                message = u"Results for " + namesBothSub[m] + u" are NOT identical within the tolerance " + unicode(tol) + u"; estimated Tolerance = " + unicode(estTol[m])
                                diff.append(namesBothSub[m])
                                fileOutput.write(message + u"\n")
                        
                        '''Pass the numpy matrix data to generate the html graph in the browser'''        
                        if (len(diff)!=0):
                           l2=[]
                           l1=[]
                           for z in diff:
                              c1 = var1[z].column
                              c2 = var2[z].column
                              l1.append(c1)
                              l2.append(c2)
                           generatehtml(f1,f2,diff,l1,l2,htmlfile,resultfile)
                                      
#    if len(allNamesOnce1) > 0:
#        print "The following variables are not contained in file " + model2.integrationResults.fileName + ":"
#    for variableName in allNamesOnce1:
#        print variableName
#    if len(allNamesOnce2) > 0:
#        print "The following variables are not contained in file " + model1.integrationResults.fileName + ":"
#    for variableName in allNamesOnce2:
#        print variableName

    lenNamesOnce = len(allNamesOnce1) + len(allNamesOnce2)
    if lenNamesOnce > 0:
        messageOnce = u"; " + unicode(lenNamesOnce) + u" only in one of the two files."
    else:
        messageOnce = u"."
    message = u"Compared results of " + unicode(nPos + nNeg) + u" variables: " + unicode(nPos) + u" identical, " + unicode(nNeg) + u" differ" + messageOnce
    # print message
    fileOutput.write(message + u"\n")

    if allIdentical:
        message = u"The results for all compared variables are identical up to the given tolerance = " + unicode(tol)
        # print message
        fileOutput.write(message + u"\n")
    message = u"Maximum estimated tolerance = " + unicode(maxEstTol)
    # print message
    fileOutput.write(message + u"\n")

    print "... done."
    ''' Function call to generate the overview report'''
    htmloverview(filewritehtml,resultfile,htmlfile,diff)

    return


def counter(func):
    def tmp(*args, **kwargs):
        tmp.count += 1
        return func(*args, **kwargs)
    tmp.count = 0
    return tmp   


def htmloverview(fileouthtml,resultfile,file,diff):
    '''This function is used to present the users with the overall comparison report of different models, The report includes, for each model the number of variables 
       differed, and a link is provided to inspect the differed variables, if there are no differed variables then no link is provided '''
    os.getcwd()
    modelname=os.path.basename(file).replace('.mat',' ')
    x=runCompareResultsInDirectories.count       
    modelname1=modelname+'res'+str(x)
    p=os.path.dirname(resultfile)
    os.chdir(p)
    filename=os.path.join(p,modelname1.replace(' ',''))
    fileerror=os.path.join(filename,'err.html').replace('\\','/')
    messerr="""<html>
<head> Differed variables </head>
<li>"""     
    
    message1= '<a href=' + os.path.relpath(resultfile) + '>' + modelname + '</a>' +' </td>' 
    if(len(diff)==0):
         emptyhref='<a href="" style="text-decoration:none;">0</a>'
         s = '\n'.join(['<tr>','<td>',message1,'<td bgcolor=#00FF00>',emptyhref,'</td>','</tr>']) 
         fileouthtml.write(s)
         fileouthtml.write('\n')   
    
    if(len(diff)>0): 
         f=open(fileerror,'w')   
         for z in xrange(len(diff)):
             str1=''.join([modelname+'_'+diff[z]+'.html'])
             x= '<a href='+str1.replace(' ','')+'>'+ diff[z]+ '</a>'+'</li>'
             if(diff[z]==diff[-1]):
                  x= '<a href='+str1.replace(' ','')+'>'+ diff[z]+ '</a>' +'</li>'+'</html>'      
             if(z==0):
               s = '\n'.join([messerr,x])
             else:         
               s = '\n'.join(['<li>',x])
                
             f.write(s)
             f.write('\n')
         f.close()
         
         diff = '<a href='+ os.path.relpath(fileerror) +'>'+str(len(diff))+'</a>'+'</td>'+'</tr>'      
         s = '\n'.join(['<tr>','<td>',message1,'<td bgcolor=#FF0000>',diff])            
         fileouthtml.write(s)
         fileouthtml.write('\n')
   
    
def checkrows(model):
   ''' This function used to delete duplicate rows in a numpy array'''
   column1=model[:,0]
   indices = numpy.setdiff1d(numpy.arange(len(column1)), numpy.unique(column1, return_index=True)[1])
   if len(indices>0):
      '''axis=0 represent the rows to be deleted from the obtained index '''
      model= numpy.delete(model, indices, axis=0)
   return model
    
    
def generatehtml(model1,model2,namesBoth,col1var,col2var,htmlfile,resultfile):
    '''This function is used to fetch the array of data from mat files and create the html graph for the differed variables which can be viewed in browser'''
    #get the modelname of the file                   
    report=os.path.basename(str(htmlfile)).replace('.mat',' ')
    x=runCompareResultsInDirectories.count       
    err=report+'res'+str(x)
    report1='\''+report+'\''
    #create a new directory for the result_files which differ
    path=os.path.dirname(os.path.abspath(str(resultfile)))
    newpath=os.path.join(path,err.replace(' ',''))
    if not os.path.exists(newpath): 
        os.mkdir(newpath)
                
        
    model1=checkrows(model1)
    model2=checkrows(model2)
    i = numpy.intersect1d(model1[:,0], model2[:,0])   
    
    # Get the appropriate datas from model1 and model2 for the variables and create a new array which will be written in the javascript part of html file   
    for z in range(len(namesBoth)):
        name=namesBoth[z]
        var1=col1var[z]
        var2=col2var[z]
        if (name != 'Time'):
             try:
                # for each variable get the appropriate column datas from model1 and model2 
               fast_c = numpy.vstack([i, model1[numpy.in1d(model1[:,0], i), var1], model2[numpy.in1d(model2[:,0], i), var2]]).T
               dygraph_array= repr(fast_c).replace('array',' ').replace('(' ,' ').replace(')' ,' ')
               htmlreport=newpath+'\\'+report+'_'+name+'.html'     
               htmlreport=htmlreport.replace(' ','').replace('\\','/')
               with open(htmlreport, 'wb') as f:
                message = """<html>
<head>
<script type="text/javascript" src="http://dygraphs.com/1.0.1/dygraph-combined.js"></script>
<style type="text/css">
    #graphdiv {
      position: absolute;
      left: 10px;
      right: 10px;
      top: 40px;
      bottom: 10px;
    }
    </style>
</head>
<body>
<div id="graphdiv"></div>
<p><input type=checkbox id="0" checked onClick="change(this)">
<label for="0">reference</label>
<input type=checkbox id="1" checked onClick="change(this)">
<label for="1">actual</label>
,  Parameters used for the comparison: Relative tolerance 1e-3 </p>
<script type="text/javascript">
g = new Dygraph(document.getElementById("graphdiv"),"""
              
                varname='title:'+'\''+name+'\''+','
                option="""xlabel: ['time'],
labels: ['time','reference','actual'],
visibility:[true,true,true]
}"""
                message2="""function change(el) {
g.setVisibility(parseInt(el.id), el.checked);
}
</script>
</body>
</html>"""

                s = '\n'.join([message,str(dygraph_array),",","{",varname,option,")",";",message2])
                f.write(s)
                f.close()
             except IndexError:
                pass
                
def simulateListMenu(model, gui):

    class SimulateListControl(QtGui.QDialog):
        ''' Class for the SimulateList Control GUI '''

        def __init__(self):
            QtGui.QDialog.__init__(self)
            self.setModal(False)
            self.setWindowTitle("Simulate List of Models")
            self.setWindowIcon(QtGui.QIcon(gui.rootDir + '/Icons/pysimulatorLists.ico'))

            mainGrid = QtGui.QGridLayout(self)

            setupFile = QtGui.QLabel("Setup file:", self)
            mainGrid.addWidget(setupFile, 0, 0, QtCore.Qt.AlignRight)
            browseSetupFile = QtGui.QPushButton("Select", self)
            mainGrid.addWidget(browseSetupFile, 0, 2)
            self.setupFileEdit = QtGui.QLineEdit("", self)
            mainGrid.addWidget(self.setupFileEdit, 0, 1)

            setupFile = QtGui.QLabel("Directory of results:", self)
            mainGrid.addWidget(setupFile, 1, 0, QtCore.Qt.AlignRight)
            browseDirResults = QtGui.QPushButton("Select", self)
            mainGrid.addWidget(browseDirResults, 1, 2)
            self.dirResultsEdit = QtGui.QLineEdit("", self)
            mainGrid.addWidget(self.dirResultsEdit, 1, 1)

            self.deleteDir = QtGui.QCheckBox("Delete existing result directories for selected simulators before simulation", self)
            mainGrid.addWidget(self.deleteDir, 2, 1, 1, 2)

            mainGrid.addWidget(QtGui.QLabel("Simulators:"), 3, 0, QtCore.Qt.AlignRight)
            self.simulator = QtGui.QListWidget(self)
            self.simulator.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
            self.simulator.setFixedHeight(70)
            for x in gui.simulatorPlugins:
                QtGui.QListWidgetItem(x, self.simulator)

            mainGrid.addWidget(self.simulator, 3, 1)


            self.stopButton = QtGui.QPushButton("Stop", self)
            mainGrid.addWidget(self.stopButton, 7, 0)
            self.stopButton.clicked.connect(self.stop)
            self.runButton = QtGui.QPushButton("Run simulations", self)
            mainGrid.addWidget(self.runButton, 7, 1)
            self.runButton.clicked.connect(self.run)
            self.closeButton = QtGui.QPushButton("Close", self)
            mainGrid.addWidget(self.closeButton, 7, 2)
            self.closeButton.clicked.connect(self._close_)
            
            self.parallelButton = QtGui.QPushButton("Parallel Simulation", self)
            mainGrid.addWidget(self.parallelButton, 8, 1)
            self.parallelButton.clicked.connect(self.parallel)

            def _browseSetupFileDo():
                (fileName, trash) = QtGui.QFileDialog().getOpenFileName(self, 'Open Simulation Setup File', os.getcwd(), '(*.txt);;All Files(*.*)')
                if fileName != '':
                    self.setupFileEdit.setText(fileName)

            def _browseDirResultsDo():
                dirName = QtGui.QFileDialog().getExistingDirectory(self, 'Select Directory of Results', os.getcwd())
                dirName = dirName.replace('\\', '/')
                if dirName != '':
                    self.dirResultsEdit.setText(dirName)

            browseSetupFile.clicked.connect(_browseSetupFileDo)
            browseDirResults.clicked.connect(_browseDirResultsDo)
            self.dirResultsEdit.setText(os.getcwd().replace('\\', '/'))


        def _close_(self):
            self.close()


        def run(self):
            if hasattr(gui, '_simThreadTesting'):
                if gui._simThreadTesting.running:
                    print "A list of simulations is still running."
                    return

            # Get data from GUI
            setupFile = self.setupFileEdit.text()
            resultsDir = self.dirResultsEdit.text()
            simulators = []
            for item in self.simulator.selectedItems():
                simulators.append(gui.simulatorPlugins[item.text()])
            deleteDir = self.deleteDir.isChecked()

            # Run the simulations
            gui._simThreadTesting = runListSimulation(gui.rootDir, setupFile, resultsDir, simulators, deleteDir)

        def parallel(self):
            if hasattr(gui, '_simThreadTesting'):
                if gui._simThreadTesting.running:
                    print "A list of simulations is still running."
                    return

            # Get data from GUI
            setupFile = self.setupFileEdit.text()
            resultsDir = self.dirResultsEdit.text()
            simulators = []
            for item in self.simulator.selectedItems():
                simulators.append(gui.simulatorPlugins[item.text()])
            deleteDir = self.deleteDir.isChecked()
                        
            # Run parallel simulations
            gui._simThreadTesting = runParallelSimulation(gui.rootDir, setupFile, resultsDir, simulators, deleteDir)

        def stop(self):
            if hasattr(gui, '_simThreadTesting'):
                if gui._simThreadTesting.running:
                    gui._simThreadTesting.stopRequest = True
                    print "Try to cancel simulations ..."



    # Code of function
    control = SimulateListControl()
    control.show()



def compareListMenu(model, gui):

    class CompareListControl(QtGui.QDialog):
        ''' Class for the CompareList Control GUI '''

        def __init__(self):
            QtGui.QDialog.__init__(self)
            self.setModal(False)
            self.setWindowTitle("Compare Result Files")
            self.setWindowIcon(QtGui.QIcon(gui.rootDir + '/Icons/pysimulatorLists.ico'))

            mainGrid = QtGui.QGridLayout(self)

            dir1 = QtGui.QLabel("Directory 1 of results:", self)
            mainGrid.addWidget(dir1, 0, 0, QtCore.Qt.AlignRight)
            self.dir1Edit = QtGui.QLineEdit("", self)
            mainGrid.addWidget(self.dir1Edit, 0, 1)
            browseDir1 = QtGui.QPushButton("Select", self)
            mainGrid.addWidget(browseDir1, 0, 2)
           
            dir2 = QtGui.QLabel("Directory 2 of results:", self)
            mainGrid.addWidget(dir2, 1, 0, QtCore.Qt.AlignRight)
            self.dir2Edit = QtGui.QLineEdit("", self)
            mainGrid.addWidget(self.dir2Edit, 1, 1)
            browseDir2 = QtGui.QPushButton("Select", self)
            mainGrid.addWidget(browseDir2, 1, 2)
           
            self.listdir = QtGui.QLabel("List of Directory:", self)
            mainGrid.addWidget(self.listdir , 2, 0, QtCore.Qt.AlignRight)
            self.directory = QtGui.QListWidget(self)
            self.directory.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
            self.directory.setFixedHeight(80)
            mainGrid.addWidget(self.directory, 2, 1)
            
            self.removeButton = QtGui.QPushButton("Remove", self)
            mainGrid.addWidget(self.removeButton, 2, 2)
            self.removeButton.clicked.connect(self.remove)
            
            tol = QtGui.QLabel("Error tolerance:", self)
            mainGrid.addWidget(tol, 3, 0, QtCore.Qt.AlignRight)
            self.tolEdit = QtGui.QLineEdit("", self)
            mainGrid.addWidget(self.tolEdit, 3, 1)

            result = QtGui.QLabel("Logging:", self)
            mainGrid.addWidget(result, 4, 0, QtCore.Qt.AlignRight)
            self.resultEdit = QtGui.QLineEdit("", self)
            mainGrid.addWidget(self.resultEdit, 4, 1)
            browseResult = QtGui.QPushButton("Select", self)
            mainGrid.addWidget(browseResult, 4, 2)
            
            browseDir1 = QtGui.QPushButton("Select", self)
            mainGrid.addWidget(browseDir1, 0, 2)
            self.dir1Edit = QtGui.QLineEdit("", self)
            mainGrid.addWidget(self.dir1Edit, 0, 1)

            
            self.stopButton = QtGui.QPushButton("Stop", self)
            mainGrid.addWidget(self.stopButton, 7, 0)
            self.stopButton.clicked.connect(self.stop)
            self.runButton = QtGui.QPushButton("Run analysis", self)
            mainGrid.addWidget(self.runButton, 7, 1)
            self.runButton.clicked.connect(self.run)
            self.closeButton = QtGui.QPushButton("Close", self)
            mainGrid.addWidget(self.closeButton, 7, 2)
            self.closeButton.clicked.connect(self._close_)
            
            self.RegressionButton = QtGui.QPushButton("Regression Chart", self)
            mainGrid.addWidget(self.RegressionButton, 8, 1)
            self.RegressionButton.clicked.connect(self.regressionreport)

            def _browseDir1Do():
                dirName = QtGui.QFileDialog().getExistingDirectory(self, 'Open Directory of Results', os.getcwd())
                dirName = dirName.replace('\\', '/')
                if dirName != '':
                    self.dir1Edit.setText(dirName)

            def _browseDir2Do():
                dirName = QtGui.QFileDialog().getExistingDirectory(self, 'Open Directory of Results', os.getcwd())
                dirName = dirName.replace('\\', '/')
                if dirName != '':
                    self.dir2Edit.setText(dirName)
                    self.directory.addItem(dirName)

            def _browseResultDo():
                (fileName, trash) = QtGui.QFileDialog().getSaveFileName(self, 'Define Analysis Result File', os.getcwd(), '(*.log);;All Files(*.*)')
                if fileName != '':
                    self.resultEdit.setText(fileName)

            browseDir1.clicked.connect(_browseDir1Do)
            browseDir2.clicked.connect(_browseDir2Do)
            browseResult.clicked.connect(_browseResultDo)

            self.tolEdit.setText('1e-3')
            self.resultEdit.setText(os.getcwd().replace('\\', '/') + '/CompareAnalysis.log')
            self.dir1Edit.setText(os.getcwd().replace('\\', '/'))
            self.dir2Edit.setText(os.getcwd().replace('\\', '/'))

        def _close_(self):
            self.close()
        
        def remove(self):
           listItems=self.directory.selectedItems()
           if not listItems: return        
           for item in listItems:
               self.directory.takeItem(self.directory.row(item))
               
        def run(self):
            if hasattr(gui, '_compareThreadTesting'):
                if gui._compareThreadTesting.running:
                    print "An analysis to compare result files is still running."
                    return

            # Get data from GUI
            dir1 = self.dir1Edit.text()
            #dir2 = self.dir2Edit.text()
            logFile = self.resultEdit.text()
            tol = float(self.tolEdit.text())
            
            listdirs=[]
            sitems=self.directory.selectedItems()
            if(len(sitems)!=0):
               for item in self.directory.selectedItems():        
                  listdirs.append(item.text())
            else:
               for i in xrange(self.directory.count()):
                 item=self.directory.item(i).text()
                 listdirs.append(item)
                 
            # Run the analysis
            if (len(listdirs)!=0):
                gui._compareThreadTesting = runCompareResultsInDirectories(gui.rootDir, dir1, listdirs, tol, logFile)
            else:
                print 'Select Directory 2 of results to be added to List of Directory to compare'
                
        def stop(self):
            if hasattr(gui, '_compareThreadTesting'):
                if gui._compareThreadTesting.running:
                    gui._compareThreadTesting.stopRequest = True
                    print "Try to cancel comparing results files ..."
       
        def regressionreport(self):
            logFile = self.resultEdit.text()
            genregressionreport(logFile)

    # Code of function
    control = CompareListControl()
    control.show()
    


def getModelCallbacks():
    return [["Simulate List of Models...", simulateListMenu], ["Compare List of Results...", compareListMenu]]


def getModelMenuCallbacks():
    return [["Compare Results", compareResults]]


def getPlotCallbacks():
    ''' see getModelCallbacks
    '''
    return []



def runListSimulation(PySimulatorPath, setupFile, resultDir, allSimulators, deleteDir=False):
    import configobj
    import csv


    print "Start running the list of simulations ..."

    f = open(setupFile, 'rb')

    '''
    # Read the general settings
    general = []
    k = 0
    endLoop = False
    while not endLoop:
        pos = f.tell()
        y = f.readline()
        if y == '': # end of file
            endLoop = True
        else:
            y = y.split('#',1)[0].replace('\n', '').strip()
            if len(y) > 0:
                if not '/' in y: # No Path information
                    f.seek(pos)
                    endLoop = True
                else:
                    k += 1
                    general.append(y)

    # Read the list of models
    modelList = numpy.genfromtxt(f, dtype='S2000, S2000, f8, f8, f8, i4, b1', names=['fileName', 'modelName', 'tStart', 'tStop', 'tol', 'nInterval', 'includeEvents'])
    '''

    line = []
    reader = csv.reader(f, delimiter=' ', skipinitialspace=True)
    for a in reader:
        if len(a) > 0:
            if not (len(a[0]) > 0 and a[0][0] == '#'):
                # if len(a) >= 7:
                line.append(a[:7])
    f.close()

    modelList = numpy.zeros((len(line),), dtype=[('fileName', 'U2000'), ('modelName', 'U2000'), ('tStart', 'f8'), ('tStop', 'f8'), ('tol', 'f8'), ('nInterval', 'i4'), ('includeEvents', 'b1')])
    for i, x in enumerate(line):
        absPath = x[0].replace('\\', '/')
        if absPath <> "" and not os.path.isabs(absPath):
            absPath = os.path.normpath(os.path.join(os.path.split(setupFile)[0], absPath)).replace('\\', '/')
        if len(x) == 7:
            modelList[i] = (absPath, x[1], float(x[2]), float(x[3]), float(x[4]), int(x[5]), True if x[6] == 'True' else False)
        else:
            modelList['fileName'][i] = absPath

    # packageName = general[0]
    #config = configobj.ConfigObj(PySimulatorPath.replace('\\', '/') + '/PySimulator.ini')
    config = configobj.ConfigObj(os.path.join(os.path.expanduser("~"), '.config', 'PySimulator', 'PySimulator.ini'), encoding='utf8')
    
   
    sim = simulationThread(None)
    sim.config = config
    # sim.packageName = packageName
    sim.modelList = modelList
    sim.allSimulators = allSimulators
    sim.resultDir = resultDir
    sim.deleteDir = deleteDir
    sim.stopRequest = False
    sim.running = False
    sim.start()

    return sim

def runParallelSimulation(PySimulatorPath, setupFile, resultDir, allSimulators, deleteDir=False):
    import configobj
    import csv
    print "Start running  Parallel simulations ..."
    f = open(setupFile, 'rb')   
    line = []
    reader = csv.reader(f, delimiter=' ', skipinitialspace=True)
    for a in reader:
        if len(a) > 0:
            if not (len(a[0]) > 0 and a[0][0] == '#'):
                line.append(a[:7])
    f.close()

    modelList = numpy.zeros((len(line),), dtype=[('fileName', 'U2000'), ('modelName', 'U2000'), ('tStart', 'f8'), ('tStop', 'f8'), ('tol', 'f8'), ('nInterval', 'i4'), ('includeEvents', 'b1')])
    for i, x in enumerate(line):
        absPath = x[0].replace('\\', '/')
        if absPath <> "" and not os.path.isabs(absPath):
            absPath = os.path.normpath(os.path.join(os.path.split(setupFile)[0], absPath)).replace('\\', '/')
        if len(x) == 7:
            modelList[i] = (absPath, x[1], float(x[2]), float(x[3]), float(x[4]), int(x[5]), True if x[6] == 'True' else False)
        else:
            modelList['fileName'][i] = absPath

    config = configobj.ConfigObj(os.path.join(os.path.expanduser("~"), '.config', 'PySimulator', 'PySimulator.ini'), encoding='utf8') 
    
    sim = simulationParallelThread(None)
    sim.config = config
    sim.modelList = modelList
    sim.allSimulators = allSimulators
    sim.resultDir = resultDir
    sim.deleteDir = deleteDir
    sim.stopRequest = False
    sim.running = False
    sim.start()

    return sim
    
    
class simulationParallelThread(QtCore.QThread):
    ''' Class for the simulation thread '''
    def __init__(self, parent):
        super(simulationParallelThread, self).__init__(parent)
    
    def run(self):
        self.running = True
        z=self.allSimulators
        for simulator in self.allSimulators:
            simulationParallelThread.simulatorName = simulator.__name__.rsplit('.', 1)[-1]
            simulationParallelThread.fullSimulatorResultPath = self.resultDir + '/' + simulationParallelThread.simulatorName
            if os.path.isdir(simulationParallelThread.fullSimulatorResultPath) and self.deleteDir:
                for file_object in os.listdir(simulationParallelThread.fullSimulatorResultPath):
                    file_object_path = os.path.join(simulationParallelThread.fullSimulatorResultPath, file_object)
                    if os.path.isfile(file_object_path):
                        os.unlink(file_object_path)
                    else:
                        shutil.rmtree(file_object_path)

            if not os.path.isdir(simulationParallelThread.fullSimulatorResultPath):
                os.makedirs(simulationParallelThread.fullSimulatorResultPath)
                
            simulator.prepareSimulationList(self.modelList['fileName'],self.modelList['modelName'], self.config)
            simulationParallelThread.y=simulator
            simulationParallelThread.con=self.config
            from multiprocessing import Pool
            from multiprocessing.dummy import Pool as ThreadPool                             
            pool = ThreadPool()
            import time
            startTime = time.time()
            pool.map(parallelsimulation, zip(self.modelList['fileName'],self.modelList['modelName'],self.modelList['tStart'],self.modelList['tStop'],self.modelList['tol'],self.modelList['nInterval'],self.modelList['includeEvents']))
            pool.close()
            pool.join()   
            elapsedTime = time.time() - startTime
            print elapsedTime         
            print "Parallel simulation completed"
            self.running = False

def parallelsimulation(modellists):
     print 'inside pack'  
     packname=[]
     packname.append(modellists[0])     
     modelname=modellists[1]    
     tstart=modellists[2]
     tstop=modellists[3]
     tolerance=modellists[4]
     interval=modellists[5]
     events=modellists[6]
     
     simulator=simulationParallelThread.y       
     config =simulationParallelThread.con
     try:
       model = simulator.Model(modelname, packname, config)
       print 'pack1'
       resultFileName = simulationParallelThread.fullSimulatorResultPath + '/' + modelname + '.' + model.integrationSettings.resultFileExtension
       print 'pack2'
       model.integrationSettings.startTime = tstart
       model.integrationSettings.stopTime  = tstop
       model.integrationSettings.errorToleranceRel = tolerance
       model.integrationSettings.gridPoints = interval
       model.integrationSettings.gridPointsMode = 'NumberOf'
       model.integrationSettings.resultFileIncludeEvents = events
       model.integrationSettings.resultFileName = resultFileName     
       print 'pack3'
       print "Simulating %s by %s (result in %s)..." % (modelname,simulationParallelThread.simulatorName,resultFileName)
       model.simulate()
       
       print 'pack4'
       model.close()
     except Exception as e:
       import traceback
       traceback.print_exc(e,file=sys.stderr)
       print e

class simulationThread(QtCore.QThread):
    ''' Class for the simulation thread '''
    def __init__(self, parent):
        super(simulationThread, self).__init__(parent)

    def run(self):
        self.running = True

        for simulator in self.allSimulators:
            simulatorName = simulator.__name__.rsplit('.', 1)[-1]
            fullSimulatorResultPath = self.resultDir + '/' + simulatorName
            if os.path.isdir(fullSimulatorResultPath) and self.deleteDir:
                for file_object in os.listdir(fullSimulatorResultPath):
                    file_object_path = os.path.join(fullSimulatorResultPath, file_object)
                    if os.path.isfile(file_object_path):
                        os.unlink(file_object_path)
                    else:
                        shutil.rmtree(file_object_path)

            if not os.path.isdir(fullSimulatorResultPath):
                os.makedirs(fullSimulatorResultPath)

            packageName = []
            globalModelList = []
            globalPackageList = []
            for i in xrange(len(self.modelList['fileName'])):
                modelName = self.modelList['modelName'][i]
                packageName.append(self.modelList['fileName'][i])
                if modelName != '':
                    canLoadAllPackages = True
                    for j in xrange(len(packageName)):
                        sp = packageName[j].rsplit('.', 1)
                        if len(sp) > 1:
                            if not sp[1] in simulator.modelExtension:
                                canLoadAllPackages = False
                                break
                        else:
                            canLoadAllPackages = False
                            break

                    if canLoadAllPackages:
                        globalModelList.append(modelName)
                        for x in packageName:
                            if x not in globalPackageList:
                                globalPackageList.append(x)

                    packageName = []
            simulator.prepareSimulationList(globalPackageList, globalModelList, self.config)
            haveCOM = False

            try:
                try:
                    import pythoncom
                    pythoncom.CoInitialize()  # Initialize the COM library on the current thread
                    haveCOM = True
                except:
                    pass
                for i in xrange(len(self.modelList['fileName'])):
                    if self.stopRequest:
                        print "... Simulations canceled."
                        self.running = False
                        return
                    modelName = self.modelList['modelName'][i]
                    packageName.append(self.modelList['fileName'][i])
                    if modelName != '':
                        canLoadAllPackages = True
                        for j in xrange(len(packageName)):
                            if packageName[j] == '':
                              continue
                            sp = packageName[j].rsplit('.', 1)
                            if len(sp) > 1:
                                if not sp[1] in simulator.modelExtension:
                                    canLoadAllPackages = False
                                    break
                            else:
                                canLoadAllPackages = False
                                break
                        if canLoadAllPackages:
                            try:
                                '''
                                Do the numerical integration in a try branch
                                to avoid loosing the thread when an intended exception is raised

                                Also guard against compilation failures when loading the model
                                '''
                                model = simulator.Model(modelName, packageName, self.config)

                                resultFileName = fullSimulatorResultPath + '/' + modelName + '.' + model.integrationSettings.resultFileExtension
                                model.integrationSettings.startTime = self.modelList['tStart'][i]
                                model.integrationSettings.stopTime = self.modelList['tStop'][i]
                                model.integrationSettings.errorToleranceRel = self.modelList['tol'][i]
                                model.integrationSettings.gridPoints = self.modelList['nInterval'][i] + 1
                                model.integrationSettings.gridPointsMode = 'NumberOf'
                                model.integrationSettings.resultFileIncludeEvents = self.modelList['includeEvents'][i]
                                model.integrationSettings.resultFileName = resultFileName
                                print "Simulating %s by %s (result in %s)..." % (modelName,simulatorName,resultFileName)
                                model.simulate()

                            except Plugins.Simulator.SimulatorBase.Stopping:
                                print("Solver cancelled ... ")
                            except Exception as e:
                                import traceback
                                traceback.print_exc(e,file=sys.stderr)
                                print e
                            finally:
                                model.close()
                        else:
                            print "WARNING: Simulator " + simulatorName + " cannot handle files ", packageName, " due to unknown file type(s)."

                        packageName = []
            except:
                pass
            finally:
                if haveCOM:
                    try:
                        pythoncom.CoUninitialize()  # Close the COM library on the current thread
                    except:
                        pass

        print "... running the list of simulations done."
        self.running = False
        
@counter        
def runCompareResultsInDirectories(PySimulatorPath, dir1, listdirs, tol, logFile):

    print "Start comparing results ..."

    compare = CompareThread(None)
    compare.dir1 = dir1
    compare.listdirs= listdirs
    compare.tol = tol
    compare.logFile = logFile
    compare.stopRequest = False
    compare.running = False
    compare.start()
    return compare
   

class CompareThread(QtCore.QThread):
    ''' Class for the simulation thread '''
    def __init__(self, parent):
        super(CompareThread, self).__init__(parent)
        
    def run(self):
      self.running = True
      encoding = sys.getfilesystemencoding()

      rdir=os.path.join(os.path.dirname(self.logFile),'rfiles').replace('\\','/')
      if os.path.exists(rdir): 
         shutil.rmtree(rdir)
         
      dir1 = self.dir1
      listdirs=self.listdirs
      files1 = os.listdir(dir1)  
      fileOut = open(self.logFile, 'w')       
      for z in xrange(len(listdirs)):
        dir2=listdirs[z]    
        files2 = os.listdir(dir2)
        
        modelName1 = []
        fileName1 = []
        for fileName in files1:
            splits = fileName.rsplit('.', 1)
            print splits
            if len(splits) > 1:
                if splits[1] in SimulationResult.fileExtension:
                    modelName1.append(splits[0])
                    fileName1.append(fileName)
        modelName2 = []
        fileName2 = []
        for fileName in files2:
            splits = fileName.rsplit('.', 1)
            if len(splits) > 1:
                if splits[1] in SimulationResult.fileExtension:
                    modelName2.append(splits[0])
                    fileName2.append(fileName) 
                    
        '''create a html result file '''
        filename,fileExtension = os.path.splitext(self.logFile)
        logfile1=self.logFile.replace(fileExtension,'.html')                
        fileOuthtml= open(logfile1,'w')
           
        fileOut.write('Output file from comparison of list of simulation results within PySimulator\n')
        fileOut.write('  directory 1 (reference) : ' + dir1.encode(encoding) + '\n')
        fileOut.write('  directory 2 (comparison): ' + dir2.encode(encoding) + '\n')

        for index, name in enumerate(modelName1):            
            if self.stopRequest:
                fileOut.write("Analysis canceled.")
                fileOut.close()
                print "... Comparing result files canceled."
                self.running = False
                return

            fileOut.write('\nCompare results from\n')            
            fileOut.write('  Directory 1: ' + fileName1[index].encode(encoding) + '\n')  # Print name of file1
            print "\nCompare results from "
            print "  Directory 1: " + fileName1[index].encode(encoding)

            try:
                i = modelName2.index(name)
            except:
                fileOut.write('  Directory 2: NO equivalent found\n')
                print '  Directory 2: NO equivalent found'
                i = -1
            if i >= 0:
                fileOut.write('  Directory 2: ' + fileName2[i].encode(encoding) + '\n')  # Print name of file2
                print "  Directory 2: " + fileName2[i].encode(encoding)


                file1 = dir1 + '/' + fileName1[index]
                file2 = dir2 + '/' + fileName2[i]
                model1 = SimulatorBase.Model(None, None, None, None)
                model1.loadResultFile(file1)
                model2 = SimulatorBase.Model(None, None, None, None)
                model2.loadResultFile(file2)
                compareResults(fileOuthtml,self.logFile,file2,model1, model2, self.tol, fileOut)
                
        fileOuthtml.close()
        '''open the html file to check the html tags are correctly closed for proper display of table and add headers'''
        with open(logfile1) as myfile:
           data=myfile.read()
           header='''<body><h1>Comparison Report </h1>
<p><font style="background-color:#00FF00">Green</font> cells means success. <font style="background-color:#FF0000">Red</font> cells represents number of variables differed .</p>
</body>'''          
           m1="<table><tr><th>Model</th><th>"+os.path.basename(os.path.dirname(file2))+'</th>'+'</tr>'
           message='\n'.join(['<html>',header,m1])
           f=open(logfile1,'w')
           s = '\n'.join([message,data,'</table>','</html>']) 
           f.write(s)                    
           f.close() 
       
        '''Save the data to prepare regression report, if the user press the regression button'''
        
        newpath=os.path.dirname(logfile1)
        name=os.path.basename(logfile1)
        newname=''.join([str(z),name])
        np1=os.path.join(newpath,'rfiles').replace('\\','/')
        np2=os.path.join(np1,newname).replace('\\','/')
        
        #create a new directory to store the result files for each run, to make parsing easy when user asks for regression chart 
        if not os.path.exists(np1): 
           os.mkdir(np1)
        shutil.copy(logfile1,np2)
                     
      #print "... running the analysis done."
      fileOut.close()
      import ctypes 
      ctypes.windll.user32.MessageBoxA(0, "running the analysis done", "Compare Analysis", 0)
      self.running = False


def get_column(n,table):
   result = []
   for line in table:
      result.append(line[n])     
   return result
    
def genregressionreport(logfile):
  ''' the function is used to parse the html files and collect the table datas from different html files and finally generate single regression chart'''
  dir1=os.path.dirname(logfile)
  dir2=os.path.join(dir1,'rfiles').replace('\\','/')
  if(os.path.isdir(dir2)):
    files=os.listdir(dir2)
    hreflist=[]
    dirname=[]
    for i in xrange(len(files)):
         os.chdir(dir2)      
         soup = BeautifulSoup(open(files[i]))
         data=soup.find_all('td')
         dir=soup.find_all('th')
         hreflist.append(data)
         dirname.append(dir)
    
    os.chdir(dir1)
    filename,fileExtension = os.path.splitext(logfile)
    logfile1=logfile.replace(fileExtension,'.html')    
    f=open(logfile1,'w')    
    m1='''<body><h1>Regression Report </h1>
<p><font style="background-color:#00FF00">Green</font> cells means success. <font style="background-color:#FF0000">Red</font> cells represents number of variables differed .</p>
</body>'''
    s='\n'.join(['<html>',m1,'<table>','<tr>','<th>','model','</th>'])
    f.write(s)
    f.write('\n')
           
    for m in xrange(len(dirname[0])):
       if(m>0):
         dname=get_column(m,dirname)   
         for n in xrange(len(dname)):
                if(n==(len(dname)-1)):
                   s=''.join([str(dname[n]),'</tr>'])
                else:
                   s=''.join([str(dname[n])])
                f.write(s)
                f.write('\n')
                
    
    for i in xrange(len(hreflist[0])):                       
      if(i%2==0):
         x=get_column(i,hreflist)
         x1=x[0].find('a').string             
         s='\n'.join(['<tr>','<td>',x1,'</td>'])
         f.write(s)
         f.write('\n')
         
      if(i%2!=0):
        x=get_column(i,hreflist)
        for z in xrange(len(x)): 
            if(z==(len(x)-1)):               
               s='\n'.join([str(x[z]),'</tr>'])
            else:
               s='\n'.join([str(x[z])])            
            f.write(s)
            f.write('\n')
            
    if(i==len(hreflist[0])-1):
         s='\n'.join(['</table>','</html>'])
         f.write(s)
         f.write('\n')
    
    f.close()
    print "Regression report generated"
    webbrowser.open(logfile1)       
    
  else:
    print 'Directory rfiles does not exist, Run the the compare analysis first to get the Regression chart'  
