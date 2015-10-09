#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
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
from multiprocessing import Pool
from bs4 import BeautifulSoup

import CompareResults
import Reporting
from ... import SimulationResult



def runParallelCompareResultsInDirectories(PySimulatorPath, dir1, listdirs, tol, logDir):
    print "Start Parallel comparison results ..."
    compare = CompareParallelThread(None)
    compare.PySimulatorPath=PySimulatorPath
    compare.dir1 = dir1
    compare.listdirs= listdirs
    compare.tol = tol
    compare.logDir = logDir
    compare.stopRequest = False
    compare.running = False
    compare.start()
    return compare

class CompareParallelThread(QtCore.QThread):
    ''' Class for the simulation thread '''
    def __init__(self, parent):
        super(CompareParallelThread, self).__init__(parent)
        
    def run(self):
      self.running = True
      
      ### create a new subdirectory if the user specifies in the directory of results in the GUI ###
      subdir=self.logDir
      if not os.path.exists(subdir): 
            os.mkdir(subdir)
      
      ### copy the dygraph script from /Plugins/Analysis/Testing/ to the result directory ###      
      dygraphpath=os.path.join(self.PySimulatorPath, 'Plugins/Analysis/Testing/dygraph-combined.js').replace('\\','/')
      if os.path.exists(dygraphpath):     
          shutil.copy(dygraphpath,self.logDir)
      
      ## create a temp file for writing results and use it later to generate the regression report
      self.logFile=os.path.join(self.logDir,'index.log').replace('\\','/')

      resultfilesize=[]    
      logfiles=[]   
      list1dir=[]
      tolerance=[]      
      dir1 = self.dir1
      listdirs=self.listdirs 
      list1dir.append(dir1)
      tolerance.append(self.tol)
      
      listdir1= list1dir*len(listdirs)
      logfiles.append(self.logFile)
      logfiles1=logfiles*len(listdirs)
      tol=tolerance*len(listdirs)
      
      ## calculate the size of directory for regression report
      dir1size=Reporting.directorysize(dir1)
      resultfilesize.append(dir1size)
      
      ## calculate the size of list of directories for regression report 
      for size in xrange(len(listdirs)):
        dir2=listdirs[size] 
        dir2size=Reporting.directorysize(dir2)
        resultfilesize.append(dir2size)         
      
      dircount=[]
      resultfiles=[]      
      for i in xrange(len(logfiles1)):
          dir_name=os.path.dirname(logfiles1[i])
          filename=os.path.basename(logfiles1[i])
          newlogfile=str(i)+'_'+filename
          newlogfilepath=os.path.join(dir_name,newlogfile).replace('\\','/')
          resultfiles.append(newlogfilepath)
          dircount.append(i)
      
      ## Create a Pool of process and run the Compare Analysis in Parallel
      pool=Pool()
      startTime = time.time() 
      pool.map(ParallelCompareAnalysis, zip(listdir1,listdirs,resultfiles,dircount,tol))
      pool.close()
      pool.join()
      elapsedTime = time.time() - startTime
      #print elapsedTime
      print "Parallel Compare Analysis Completed"
      totaldir=len(listdirs)
      filecount=len(os.listdir(dir1))
      resultdirsize=sum(resultfilesize)      
      
      Reporting.genlogfilesreport(self.logFile)
      Reporting.genregressionreport(self.logFile,totaldir,filecount,elapsedTime,resultdirsize,dir1)      
      
      ## Remove the temporary logfiles and rfiles directories after the regression report completed
      logfilesdir=os.path.join(os.path.dirname(self.logFile),'logfiles').replace('\\','/')
      if os.path.exists(logfilesdir): 
         shutil.rmtree(logfilesdir)
               
      regressionfilesdir=os.path.join(os.path.dirname(self.logFile),'rfiles').replace('\\','/')
      if os.path.exists(regressionfilesdir): 
         shutil.rmtree(regressionfilesdir)
      
            
      self.running = False

