# Dev-only: run from the FreeCAD Python console to pick up smenu/ edits
# without restarting FreeCAD. InitGui.py-level changes still need a restart,
# as does the preferences page: FreeCAD keeps the class registered at startup.

import importlib

import smenu
from smenu import commands, config, drag, preferences, search, setup, widget

setup.teardown()

for module in (smenu, config, commands, drag, search, widget, preferences, setup):
    importlib.reload(module)

setup.install()
