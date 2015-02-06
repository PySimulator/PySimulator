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

import csv, numpy, collections, math

from Plugins.SimulationResult import IntegrationResults


fileExtension = 'csvx'
description = 'Comma Separated Values for SimulationX'

class Results(IntegrationResults.Results):
    ''' Class for hosting simulation results in csv format:
        First row: Names of variables
        Second row: Unit (- marks no unit)
        First column: Independent variable, e.g. t
        Example:

        t;Mechanical.Inertia.J;y;Mechnical.Inertia.w
        s;-;-;rad/s;
        0.0;20.0;3.6820238572822689e-4;0.0
        0.1;20.0;6.7829872398723383e-4;0.7293789273984797e-2
        0.2;20.0;4.0290389058209473e-3;0.7823794579232536e-1

    '''
    def __init__(self, fileName):
        IntegrationResults.Results.__init__(self)

        self.fileName = fileName  # File name of result file
        ''' Load file
        '''

        self._name = []
        self._unit = []

        self.fileInfo = dict()

        if self.fileName is not None:
            if self.fileName == '':
                return
        else:
            return


        # Load main data
        csvfile = open(self.fileName, 'rb')
        reader = csv.reader(csvfile, delimiter=';')
        self._name = reader.next()  # first row contains the variable names
        self._unit = reader.next()  # second row contains the units
        data = numpy.loadtxt(csvfile, delimiter=';')
        csvfile.close()
        self.fileInfo['Rows'] = str(data.shape[0])

        self._isParameter = len(self._name) * [False]
        if numpy.ndim(data) > 1:
            self.fileInfo['Columns'] = str(data.shape[1])
            self.timeSeries.append(IntegrationResults.TimeSeries(data[:, 0], data[:, 1:], "linear"))

            self._name = self._name[1:]  # delete 'Time'
            self._unit = self._unit[1:]  # delete unit of 'Time'
            self._isParameter = self._isParameter[1:]  # delete isParameter of 'Time'
        else:
            self.fileInfo['Columns'] = 1
            data = numpy.reshape(data, (len(data), 1))
            self.timeSeries.append(IntegrationResults.TimeSeries(data, data, "linear"))


        # Load parameters
        try:
            csvfile = open(self.fileName + 'p', 'rb')
            parameterFileExists = True
        except IOError:
            parameterFileExists = False


        if parameterFileExists:
            reader = csv.reader(csvfile, delimiter=';')
            name2 = reader.next()  # first row contains the variable names
            unit2 = reader.next()  # second row contains the units
            data = numpy.loadtxt(csvfile, delimiter=';')
            csvfile.close()

            if len(numpy.shape(data)) == 0:
                data = numpy.array([data])
            data = numpy.reshape(data, (1, len(data)))
            self.timeSeries.append(IntegrationResults.TimeSeries(None, data, "constant"))
            self._isParameter.extend(len(name2) * [True])
            self._name.extend(name2)
            self._unit.extend(unit2)


        self._info = len(self._name) * ['']
        self._filterName()
        self._filterUnit()

        self.nTimeSeries = len(self.timeSeries)


        # Hack to transform deg -> rad
        for i in xrange(len(self._unit)):
            if self._unit[i] is not None:
                if self._unit[i] == 'deg':
                    self._unit[i] = 'rad'
                    if self._isParameter[i]:
                        self.timeSeries[1].data[0, i - self.timeSeries[0].data.shape[1]] *= math.pi / 180.0
                    else:
                        self.timeSeries[0].data[:, i] *= math.pi / 180.0


        self.isAvailable = True  # Shows, if there is a file available to be read

    def _filterUnit(self):

        for i in xrange(len(self._unit)):
            x = self._unit[i]
            if x == '-':
                self._unit[i] = None

    def _filterName(self):

        for i in xrange(len(self._name)):
            x = self._name[i]
            k = x.find('=')
            if k > -1:  # Skip the parts behind "="
                self._info[i] = x[k:]
                x = x[:k]

            # if len(x)>5:  # Convert der(a.b.c.d) to a.b.c.der(d)
            #    if x[:4] == 'der(':
            #        k = x.rfind('.')
            #        if k > -1:
            #            x = x[4:k] + '.der(' + x[k+1:]
            self._name[i] = x


    def readData(self, variableName):
        nameIndex = self._name.index(variableName)
        if nameIndex < 0:
            return None, None, None
        if self._isParameter[nameIndex]:
            y = numpy.array([self.timeSeries[1].data[0, nameIndex - self.timeSeries[0].data.shape[1]]])
            i = 1
        else:
            y = self.timeSeries[0].data[:, nameIndex]
            i = 0

        t = self.timeSeries[i].independentVariable
        method = self.timeSeries[i].interpolationMethod

        return t, y, method


    def getVariables(self):
        # Generate the dict
        variables = dict()

        # Fill the values of the dict
        sign = 1
        for i in xrange(len(self._name)):
            name = self._name[i]

            if self._isParameter[i]:
                variability = 'fixed'
                value = self.timeSeries[1].data[0, i - self.timeSeries[0].data.shape[1]]
                seriesIndex = 1
                column = i - self.timeSeries[0].data.shape[1]
            else:
                variability = 'continuous'
                value = None
                seriesIndex = 0
                column = i
            infos = collections.OrderedDict()
            infos['Variability'] = variability
            if not self._info[i] == '':
                infos['Description'] = self._info[i]
            unit = self._unit[i]

            if name in variables.keys():
                print "Same name twice " + ('(Parameter): ' if self._isParameter[i] else '(Variable): ') + name
            else:
                variables[name] = IntegrationResults.ResultVariable(value, unit, variability, infos, seriesIndex, column, sign)

        return variables

    def getFileInfos(self):
        return self.fileInfo

    def close(self):
        if hasattr(self, 'timeSeries'):
            del self.timeSeries
        if hasattr(self, 'fileInfo'):
            del self.fileInfo
        if hasattr(self, '_name'):
            del self._name
        if hasattr(self, '_unit'):
            del self._unit
        if hasattr(self, '_isParameter'):
            del self._isParameter
        if hasattr(self, '_info'):
            del self._info
