#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (C) 2011-2014
Open Source Modelica Consortium
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

'''
Author : Anand Kalaiarasi Ganeson, ganan642@student.liu.se,
Maintainer: Adeel Asghar, adeel.asghar@liu.se
***************************
This OpenModelica plugin can load Modelica models (assuming that OpenModelica 1.8 or later is installed)
and simulation executable of OpenModelica. It runs the executable and loads the result file.
***************************
'''

import Plugins.Simulator.SimulatorBase
import OMPython
import Plugins.SimulationResult.DymolaMat.DymolaMat as DymolaMat
import os, sys, shutil
import subprocess
import SocketServer
import re
import threading

iconImage = 'simulatorOpenModelica.ico'
modelExtension = ['mo', 'exe']  # e.g. ['mo']
parameters_changed = False
simulationProgressData = 0.0

def closeSimulationPlugin():
    try:
        OMPython.execute("quit()")
    except SystemExit:
        pass

# Change the parameters of the model file
def setNewParameters(cmd):
    OMPython.execute(cmd);
    global parameters_changed  # Set this variable if the parameters are changed
    parameters_changed = True
    return

# Set the parameters in the model_init.xml file
def setInitXmlValues(modelName, varName, value):
    modelName = modelName + "_init.xml"
    OMPython.execute("setInitXmlStartValue(\"" + modelName + "\",variableName=\"" + varName + "\",startValue=\"" + value + "\",outputFile=\"temp.xml\")")

    if os.path.exists(modelName):
        os.remove(modelName)
        os.rename("temp.xml", modelName)
    return

class Model(Plugins.Simulator.SimulatorBase.Model):

    def __init__(self, modelName, modelFileName, config):

        Plugins.Simulator.SimulatorBase.Model.__init__(self, modelName, modelFileName, 'OpenModelica', config)

        self.onlyResultFile = False
        self.integrationSettings.resultFileExtension = 'mat'

        self._availableIntegrationAlgorithms = ['Dassl', 'Euler', 'Rungekutta', 'Dopri5']
        self.integrationSettings.algorithmName = self._availableIntegrationAlgorithms[0]

        self._IntegrationAlgorithmHasFixedStepSize = [False, True, True, False]
        self._IntegrationAlgorithmCanProvideStepSizeResults = [False, True, True, False]

        self.compileModel()

        if self.resFile != '""':
            self._initialResult = loadResultFileInit(os.path.join(os.getcwd(), self.name + "_init.xml"))
        else:
            print "The selected model could not be instantiated, check for any dependencies that the model might have"
            return

        # SocketServer setup to visualize the simulation progress bar
        HOST, PORT = "localhost", 0
        self.server = SocketServer.TCPServer((HOST, PORT), ThreadedTCPRequestHandler)
        self.ip, self.port = self.server.server_address
        self.server_port = self.port

        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.setDaemon(True)
        self.server_thread.start()

    def compileModel(self):
        """
        This function is needed to load the data into the VariablesBrowser
        before simulating the model with parameters.
        """
        if len(self.fileName) == 1:
          if self.fileName[0] <> "":
            # Load the Modelica Standard library only if there is a uses-annotation on the model (done automagically)
            if not (os.path.isfile(self.fileName[0]) and OMPython.sendExpression("loadFile(\"" + self.fileName[0].encode(sys.getfilesystemencoding()) + "\")")):
                print OMPython.sendExpression("getErrorString()")
                raise FileDoesNotExist("compileModel failed, file '" + self.fileName[0] + "' does not exist")
          else:
            pack = str(self.name.split(".",1)[0])
            if not OMPython.sendExpression("loadModel(" + pack + ")"):
              print OMPython.sendExpression("getErrorString()")
              raise FileDoesNotExist("compileModel failed, package " + pack + " does not exist")

          # set the working directory in OMC
          pwd = os.path.abspath('.').replace('\\', '/')
          workdir = OMPython.sendExpression("cd(\"" + pwd + "\")")
          # simulate the model
          simResult = OMPython.sendExpression(str("buildModel(" + self.name + ")"))
          if simResult[0] == "":
            raise BuildModelFail(OMPython.sendExpression("getErrorString()"))
          # call getErrorString() to get complete error.
          print OMPython.sendExpression("getErrorString()"),
          # read the result file
          self.resFile = os.path.join(workdir,self.name + "_res.mat")

    def getReachedSimulationTime(self):
        '''
        Read the current simulation time during a simulation
        from the Model.exe file generated during loadFile()
        '''
        t = ((simulationProgressData * self.integrationSettings.stopTime) / 100.0)
        return t

    def simulate(self):

        def precheck_for_set_sim_options():
            s = self.integrationSettings
            settings = s.__dict__

            # prepare the simulation options string for OpenModelica
            set_sim_options = ['startTime', 'stopTime', 'errorToleranceTol', 'resultFileFormat', 'fixedStepSize', 'algorithmName']
            om_sim_options = ['startTime', 'stopTime', 'tolerance', 'outputFormat', 'fixedStepSize', 'method']
            simulate_options = []
            for k, v in settings.iteritems():
                if k in set_sim_options:
                    i = set_sim_options.index(k)
                    if v != None and v != "":
                        if k == "algorithmName":
                            v = str(v).lower()
                        simulate_options += [om_sim_options[i] + "=" + str(v)]
            return ",".join(simulate_options)

        def precheck_for_model():
            self.sim_opts = precheck_for_set_sim_options()

        def readStatistics():
            '''
            Read statistics from the LOG_STATS.txt file
            '''
            work_dir = os.getcwd()
            result_exe = os.path.join(work_dir, self.name + (".exe" if os.name == "nt" else "")) + " -lv LOG_STATS" + " -r=\"" + os.path.abspath(self.integrationSettings.resultFileName) + "\""
            if self.sim_opts <> "":
              result_exe += " -override=" + self.sim_opts
            result_exe += " -port=%d" % self.server_port

            with open('LOG_STATS.txt', 'w') as output_f:
                p = subprocess.Popen(result_exe,
                    stdout=output_f, shell=True)

            import time
            attempts = 0
            while True:
                if not os.path.isfile('LOG_STATS.txt'):
                    time.sleep(0.15)
                    attempts += 1
                    if attempts == 10:
                        return
                else:
                    statistics = open('LOG_STATS.txt', 'r')
                    break

            nTimeEvents = 0
            nStateEvents = 0
            currentGridPoints = 0
            currentTime = self.integrationSettings.startTime

            if statistics != None:
                fact = [line.strip() for line in statistics]
                for i in fact:
                    if "State Events" in i:
                        nStateEvents = int(i.split(':', 1)[1])
                    if "Sample Events" in i:
                        nTimeEvents = int(i.split(':', 1)[1])
                    if "simulation time" in i:
                        currentTime = float(i.split(':', 1)[1])
                statistics.close()

            currentTime = self.integrationSettings.stopTime
            # Wait for the process to finish; otherwise we cannot read the result-file
            p.wait()

            self.integrationStatistics.nTimeEvents = nTimeEvents
            self.integrationStatistics.nStateEvents = nStateEvents
            self.integrationStatistics.nGridPoints = currentGridPoints
            self.integrationStatistics.reachedTime = currentTime

        precheck_for_model()
        readStatistics()
        if not os.path.isfile(self.integrationSettings.resultFileName):
          raise FileDoesNotExist(self.integrationSettings.resultFileName)

    def setVariableTree(self):
        if self.resFile == '""':
            return
        for v in self._initialResult:
            value = None
            if v['variability'] == 'fixed' or v['valueEdit']:
              value = v['value']
            else:
              value = None

            variableAttribute = ''
            if v['description'] != '' :
                variableAttribute += 'Description:' + chr(9) + v['description'] + '\n'
            variableAttribute += 'Causality:' + chr(9) + v['causality'] + '\n'
            variableAttribute += 'Variability:' + chr(9) + v['variability'] + '\n'
            variableAttribute += 'Type:' + chr(9) + v['type']

            self.variableTree.variable[v['name'].replace('[', '.[')] = Plugins.Simulator.SimulatorBase.TreeVariable(self.structureVariableName(v['name'].replace('[', '.[')), value, v['valueEdit'], v['unit'], v['variability'], variableAttribute)

    def getAvailableIntegrationAlgorithms(self):
        return self._availableIntegrationAlgorithms

    def getIntegrationAlgorithmHasFixedStepSize(self, algorithmName):
        return self._IntegrationAlgorithmHasFixedStepSize[self._availableIntegrationAlgorithms.index(algorithmName)]

    def getIntegrationAlgorithmCanProvideStepSizeResults(self, algorithmName):
        return self._IntegrationAlgorithmCanProvideStepSizeResults[self._availableIntegrationAlgorithms.index(algorithmName)]


