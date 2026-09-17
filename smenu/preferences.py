# Preferences page: grid size, trigger key, and which workspaces get their own palette.

import os

import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from smenu import UI_DIRECTORY, config

PAGE_GROUP = "SMenu"
WORKSPACE_NAME_ROLE = QtCore.Qt.UserRole


class SMenuPreferencesPage:
    def __init__(self, parent: QtWidgets.QWidget = None):
        self.form = Gui.PySideUic.loadUi(os.path.join(UI_DIRECTORY, "Preferences.ui"))
        self.form.workspaceFilter.textChanged.connect(self._filterWorkspaces)

    def loadSettings(self) -> None:
        self.form.gridRows.setValue(config.getGridRows())
        self.form.gridColumns.setValue(config.getGridColumns())
        self.form.cellSize.setValue(config.getCellSize())
        self.form.showCellFrames.setChecked(config.getShowCellFrames())
        self.form.triggerKey.setText(config.getTriggerKey())
        self._fillWorkspaceList()

    def saveSettings(self) -> None:
        config.setGridRows(self.form.gridRows.value())
        config.setGridColumns(self.form.gridColumns.value())
        config.setCellSize(self.form.cellSize.value())
        config.setShowCellFrames(self.form.showCellFrames.isChecked())
        config.setTriggerKey(self.form.triggerKey.text())
        for item in self._workspaceItems():
            config.setHasOwnPalette(
                item.data(WORKSPACE_NAME_ROLE), item.checkState() == QtCore.Qt.Checked
            )

    def _fillWorkspaceList(self) -> None:
        self.form.workspaceList.clear()
        for name, label in config.listWorkspaces():
            item = QtWidgets.QListWidgetItem(label, self.form.workspaceList)
            item.setData(WORKSPACE_NAME_ROLE, name)
            item.setToolTip(name)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(
                QtCore.Qt.Checked if config.hasOwnPalette(name) else QtCore.Qt.Unchecked
            )
        self._filterWorkspaces(self.form.workspaceFilter.text())

    def _filterWorkspaces(self, filterText: str) -> None:
        needle = filterText.strip().lower()
        for item in self._workspaceItems():
            searchable = (item.text(), item.data(WORKSPACE_NAME_ROLE))
            item.setHidden(not any(needle in text.lower() for text in searchable))

    def _workspaceItems(self) -> list:
        workspaceList = self.form.workspaceList
        return [workspaceList.item(index) for index in range(workspaceList.count())]


def install() -> None:
    Gui.addPreferencePage(SMenuPreferencesPage, PAGE_GROUP)
