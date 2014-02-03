import distribute_setup
distribute_setup.use_setuptools()

import setuptools

setuptools.setup(
    name="PySimulator",
    version="0.6",  
    packages=setuptools.find_packages(),
    package_dir={"": "."},
    include_package_data=True,
    package_data={"": ["Examples/FMU1.0/*", "Examples/LinearSystems/*", "Examples/Testing/*", "Icons/*", "Documentation/*", "*.txt", "*.pdf", "*.pyd"]},    
    entry_points={
        "setuptools.installation":  ['PySimulator = PySimulator.PySimulator:start_PySimulator'],
        "gui_scripts":              ['PySimulator = PySimulator.PySimulator:start_PySimulator'],
        "console_scripts":          ['PySimulatorConsole = PySimulator.PySimulator:start_PySimulator']
        },

    install_requires=[
        #"setuptools>=0.6",
        "PySide>=1.1",
        "Traits>=4.2",
        "Enable>=4.2",
        "Chaco>=4.2",
        "configobj>=4.7",
        "winshell>=0.6",
        # strange dependencies by assimulo, it requires the following package according to the documentation of its setup.py
        # but they are not mentioned in the code - weird! ; Hopefully these dependencies are dropped in future
        #    "Assimulo>=2.1",
            "matplotlib>=1.0",
        "numpy>=1.6",
        #    "Cython>=0.15",
        ],

    author="Deutsches Zentrum fuer Luft- und Raumfahrt e.V. - DLR (German Aerospace Center); Institute for System Dynamics and Control",
    author_email="Andreas Pfeiffer <Andreas.Pfeiffer@dlr.de>",
    description="Simulation and Analysis Environment in Python with Plugin Infrastructure",
    license="LGPL",
    keywords="Simulator, Simulation, FMU, MTSF, Modelica, Plotting, Analysis, Simulation Analysis",
    url="www.pysimulator.org",
    platforms="Windows XP/Vista/7/8"
)


