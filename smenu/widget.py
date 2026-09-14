# Grid + search popup: opens at the cursor, pin-via-drag, Alt+drag to rearrange.

from PySide import QtCore, QtGui, QtWidgets

from smenu import commands, config, drag, search

CELL_SIZE = 28
CELL_ICON_SIZE = 20
GRID_SPACING = 4
SEARCH_GAP = 10
PANEL_MARGIN = 4


class SMenuCell(QtWidgets.QToolButton):
    def __init__(self, row: int, column: int, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.row = row
        self.column = column
        self.commandName = ""
        self.setFixedSize(CELL_SIZE, CELL_SIZE)
        self.setIconSize(QtCore.QSize(CELL_ICON_SIZE, CELL_ICON_SIZE))
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setProperty("smenuDropTarget", False)

    def setCommand(self, commandName: str) -> None:
        self.commandName = commandName
        icon = commands.iconFor(commandName) if commandName else QtGui.QIcon()
        self.setIcon(icon)
        self.setText(_abbreviate(commandName) if icon.isNull() else "")
        self.setToolButtonStyle(
            QtCore.Qt.ToolButtonIconOnly if not icon.isNull() else QtCore.Qt.ToolButtonTextOnly
        )
        self.setToolTip(commands.toolTipFor(commandName) if commandName else "")
        self.setDropTarget(False)

    def setDropTarget(self, isDropTarget: bool) -> None:
        if self.property("smenuDropTarget") == isDropTarget:
            return
        self.setProperty("smenuDropTarget", isDropTarget)
        self.style().unpolish(self)
        self.style().polish(self)


class SMenuWidget(QtWidgets.QFrame):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent, QtCore.Qt.Popup)
        self.setObjectName("SMenuPopup")
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setAutoFillBackground(True)
        self.setStyleSheet(_PANEL_STYLE)
        self.setMouseTracking(True)
        self.cells: list[SMenuCell] = []
        self.paletteName = config.DEFAULT_PALETTE
        self.drag = drag.CommandDrag()
        self.pressedResult = None
        self.pressedCell = None
        self.pressPosition = QtCore.QPoint()

        panelLayout = QtWidgets.QVBoxLayout(self)
        panelLayout.setSpacing(SEARCH_GAP)
        panelLayout.setContentsMargins(PANEL_MARGIN, PANEL_MARGIN, PANEL_MARGIN, PANEL_MARGIN)

        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setSpacing(GRID_SPACING)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        panelLayout.addLayout(self.gridLayout)

        self.searchField = search.createSearchField(self, CELL_SIZE, self.hide)
        panelLayout.addWidget(self.searchField)

    def rebuildGrid(self) -> None:
        self._clearGrid()
        self.paletteName = config.getActivePalette()
        for row in range(config.getGridRows()):
            for column in range(config.getGridColumns()):
                cell = SMenuCell(row, column, self)
                cell.setCommand(config.getPinnedCommand(self.paletteName, row, column))
                cell.clicked.connect(lambda checked=False, source=cell: self._runCell(source))
                self.gridLayout.addWidget(cell, row, column)
                self.cells.append(cell)

    def showAtCursor(self) -> None:
        self.rebuildGrid()
        self.searchField.clear()
        self.adjustSize()
        self.move(_topLeftAt(QtGui.QCursor.pos(), self.size()))
        self.show()
        self.raise_()
        self.searchField.setFocus(QtCore.Qt.PopupFocusReason)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        QtWidgets.QApplication.instance().installEventFilter(self)
        super().showEvent(event)

    def hideEvent(self, event: QtGui.QHideEvent) -> None:
        QtWidgets.QApplication.instance().removeEventFilter(self)
        self._cancelDrag()
        search.hideResults(self.searchField)
        super().hideEvent(event)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        # The popup grab scatters mouse events over the menu, the grid cells and
        # the result list, none of which see the whole gesture on their own.
        eventType = event.type()
        if eventType == QtCore.QEvent.MouseMove:
            return self._handleMove(QtGui.QCursor.pos())
        if eventType == QtCore.QEvent.MouseButtonPress:
            return self._handlePress(QtGui.QCursor.pos(), event.modifiers())
        if eventType == QtCore.QEvent.MouseButtonRelease:
            return self._handleRelease(QtGui.QCursor.pos())
        if eventType == QtCore.QEvent.Wheel:
            return search.scrollResults(
                self.searchField, QtGui.QCursor.pos(), event.angleDelta().y()
            )
        return super().eventFilter(watched, event)

    def _handlePress(self, position: QtCore.QPoint, modifiers: QtCore.Qt.KeyboardModifiers) -> bool:
        self.pressPosition = position
        cell = self._cellAt(position)
        if cell is not None:
            self.pressedCell = cell if modifiers & QtCore.Qt.AltModifier else None
            return self.pressedCell is not None
        if not search.coversPoint(self.searchField, position):
            return False
        self.pressedResult = search.resultAt(self.searchField, position)
        return True

    def _handleMove(self, position: QtCore.QPoint) -> bool:
        if self.drag.isActive():
            self.drag.moveTo(position)
            self._markDropTarget(self._cellAt(position))
            return True
        if self._hasPendingPress() and drag.exceedsThreshold(self.pressPosition, position):
            self._startDrag(position)
            return True
        search.hoverResultAt(self.searchField, position)
        return False

    def _handleRelease(self, position: QtCore.QPoint) -> bool:
        if self.drag.isActive():
            self._dropAt(position)
            self._clearPress()
            return True
        activatedResult = self.pressedResult
        wasPending = self._hasPendingPress()
        self._clearPress()
        if activatedResult is not None:
            search.activateResultAt(self.searchField, position)
        return wasPending

    def _startDrag(self, position: QtCore.QPoint) -> None:
        source = self.pressedCell
        commandName = (
            source.commandName
            if source is not None
            else commands.commandNameFromResult(self.pressedResult)
        )
        self._clearPress()
        if not commandName:
            return
        search.hideToolInfo(self.searchField)
        self.drag.start(commandName, commands.iconFor(commandName), position, source)
        self._markDropTarget(self._cellAt(position))

    def _dropAt(self, position: QtCore.QPoint) -> None:
        target = self._cellAt(position)
        source = self.drag.source
        commandName = self.drag.finish()
        self._markDropTarget(None)
        if target is None or target is source:
            return
        if source is not None:
            self._pin(source, target.commandName)
        self._pin(target, commandName)

    def _pin(self, cell: SMenuCell, commandName: str) -> None:
        config.setPinnedCommand(self.paletteName, cell.row, cell.column, commandName)
        cell.setCommand(commandName)

    def _hasPendingPress(self) -> bool:
        return self.pressedResult is not None or self.pressedCell is not None

    def _clearPress(self) -> None:
        self.pressedResult = None
        self.pressedCell = None

    def _cancelDrag(self) -> None:
        self._clearPress()
        if self.drag.isActive():
            self.drag.finish()
            self._markDropTarget(None)

    def _markDropTarget(self, target: SMenuCell) -> None:
        for cell in self.cells:
            cell.setDropTarget(cell is target)

    def _cellAt(self, globalPosition: QtCore.QPoint) -> SMenuCell:
        child = self.childAt(self.mapFromGlobal(globalPosition))
        return child if isinstance(child, SMenuCell) else None

    def _runCell(self, cell: SMenuCell) -> None:
        if not cell.commandName:
            return
        self.hide()
        commands.run(cell.commandName)

    def _clearGrid(self) -> None:
        for cell in self.cells:
            self.gridLayout.removeWidget(cell)
            cell.setParent(None)
            cell.deleteLater()
        self.cells.clear()


