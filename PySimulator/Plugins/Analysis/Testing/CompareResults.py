#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (C) 2011-2015 German Aerospace Center DLR
(Deutsches Zentrum fuer Luft- und Raumfahrt e.V.),
Institute of System Dynamics and Control
Copyright (C) 2014-2015 Open Source Modelica Consortium
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
import os, sys
import shutil
import time
from bs4 import BeautifulSoup
import numpy

import ParallelComparison
import Reporting
import Compare
from ... import SimulationResult
from ... import Simulator



def compareListMenu(model, gui):

    class CompareListControl(QtGui.QDialog):
        ''' Class for the CompareList Control GUI '''

        def __init__(self):
            QtGui.QDialog.__init__(self)
            self.setModal(False)
            self.setWindowTitle("Compare Result Files")
            self.setWindowIcon(QtGui.QIcon(gui.rootDir + '/Icons/pysimulatorLists.ico'))

            mainGrid = QtGui.QGridLayout(self)

            dir1 = QtGui.QLabel("Baseline results:", self)
            mainGrid.addWidget(dir1, 0, 0, QtCore.Qt.AlignRight)
            self.dir1Edit = QtGui.QLineEdit("", self)
            mainGrid.addWidget(self.dir1Edit, 0, 1)
            browseDir1 = QtGui.QPushButton("Select", self)
            mainGrid.addWidget(browseDir1, 0, 2)
           
            #dir2 = QtGui.QLabel("Directory 2 of results:", self)
            #mainGrid.addWidget(dir2, 1, 0, QtCore.Qt.AlignRight)
            #self.dir2Edit = QtGui.QLineEdit("", self)
            #mainGrid.addWidget(self.dir2Edit, 1, 1)
            browseDir2 = QtGui.QPushButton("Select", self)
            mainGrid.addWidget(browseDir2, 1, 2)
           
            self.listdir = QtGui.QLabel("List of Directories:", self)
            mainGrid.addWidget(self.listdir , 1, 0, QtCore.Qt.AlignRight)
            self.directory = QtGui.QListWidget(self)
            self.directory.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
            self.directory.setFixedHeight(80)
            mainGrid.addWidget(self.directory, 1, 1, 2, 1)
            
            self.removeButton = QtGui.QPushButton("Remove", self)
            mainGrid.addWidget(self.removeButton, 2, 2)
            self.removeButton.clicked.connect(self.remove)
            
            tol = QtGui.QLabel("Error tolerance:", self)
            mainGrid.addWidget(tol, 3, 0, QtCore.Qt.AlignRight)
            self.tolEdit = QtGui.QLineEdit("", self)
            mainGrid.addWidget(self.tolEdit, 3, 1)

            result = QtGui.QLabel("Report Directory:", self)
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
            
            self.parallelrunButton = QtGui.QPushButton("Parallel analysis", self)
            mainGrid.addWidget(self.parallelrunButton, 8, 1)
            self.parallelrunButton.clicked.connect(self.parallelrun)
            
            def _browseDir1Do():
                dirName = QtGui.QFileDialog().getExistingDirectory(self, 'Open Directory of Results', os.getcwd())
                dirName = dirName.replace('\\', '/')
                if dirName != '':
                    self.dir1Edit.setText(dirName)

            def _browseDir2Do():
                dirName = QtGui.QFileDialog().getExistingDirectory(self, 'Open Directory of Results', os.getcwd())
                dirName = dirName.replace('\\', '/')
                if dirName != '':
                    #self.dir2Edit.setText(dirName)
                    self.directory.addItem(dirName)

            def _browseResultDo():
                #(fileName, trash) = QtGui.QFileDialog().getSaveFileName(self, 'Define Analysis Result File', os.getcwd(), '(*.log);;All Files(*.*)')
                dirName = QtGui.QFileDialog().getExistingDirectory(self, 'Select Directory of Results', os.getcwd())
                dirName = dirName.replace('\\', '/')
                if dirName != '':
                    self.resultEdit.setText(dirName)

            browseDir1.clicked.connect(_browseDir1Do)
            browseDir2.clicked.connect(_browseDir2Do)
            browseResult.clicked.connect(_browseResultDo)

            self.tolEdit.setText('1e-3')
            self.resultEdit.setText(os.getcwd().replace('\\', '/')+'/RegressionReport')

            self.dir1Edit.setText(os.getcwd().replace('\\', '/'))
            #self.dir2Edit.setText(os.getcwd().replace('\\', '/'))

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
            logDir = self.resultEdit.text()
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
                gui._compareThreadTesting = runCompareResultsInDirectories(gui.rootDir, dir1, listdirs, tol, logDir)
            else:
                print 'Select List of Directories to compare'

        def parallelrun(self):
            if hasattr(gui, '_compareThreadTesting'):
                if gui._compareThreadTesting.running:
                    print "An analysis to compare result files is still running."
                    return

            # Get data from GUI
            dir1 = self.dir1Edit.text()
            #dir2 = self.dir2Edit.text()
            logDir = self.resultEdit.text()
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
                gui._compareThreadTesting = ParallelComparison.runParallelCompareResultsInDirectories(gui.rootDir, dir1, listdirs, tol, logDir)
            else:
                print 'Select List of Directories to compare'
                
        def stop(self):
            if hasattr(gui, '_compareThreadTesting'):
                if gui._compareThreadTesting.running:
                    gui._compareThreadTesting.stopRequest = True
                    print "Try to cancel comparing results files ..."
       
    # Code of function
    control = CompareListControl()
    control.show()

