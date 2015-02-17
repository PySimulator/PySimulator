#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import winshell

link_filepath = os.path.join(winshell.desktop(), 'PySimulator.lnk')
with winshell.shortcut(link_filepath) as link:
    link.path = sys.prefix + r'\\pythonw.exe'
    link.description = 'PySimulator - Simulation and Analysis Environment in Python'
    link.arguments = '-m PySimulator'
    p = [s for s in sys.path if 'pysimulator' in s]
    if len(p) == 1:
        link.working_directory = os.path.join(p[0], 'PySimulator')
        link.icon_location = (os.path.join(link.working_directory, 'Icons', 'pysimulator.ico'), 0)


assimulo_name = None
sundials_name = None

import win32ui, win32con
import platform
import urllib

try:
    from assimulo.problem import Explicit_Problem
    from assimulo.problem import Implicit_Problem
    from assimulo.solvers import CVode
    from assimulo.solvers import IDA
    from assimulo.solvers import RungeKutta34
except:
    if sys.version_info >= (2,7) and sys.version_info < (2,8):
        if win32ui.MessageBox('PySimulator optionally requires Assimulo which could not be installed by the automated installer.\nYou can manually download Assimulo from: http://www.jmodelica.org/assimulo\nDo you want to download and install Assimulo now?', 'Install Assimulo?', win32con.MB_YESNO) == win32con.IDYES:
            if platform.architecture()[0] == '32bit':
                assimulo_name = 'Assimulo-2.5.1.win32-py2.7.exe'
            elif platform.architecture()[0] == '64bit':
                assimulo_name = 'Assimulo-2.5.1.win-amd64-py2.7.exe'

if assimulo_name is not None:
    urllib.urlretrieve('http://tbeu.de/py/' + assimulo_name, assimulo_name)
    os.startfile(assimulo_name)

