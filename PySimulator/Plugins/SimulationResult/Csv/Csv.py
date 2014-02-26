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

import csv, numpy, collections
from Plugins.SimulationResult import IntegrationResults


fileExtension = 'csv'
description = 'Comma Separated Values for FMI Compliance Checker'


class Results(IntegrationResults.Results):
    ''' Class for hosting simulation results in csv format:
        First row: Names of variables
        First column: Independent variable, e.g. Time
        Example:

        Time;Mechanical.Inertia.J;y;Mechnical.Inertia.w
        0.0;20.0;3.6820238572822689e-4;0.0
        0.1;20.0;6.7829872398723383e-4;0.7293789273984797e-2
        0.2;20.0;4.0290389058209473e-3;0.7823794579232536e-1

    '''
    def __init__(self, fileName):
        IntegrationResults.Results.__init__(self)

        self.fileName = fileName  # File name of result file
        ''' Load file
        '''

        '''
        csvfile = open(self.fileName, 'rb')
        reader = csv.reader(csvfile, delimiter=';')
        self._name = reader.next() # first row contains the variable names
        self._data = numpy.array(reader.next(), dtype='float64')
        i=0
        for row in reader:
            self._data = numpy.row_stack((self._data, numpy.array(row, dtype='float64')))
            print i
            i=i+1

        csvfile.close()
        '''
        csvfile = open(self.fileName, 'rb')
        dialect = csv.Sniffer().sniff(csvfile.readline())
        csvfile.seek(0)
        reader = csv.reader(csvfile, dialect)
        self._name = reader.next()  # first row contains the variable names
        self._info = len(self._name) * ['']
        self._filterName()
        data = numpy.loadtxt(csvfile, delimiter=dialect.delimiter)

        t = data[:, 0]
        self.timeSeries.append(IntegrationResults.TimeSeries(t, data, "linear"))
        self.nTimeSeries = len(self.timeSeries)


        csvfile.close()

        self.isAvailable = True  # Shows, if there is a file available to be read


    def _filterName(self):

        for i in xrange(len(self._name)):
            x = self._name[i]
            k = x.find('=')
            if k > -1:  # Skip the parts behind "="
                self._info[i] = x[k:]
                x = x[:k]

            if len(x) > 5:  # Convert der(a.b.c.d) to a.b.c.der(d)
                if x[:4] == 'der(':
                    k = x.rfind('.')
                    if k > -1:
                        x = x[4:k] + '.der(' + x[k + 1:]
            self._name[i] = x


    def readData(self, variableName):
        nameIndex = self._name.index(variableName)
        if nameIndex < 0:
            return None, None, None
        y = self.timeSeries[0].data[:, nameIndex]
        t = self.timeSeries[0].independentVariable
        method = self.timeSeries[0].interpolationMethod
        return t, y, method

    def data(self, variableName):
        nameIndex = self._name.index(variableName)
        if nameIndex < 0:
            return None
        return self.timeSeries[0].data[:, nameIndex]


    def getVariables(self):
        # Generate the dict
        variables = dict()

        # Fill the values of the dict
        for i in xrange(len(self._name)):
            name = self._name[i]
            variability = 'continuous'
            value = None
            infos = collections.OrderedDict()
            infos['Variability'] = variability
            if not self._info[i] == '':
                infos['Description'] = self._info[i]
            unit = None
            seriesIndex = 0
            column = i
            sign = 1
            variables[name] = IntegrationResults.ResultVariable(value, unit, variability, infos, seriesIndex, column, sign)

        return variables

    def getFileInfos(self):
        # No relevant file infos stored in a csv result file
        return dict()





