import os


def get_immediate_subdirectories(directory):
    return [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name)) and name[0] != '.']

PlugInNames = get_immediate_subdirectories(os.path.abspath(os.path.dirname(__file__)))
plugin = []
for i in range(len(PlugInNames)):
    try:
        mod = __import__(PlugInNames[i] + "." + PlugInNames[i], locals(), globals(), [PlugInNames[i] + "." + PlugInNames[i]])
        plugin.append(mod)
    except ImportError as e:
        print PlugInNames[i] + " plug-in could not be loaded. Error message: '" + e.message + "'"
    except SyntaxError as e:
        print PlugInNames[i] + " plug-in could not be loaded. Error message: '" + str(e) + "'"
    except Exception as e:
        info = str(e)
        if info == '' or info is None:
            print PlugInNames[i] + " plug-in could not be loaded."
        else:
            print PlugInNames[i] + " plug-in could not be loaded. Error message: '" + info + "'"
fileExtension = []
description = []
for p in plugin:
    fileExtension.append(p.fileExtension)
    description.append(p.description)
