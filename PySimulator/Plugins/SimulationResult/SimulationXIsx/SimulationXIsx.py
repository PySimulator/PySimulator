'''
Copyright (C) 2014 ITI GmbH
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
import types
from xml.dom import minidom
import zipfile
import string

import numpy

from Plugins.SimulationResult import IntegrationResults
import PyResultX as isx
from SimXUnitSI import unitSI


fileExtension = 'isx'
description = 'SimulationX Project File'

class Results(IntegrationResults.Results):
	""" Result Object to hold a SimulationX project file, see also
		class IntegrationResults.Results
	"""
	def __init__(self, fileName):
		IntegrationResults.Results.__init__(self)

		self.fileName = fileName

		self._info = []
		self._name = []
		self._unit = []

		self._fileInfo = dict()

		if fileName is None:
			return
		if fileName is '':
			return

		# Determine complete file name
		self._fullFileName = os.path.abspath(fileName)

		results = []
		with isx.readModel(self._fullFileName, 'doc', results) as model:
			if len(results) > 0:
				try:
					doc = isx.SimXObject(model, 'doc' , None, [], results, 0)
					doc_t = doc.LoadResult('doc.t')
				except:
					raise Exception("Result variable 't' not stored in file " + self._fullFileName)
				cols = 0
				for result in results:
					if result.ndims == 1:
						# Scalar dimension
						cols += 1
					elif result.ndims == 2:
						# Vector dimension
						cols += result.Dimension[1]
					elif result.ndims == 3:
						# Matrix dimension
						cols += result.Dimension[1]*result.Dimension[2]
				rows = len(doc_t)
				data = numpy.empty((rows, cols))  # pre-allocate array
				self._fileInfo['Rows'] = str(len(doc_t))
				cols = 0
				for result in results:
					try:
						res = doc.LoadResult(result.strIdent)
						if res.shape[0] == rows:
							ident = '.'.join(result.Ident[1:])
							quantity = string.rsplit(result.Quantity, '.', 1)[-1]
							if quantity in unitSI:
								unit = unitSI[quantity]
							else:
								unit = None
							if result.ndims == 1:
								# Scalar dimension
								data[:, cols] = res
								cols += 1
								self._name.append(ident)
								self._unit.append(unit)
								self._info.append(result.Quantity)
							elif result.ndims == 2:
								# Vector dimension
								data[:, range(cols, cols + result.Dimension[1])] = res
								cols += result.Dimension[1]
								for i in range(1, result.Dimension[1] + 1):
									self._name.append(ident + '[' + str(i) + ']')
									self._unit.append(unit)
									self._info.append(result.Quantity)
							elif result.ndims == 3:
								# Matrix dimension
								for i in range(1, result.Dimension[1] + 1):
									data[:, range(cols, cols + result.Dimension[1])] = res[:, i - 1, :]
									cols += result.Dimension[2]
									for j in range(1, result.Dimension[2] + 1):
										self._name.append(ident + '[' + str(i) + ',' + str(j) + ']')
										self._unit.append(unit)
										self._info.append(result.Quantity)
					except:
						pass
				self._fileInfo['Columns'] = str(cols)
				self.timeSeries.append(IntegrationResults.TimeSeries(doc_t, data, "linear"))
				self._filterUnit()
				self.isAvailable = True  # Shows, if there is a file available to be read
			else:
				raise Exception('No results stored in file ' + self._fullFileName)

		self.nTimeSeries = len(self.timeSeries)

	def _filterUnit(self):

		for i in xrange(len(self._unit)):
			x = self._unit[i]
			if x == '-':
				self._unit[i] = None

	def readData(self, variableName):
		nameIndex = self._name.index(variableName)
		if nameIndex < 0:
			return None, None, None
		y = self.timeSeries[0].data[:, nameIndex]
		t = self.timeSeries[0].independentVariable
		method = self.timeSeries[0].interpolationMethod

		return t, y, method


	def getVariables(self):
		# Generate the dict
		variables = dict()

		# Fill the values of the dict
		variability = 'continuous'
		value = None
		seriesIndex = 0
		sign = 1
		for col in xrange(len(self._name)):
			name = self._name[col]
			infos = collections.OrderedDict()
			infos['Variability'] = variability
			if not self._info[col] == '':
				infos['Quantity'] = self._info[col]
			unit = self._unit[col]

			if name in variables.keys():
				print "Same name twice (Variable): " + name
			else:
				variables[name] = IntegrationResults.ResultVariable(value, unit, variability, infos, seriesIndex, col, sign)

		return variables

	def getFileInfos(self):
		with zipfile.ZipFile(self._fullFileName, 'r') as model:
			with model.open('docProps/app.xml', 'rU') as app:
				dom = minidom.parseString(app.read())
				nodes = dom.getElementsByTagName('AppVersion')
				if len(nodes) > 0:
					if type(nodes[0].firstChild) is not types.NoneType:
						self._fileInfo['SimulationX'] = nodes[0].firstChild.nodeValue
				nodes = dom.getElementsByTagName('Company')
				if len(nodes) > 0:
					if type(nodes[0].firstChild) is not types.NoneType:
						self._fileInfo['Company'] = nodes[0].firstChild.nodeValue
			with model.open('docProps/core.xml', 'rU') as core:
				dom = minidom.parseString(core.read())
				nodes = dom.getElementsByTagName('dc:title')
				if len(nodes) > 0:
					if type(nodes[0].firstChild) is not types.NoneType:
						self._fileInfo['Title'] = nodes[0].firstChild.nodeValue
				nodes = dom.getElementsByTagName('dc:subject')
				if len(nodes) > 0:
					if type(nodes[0].firstChild) is not types.NoneType:
						self._fileInfo['Subject'] = nodes[0].firstChild.nodeValue
				nodes = dom.getElementsByTagName('dc:creator')
				if len(nodes) > 0:
					if type(nodes[0].firstChild) is not types.NoneType:
						self._fileInfo['Creator'] = nodes[0].firstChild.nodeValue
				nodes = dom.getElementsByTagName('dc:keywords')
				if len(nodes) > 0:
					if type(nodes[0].firstChild) is not types.NoneType:
						self._fileInfo['Keywords'] = nodes[0].firstChild.nodeValue
				nodes = dom.getElementsByTagName('dc:description')
				if len(nodes) > 0:
					if type(nodes[0].firstChild) is not types.NoneType:
						self._fileInfo['Description'] = nodes[0].firstChild.nodeValue
		return self._fileInfo

	def close(self):
		if hasattr(self, 'timeSeries'):
			del self.timeSeries
		if hasattr(self, '_fileInfo'):
			del self._fileInfo
		if hasattr(self, '_name'):
			del self._name
		if hasattr(self, '_unit'):
			del self._unit
		if hasattr(self, '_info'):
			del self._info