def _abbreviate(commandName: str) -> str:
    return commandName.rpartition("_")[2][:2]


def _topLeftAt(point: QtCore.QPoint, size: QtCore.QSize) -> QtCore.QPoint:
    screen = QtGui.QGuiApplication.screenAt(point) or QtGui.QGuiApplication.primaryScreen()
    available = screen.availableGeometry()
    left = max(available.left(), min(available.right() - size.width(), point.x()))
    top = max(available.top(), min(available.bottom() - size.height(), point.y()))
    return QtCore.QPoint(left, top)


_PANEL_STYLE = """
#SMenuPopup {
    background-color: #2b2b2b;
    border: 1px solid #555555;
    border-radius: 4px;
}
#SMenuPopup > QToolButton {
    border: 1px solid #343434;
    border-radius: 3px;
    background-color: transparent;
    color: #909090;
}
#SMenuPopup > QToolButton:hover {
    border-color: #3daee9;
    background-color: #3a3a3a;
}
#SMenuPopup > QToolButton[smenuDropTarget="true"] {
    border-color: #3daee9;
    background-color: #3a4a52;
}
#SMenuPopup QLineEdit {
    border: 1px solid #343434;
    border-radius: 3px;
    background-color: transparent;
    color: #d0d0d0;
    padding-left: 4px;
    padding-right: 4px;
}
#SMenuPopup QLineEdit:focus {
    border-color: #3daee9;
}
"""
