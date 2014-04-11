@echo off
cls
echo ###############################################################################
echo ####################[ PySimulator Installation Script ]########################
echo ###############################################################################
echo .
echo PySimulator requires certain additional applications to run. This installer
echo will attempt to automatically download and install the required files. Already 
echo installed software compontents don't need to be installed again and can be 
echo skipped.
echo .
echo .
echo Due to a bug in the current Python XY Version, the MSVC Redistributable has to
echo be installed manually.
echo If unsure select "y"
set /p installmsvc=Download and start installer for Microsoft Visual C++ 2008 Redistributable Package (x86)?(Y/N):
if /I not "%installmsvc%"=="y" goto skipmsvc
bitsadmin /TRANSFER "PySimulaterInstallation" /PRIORITY FOREGROUND http://download.microsoft.com/download/1/1/1/1116b75a-9ec3-481a-a3c8-1777b5381140/vcredist_x86.exe %TEMP%/vcredist_x86.exe
call %TEMP%/vcredist_x86.exe
:skipmsvc

cls
echo PySimulator is based on Python and requires a valid Python installation along
echo side a variaty of additional software libraries. Python XY offers all of this
echo software in one package.
echo During the installation please make sure to minimally install all default
echo selected packages or select the option "Full".
echo If unsure select "y"
set /p installpxy=Download and start installer for Python XY 2.7.6?(Y/N):
if /I not "%installpxy%"=="y" goto skippxy
bitsadmin /TRANSFER "PySimulaterInstallation" /PRIORITY FOREGROUND http://ftp.ntua.gr/pub/devel/pythonxy/Python(x,y)-2.7.6.0.exe %TEMP%/pxy.exe
call %TEMP%/pxy.exe
:skippxy

cls
echo The Python XY installation by default does not include the Enthought Tool
echo Suite, required by PySimulator. If you already installed ETS during the
echo previous step or you selected the "Full" option, this is not required but
echo is also unlikely to cause any problems.
echo If unsure select "y"
set /p installets=Download and start installer for Enthought Tool Suite 4.4.1-6?(Y/N):
if /I not "%installets%"=="y" goto skipets
bitsadmin /TRANSFER "PySimulaterInstallation" /PRIORITY FOREGROUND http://heanet.dl.sourceforge.net/project/python-xy/plugins/EnthoughtToolSuite-4.4.1-6_py27.exe %TEMP%/EnthoughtToolSuite-4.4.1-6_py27.exe
call %TEMP%/EnthoughtToolSuite-4.4.1-6_py27.exe
:skipets

C:\Python27\python.exe setup.py install
C:\Python27\python.exe post_setup.py

echo ###############################################################################
echo .
echo .
echo PySimulator installation Script finished
pause
