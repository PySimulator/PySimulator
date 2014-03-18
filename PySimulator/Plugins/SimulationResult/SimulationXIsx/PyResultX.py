# -*- coding: utf-8-*-

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

import re
import zipfile

import numpy

import struct as pStruct

def readModel(filename, docname, ResultList):
	''' This function creates a list of SimXResult Objects. The result objects in this list know the ident, dimension the relative path of the protocol and the dimension: \n
	Ident="springDamper.dx" RelPath="protocol\file141.bin" Quantity="Mechanics.Translation.Displace" Unit="m" Dimension="3805"

	The results within ResultList know the string assossiated by the parameter docname. The results yet do not know the SimXObject they belong to.

	The functions resturn Value is a zipFile object. '''
	Model = zipfile.ZipFile(filename, 'r')
	# print Model.namelist()
	Protocol_content = Model.open("protocol/content.xml", 'rU')
	results = Protocol_content.readlines()
	# firstline=re.search('((<Result Ident=)+(.*?)(/>)+)', results[1])
	# print firstline.group(1)
	matches = re.findall('((<Result )+(.*?)(/>)+)', results[1])
	for tup in matches :
		Result = SimXResult(filename, Model, docname, tup[2])
		ResultList.append(Result)
		# print str(Result.RelPath)
		# print Result.Ident, Result.Dimension, Result.Unit
	return Model

class SimXUnit:
	def __init__(self, string, scale=1, offset=0):
		self.Offset = offset
		self.Scale = scale
		self.String = string.decode('utf-8')

# Ident="fahrer1.dx1" RelPath="protocol\file141.bin" Quantity="Mechanics.Translation.Displace" Unit="m" Dimension="3805"
class SimXResult:
	def __init__(self, ModelFileName, ModelZipFile, Document, line=None, *arguments, **keywords):
		keys = keywords.keys()
		keys.sort()
		for kw in keys:
			if kw == 'Unit':
				Unit = keywords[kw]
			elif kw == 'Quantity':
				Quantity = keywords[kw]
			elif kw == 'Ident':
				Ident = keywords[kw]
			elif kw == 'Data':
				self.Data = keywords[kw]
			else:
				print kw, 'Parameter not found!'
		if line == None:
			self.StorageType = 'calc'
			# TODO: create line
			strDimension = ''
			for n in self.Data.shape:
				strDimension = strDimension + str(n) + ','
			strDimension = strDimension[:-1]
			line = "Ident=\"" + Ident + "\" Quantity=\"" + Quantity + '\" Unit=\"' + Unit + '\" Dimension=\"' + strDimension + '\"'
			print 'A calculated result is constructed: ', line
		else:
			self.Data = None
			self.StorageType = 'zip'

		self.ModelFile = ModelFileName
		self.ModelZipFile = ModelZipFile
		match = re.search('(?<=Ident=")(.+?)("+?)', line)
		self.strIdent = match.group(1)
		self.Ident = [Document]
		matches = re.findall('(\w+)(\.)*', self.strIdent)
		for match in matches:
			self.Ident.append(match[0])  # ident auffuellen
		self.Name = self.Ident[-1]
		if self.StorageType == 'zip':
			match = re.search('(?<=RelPath=")((\w+)(\\\\)(\w+)(.\w+)*)', line)
			self.RelPath = match.group(0)
			self.RelPath = re.sub('(\\\\)', '/', self.RelPath)
		else:
			self.RelPath = None
		match = re.search('(?<=Quantity=")(.+?)("+?)', line)
		self.Quantity = match.group(1)
		match = re.search('(?<=Unit=")(.+?)("+?)', line)
		self.Unit = match.group(1)
		self.Unit = self.Unit.decode('utf-8')
		self.Scale = 1
		match = re.search('(?<=Dimension=")(.+?)("+?)', line)
		self.strDimension = match.group(1)
		matches = re.findall('(\d+)(, )*', self.strDimension)
		self.Dimension = []
		for match in matches:
			self.Dimension.append(int(match[0]))
		self.ndims = len(self.Dimension)
		self.strIdent = ''
		for name in self.Ident:
			self.strIdent = self.strIdent + '.' + name
		self.strIdent = self.strIdent[1:]
		self.strLabel = None
		self.set_ParentObject()
		self.TeX_Label = re.sub(u'_', u"\\_", self.strIdent)

	def get_TeXLabel(self):
		if self.strLabel != None:
			self.TeX_Label = re.sub(u'_', u"\\_", self.strLabel)  # replace underscore for LaTeX Label
			self.TeX_Label = re.sub(u' ', u"\\ ", self.strLabel)  # replace underscore for LaTeX Label
		else :
			self.TeX_Label = re.sub(u'_', u"\\_", self.strIdent)  # replace underscore for LaTeX Label
		return self.TeX_Label

	def set_Label(self, labelstring):
		self.strLabel = labelstring
		return labelstring

	def set_Unit(self, Unit):
		self.Unit = Unit.String
		self.Scale = Unit.Scale

	def get_Unit(self):
		return SimXUnit(self.Unit, self.Scale)

	def __eq__(self, other):
		if other == None:
			return False
		if self.Ident == other.Ident:
			return True
		return False

	def set_ParentObject(self, ParentObject=None):
		self.ParentObject = ParentObject

	def get_ParentObject(self):
		return self.ParentObject

	# def get_data(self):
	# 	return self.ParentObject.LoadResult(self.strIdent)

	def nCurves(self):
		return numpy.array(self.Dimension[1:]).prod()

	def get_data(self):
		if self.StorageType == 'zip':
			filename = self.ModelZipFile.read(self.RelPath)
			if self.ndims > 1:  # for arrays or vectors
				nReadValues = numpy.array(self.Dimension[:]).prod()  # overall double values to read
				# nValues = array(self.Dimension[1:]).prod()
				# print 'nValues: ',  nValues # DEBUG
				dbl_Result = numpy.array(pStruct.unpack_from(str(nReadValues) + 'd', filename))  # Read the binary values
				dbl_Result = numpy.reshape(dbl_Result, self.Dimension)
			else:  # for scalars
				dbl_Result = numpy.array(pStruct.unpack_from(str(self.Dimension[0]) + 'd', filename))
			# Debug: print 'scaling with: ',  self.Scale
			dbl_Result = self.Scale * dbl_Result
		else:
			dbl_Result = self.Scale * self.Data
		return dbl_Result

	def getAllAlongDim(self, dim, indexlist):
		iarray = self.get_data()
		indexarray = numpy.array(indexlist)
		# print 'SimXResult.getAllAlongDim:',  dim , indexarray,  iarray,  indexlist
		indexarray = numpy.concatenate((indexarray[:dim], numpy.array([0]), indexarray[dim:]))
		j = 0
		for i in indexarray:
			if j > dim:
				iarray = iarray[:, i]
			elif j < dim:
				iarray = iarray[i, :]
			j = j + 1
		return iarray

