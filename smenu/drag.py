# Dragging a command onto a grid cell, driven by the S-menu's own mouse events.

from PySide import QtCore, QtGui, QtWidgets

GHOST_ICON_SIZE = 24
GHOST_CURSOR_OFFSET = 6


class CommandDrag:
    """A drag in progress.

    The S-menu is a Qt.Popup and holds a mouse grab, so QDrag's own event loop
    never sees the press; the menu forwards press/move/release in here instead.
    """

    def __init__(self):
        self.commandName = ""
        self.source = None
        self.ghost = QtWidgets.QLabel(None, QtCore.Qt.ToolTip | QtCore.Qt.FramelessWindowHint)
        self.ghost.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.ghost.setFixedSize(GHOST_ICON_SIZE, GHOST_ICON_SIZE)

    def isActive(self) -> bool:
        return bool(self.commandName)

    def start(
        self,
        commandName: str,
        icon: QtGui.QIcon,
        globalPosition: QtCore.QPoint,
        source: QtWidgets.QWidget = None,
    ) -> None:
        self.commandName = commandName
        self.source = source
        self.ghost.setPixmap(icon.pixmap(GHOST_ICON_SIZE, GHOST_ICON_SIZE))
        self.moveTo(globalPosition)
        self.ghost.show()
        self.ghost.raise_()

    def moveTo(self, globalPosition: QtCore.QPoint) -> None:
        self.ghost.move(globalPosition + QtCore.QPoint(GHOST_CURSOR_OFFSET, GHOST_CURSOR_OFFSET))

    def finish(self) -> str:
        droppedCommand = self.commandName
        self.commandName = ""
        self.source = None
        self.ghost.hide()
        return droppedCommand


def exceedsThreshold(origin: QtCore.QPoint, globalPosition: QtCore.QPoint) -> bool:
    return (globalPosition - origin).manhattanLength() >= QtWidgets.QApplication.startDragDistance()
