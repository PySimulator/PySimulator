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

import numpy
import os, sys
import shutil
import time
from PySide import QtCore
from ... import Simulator
from multiprocessing import Pool
import jsonpickle


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
                if a[0] != '':
                    line.append(a)
                
    f.close()
    modelList = numpy.zeros((len(line),), dtype=[('fileName', 'U2000'), ('modelName', 'U2000'), ('subDirectory', 'U2000'), ('tStart', 'f8'), ('tStop', 'f8'), ('tol', 'f8'), ('stepSize', 'f8'), ('nInterval', 'i4'), ('includeEvents', 'b1')])
    for i, x in enumerate(line):
        absPath = x[0].replace('\\', '/')
        if absPath <> "" and not os.path.isabs(absPath):
            absPath = os.path.normpath(os.path.join(os.path.split(setupFile)[0], absPath)).replace('\\', '/')
        if len(x) >= 9:
            modelList[i] = (absPath, x[1], x[2], float(x[3]), float(x[4]), float(x[5]), float(x[6]), int(x[7]), True if x[8].lower() == 'true' else False)
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

            ## Call prepareSimulationList to translate models in Dymola 
            simulator.prepareSimulationList(globalPackageList, globalModelList, self.config)
            
  
            ## create a login directory for logging multiprocessing output from terminal to a file ##
            logdir =os.path.join(os.getcwd(),'loginentries').replace('\\','/')
            if not os.path.exists(logdir):
                os.mkdir(logdir)
            
            ## create a list of directories for each model and run the simulation in their respective directory to avoid conflicts 
            curdir=os.getcwd()
            dirs=[]
            processlog=[]
            for z in xrange(len(self.modelList['modelName'])):
                s=str(self.modelList['modelName'][z])+simulatorName+str(z)
                np=os.path.join(curdir,s).replace('\\','/')
                txt=str(self.modelList['modelName'][z])+simulatorName+'.txt'
                log=os.path.join(logdir,txt).replace('\\','/')
                processlog.append(log)
                '''if not os.path.exists(logdir):
                    os.mkdir(logdir)'''
                dirs.append(np)
                
            ## Pickle the simulator plugin object using jsonpickle as a string to be pickled by multiprocessing package
            pickleobj=jsonpickle.encode(simulator,max_depth=1)
           
            #check the subdirectory for empty strings and replace it with 'N' , as it cannot process empty list of strings to multiprocess module
            subdirlist= ["N" if not x else x for x in self.modelList['subDirectory']]
           
            ## Create a Pool of process and run the Simulation in Parallel
            pool=Pool()
            #startTime = time.time()
            for i in xrange(len(self.modelList['modelName'])):
               model=self.modelList['modelName'][i]
               packname=self.modelList['fileName'][i]
               tStart=self.modelList['tStart'][i]
               tStop = self.modelList['tStop'][i]
               tol = self.modelList['tol'][i]
               stepSize = self.modelList['stepSize'][i]
               nInterval = self.modelList['nInterval'][i] + 1
               events = self.modelList['includeEvents'][i]
               dir=dirs[i]
               subdir=subdirlist[i]
               logfile=processlog[i]               
               pool.apply_async(ParallelSimulation, args=(model,[packname],tStart,tStop,tol,stepSize,nInterval,events,dir,self.config,fullSimulatorResultPath,pickleobj,simulatorName,subdir,logfile))                        
            pool.close()
            pool.join()
            #elapsedTime = time.time() - startTime
            #print elapsedTime
            
            ## print the process log entries to GUI             
            for i in xrange(len(processlog)):
                f=open(processlog[i],'r')
                processlogentries=f.read()
                print processlogentries
            f.close()
                    
        shutil.rmtree(logdir)
        print "Parallel simulation completed"
        self.running = False

class Logger(object):
    def __init__(self,logname):
        self.terminal = sys.stdout
        self.log = open(logname, "w")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        
def ParallelSimulation(modelname,packname,tstart,tstop,tolerance,stepsize,interval,events,dirname,config,resultpath,pickleobj,simulatorname,subdir,logfile):
     ##run the simuations in parallel using the multiprocessing module##
     
     simulator=jsonpickle.decode(pickleobj) 
     try:
        try:
          import pythoncom
          pythoncom.CoInitialize()  # Initialize the COM library on the current thread
          haveCOM = True
        except:
          pass

        canLoadAllPackages = True
        sp = packname[0].rsplit('.', 1)
        if len(sp) > 1:
           if not sp[1] in simulator.modelExtension:
              canLoadAllPackages = False
        else:
           canLoadAllPackages = False

        #Write the process output to a file 

        sys.stdout=Logger(logfile)
        if canLoadAllPackages:
            #create separate working directory for each model
            if(simulatorname!='FMUSimulator'):
              if not os.path.exists(dirname):
                 os.mkdir(dirname)
              os.chdir(dirname)
            try:
               model=simulator.getNewModel(modelname, packname, config)
               if (subdir == 'N'):
                  resultDir = resultpath
               else:
                  resultDir = resultpath + '/' + subdir
                  if not os.path.isdir(resultDir):
                     os.makedirs(resultDir)

               resultFileName = resultDir + '/' + modelname + '.' + model.integrationSettings.resultFileExtension
               model.integrationSettings.startTime = tstart
               model.integrationSettings.stopTime  = tstop
               model.integrationSettings.errorToleranceRel = tolerance
               model.integrationSettings.fixedStepSize = stepsize
               model.integrationSettings.gridPoints = interval
               model.integrationSettings.gridPointsMode = 'NumberOf'
               model.integrationSettings.resultFileIncludeEvents = events
               model.integrationSettings.resultFileName = resultFileName
               print "Simulating %s by %s (result in %s)..." % (modelname,simulatorname,resultFileName)
               model.simulate()
            except Simulator.SimulatorBase.Stopping:
               print("Solver cancelled ... ")
            except Exception as e:
               import traceback
               traceback.print_exc(e,file=sys.stderr)
               print e
            finally:
               model.close()
        else:
            print "WARNING: Simulator " + simulatorname + " cannot handle files ", packname[0], " due to unknown file type(s)."
     except:
         pass
     finally:
         if haveCOM:
            try:
               pythoncom.CoUninitialize()  # Close the COM library on the current thread
            except:
               pass 
