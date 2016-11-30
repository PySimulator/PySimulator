#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (C) 2011-2015 German Aerospace Center DLR
(Deutsches Zentrum fuer Luft- und Raumfahrt e.V.),
Institute of System Dynamics and Control
Copyright (C) 2014-2016 ESI ITI GmbH
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
***************************
This Simulator plugin can load Modelica models (assumed SimulationX is installed),
simulate them by SimulationX and save the results.
***************************
'''

import csv
import locale
import os
import re
import string
import time
import types

import pythoncom
import win32com.client

from ...SimulationResult.SimulationXCsv import SimulationXCsv
from .. import SimulatorBase
import _winreg as winreg
from SimXEnums import *


iconImage = 'simulatorSimulationX.ico'
modelExtension = ['mo', 'ism', 'isx']

def closeSimulatorPlugin():
	pass

def prepareSimulationList(fileName, name, config):
	pass

def getNewModel(modelName=None, modelFileName=None, config=None):
	return Model(modelName, modelFileName, config)

def _isNumeric(s):
	'''  Check if a string value can be successfully converted to a double value
	'''
	if not s:
		# Empty string
		return True
	else:
		try:
			float(s)
			return True
		except ValueError:
			return False
		except TypeError:
			return False

class Model(SimulatorBase.Model):

	def __init__(self, modelName, modelFileName, config):
		SimulatorBase.Model.__init__(self, modelName, modelFileName, config)
		self.modelType = 'SimulationX'

		sim = None
		self._doc = None

		try:
			if not config['Plugins']['SimulationX'].has_key('version'):
				config['Plugins']['SimulationX']['version'] = 'Iti.Simx37'
				config.write()
			dispatch = config['Plugins']['SimulationX']['version']
			if dispatch == 'Iti.Simx36':
				sub_key = r'Software\ITI GmbH\SimulationX 3.6\Modelica'
			elif dispatch == 'Iti.Simx37':
				sub_key = r'Software\ITI GmbH\SimulationX 3.7\Modelica'
			elif dispatch == 'Iti.Simx38':
				sub_key = r'Software\ESI Group\SimulationX 3.8\Modelica'
			else:
				sub_key = r'Software\ITI GmbH\SimulationX 3.5\Modelica'
			# Make sure Modelica models can be simulated
			try:
				key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key, 0, winreg.KEY_ALL_ACCESS)
			except WindowsError:
				key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, sub_key, 0, winreg.KEY_ALL_ACCESS)
			winreg.SetValueEx(key, 'AutoCreateSimModel', 0, winreg.REG_DWORD, 1)
			winreg.CloseKey(key)

			pythoncom.CoInitialize()

			# A dummy object to get result properties:
			self.integrationResults = SimulationXCsv.Results('')
			self.integrationSettings.resultFileExtension = 'csvx'

			if dispatch == 'Iti.Simx38':
				self._availableIntegrationAlgorithms = ['BDF (Byte code)', 'BDF (C code)', 'MEBDF (Byte code)', 'MEBDF (C code)', 'CVODE (C code)', 'Fixed Step (C code)']
				self._solverByName = dict([('BDF (Byte code)', 'MultiStepMethod2'), ('BDF (C code)', 'BDFCompiled'), ('MEBDF (Byte code)', 'MEBDFDAE'), ('MEBDF (C code)', 'MEBDFCompiled'), ('CVODE (C code)', 'CVODE'), ('Fixed Step (C code)', 'FixStep')])
				self._IntegrationAlgorithmHasFixedStepSize = [False, False, False, False, False, True]
				self._IntegrationAlgorithmCanProvideStepSizeResults = [False, False, False, False, False, True]
			else:
				self._availableIntegrationAlgorithms = ['BDF (Byte code)', 'MEBDF (Byte code)', 'CVODE (C code)', 'Fixed Step (C code)']
				self._solverByName = dict([('BDF (Byte code)', 'MultiStepMethod2'), ('MEBDF (Byte code)', 'MEBDFDAE'), ('CVODE (C code)', 'CVODE'), ('Fixed Step (C code)', 'FixStep')])
				self._IntegrationAlgorithmHasFixedStepSize = [False, False, False, True]
				self._IntegrationAlgorithmCanProvideStepSizeResults = [False, False, False, True]

			self.integrationSettings.algorithmName = self._availableIntegrationAlgorithms[0]
			self.simulationStopRequest = False

			# Open SimulationX
			try:
				sim = win32com.client.GetActiveObject(dispatch)
			except:
				sim = win32com.client.Dispatch(dispatch)

			# Show SimulationX window
			sim.Visible = True

			# Wait till SimulationX is initialized
			if sim.InitState == simUninitialized:
				while sim.InitState != simInitBase:
					time.sleep(0.1)

			# SimulationX in non-interactive mode
			sim.Interactive = False

			# Load libraries
			if sim.InitState == simInitBase:
				sim.InitSimEnvironment()

			self.modelType += ' ' + sim.Version

			if len(modelFileName) == 1:
				strMsg = 'PySimulator: Load model'

				split = unicode.rsplit(modelFileName[0], '.', 1)
				if len(split) > 1:
					suffix = split[1]
				else:
					suffix = ''

				if suffix in ['ism', 'isx']:
					# Try to load as file
					try:
						# Write tracing marker message to output window in SimulationX
						sim.Trace(SimTraceMsgLocationFile, SimTraceMsgTypeInfo, strMsg, '')
						self._doc = sim.Documents.Open(modelFileName[0])
					except win32com.client.pywintypes.com_error:
						self._doc = None
						print 'SimulationX: COM Error.'

				elif suffix == 'mo':
					# Try to load as library
					try:
						try:
							libraryFileName = modelFileName[0].replace('/', '\\')
							sim.LoadLibrary(libraryFileName)
						except:
							pass
						# Write tracing marker message to output window in SimulationX
						sim.Trace(SimTraceMsgLocationFile, SimTraceMsgTypeInfo, strMsg, '')
						self._doc = sim.Documents.Open(modelName)
					except win32com.client.pywintypes.com_error:
						self._doc = None
						print 'SimulationX: COM Error.'

				if suffix in modelExtension:
					# Read complete tracing to string
					strTracing = sim.GetTraceMessages(SimTraceMsgLocationFile)
					# Find last occurrence of tracing marker message
					pos = strTracing.rfind(strMsg)
					if pos >= 0:
						strTracing = strTracing[pos + len(strMsg):].strip()
						if len(strTracing):
							print strTracing
							self._doc.Close(False)
							self._doc = None

				if not type(self._doc) is types.NoneType:
					self._marshalled_doc = pythoncom.CreateStreamOnHGlobal()
					pythoncom.CoMarshalInterface(self._marshalled_doc, pythoncom.IID_IDispatch, self._doc._oleobj_, pythoncom.MSHCTX_INPROC)
					self._marshalled_doc.Seek(0, pythoncom.STREAM_SEEK_SET)
				else:
					self._marshalled_doc = None
					print 'SimulationX: Load error.'

		except:
			print 'SimulationX: Error.'

		finally:
			try:
				if not type(sim) is types.NoneType:
					# SimulationX in interactive mode
					sim.Interactive = True
			except:
				pass

	def __exit__(self, _type, _value, _traceback):
		pythoncom.CoUninitialize()

	def close(self):
		''' Close a Modelica/SimulationX model
		'''
		sim = None
		try:
			doc = win32com.client.Dispatch(pythoncom.CoUnmarshalInterface(self._marshalled_doc, pythoncom.IID_IDispatch))
			self._marshalled_doc.Seek(0, pythoncom.STREAM_SEEK_SET)
			if not type(doc) is types.NoneType:
				sim = doc.Application
				sim.Interactive = False
				doc.Close(False)
				doc = None
				pythoncom.CoReleaseMarshalData(self._marshalled_doc)
				self._marshalled_doc = None
		except win32com.client.pywintypes.com_error:
			print 'SimulationX: COM error.'
		except:
			print 'SimulationX: Error.'
		finally:
			SimulatorBase.Model.close(self)
			if not type(sim) is types.NoneType:
				sim.Interactive = True
				sim = None

		if hasattr(self, 'variableTree'):
			del self.variableTree
		if hasattr(self, '_availableIntegrationAlgorithms'):
			del self._availableIntegrationAlgorithms
		if hasattr(self, '_solverByName'):
			del self._solverByName
		if hasattr(self, '_IntegrationAlgorithmHasFixedStepSize'):
			del self._IntegrationAlgorithmHasFixedStepSize
		if hasattr(self, '_IntegrationAlgorithmCanProvideStepSizeResults'):
			del self._IntegrationAlgorithmCanProvideStepSizeResults

	def setVariableTree(self):
		''' Generate variable tree
		'''
		sim = None
		try:
			if not type(self._doc) is types.NoneType:
				sim = self._doc.Application
				sim.Interactive = False
				self._fillTree(self._doc, self._doc)
		except win32com.client.pywintypes.com_error:
			print 'SimulationX: COM error.'
		finally:
			if not type(sim) is types.NoneType:
				sim.Interactive = True

	def _fillTree(self, pObject, doc):
		''' Scan a SimulationX entity object for all child parameters and results
		'''
		for pBaseEntity in pObject.BaseEntities:
			self._fillTree(pBaseEntity, doc)

		for pChild in pObject.Children:
			if pChild.Kind == simType:
				continue
			if pChild.GetProperty(simIsBaseClass) or pChild.GetProperty(simIsHidden) or pChild.GetProperty(simIsProtected) or pChild.GetProperty(simIsForCompat):
				continue
			childIsASimVariable = pChild.IsA(simVariable)
			if ((pChild.IsA(simParameter) or pChild.IsA(simGeneralParameter)) and not childIsASimVariable) or (pChild.GetProperty(simIsInput) and childIsASimVariable):
				# Parameter
				self._fillTreeParam(pObject, doc, pChild)
			elif childIsASimVariable:
				# Result
				self._fillTreeResult(pObject, doc, pChild)
			if not pChild.GetProperty(simIsInner) and pChild.GetProperty(simIsOuter):
				continue
			childEntityClass = pChild.Class
			if childEntityClass == simSimObject or childEntityClass == simSimBlock or childEntityClass == simConservConnection or childEntityClass == simFluidConnection or childEntityClass == simModelicaPin:
				self._fillTree(pChild, doc)

	def _fillTreeParam(self, pObject, doc, pChild):
		''' Scan a SimulationX parameter object
		'''
		docIdentDot = doc.Ident + '.'
		dim = pChild.Execute('GetDimension', [])[0]
		if dim == '':
			# Scalar dimension
			childTypeIdent = pChild.Type.Ident
			if not childTypeIdent == 'BuiltIn.BaseModel.ProtKind' and not childTypeIdent == 'StateSelect':
				# childRelIdent = pChild.GetRelIdent(doc)
				childRelIdent = pChild.Ident
				if childRelIdent.startswith(docIdentDot):
					childRelIdent = childRelIdent[len(docIdentDot):]
				if (not pChild.Parent == doc and not pObject.Name.find('_base') == 0) or (not childRelIdent == 'iSim' and not childRelIdent == 'tStart' and not childRelIdent == 'tStop'):
					childValue = pChild.Value
					childValueEdit = True
					childUnit = pChild.Unit
					if childUnit == '-':
						childUnit = None
					childVariability = 'fixed'
					childVariableAttr = ''
					childComment = pChild.comment
					if childComment != '':
						childVariableAttr += 'Description:' + chr(9) + childComment + '\n'
					childVariableAttr += 'Causality:' + chr(9) + 'parameter' + '\n'
					childVariableAttr += 'Variability:' + chr(9) + childVariability  # + '\n'
					if pChild.IsA(simEnumeration):
						childVariableAttr += '\nEnumeration:' + chr(9)
						for a in pChild.Alternatives:
							childVariableAttr += str(a.Value) + '=' + a.Name + ', '
						childVariableAttr = childVariableAttr.rstrip(', ')
					self.variableTree.variable[childRelIdent] = SimulatorBase.TreeVariable(self.structureVariableName(childRelIdent), childValue, childValueEdit, childUnit, childVariability, childVariableAttr)
		elif _isNumeric(dim):
			# Fixed vector dimension
			childTypeIdent = pChild.Type.Ident
			if not childTypeIdent == 'BuiltIn.BaseModel.ProtKind' and not childTypeIdent == 'StateSelect':
				# childRelIdent = pChild.GetRelIdent(doc)
				childRelIdent = pChild.Ident
				if childRelIdent.startswith(docIdentDot):
					childRelIdent = childRelIdent[len(docIdentDot):]
				if (not pChild.Parent == doc and not pObject.Name.find('_base') == 0) or (not childRelIdent == 'iSim' and not childRelIdent == 'tStart' and not childRelIdent == 'tStop'):
					dim = int(dim)
					childValue = pChild.Value
					childValue = re.sub('[\{\}\[\] ]', '', childValue)
					childValue = childValue.replace(';', ',')
					childValueList = childValue.split(',')
					if len(childValueList) == dim:
						childValueEdit = True
						childUnit = pChild.Unit
						if childUnit == '-':
							childUnit = None
						childVariability = 'fixed'
						childVariableAttr = ''
						childComment = pChild.Comment
						if childComment != '':
							childVariableAttr += 'Description:' + chr(9) + childComment + '\n'
						childVariableAttr += 'Causality:' + chr(9) + 'parameter' + '\n'
						childVariableAttr += 'Variability:' + chr(9) + childVariability  # + '\n'
						for i in range(1, dim + 1):
							if _isNumeric(childValueList[i - 1]):
								self.variableTree.variable[childRelIdent + '[' + str(i) + ']'] = SimulatorBase.TreeVariable(self.structureVariableName(childRelIdent + '[' + str(i) + ']'), childValueList[i - 1], childValueEdit, childUnit, childVariability, childVariableAttr)

	def _fillTreeResult(self, pObject, doc, pChild):
		''' Scan a SimulationX result object
		'''
		docIdentDot = doc.Ident + '.'
		dim = pChild.Execute('GetDimension', [])[0]
		if dim == '':
			# Scalar dimension
			# childRelIdent = pChild.GetRelIdent(doc)
			childRelIdent = pChild.Ident
			if childRelIdent.startswith(docIdentDot):
				childRelIdent = childRelIdent[len(docIdentDot):]
			if (not pChild.Parent == doc and not pObject.Name.find('_base') == 0) or (not childRelIdent == 't' and not childRelIdent == 'dt' and not childRelIdent == 'solverInfo' and not childRelIdent == 'lambdaHomotopy' and not childRelIdent == 'lambdaSteadyState'):
				childValue = None
				childValueEdit = False
				childUnit = pChild.Unit
				if childUnit == '-':
					childUnit = None
				if (pChild.GetProperty(simIsDiscrete)):
					childVariability = 'discrete'
				else:
					childVariability = 'continuous'
				childVariableAttr = ''
				childComment = pChild.Comment
				if childComment != '' :
					childVariableAttr += 'Description:' + chr(9) + childComment + '\n'
				childVariableAttr += 'Causality:' + chr(9) + 'state' + '\n'
				childVariableAttr += 'Variability:' + chr(9) + childVariability  # + '\n'
				self.variableTree.variable[childRelIdent] = SimulatorBase.TreeVariable(self.structureVariableName(childRelIdent), childValue, childValueEdit, childUnit, childVariability, childVariableAttr)
		elif _isNumeric(dim):
			# Fixed vector dimension
			# childRelIdent = pChild.GetRelIdent(doc)
			childRelIdent = pChild.Ident
			if childRelIdent.startswith(docIdentDot):
				childRelIdent = childRelIdent[len(docIdentDot):]
			if (not pChild.Parent == doc and not pObject.Name.find('_base') == 0) or (not childRelIdent == 't' and not childRelIdent == 'dt' and not childRelIdent == 'solverInfo' and not childRelIdent == 'lambdaHomotopy'):
				dim = int(dim)
				childValue = None
				childValueEdit = False
				childUnit = pChild.Unit
				if childUnit == '-':
					childUnit = None
				if (pChild.GetProperty(simIsDiscrete)):
					childVariability = 'discrete'
				else:
					childVariability = 'continuous'
				childVariableAttr = ''
				childComment = pChild.Comment
				if childComment != '':
					childVariableAttr += 'Description:' + chr(9) + childComment + '\n'
				childVariableAttr += 'Causality:' + chr(9) + 'state' + '\n'
				childVariableAttr += 'Variability:' + chr(9) + childVariability  # + '\n'
				for i in range(1, dim + 1):
					self.variableTree.variable[childRelIdent + '[' + str(i) + ']'] = SimulatorBase.TreeVariable(self.structureVariableName(childRelIdent + '[' + str(i) + ']'), childValue, childValueEdit, childUnit, childVariability, childVariableAttr)

	def getReachedSimulationTime(self):
		''' Read the current simulation time during a simulation
		'''
		sim = None
		rTime = None
		try:
			if not type(self._doc) is types.NoneType:
				sim = self._doc.Application
				sim.Interactive = False
				if self._doc.SolutionState > simReady:
					rTime = self._doc.Lookup('t').LastValue
		except:
			rTime = None
		finally:
			if not type(sim) is types.NoneType:
				sim.Interactive = True

		return rTime

	def simulate(self):
		''' Run a simulation of a Modelica/SimulationX model
		'''
		sim = None
		try:
			doc = win32com.client.Dispatch(pythoncom.CoUnmarshalInterface(self._marshalled_doc, pythoncom.IID_IDispatch))
			self._marshalled_doc.Seek(0, pythoncom.STREAM_SEEK_SET)
			if not type(doc) is types.NoneType:
				sim = doc.Application
				sim.Interactive = False
				self._simulate_sync(doc)
		except win32com.client.pywintypes.com_error:
			print 'SimulationX: COM error.'
			raise(SimulatorBase.Stopping)
		except:
			raise(SimulatorBase.Stopping)
		finally:
			if not type(sim) is types.NoneType:
				sim.Interactive = True

	def _simulate_sync(self, doc):
		simulation = self.integrationSettings

		# Integration settings
		doc.Lookup('tStart').Value = simulation.startTime
		doc.Lookup('tStop').Value = simulation.stopTime
		doc.Lookup('relTol').Value = simulation.errorToleranceRel
		if simulation.errorToleranceAbs is None:
			if not self.config['Plugins']['SimulationX'].has_key('absTol'):
				absTol = simulation.errorToleranceRel
			else:
				absTol = self.config['Plugins']['SimulationX']['absTol']
			doc.Lookup('absTol').Value = absTol
		else:
			doc.Lookup('absTol').Value = simulation.errorToleranceAbs

		ialg = self._availableIntegrationAlgorithms.index(simulation.algorithmName)
		if self._IntegrationAlgorithmHasFixedStepSize[ialg]:
			doc.Lookup('dtMin').Value = simulation.fixedStepSize
		else:
			if not self.config['Plugins']['SimulationX'].has_key('dtMin'):
				dtMin = '1e-010'
			else:
				dtMin = self.config['Plugins']['SimulationX']['dtMin']
			doc.Lookup('dtMin').Value = dtMin
		if simulation.gridPointsMode == 'NumberOf':
			if simulation.gridPoints > 1:
				dtProtMin = (simulation.stopTime - simulation.startTime) / (simulation.gridPoints - 1)
				protKind = 0  # = 'BaseModel.ProtKind.EquidistantTimeSteps'
			else:
				dtProtMin = (simulation.stopTime - simulation.startTime) / 500
				protKind = 0  # = 'BaseModel.ProtKind.EquidistantTimeSteps'
		elif simulation.gridPointsMode == 'Width':
			dtProtMin = simulation.gridWidth
			protKind = 0  # = 'BaseModel.ProtKind.EquidistantTimeSteps'
		elif simulation.gridPointsMode == 'Integrator':
			dtProtMin = 'dtDetect'
			protKind = 3  # = 'BaseModel.ProtKind.MinTimeStepsPrePostEvents'
		doc.Lookup('dtProtMin').Value = dtProtMin
		doc.Lookup('protKind').Value = protKind
		try:
			doc.SolverByName = self._solverByName[simulation.algorithmName]
		except KeyError:
			pass

		for name, newValue in self.changedStartValue.iteritems():
			i = name.find('[')
			if i >= 0 and name.endswith(']'):
				value = doc.Lookup(name[0:i]).Value
				n = name[i:]
				n = re.sub('[\[\]]', '', n)
				if _isNumeric(n):
					n = int(n)
					value = re.sub('[\{\}\[\] ]', '', value)
					value = value.replace(';', ',')
					valueList = value.split(',')
					valueList[n - 1] = newValue
					doc.Lookup(name[0:i]).Value = '{' + ','.join(valueList) + '}'
			else:
				doc.Lookup(name).Value = newValue

		# Build variable tree if empty, e.g. if simulate is called by the Testing plugin
		if not bool(self.variableTree.variable):
			self._fillTree(doc, doc)
			treeWasEmpty = True
		else:
			treeWasEmpty = False

		# Log all parameters and variables
		paramName = list()
		paramUnit = list()
		paramValue = list()
		for name, item in self.variableTree.variable.iteritems():
			pChild = doc.Lookup(name)
			childIsASimVariable = pChild.IsA(simVariable)
			if childIsASimVariable and not pChild.GetProperty(simIsInput):
				# Result
				try:
					pChild.Protocol = True
				except:
					try:
						pChild.Parent.Results(pChild.Name).Protocol = True
					except:
						pass
			elif ((pChild.IsA(simParameter) or pChild.IsA(simGeneralParameter)) and not childIsASimVariable) or (pChild.GetProperty(simIsInput) and childIsASimVariable):
				# Parameter
				childRelIdent = re.sub(r'\[.*?\]', '', name)
				childUnit = pChild.Unit.encode(locale.getpreferredencoding())
				childValue = pChild.Value
				dim = pChild.Execute('GetDimension', [])[0]
				if dim == '':
					# Scalar dimension
					if not childRelIdent in paramName:
						paramName.append(childRelIdent)
						paramUnit.append(childUnit)
						if childValue == '':
							childValue = 0
						if not _isNumeric(childValue):
							childValue = pChild.Eval()
							if type(childValue) == types.BooleanType:
								if childValue:
									childValue = '1'
								else:
									childValue = '0'
							else:
								childValue = '{0}'.format(childValue)
						paramValue.append(childValue)
				elif _isNumeric(dim):
					# Fixed vector dimension
					dim = int(dim)
					childValue = re.sub('[\{\}\[\] ]', '', childValue)
					childValue = childValue.replace(';', ',')
					childValueList = childValue.split(',')
					if len(childValueList) == dim:
						for i in range(1, dim + 1):
							if _isNumeric(childValueList[i - 1]):
								childCompName = childRelIdent + '[' + str(i) + ']'
								if not childCompName in paramName:
									paramName.append(childCompName)
									paramUnit.append(childUnit)
									childValue = childValueList[i - 1]
									if childValue == '':
										childValue = 0
									paramValue.append(childValue)

		# Start simulation
		doc.Reset()
		time.sleep(0.01)
		doc.Start()

		# Wait till simulation is finished
		while doc.SolutionState < simStopped:
			if self.simulationStopRequest:
				doc.Stop()
				self.simulationStopRequest = False
				raise(SimulatorBase.Stopping)
			time.sleep(0.1)

		# Integration is finished
		if doc.SolutionState == simStopped:
			# Save results in CSV file
			resultFileName = os.path.abspath(simulation.resultFileName).replace('\\', '/')
			ver = self.config['Plugins']['SimulationX']['version']
			canExportDisplayUnit = True
			if ver == 'Iti.Simx36':
				sub_key = r'Software\ITI GmbH\SimulationX 3.6\DataFilter'
			elif ver == 'Iti.Simx37':
				sub_key = r'Software\ITI GmbH\SimulationX 3.7\DataFilter'
			elif ver == 'Iti.Simx38':
				sub_key = r'Software\ESI Group\SimulationX 3.8\DataFilter'
			else:
				sub_key = r'Software\ITI GmbH\SimulationX 3.5\DataFilter'
				canExportDisplayUnit = False

			try:
				key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key, 0, winreg.KEY_ALL_ACCESS)
			except WindowsError:
				key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, sub_key, 0, winreg.KEY_ALL_ACCESS)
			try:
				frt = winreg.QueryValueEx(key, 'Format')
			except WindowsError:
				frt = (u'%.15lg', winreg.REG_SZ)
			try:
				dec = winreg.QueryValueEx(key, 'Dec')
			except WindowsError:
				dec = (u'.', winreg.REG_SZ)
			try:
				sep = winreg.QueryValueEx(key, 'Separator')
			except WindowsError:
				sep = (u'\t', winreg.REG_SZ)
			try:
				adT = winreg.QueryValueEx(key, 'AddTableName')
			except WindowsError:
				adT = (0, winreg.REG_DWORD)
			try:
				adN = winreg.QueryValueEx(key, 'AddColumnNames')
			except WindowsError:
				adN = (1, winreg.REG_DWORD)
			try:
				adU = winreg.QueryValueEx(key, 'AddColumnUnits')
			except WindowsError:
				adU = (0, winreg.REG_DWORD)
			winreg.SetValueEx(key, 'Format', 0, winreg.REG_SZ, '%.17lg')
			winreg.SetValueEx(key, 'Dec', 0, winreg.REG_SZ, '.')
			winreg.SetValueEx(key, 'Separator', 0, winreg.REG_SZ, ';')
			winreg.SetValueEx(key, 'AddTableName', 0, winreg.REG_DWORD, 0)
			winreg.SetValueEx(key, 'AddColumnNames', 0, winreg.REG_DWORD, 2)
			winreg.SetValueEx(key, 'AddColumnUnits', 0, winreg.REG_DWORD, 1)
			winreg.FlushKey(key)
			if canExportDisplayUnit:
				doc.StoreAllResultsAsText(resultFileName, False)  # Export in displayUnit
			else:
				doc.StoreAllResultsAsText(resultFileName)  # Export in SI-Unit
			winreg.SetValueEx(key, 'Format', 0, winreg.REG_SZ, frt[0])
			winreg.SetValueEx(key, 'Dec', 0, winreg.REG_SZ, dec[0])
			winreg.SetValueEx(key, 'Separator', 0, winreg.REG_SZ, sep[0])
			winreg.SetValueEx(key, 'AddTableName', 0, winreg.REG_DWORD, adT[0])
			winreg.SetValueEx(key, 'AddColumnNames', 0, winreg.REG_DWORD, adN[0])
			winreg.SetValueEx(key, 'AddColumnUnits', 0, winreg.REG_DWORD, adU[0])
			winreg.CloseKey(key)

			# Save parameters in CSV file
			if len(paramName) > 0:
				with open(resultFileName + 'p', 'wb') as csvfile:
					csvwriter = csv.writer(csvfile, delimiter=';')
					csvwriter.writerow(paramName)
					csvwriter.writerow(paramUnit)
					csvwriter.writerow(paramValue)

			self.integrationStatistics.reachedTime = simulation.stopTime
			self.integrationStatistics.nGridPoints = len(doc.Lookup('t').ProtValues)
		elif doc.SolutionState == simFailed:
			print('SimulationX: Simulation error.')

		if treeWasEmpty:
			self.variableTree.variable.clear()

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
