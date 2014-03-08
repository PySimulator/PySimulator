import os, sys
import winshell

link_filepath = os.path.join(winshell.desktop(), "PySimulator.lnk")
with winshell.shortcut(link_filepath) as link:
  link.path = sys.prefix + r"\\pythonw.exe"
  link.description = "PySimulator - Simulation and Analysis Environment in Python"
  link.arguments = "-m PySimulator"
  p = [s for s in sys.path if 'pysimulator' in s]
  if len(p) == 1:
    link.working_directory = os.path.join(p[0], 'PySimulator')
    link.icon_location = (os.path.join(link.working_directory, 'Icons', 'pysimulator.ico'), 0)

import win32ui, win32con
import urllib

if win32ui.MessageBox("Thank you for installing PySimulator!\nPySimulator requires Assimulo which couldn't be installed by the automated installer.\nYou can manually download Assimulo from: www.jmodelica.org/assimulo\nDo you want to download and install Assimulo now?", "Install Assimulo?", win32con.MB_YESNO) == win32con.IDYES:
  urllib.urlretrieve("https://trac.jmodelica.org/assimulo/export/486/releases/Assimulo-2.3.win32-py2.7.exe", "Assimulo-2.3.win32-py2.7.exe")
  os.startfile("Assimulo-2.3.win32-py2.7.exe")
