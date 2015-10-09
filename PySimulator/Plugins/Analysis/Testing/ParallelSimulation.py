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
from PySide import QtCore
from multiprocessing import Pool



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
            
            
            '''create a new list of resultpath, config, and simulatorname to be pickled by the multiprocessing pool.map()'''
            p=[]
            c=[]
            n=[]     
            p.append(fullSimulatorResultPath)
            c.append(self.config)
            n.append(simulatorName)
            
            resultpath=p*len(self.modelList['modelName'])
            config=c*len(self.modelList['modelName'])
            simname=n*len(self.modelList['modelName'])
            
            '''create a list of directories for each model and run the simulation in their respective directory to avoid conflicts '''
            dir=os.getcwd()
            dirs=[]
            for z in xrange(len(self.modelList['modelName'])):
                s=str(self.modelList['modelName'][z])+str(z)
                np=os.path.join(fullSimulatorResultPath,s).replace('\\','/')
                if not os.path.exists(np): 
                    os.mkdir(np)
                dirs.append(np)
    
            #check the subdirectory for empty strings and replace it with 'N' for passing to pool.map(), as it cannot process empty list of strings to multiprocess module
            subdirlist= ["N" if not x else x for x in self.modelList['subDirectory']]
            ## Create a Pool of process and run the Simulation in Parallel
            pool=Pool()
            #startTime = time.time() 
            pool.map(ParallelSimulation, zip(self.modelList['fileName'],self.modelList['modelName'],subdirlist,self.modelList['tStart'],self.modelList['tStop'],self.modelList['tol'],self.modelList['stepSize'],self.modelList['nInterval'],self.modelList['includeEvents'],dirs,resultpath,config,simname))
            pool.close()
            pool.join()
            #elapsedTime = time.time() - startTime
            #print elapsedTime         
        print "Parallel simulation completed"
        self.running = False
            
  
def ParallelSimulation(modellists):
     'unpacks the modelists and run the simuations in parallel using the multiprocessing module'
     packname=[]
     packname.append(modellists[0])     
     modelname=modellists[1]
     subdir=modellists[2]     
     tstart=modellists[3]
     tstop=modellists[4]
     tolerance=modellists[5]
     stepsize=modellists[6]
     interval=modellists[7]
     events=modellists[8]
     dirname=modellists[9]
     path=modellists[10]
     config=modellists[11]
     simulator=modellists[12]
     filename,fileExtension = os.path.splitext(packname[0])
     os.chdir(dirname)
     try:
       '''load the Simulator Module like this, depending on the simulator selected by the users as the pool.map() cannot pickle module types '''
       if(simulator=='OpenModelica'):
           from ...Simulator.OpenModelica import OpenModelica
           extension=OpenModelica.modelExtension
           checkextension = [s for s in extension if (fileExtension).replace('.','') in s]
           if checkextension:
              model=OpenModelica.getNewModel(modelname, packname, config)
           else:
              print "WARNING: Simulator OpenModelica " + " cannot handle files ", packname[0], " due to unknown file type(s)."
             
       if(simulator=='Dymola'):
           from ...Simulator.Dymola import Dymola
           extension=Dymola.modelExtension
           checkextension = [s for s in extension if (fileExtension).replace('.','') in s]
           if checkextension:
             model=Dymola.getNewModel(modelname, packname, config)
           else:
             print "WARNING: Simulator Dymola " + " cannot handle files ", packname[0], " due to unknown file type(s)."
             
       if(simulator=='FMUSimulator'):
           from ...Simulator.FMUSimulator import FMUSimulator
           extension=FMUSimulator.modelExtension
           checkextension = [s for s in extension if (fileExtension).replace('.','') in s]
           if checkextension:
              model=FMUSimulator.getNewModel(modelname, packname, config)
           else:
             print "WARNING: Simulator FMUSimulator " + " cannot handle files ", packname[0], " due to unknown file type(s)."
               
       if(simulator=='SimulationX'):
           from ...Simulator.SimulationX import SimulationX
           extension=SimulationX.modelExtension
           checkextension = [s for s in extension if (fileExtension).replace('.','') in s]
           if checkextension:
               model=SimulationX.getNewModel(modelname, packname, config)
           else:
             print "WARNING: Simulator SimulationX " + " cannot handle files ", packname[0], " due to unknown file type(s)."

       if(simulator=='Wolfram'):
           from ...Simulator.Wolfram import Wolfram
           extension=Wolfram.modelExtension
           checkextension = [s for s in extension if (fileExtension).replace('.','') in s]
           if checkextension:
              model=Wolfram.getNewModel(modelname, packname, config)
           else:
             print "WARNING: Simulator Wolfram " + " cannot handle files ", packname[0], " due to unknown file type(s)."
 
       if (subdir == 'N'):
          resultDir = path        
       else:
          resultDir = path + '/' + subdir
          if not os.path.isdir(resultDir):
              os.makedirs(resultDir)
         
       if checkextension:
         resultFileName = resultDir + '/' + modelname + '.' + model.integrationSettings.resultFileExtension
         model.integrationSettings.startTime = tstart
         model.integrationSettings.stopTime  = tstop
         model.integrationSettings.errorToleranceRel = tolerance
         model.integrationSettings.fixedStepSize = stepsize
         model.integrationSettings.gridPoints = interval
         model.integrationSettings.gridPointsMode = 'NumberOf'
         model.integrationSettings.resultFileIncludeEvents = events
         model.integrationSettings.resultFileName = resultFileName     
         print "Simulating %s by %s (result in %s)..." % (modelname,simulator,resultFileName)
         model.simulate()
         model.close()
     except Exception as e:
       import traceback
       traceback.print_exc(e,file=sys.stderr)
       print e
       
