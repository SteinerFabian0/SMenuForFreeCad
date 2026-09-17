# The S-menu's searchable command index, built from FreeCAD's command registry.

import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

from smenu import commands

COMMAND_HANDLER = "smenuCommand"


class CommandIndex:
    """Search groups in the shape SearchBar's search box expects.

    A group's position in `groups` is the id the search box hands back, so every
    refresh reassigns the ids of the whole list.
    """

    def __init__(self):
        self.groups: list[dict] = []
        self.groupsByCommand: dict[str, dict] = {}

    def refresh(self) -> list[dict]:
        for commandName in Gui.listCommands():
            group = self.groupsByCommand.get(commandName)
            if group is None:
                self.groupsByCommand[commandName] = _group(commandName)
            elif group["icon"] is None:
                # A command indexed before its workbench loaded had no icon to
                # find yet; it gets one as soon as the workbench registers it.
                group["icon"] = _icon(commandName)
        self.groups = sorted(self.groupsByCommand.values(), key=lambda group: group["text"].lower())
        for groupId, group in enumerate(self.groups):
            group["id"] = groupId
        return self.groups

    def commandNameFor(self, groupId: int) -> str:
        group = self._groupFor(groupId)
        return group["action"]["command"] if group is not None else ""

    def toolTipWidgetFor(self, groupId: int) -> QtWidgets.QWidget:
        group = self._groupFor(groupId)
        if group is None:
            return _toolTipWidget("")
        return _toolTipWidget(
            "<b>{0}</b><p>{1}</p><p><i>{2}</i></p>".format(
                group["text"], group["toolTip"], group["action"]["command"]
            )
        )

    def _groupFor(self, groupId: int) -> dict:
        if groupId is None or not 0 <= groupId < len(self.groups):
            return None
        return self.groups[groupId]


def _icon(commandName: str) -> QtGui.QIcon:
    icon = commands.iconFor(commandName)
    return icon if not icon.isNull() else None


def _group(commandName: str) -> dict:
    return {
        "id": 0,
        "text": commands.labelFor(commandName),
        "icon": _icon(commandName),
        "action": {"handler": COMMAND_HANDLER, "command": commandName},
        "toolTip": commands.toolTipFor(commandName),
        "subitems": [],
    }


def _toolTipWidget(html: str) -> QtWidgets.QWidget:
    label = QtWidgets.QLabel(html)
    label.setTextFormat(QtCore.Qt.RichText)
    label.setWordWrap(True)
    label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
    label.setMargin(6)
    return label