def ParallelCompareAnalysis(directories):
    'unpack the directories and start running the compare analysis in parallel'
    
    dir1=directories[0]
    dir2=directories[1]
    logfile=directories[2]
    dircount=directories[3]
    tolerance=directories[4]
    
    files1 = os.listdir(dir1)
    files2 = os.listdir(dir2)
    
    encoding = sys.getfilesystemencoding()
    
    modelName1 = []
    fileName1 = []
    for fileName in files1:
         splits = fileName.rsplit('.', 1)
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
    filename,fileExtension = os.path.splitext(logfile)
    logfile1=logfile.replace(fileExtension,'.html') 
    
    fileOut = open(logfile, 'w')         
    fileOuthtml= open(logfile1,'w')
           
    fileOut.write('Output file from comparison of list of simulation results within PySimulator\n')
    fileOut.write('  directory 1 (reference) : ' + dir1.encode(encoding) + '\n')
    fileOut.write('  directory 2 (comparison): ' + dir2.encode(encoding) + '\n')
    
    for index, name in enumerate(modelName1):                      
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
               
                from ...Simulator import SimulatorBase 
                
                model1 = SimulatorBase.Model(None, None, None)
                model1.loadResultFile(file1)
                model2 = SimulatorBase.Model(None, None, None)
                model2.loadResultFile(file2)
                CompareResults.compareResults(model1, model2, dircount, tolerance, fileOut, fileOuthtml,logfile,file2,file1)
                
    fileOut.write('\n')    
    fileOut.write("******* Compare Analysis Completed   *******" + u"\n")
    fileOut.write('\n') 
    fileOut.close()      
    fileOuthtml.close()
    
    green=[]
    red=[]
    '''open the html file to insert start html tags and add add headers of the directory name'''
    with open(logfile1) as myfile:
        htmldata=myfile.read()          
        m1="<table><tr><th id=0>Model</th><th id=0>"+os.path.basename(os.path.dirname(file2))+'</th>'+'</tr>'
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
        colorpercent=int((len(green))*100/(len(green)+len(red)))
        if (colorpercent==100):
            m1='<tr><td></td><td id=1 bgcolor="#00FF00" align="center">'+ str(len(green))+' passed'+' / '+str(len(red))+' failed'+'</td></tr>'
            percentage=str((len(green))*100/(len(green)+len(red)))+'%'+' passed'
            m2='<tr><td></td><td id=100 bgcolor="#00FF00" align="center">'+percentage+'</td></tr>'
            m3='\n'.join([message,m1,m2,htmldata,'</table>','</html>'])
            f.write(m3)
            f.write('\n')
        if(colorpercent>=51 and colorpercent<=99):
            m1='<tr><td></td><td id=1 bgcolor="#FFA500" align="center">'+ str(len(green))+' passed'+' / '+str(len(red))+' failed'+'</td></tr>'
            percentage=str((len(green))*100/(len(green)+len(red)))+'%'+' passed'
            m2='<tr><td></td><td id=100 bgcolor="#FFA500" align="center">'+percentage+'</td></tr>'
            m3='\n'.join([message,m1,m2,htmldata,'</table>','</html>'])
            f.write(m3)
            f.write('\n')
        if(colorpercent<=50):
            m1='<tr><td></td><td id=1 bgcolor="#FF0000" align="center">'+ str(len(green))+' passed'+' / '+str(len(red))+' failed'+'</td></tr>'
            percentage=str((len(green))*100/(len(green)+len(red)))+'%'+' passed'
            m2='<tr><td></td><td id=100 bgcolor="#FF0000" align="center">'+percentage+'</td></tr>'
            m3='\n'.join([message,m1,m2,htmldata,'</table>','</html>'])
            f.write(m3)
            f.write('\n')
        f.close() 
                   
    logfiledir=os.path.dirname(logfile)
    logfilename=os.path.basename(logfile)
    logfilenp1=os.path.join(logfiledir,'logfiles').replace('\\','/')
    logfilenp2=os.path.join(logfilenp1,logfilename).replace('\\','/')
    
    if not os.path.exists(logfilenp1): 
       os.mkdir(logfilenp1)
    shutil.move(logfile,logfilenp2)  
    
        
    newpath=os.path.dirname(logfile1)
    name=os.path.basename(logfile1)
    np1=os.path.join(newpath,'rfiles').replace('\\','/')
    np2=os.path.join(np1,name).replace('\\','/')
        
    #create a new directory to store the result files for each run, to prepare regression chart 
    if not os.path.exists(np1): 
       os.mkdir(np1)
    shutil.move(logfile1,np2)  
    

