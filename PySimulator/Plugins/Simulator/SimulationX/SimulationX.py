'''
Copyright (C) 2011-2014 German Aerospace Center DLR
(Deutsches Zentrum fuer Luft- und Raumfahrt e.V.),
Institute of System Dynamics and Control
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

'''
***************************
This Simulator plugin can load Modelica models (assumed SimulationX is installed),
simulate them by SimulationX and save the results.
***************************
'''

import csv
import pythoncom
import re
import os
import locale
import string
import time
import types
import _winreg as winreg
import win32com.client

import Plugins.SimulationResult.SimulationXCsv.SimulationXCsv as SimulationXCsv
import Plugins.Simulator.SimulatorBase

from simx import *

iconImage = 'simulatorSimulationX.ico'
modelExtension = ['mo', 'ism', 'isx']

def closeSimulatorPlugin():
	pass

def prepareSimulationList(fileName, name, config):
	pass

class Model(Plugins.Simulator.SimulatorBase.Model):

	def __init__(self, modelName, modelFileName, config):
		Plugins.Simulator.SimulatorBase.Model.__init__(self, modelName, modelFileName, 'SimulationX', config)

		sim = None
		self._doc = None

		try:
			if not config['Plugins']['SimulationX'].has_key('version'):
				config['Plugins']['SimulationX']['version'] = 'Iti.Simx36'
				config.write()
			dispatch = config['Plugins']['SimulationX']['version']
			if dispatch == 'Iti.Simx36':
				ver = '3.6'
			elif dispatch == 'Iti.Simx37':
				ver = '3.7'
			else:
				ver = '3.5'
			# Make sure Modelica models can be simulated
			key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\ITI GmbH\SimulationX ' + ver + r'\Modelica', 0, winreg.KEY_ALL_ACCESS)
			winreg.SetValueEx(key, 'AutoCreateSimModel', 0, winreg.REG_DWORD, 1)
			winreg.CloseKey(key)

			pythoncom.CoInitialize()

			# A dummy object to get result properties:
			self.integrationResults = SimulationXCsv.Results('')
			self.integrationSettings.resultFileExtension = 'csvx'

			self._availableIntegrationAlgorithms = ['BDF', 'MEBDF', 'CVODE', 'FixedStep']
			self._solverByName = dict([('BDF', 'MultiStepMethod2'), ('MEBDF', 'MEBDFDAE'), ('CVODE', 'CVODE'), ('FixedStep', 'FixStep')])

			self._IntegrationAlgorithmHasFixedStepSize = [False, False, False, True]
			self._IntegrationAlgorithmCanProvideStepSizeResults = [False, False, False, False]

			self.integrationSettings.algorithmName = self._availableIntegrationAlgorithms[0]
			self.simulationStopRequest = False

			# Open SimulationX
			sim = win32com.client.Dispatch(dispatch)

			# Show SimulationX window
			sim.Visible = True

			# Wait till SimulationX starts and loads libraries
			if sim.InitState == simUninitialized:
				while sim.InitState != simInitBase:
					time.sleep(0.1)

			# SimulationX in non-interactive mode
			sim.Interactive = False

			if sim.InitState == simInitBase:
				sim.InitSimEnvironment()  # Necessary when a script is used to start SimulationX

			if len(modelFileName) == 1:
				strMsg = 'PySimulator: Load model'

				split = string.rsplit(modelFileName[0], '.', 1)
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
							sim.LoadLibrary(modelFileName[0])
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
			Plugins.Simulator.SimulatorBase.Model.close(self)
			if not type(sim) is types.NoneType:
				sim.Interactive = True

	def _isNumeric(self, s):
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
			childRelIdent = pChild.GetRelIdent(doc)
			if not pChild.Kind == simType:
				if not pChild.GetProperty(simIsBaseClass) and not pChild.GetProperty(simIsHidden) and not pChild.GetProperty(simIsProtected) and not pChild.GetProperty(simIsForCompat):
					childIsASimVariable = pChild.IsA(simVariable)
					if ((pChild.IsA(simParameter) or pChild.IsA(simGeneralParameter)) and not childIsASimVariable) or (pChild.GetProperty(simIsInput) and childIsASimVariable):
						# Parameter
						dim = pChild.Execute('GetDimension', [])[0]
						if dim == '':
							# Scalar dimension
							childTypeIdent = pChild.Type.Ident
							if not childTypeIdent == 'BuiltIn.BaseModel.ProtKind' and not childTypeIdent == 'StateSelect' and self._isNumeric(pChild.Value):
								childRelIdent = pChild.GetRelIdent(doc)
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
									self.variableTree.variable[childRelIdent] = Plugins.Simulator.SimulatorBase.TreeVariable(self.structureVariableName(childRelIdent), childValue, childValueEdit, childUnit, childVariability, childVariableAttr)
						elif self._isNumeric(dim):
							# Fixed vector dimension
							childTypeIdent = pChild.Type.Ident
							if not childTypeIdent == 'BuiltIn.BaseModel.ProtKind' and not childTypeIdent == 'StateSelect':
								childRelIdent = pChild.GetRelIdent(doc)
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
											if self._isNumeric(childValueList[i - 1]):
												self.variableTree.variable[childRelIdent + '[' + str(i) + ']'] = Plugins.Simulator.SimulatorBase.TreeVariable(self.structureVariableName(childRelIdent + '[' + str(i) + ']'), childValueList[i - 1], childValueEdit, childUnit, childVariability, childVariableAttr)
					elif childIsASimVariable:
						# Result
						dim = pChild.Execute('GetDimension', [])[0]
						if dim == '':
							# Scalar dimension
							childRelIdent = pChild.GetRelIdent(doc)
							if (not pChild.Parent == doc and not pObject.Name.find('_base') == 0) or (not childRelIdent == 't' and not childRelIdent == 'dt' and not childRelIdent == 'solverInfo' and not childRelIdent == 'lambdaHomotopy'):
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
								self.variableTree.variable[childRelIdent] = Plugins.Simulator.SimulatorBase.TreeVariable(self.structureVariableName(childRelIdent), childValue, childValueEdit, childUnit, childVariability, childVariableAttr)
						elif self._isNumeric(dim):
							# Fixed vector dimension
							childRelIdent = pChild.GetRelIdent(doc)
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
									self.variableTree.variable[childRelIdent + '[' + str(i) + ']'] = Plugins.Simulator.SimulatorBase.TreeVariable(self.structureVariableName(childRelIdent + '[' + str(i) + ']'), childValue, childValueEdit, childUnit, childVariability, childVariableAttr)
				childIsOuter = pChild.GetProperty(simIsOuter)
				if not childIsOuter or (childIsOuter and pChild.GetProperty(simIsInner)):
					childEntityClass = pChild.Class
					if childEntityClass == simSimObject or childEntityClass == simSimBlock or childEntityClass == simConservConnection or childEntityClass == simFluidConnection or childEntityClass == simModelicaPin:
						self._fillTree(pChild, doc)

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
			raise(Plugins.Simulator.SimulatorBase.Stopping)
		except:
			raise(Plugins.Simulator.SimulatorBase.Stopping)
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
				gridWidth = (simulation.stopTime - simulation.startTime) / (simulation.gridPoints - 1)
			else:
				gridWidth = (simulation.stopTime - simulation.startTime) / 500
		elif simulation.gridPointsMode == 'Width':
			gridWidth = simulation.gridWidth
		doc.Lookup('dtProtMin').Value = gridWidth
		doc.Lookup('protKind').Value = 0  # = 'BaseModel.ProtKind.EquidistantTimeSteps'
		try:
			doc.SolverByName = self._solverByName[simulation.algorithmName]
		except KeyError:
			pass

		for name, newValue in self.changedStartValue.iteritems():
			i = name.find('[')
			if i >= 0 and name.endswith(']'):
				value = doc.Parameters(name[0:i]).Value
				n = name[i:]
				n = re.sub('[\[\]]', '', n)
				if self._isNumeric(n):
					n = int(n)
					value = re.sub('[\{\}\[\] ]', '', value)
					value = value.replace(';', ',')
					valueList = value.split(',')
					valueList[n - 1] = newValue
					doc.Parameters(name[0:i]).Value = '{' + ','.join(valueList) + '}'
			else:
				doc.Parameters(name).Value = newValue

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
						paramValue.append(childValue)
				elif self._isNumeric(dim):
					# Fixed vector dimension
					dim = int(dim)
					childValue = re.sub('[\{\}\[\] ]', '', childValue)
					childValue = childValue.replace(';', ',')
					childValueList = childValue.split(',')
					if len(childValueList) == dim:
						for i in range(1, dim + 1):
							if self._isNumeric(childValueList[i - 1]):
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
				raise(Plugins.Simulator.SimulatorBase.Stopping)
			time.sleep(0.1)

		# Integration is finished
		if doc.SolutionState == simStopped:
			# Save results in CSV file
			resultFileName = os.path.abspath(simulation.resultFileName).replace('\\', '/')
			ver = self.config['Plugins']['SimulationX']['version']
			if ver == 'Iti.Simx36':
				ver = '3.6'
			elif ver == 'Iti.Simx37':
				ver = '3.7'
			else:
				ver = '3.5'

			try:
				key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\ITI GmbH\SimulationX ' + ver + r'\DataFilter', 0, winreg.KEY_ALL_ACCESS)
			except WindowsError:
				key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, r'Software\ITI GmbH\SimulationX ' + ver + r'\DataFilter', 0, winreg.KEY_ALL_ACCESS)
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
			winreg.SetValueEx(key, 'AddColumnNames', 0, winreg.REG_DWORD, 1)
			winreg.SetValueEx(key, 'AddColumnUnits', 0, winreg.REG_DWORD, 1)
			winreg.FlushKey(key)
			if float(ver) >= 3.6:
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
