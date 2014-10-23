#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (C) 2014 tbeu
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

import collections
import os

import numpy

from Plugins.SimulationResult import IntegrationResults
from recon.meld import MeldReader


fileExtension = 'mld'
description = 'Recon Meld Format'

class Results(IntegrationResults.Results):
	''' Class for hosting recon meld format:
	'''
	def __init__(self, fileName):
		IntegrationResults.Results.__init__(self)

		self.fileName = fileName

		self._info = []
		self._name = []
		self._unit = []

		self.fileInfo = dict()
		self.tid = dict()

		if fileName is None:
			return
		if fileName is '':
			return

		# Determine complete file name
		fullFileName = os.path.abspath(fileName)

		with open(fullFileName, "rb") as fp:
			meld = MeldReader(fp)
			tables = meld.tables()
			tid = 0
			for tabname in tables:
				table = meld.read_table(tabname)
				try:
					t = table.data('time')
				except:
					try:
						t = table.data('Time')
					except:
						t = None

				if t is not None:
					signals = table.signals()
					rows = len(t)
					cols = len(signals)
					data = numpy.empty((rows, cols))  # pre-allocate array
					col = 0
					for signal in signals:
						self._name.append(tabname + '.' + signal)
						self.tid[tabname + '.' + signal] = (tid, col)
						self._unit.append(None)
						data[:, col] = numpy.array(table.data(signal))
						col += 1
					self.timeSeries.append(IntegrationResults.TimeSeries(numpy.array(t), data, "linear"))
				tid += 1

		self._info = len(self._name)*['']
		self._filterName()
		self._filterUnit()

		self._isParameter = len(self._name) * [False]
		self.nTimeSeries = len(self.timeSeries)

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

			#if len(x)>5:  # Convert der(a.b.c.d) to a.b.c.der(d)
			#    if x[:4] == 'der(':
			#        k = x.rfind('.')
			#        if k > -1:
			#            x = x[4:k] + '.der(' + x[k+1:]
			self._name[i] = x


	def readData(self, variableName):
		nameIndex = self.tid[variableName][1]
		if nameIndex < 0:
			return None, None, None
		i = self.tid[variableName][0]
		y = self.timeSeries[i].data[:,nameIndex]
		t = self.timeSeries[i].independentVariable
		method = self.timeSeries[i].interpolationMethod

		return t, y, method


	def getVariables(self):
		# Generate the dict
		variables = dict()

		# Fill the values of the dict
		for i in xrange(len(self._name)):
			name = self._name[i]
			seriesIndex = self.tid[name][0]
			column = self.tid[name][1]
			variability = 'continuous'
			value = None
			infos = collections.OrderedDict()
			infos['Variability'] = variability
			if not self._info[i] == '':
				infos['Description'] = self._info[i]
			unit = self._unit[i]
			sign = 1

			if name in variables.keys():
				print "Same name twice (Variable): " + name
			else:
				variables[name] = IntegrationResults.ResultVariable(value, unit, variability, infos, seriesIndex, column, sign)

		return variables

	def getFileInfos(self):
		# No relevant file infos stored in a csv result file
		return dict()