# Adapted from DymolaMat/DymolaMat.py for OpenModelica #

import scipy.io, string

# Exception classes
class FileDoesNotExist (Exception): pass
class WrongResultFile (Exception): pass
class BuildModelFail (Exception): pass
class OMInitXMLParseException (Exception): pass

def loadResultFileInit(fileName):
    """ Load Dymola initial data in an object.

    """
    # Correct file path if needed
    if os.name == "nt":
      fileName = fileName.replace("/", "\\")

    # If no fileName given, inquire it interactively
    if fileName == None:
        return
        # fileName = selectResultFile()

    # Check if fileName exists
    if not os.path.isfile(fileName):
        raise FileDoesNotExist("File '" + fileName + "' does not exist")

    # Determine complete file name
    fullFileName = os.path.abspath(fileName)

    from xml.parsers import expat

    p = expat.ParserCreate()
    def start(name,attr):
      if name == "ScalarVariable":
        start.cname = attr['name']
        start.cdesc = attr.get('description') or ''
        start.cunit = ''
        start.cvalue = ''
        start.cvalueEdit = attr.get('isValueChangeable') == 'true'
        start.ctype = ''
        start.cvar = attr['variability']
        start.ccaus = attr['causality']
      elif name in ["Real","Integer","String","Boolean"]:
        start.cvalue = attr.get('start') or ''
        start.cunit = attr.get('unit') or ''
        start.ctype = name
    def end(name):
      if name == "ScalarVariable":
        end.result += [{'name':start.cname,'value':start.cvalue,'valueEdit':start.cvalueEdit,'unit':start.cunit,'variability':start.cvar,'description':start.cdesc,'causality':start.ccaus,'type':start.ctype}]
    end.result = []
    p.StartElementHandler = start
    p.EndElementHandler = end
    f = open(fullFileName,"r")
    try:
      p.ParseFile(f)
    except:
      raise OMInitXMLParseException("Failed to parse " + fullFileName)
    return end.result

def prepareSimulationList(fileName, names, config):
  pass

class ThreadedTCPRequestHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        global simulationProgressData
        while 1:
          line = self.rfile.readline().strip()
          if line:
            simulationProgressData = float(line.split(" ")[0])/100.0
          else:
            return

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass
