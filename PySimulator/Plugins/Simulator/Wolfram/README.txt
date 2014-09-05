2014-08-12 [alachew.mengist@liu.se]
--------------------------------------------

Quick Install
=============
- Install Wolfram SystemModeler 3.0.2
- Install Mathemathica 9.0.1
- Install Pythonica
    Pythonica is located in PySimulator/PySimulator/Plugins/Simulator/Wolfram/pythonica
  	"python setup.py install". This will add Pythonica to the python 3rd party libraries.
- Install mathlink
    mathlink is located in /path/to/Mathematica/<Version>/SystemFiles/Links/Python
    Run "SET VS90COMNTOOLS=%VS100COMNTOOLS%". mathlink requires VC for compiling. In the command Visual Studio 10 is used, change it according to your version.
    "python setup.py install". This will add mathlink to the python 3rd party libraries.