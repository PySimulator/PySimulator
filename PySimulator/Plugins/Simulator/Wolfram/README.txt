2014-08-12 [alachew.mengist@liu.se]
--------------------------------------------

Quick Install
=============
1.  Install Mathematica 9.0.1
2.  Install mathlink
      mathlink is located in /path/to/Mathematica/<Version>/SystemFiles/Links/Python
      Run "SET VS90COMNTOOLS=%VS100COMNTOOLS%". mathlink requires VC for compiling. In the command Visual Studio 10 is used, change it according to your version.
      "python setup.py install". This will add mathlink to the python 3rd party libraries.
3.  Install Wolfram SystemModeler 4.0
4.  Configure a link between SystemModeler and Mathematica (Skip this step if you have already done it in step 3). In SystemModeler go to Tools->Options->Global->Mathematica and specify the Mathematica installation directory.
