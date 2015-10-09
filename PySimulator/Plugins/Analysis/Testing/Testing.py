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


import SimulateList
import CompareResults



def getModelCallbacks():
    return [["Simulate List of Models...", SimulateList.simulateListMenu], ["Compare List of Results...", CompareResults.compareListMenu]]


def getModelMenuCallbacks():
    return [["Compare Results", CompareResults.compareResults]]


def getPlotCallbacks():
    ''' see getModelCallbacks
    '''
    return []

