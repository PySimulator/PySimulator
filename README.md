PySimulator
===========

The environment provides a graphical user interface for simulating different
model types (currently Functional Mockup Units, Modelica Models and SimulationX
Models), plotting result variables and applying simulation result analysis tools
like Fast Fourier Transform. Additionally advanced tools for linear system
analysis are provided that can be applied to the automatically linearized models.
The modular concept of the software enables easy development of further plugins
for both simulation and analysis.

####Further information
 * Pfeiffer A., Hellerer M., Hartweg S., Otter M. and Reiner M.: [PySimulator – A Simulation and Analysis Environment in Python with Plugin Infrastructure](http:/www.ep.liu.se/ecp/076/053/ecp12076053.pdf). In: Proceedings of 9th International Modelica Conference, Munich, Germany, Sept. 2012.
 * Ganeson A. K., Fritzson P., Rogovchenko O., Asghar A., Sjölund M. and Pfeiffer A.: [An OpenModelica Python Interface and its use in PySimulator](http:/www.ep.liu.se/ecp/076/054/ecp12076054.pdf). In: Proceedings of 9th International Modelica Conference, Munich, Germany, Sept. 2012.
 * Pfeiffer A., Hellerer M., Hartweg S., Otter M., Reiner M. and Tobolar J.: [System Analysis and Applications
with PySimulator](http:www.modprod.liu.se/modprod2013-program/1.456422/modprod2013-day2-talk05a-AndreasPfeiffer.pdf). Invited talk at 7th MODPROD Workshop on Model-Based Product Development, Linköping, Sweden, Feb. 2013.

####Supported Platforms
* Windows (Other platforms have not been tested.)

####Installation
* Start "Install PySimulator.bat". This batch file installs the 32 Bit Python(x,y) and all other necessary packages.
* Run PySimulator by clicking on the desktop icon after the installation.
* Further information about the installation can be found in the [wiki](../../wiki/Installation).

####Release notes

* [Version 0.61](https://github.com/PySimulator/PySimulator/archive/0.61.zip) (2014-03-07) for 10th Modelica Conference 2014:
 - Added Simulator plugin SimulationX
 - Added Simulator plugin OpenModelica
 - Bug fixes

* [Version 0.6](https://github.com/PySimulator/PySimulator/archive/0.6.zip) (2014-02-03):
 - New plugin for comparing result files (Testing plugin)
 - Simulation of lists of models (Testing plugin)
 - Improved simulator plugin interfaces
 - FMUSimulator including JModelica.org's Assimulo
 - Introduction of a working directory

* [Version 0.5](https://github.com/PySimulator/PySimulator/archive/0.5.zip) (2012-09-03):
 - Initial version including plugins for Dymola and FMU simulator