def runCompareResultsInDirectories(PySimulatorPath, dir1, listdirs, tol, logDir):

    print "Start comparing results ..."
    compare = CompareThread(None)
    compare.PySimulatorPath=PySimulatorPath
    compare.dir1 = dir1
    compare.listdirs= listdirs
    compare.tol = tol
    compare.logDir = logDir
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
      
      try:
        import pydevd
        pydevd.connected = True
        pydevd.settrace(suspend=False)
      except:
        # do nothing, since error message only indicates we are not in debug mode
        pass
            
      workdir=os.getcwd()
      encoding = sys.getfilesystemencoding()
      dir1 = self.dir1
      files1 = os.listdir(dir1) 
      if (len(files1)!=0): 
          
          subdir=self.logDir          
          ## clear the regression report directory if already exists
          if os.path.exists(subdir): 
              shutil.rmtree(subdir, True)
              
          ### create a RegressionReport Directory in the current working directory ###
          if not os.path.exists(subdir): 
              os.mkdir(subdir)
                
          ### copy the dygraph script from /Plugins/Analysis/Testing/ to the result directory ###      
          dygraphpath=os.path.join(self.PySimulatorPath, 'Plugins/Analysis/Testing/dygraph-combined.js').replace('\\','/')
          if os.path.exists(dygraphpath):     
              shutil.copy(dygraphpath,self.logDir)
              
          resultfilesize=[]   
          #dir1 = self.dir1
          ## calculate the size of directory for regression report
          dir1size=Reporting.directorysize(dir1)
          resultfilesize.append(dir1size)
          
          listdirs=self.listdirs
          #files1 = os.listdir(dir1) 
          
          ## create a temp file for writing results and use it later to generate the regression report
          self.logFile=os.path.join(self.logDir, "index.log").replace('\\','/')
          
          fileOut = open(self.logFile, 'w')
          startTime = time.time()
          for dircount in xrange(len(listdirs)):
            dir2=listdirs[dircount] 
            ## calculate the size of list of directories for regression report
            dir2size=Reporting.directorysize(dir2)
            resultfilesize.append(dir2size)                   
            
            files2 = os.listdir(dir2)    
            modelName1 = []
            fileName1 = []
            for fileName in files1:
                splits = fileName.rsplit('.', 1)
                #print splits
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
                    ### codes to handle empty directory list in comparing results
                    model1 = Simulator.SimulatorBase.Model(None, None, None)
                    filepath = dir1 + '/' + fileName1[index]
                    model1.loadResultFile(filepath)
                    var = model1.integrationResults.getVariables()
                    message1= '<a href >' + fileName1[index].encode(encoding).replace('.mat','') +'-'+str(len(var))+'</a>' +' </td>'
                    emptyhref= "Not-Found"
                    s = '\n'.join(['<tr>','<td id=2>',message1,'<td id=2 bgcolor=#FFFFFF align="center">',emptyhref,'</td>','</tr>']) 
                    fileOuthtml.write(s)
                    fileOuthtml.write('\n')
                    i = -1
                if i >= 0:
                    fileOut.write('  Directory 2: ' + fileName2[i].encode(encoding) + '\n')  # Print name of file2
                    print "  Directory 2: " + fileName2[i].encode(encoding)


                    file1 = dir1 + '/' + fileName1[index]
                    file2 = dir2 + '/' + fileName2[i]
                    model1 = Simulator.SimulatorBase.Model(None, None, None)
                    model1.loadResultFile(file1)
                    model2 = Simulator.SimulatorBase.Model(None, None, None)
                    model2.loadResultFile(file2)
                    compareResults(model1, model2, dircount, self.tol, fileOut, fileOuthtml,self.logFile,file2,file1)
            
            fileOut.write('\n')    
            fileOut.write("******* Compare Analysis Completed   *******" + u"\n")
            fileOut.write('\n')                   
            fileOuthtml.close()
            green=[]
            red=[]
            
            '''open the html file to insert start html tags and add add headers of the directory name'''
            with open(logfile1) as myfile:
               htmldata=myfile.read()          
               m1="<table><tr><th id=0>Model</th><th id=0>"+os.path.basename(dir2)+'</th>'+'</tr>'
               soup = BeautifulSoup(open(logfile1))
               data=soup.find_all('td',{"bgcolor":["#00FF00","#FF0000"]})         
               for i in xrange(len(data)):
                  x=BeautifulSoup(str(data[i]))
                  tag=x.td
                  checkcolor=tag['bgcolor']
                  if(checkcolor=="#00FF00"):
                       green.append(checkcolor)
                  else:
                       red.append(checkcolor)

               message='\n'.join(['<html>',m1])
               f=open(logfile1,'w')
               if (len(green)==0 and len(red)==0): 
                 colorpercent=0
               else:
                 colorpercent=int((len(green))*100/(len(green)+len(red)))
                 
               if (colorpercent==100):
                   m1='<tr><td></td><td id=1 bgcolor="#00FF00" align="center">'+ str(len(green))+' passed'+' / '+str(len(red))+' failed'+'</td></tr>'
                   #percentage=str((len(green))*100/(len(green)+len(red)))+'%'+' passed'
                   percentage=str(colorpercent)+'%'+' passed'
                   m2='<tr><td></td><td id=100 bgcolor="#00FF00" align="center">'+percentage+'</td></tr>'
                   m3='\n'.join([message,m1,m2,htmldata,'</table>','</html>'])
                   f.write(m3)
                   f.write('\n')
               if(colorpercent>=51 and colorpercent<=99):
                   m1='<tr><td></td><td id=1 bgcolor="#FFA500" align="center">'+ str(len(green))+' passed'+' / '+str(len(red))+' failed'+'</td></tr>'
                   #percentage=str((len(green))*100/(len(green)+len(red)))+'%'+' passed'
                   percentage=str(colorpercent)+'%'+' passed'
                   m2='<tr><td></td><td id=100 bgcolor="#FFA500" align="center">'+percentage+'</td></tr>'
                   m3='\n'.join([message,m1,m2,htmldata,'</table>','</html>'])
                   f.write(m3)
                   f.write('\n')
               if(colorpercent<=50):
                   m1='<tr><td></td><td id=1 bgcolor="#FF0000" align="center">'+ str(len(green))+' passed'+' / '+str(len(red))+' failed'+'</td></tr>'
                   #percentage=str((len(green))*100/(len(green)+len(red)))+'%'+' passed'
                   percentage=str(colorpercent)+'%'+' passed'
                   m2='<tr><td></td><td id=100 bgcolor="#FF0000" align="center">'+percentage+'</td></tr>'
                   m3='\n'.join([message,m1,m2,htmldata,'</table>','</html>'])
                   f.write(m3)
                   f.write('\n')
               f.close()
           
            '''Save the data to prepare regression report'''
            
            newpath=os.path.dirname(logfile1)
            name=os.path.basename(logfile1)
            newname=''.join([str(dircount),'_',name])
            np1=os.path.join(newpath,'rfiles').replace('\\','/')
            np2=os.path.join(np1,newname).replace('\\','/')
            
            #create a new directory to store the result files for each run, to make parsing easy when user asks for regression chart 
            if not os.path.exists(np1): 
               os.mkdir(np1)
            shutil.copy(logfile1,np2)
                      
          print "... running the analysis done."
          elapsedTime = time.time() - startTime
          fileOut.close()
          totaldir=len(listdirs)
          filecount=len(files1)
          resultdirsize=sum(resultfilesize)
          Reporting.genregressionreport(self.logFile,totaldir,filecount,elapsedTime,resultdirsize,dir1,self.tol)
          
          ## remove the temporary rfiles directory after the Regression report generated          
          regressionfilesdir=os.path.join(os.path.dirname(self.logFile),'rfiles').replace('\\','/')
          if os.path.exists(regressionfilesdir): 
              shutil.rmtree(regressionfilesdir)
              
          ## change the directory to workdir after regression report
          os.chdir(workdir)
      else:
          print 'directory 1:'+'\'' + dir1 + '\'' +' is Empty and Report cannot be Generated'
          print "... running the analysis done."
      
      self.running = False

