import os


def get_immediate_subdirectories(directory):
    return [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name)) and name[0] != '.']

PlugInNames = get_immediate_subdirectories(os.path.abspath(os.path.dirname(__file__)))
plugin = []
for i in range(len(PlugInNames)):
    mod = __import__(PlugInNames[i] + "." + PlugInNames[i], locals(), globals(), [PlugInNames[i] + "." + PlugInNames[i]])
    plugin.append(mod)

fileExtension = []
description = []
for p in plugin:
    fileExtension.append(p.fileExtension)
    description.append(p.description)
   