class SimXObject:
	def __init__(self, Model, Name, Parent, ParentIdent, ResultList, Layer, *arguments, **keywords):
		self.Model = Model
		self.ParentIdent = ParentIdent[:]
		self.Layer = Layer
		self.Name = Name
		self.Parent = Parent
		self.ObjectList = SimXObjects(self.Parent)
		self.ResultList = []
		self.strIdent = ''
		self.Comment = Name

		keys = keywords.keys()
		keys.sort()
		for kw in keys:
			if kw == 'Comment':
				self.Comment = keywords[kw]
			else:
				print kw, 'Parameter not found!'

		for Result in ResultList :
			# ueberpruefe ob das Ergebnis einen laengeren Ident hat als die eigene Ebene UND der Ident bis hierher zum Object passt
			if len(Result.Ident) > (Layer + 1) and  Result.Ident[:Layer] == ParentIdent and Result.Ident[Layer] == self.Name:
				Object = self.ObjectList.Item(Result.Ident[Layer + 1])  # dann versuchen wir das passende SimXObject ueber seinen Namen zu greifen
				if Object == None and len(Result.Ident) > (Layer + 2) :  # gibt es das Object noch nicht, aber der Ident ist noch laenger, dann muss es eine
					# Komponente geben, die so heisst und das betreffende Ergebnis enthaelt.
					self.ObjectList.append(SimXObject(Model, Result.Ident[Layer + 1], self , Result.Ident[:(Layer + 1)], ResultList, Layer + 1))
				elif Object == None :  # das Object gibts noch nicht, der Ident hoert aber bei Layer+1 auf, dann ist es eine Ergebnisgroesse des akutellen SimXObject
					try:
						# versuche die Ergebnisgroesse in der eigenen Ergebnisliste zu finden
						idx = self.ResultList.index(Result)
					except ValueError:
						# wenns die nicht schon gibt wird sie angelegt
						Result.set_ParentObject(self)
						self.ResultList.append(Result)
		ParentIdent.append(Name)
		self.Ident = ParentIdent[:]
		for name in self.Ident:
			self.strIdent = self.strIdent + '.' + name
		self.strIdent = self.strIdent[1:]

	def add_Result(self, Result):
		ResultList = []
		ResultList.append(Result)
		ParentIdent = self.ParentIdent[:]
		Layer = self.Layer
		# ueberpruefe ob das Ergebnis einen laengeren Ident hat als die eigene Ebene UND der Ident bis hierher zum Object passt
		print 'Result.Ident,  self.Layer,  Result.Ident[:Layer],  self.ParentIdent,  self.Name'
		print Result.Ident, self.Layer, Result.Ident[:Layer], self.ParentIdent, self.Name
		if len(Result.Ident) > (Layer + 1) and  Result.Ident[:Layer] == self.ParentIdent and Result.Ident[Layer] == self.Name:
			Object = self.ObjectList.Item(Result.Ident[Layer + 1])  # dann versuchen wir das passende SimXObject ueber seinen Namen zu greifen
			if Object == None and len(Result.Ident) > (Layer + 2) :  # gibt es das Object noch nicht, aber der Ident ist noch laenger, dann muss es eine
				# Komponente geben, die so heisst und das betreffende Ergebnis enthaelt.
				self.ObjectList.append(SimXObject(self.Model, Result.Ident[Layer + 1], self , Result.Ident[:(Layer + 1)], ResultList, Layer + 1))
			elif Object == None :  # das Object gibts noh nicht, der Ident hoert aber bei Layer+1 auf, dann ist es eine Ergebnisgroesse des akutellen SimXObject
				try:
					# versuche die Ergebnisgroesse in der eigenen Ergebnisliste zu finden
					idx = ResultList.index(Result)
				except ValueError:
					# wenns die nicht schon gibt wird sie angelegt
					Result.set_ParentObject(self)
					self.ResultList.append(Result)
			# elif len(Result.Ident)>(Layer+2) : #das object gibt es schon, das Result aht aber einen längeren Ident und muss daher mindestens eine Ebene tiefer eingefügt werden
			# 	self.add_Result(Result)
			else:  # das Object gibt es schon
				try:
					# versuche die Ergebnisgroesse in der Ergebnisliste des Objects zu finden
					idx = Object.ResultList.index(Result)
				except ValueError:
					# wenns die nicht schon gibt wird sie angelegt
					Result.set_ParentObject(Object)
					Object.ResultList.append(Result)

	def SimObjects(self):
		for index in range(0, len(self.ObjectList), 1):
			yield self.ObjectList[index]

	def ExtractIdentFromStr(self, string):
		matches = re.findall('(\w+)(\.)*', string)
		Ident = []
		for match in matches:
			Ident.append(match[0])  # ident auffuellen
		return Ident

	def LookUp(self, strIdent):
		Ident = self.ExtractIdentFromStr(strIdent)
		# Debug: print 'Lookup: '+strIdent
		if self.Ident == Ident:  # is it me?
			return self
		if self.Ident[:(self.Layer + 1)] == Ident[:(self.Layer + 1)]:  # its not me but the ident matches to my layer
		# may be one of my components or results
			for Object in self.SimObjects():  # for each of my components
				if Object.Ident[:(Object.Layer + 1)] == Ident[:(Object.Layer + 1)]:  # check if the Ident of the searched string matches to one of them at least down to its layer
					return Object.LookUp(strIdent)  # in this case, let him do the work
			for Result in self.Results():  # its none of my components so it still may be one of my results
				if Result.Ident == Ident:
					return Result
					# its none of my results
		# The Ident does not match to me, down to my Layer, so my Parent has to find the right Object
		return self.Parent.LookUp(strIdent)

	def LoadResult(self, strIdent):
		Result = self.LookUp(strIdent)
