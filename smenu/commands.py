# Resolving search results to FreeCAD commands, and running/rendering them.

import FreeCADGui as Gui
from PySide import QtGui, QtWidgets

PINNABLE_HANDLERS = ("tool", "subTool")


def commandNameFromResult(result: dict) -> str:
    action = result.get("action", {}) if result else {}
    if action.get("handler") not in PINNABLE_HANDLERS:
        return ""
    if action.get("showMenu"):
        return ""

    toolAction = _toolbarAction(
        action.get("toolbar", ""), action.get("tool", ""), action.get("subTool", "")
    )
    return toolAction.objectName() if toolAction is not None else ""


def iconFor(commandName: str) -> QtGui.QIcon:
    action = _commandAction(commandName)
    if action is not None and not action.icon().isNull():
        return action.icon()
    return QtGui.QIcon(_resourcePathFor(commandName))


def toolTipFor(commandName: str) -> str:
    action = _commandAction(commandName)
    if action is not None:
        return action.toolTip()
    return _commandInfo(commandName).get("toolTip", commandName)


def run(commandName: str) -> None:
    Gui.runCommand(commandName, 0)


def _toolbarAction(toolbarName: str, toolText: str, subToolText: str) -> QtGui.QAction:
    mainWindow = Gui.getMainWindow()
    for toolbar in mainWindow.findChildren(QtWidgets.QToolBar, toolbarName):
        for button in toolbar.findChildren(QtWidgets.QToolButton):
            if button.text() != toolText:
                continue
            if not subToolText:
                return button.defaultAction()
            return _menuAction(button.menu(), subToolText)
    return None


def _menuAction(menu: QtWidgets.QMenu, text: str) -> QtGui.QAction:
    if menu is None:
        return None
    for action in menu.actions():
        if action.text() == text:
            return action
    return None


def _commandAction(commandName: str) -> QtGui.QAction:
    if not commandName:
        return None
    return Gui.getMainWindow().findChild(QtGui.QAction, commandName)


def _commandInfo(commandName: str) -> dict:
    command = Gui.Command.get(commandName)
    return command.getInfo() if command is not None else {}


def _resourcePathFor(commandName: str) -> str:
    pixmap = _commandInfo(commandName).get("pixmap", "")
    if not pixmap:
        return ""
    return pixmap if pixmap.startswith(":") else ":/icons/" + pixmap
