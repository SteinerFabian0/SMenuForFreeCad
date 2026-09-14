# Registers the S-menu command and owns the global trigger shortcut.

import FreeCADGui as Gui
from PySide import QtCore, QtGui

from smenu import config, widget

OPEN_COMMAND_NAME = "SMenu_Open"

menuWidget: widget.SMenuWidget = None
triggerShortcut: QtGui.QShortcut = None


class OpenSMenuCommand:
    def GetResources(self):
        return {
            "Pixmap": "SMenu",
            "MenuText": "Open S-menu",
            "ToolTip": "Open the S-menu command grid at the cursor",
        }

    def Activated(self):
        openMenu()

    def IsActive(self):
        return menuWidget is not None


def openMenu() -> None:
    menuWidget.showAtCursor()


def install() -> None:
    global menuWidget, triggerShortcut
    mainWindow = Gui.getMainWindow()
    menuWidget = widget.SMenuWidget(mainWindow)
    Gui.addCommand(OPEN_COMMAND_NAME, OpenSMenuCommand())

    # FreeCAD only builds a command's QAction once the command is placed in a
    # menu or toolbar, so a Customize-assigned shortcut would never fire from
    # other workbenches. The S-menu therefore owns its trigger key directly.
    triggerShortcut = QtGui.QShortcut(QtGui.QKeySequence(config.getTriggerKey()), mainWindow)
    triggerShortcut.setContext(QtCore.Qt.ApplicationShortcut)
    triggerShortcut.activated.connect(openMenu)


def teardown() -> None:
    global menuWidget, triggerShortcut
    if triggerShortcut is not None:
        triggerShortcut.setEnabled(False)
        triggerShortcut.deleteLater()
        triggerShortcut = None
    if menuWidget is not None:
        menuWidget.close()
        menuWidget.deleteLater()
        menuWidget = None