# 		filename=self.Model.read(Result.RelPath)
# 		if len(Result.Dimension)>1:
# 			nReadValues=array(Result.Dimension[:]).prod()
# 			nValues=array(Result.Dimension[1:]).prod()
# 			# print 'nValues: ',  nValues # DEBUG
# 			dbl_Result=array(pStruct.unpack_from(str(nReadValues)+'d', filename))
# 			dbl_Result=reshape(dbl_Result,  Result.Dimension)
# 		else:
# 			dbl_Result=array(pStruct.unpack_from(str(Result.Dimension[0])+'d', filename))
# 		return dbl_Result
		return Result.get_data()

	def __eq__(self, other):
		if other == None:
			return False
		if self.Ident == other.Ident:
			return True
		return False

	def Results(self):
		for index in range(0, len(self.ResultList), 1):
			yield self.ResultList[index]

	def printObject(self) :
		tabs = ''
		for i in range(self.Layer):
			tabs = tabs + '\t'
		print tabs, self.Name
		tabs = tabs + '\t'
		print tabs, self.ResultList
# 		for Object in self.ObjectList: #.data:
# 			Object.printObject()

class SimXObjects :
	def __init__(self, Parent) :
		self.data = [];
		self.Parent = Parent
	def Item(self, Name) :
		for idx in range(len(self.data)) :
			if self.data[idx].Name == Name :
				return self.data[idx]
		return None

	def append(self, Object):
		self.data.append(Object)

	def __len__(self):
		return len(self.data)

	def __getitem__(self, idx):
		return self.data[idx]

	def __iter__(self):
		# return SimXObjectsIteratorTree(self.data)
		return SimXObjectsIteratorTree(self)


class SimXObjectsIterator:
	def __init__(self, data):
		self.data = data
		self.index = 0

	def __iter__(self):
		return self

	def next(self):
		if self.index > (len(self.data) - 1):
			raise StopIteration
		self.index = self.index + 1
		return self.data[self.index - 1]

class SimXObjectsIteratorTree:
	def __init__(self, ObjectList):
		self.List = ObjectList
		self.data = ObjectList.data
		self.index = 0
		self.subIterator = None

	def __iter__(self):
		return self

	def next(self):
		if self.index > (len(self.data) - 1) and self.List.Parent == None:
			raise StopIteration
		elif self.index > (len(self.data) - 1):
			return None
		if self.subIterator == None:
			self.subIterator = self.data[self.index].ObjectList.__iter__()
		sublevel = self.subIterator.next()
		if sublevel != None:
			return sublevel
		self.subIterator = None
		self.index = self.index + 1
		return self.data[self.index - 1]
