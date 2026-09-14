# Bootstrap loaded by FreeCAD at GUI startup; real logic lives in smenu/.

# FreeCAD execs this file with separate globals and locals dicts, so names
# bound here are invisible to class bodies and methods. Everything below
# therefore resolves its imports locally or is assigned after the class body.

import os

import FreeCADGui as Gui

from smenu import ICONS_DIRECTORY, preferences, setup


class SMenuWorkbench(Gui.Workbench):
    MenuText = "SMenu"
    ToolTip = "SolidWorks-style S-menu for FreeCAD"

    def Initialize(self):
        from smenu import setup

        self.appendMenu("S-menu", [setup.OPEN_COMMAND_NAME])

    def Activated(self):
        pass

    def Deactivated(self):
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


SMenuWorkbench.Icon = os.path.join(ICONS_DIRECTORY, "SMenu.svg")

Gui.addIconPath(ICONS_DIRECTORY)
Gui.addWorkbench(SMenuWorkbench())

preferences.install()

# The S-menu itself must work from any workbench (Sketcher, PartDesign,
# Assembly, ...), so it is installed globally at import time rather than
# gated behind workbench activation.
setup.install()
