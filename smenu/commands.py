# Labels, icons, tooltips and execution for FreeCAD commands, addressed by name.

import FreeCADGui as Gui
from PySide import QtGui


def labelFor(commandName: str) -> str:
    menuText = _commandInfo(commandName).get("menuText", "")
    return menuText.replace("&", "") if menuText else commandName


def iconFor(commandName: str) -> QtGui.QIcon:
    # A command's QAction only exists once the command sits in some menu or
    # toolbar, so its pixmap name is resolved through FreeCAD's icon factory
    # first — that works for every registered command, listed or not.
    icon = _factoryIcon(_commandInfo(commandName).get("pixmap", ""))
    if not icon.isNull():
        return icon
    action = _commandAction(commandName)
    return action.icon() if action is not None else QtGui.QIcon()


def toolTipFor(commandName: str) -> str:
    return _commandInfo(commandName).get("toolTip", "") or labelFor(commandName)


def run(commandName: str) -> None:
    Gui.runCommand(commandName, 0)


def _commandAction(commandName: str) -> QtGui.QAction:
    if not commandName:
        return None
    return Gui.getMainWindow().findChild(QtGui.QAction, commandName)


def _commandInfo(commandName: str) -> dict:
    command = Gui.Command.get(commandName) if commandName else None
    return command.getInfo() if command is not None else {}


def _factoryIcon(pixmapName: str) -> QtGui.QIcon:
    if not pixmapName:
        return QtGui.QIcon()
    try:
        icon = Gui.getIcon(pixmapName)
    except Exception:
        return QtGui.QIcon()
    return icon if icon is not None else QtGui.QIcon()