def compareResults(model1, model2, dircount=None, tol=1e-3, fileOutput=sys.stdout, filewritehtml=None,resultfile=None,htmlfile=None,file1=None):
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
    
    ## count the number of total variables in each result file
    model1var=str(len(var1))
    model2var=str(len(var2))
        
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
    
    diff3=[]
    diff2=[]
    diff=[] 
    for i in xrange(model1.integrationResults.nTimeSeries):
        if len(timeSeries1Names[i]) > 0:
            t1 = model1.integrationResults.timeSeries[i].independentVariable
            f1 = model1.integrationResults.timeSeries[i].data
           
            if model1.integrationResults.timeSeries[i].interpolationMethod == "constant" and t1 is not None:
                t1, f1 = prepareMatrix(t1, f1)
            for j in xrange(model2.integrationResults.nTimeSeries):
                if len(timeSeries2Names[j]) > 0:
                    check1 = set(timeSeries1Names[i])
                    check2 = set(timeSeries2Names[j])
                    namesBothSub = list(check1 & check2)
    
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
                        f2 = model2.integrationResults.timeSeries[j].data
                        
                        if model2.integrationResults.timeSeries[j].interpolationMethod == "constant" and t2 is not None:
                            if pMatrix2[j] is None:
                                t2, f2 = prepareMatrix(t2, f2)
                                pMatrix2[j] = (t2, f2)
                            else:
                                t2 = pMatrix2[j][0]
                                f2 = pMatrix2[j][1]
                        
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
                        for m in xrange(len(identical)):
                            if not identical[m]:
                                message = u"Results for " + namesBothSub[m] + u" are NOT identical within the tolerance " + unicode(tol) + u"; estimated Tolerance = " + unicode(estTol[m])
                                message2=namesBothSub[m]+'#'+unicode(estTol[m])
                                tupl=()
                                tupl=(namesBothSub[m],unicode(estTol[m]))
                                diff.append(namesBothSub[m])
                                diff2.append(message2)
                                diff3.append(tupl)
                                fileOutput.write(message + u"\n")
                        
    ## sort the differed variable by name                          
    diff1=sorted(diff2)
    ## sort the differed variable by highest error        
    difftol=sorted(diff3,key=lambda x: x[1],reverse=True)
    if (len(diff)!=0):
         Reporting.generatehtml(model1,model2,diff,htmlfile,resultfile,dircount)                   
                                  
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
    totalComparedvar= unicode(nPos + nNeg)
    if allIdentical:
        message = u"The results for all compared variables are identical up to the given tolerance = " + unicode(tol)
        # print message
        fileOutput.write(message + u"\n")
    message = u"Maximum estimated tolerance = " + unicode(maxEstTol)
    # print message
    fileOutput.write(message + u"\n")

    print "... done."
    ''' Function call to generate the overview report'''
    if htmlfile is not None:
        Reporting.htmloverview(filewritehtml,resultfile,htmlfile,file1,diff1,difftol,dircount,model1var,model2var,totalComparedvar,maxEstTol)

    return


