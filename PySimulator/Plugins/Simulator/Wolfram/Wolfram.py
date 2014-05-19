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

import Plugins.Simulator.SimulatorBase
import os
iconImage = 'simulatorWolfram.ico'
modelExtension = ['mo']  # e.g. ['mo']

def closeSimulationPlugin():
    try:
        print("Wolfram")
    except SystemExit:
        pass

class Model(Plugins.Simulator.SimulatorBase.Model):

    def __init__(self, modelName, modelFileName, config):
        Plugins.Simulator.SimulatorBase.Model.__init__(self, modelName, modelFileName, 'Wolfram', config)

        self.onlyResultFile = False
        self.integrationSettings.resultFileExtension = 'mat'

        self._availableIntegrationAlgorithms = ['DASSL', 'CVODES', 'Explicit Euler', 'Heuns method', 'Runge-Kutta (RK4)']
        self.integrationSettings.algorithmName = self._availableIntegrationAlgorithms[0]

        self._IntegrationAlgorithmHasFixedStepSize = [False, True, False, False, True, False]
        self._IntegrationAlgorithmCanProvideStepSizeResults = [False, True, False, False, True, False]

        self.compileModel()


    def compileModel(self):
        """
        This function is needed to load the data into the VariablesBrowser
        before simulating the model with parameters.
        """
        if len(self.fileName) == 1:
            if not os.path.isfile(self.fileName[0]):
                raise FileDoesNotExist("File '" + self.fileName[0] + "' does not exist")

    def getReachedSimulationTime(self):
        '''
        Read the current simulation time during a simulation
        from ?????
        '''
    def simulate(self):
        ''' Simulate a Modelica model by executing Wolfram's simulation executable.
        '''

        def compile_model(simulate_options):

            if self.fileName != None:
                print("okey")

        def precheck_for_set_sim_options():
            s = self.integrationSettings
            settings = s.__dict__

        def precheck_for_model():
            sim_opts = precheck_for_set_sim_options()
            if sim_opts != '':
                compile_model(sim_opts)
            else:
                compile_model('')

        def readStatistics():
            '''
            Read statistics from the ?? file
            '''

    def setVariableTree(self):
        if self.resFile == '""':
            return

    def getAvailableIntegrationAlgorithms(self):
        ''' Returns a list of strings with available integration algorithms
        '''
        return self._availableIntegrationAlgorithms

    def getIntegrationAlgorithmHasFixedStepSize(self, algorithmName):
        ''' Returns True or False dependent on the fact,
            if the integration algorithm given by the string algorithmName
            has a fixed step size or not (if not it has a variable step size).
        '''
        return self._IntegrationAlgorithmHasFixedStepSize[self._availableIntegrationAlgorithms.index(algorithmName)]

    def getIntegrationAlgorithmCanProvideStepSizeResults(self, algorithmName):
        ''' Returns True or False dependent on the fact,
            if the integration algorithm given by the string algorithmName
            can provide result points at every integration step.
        '''
        return self._IntegrationAlgorithmCanProvideStepSizeResults[self._availableIntegrationAlgorithms.index(algorithmName)]

