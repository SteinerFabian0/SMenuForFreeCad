# Search field for the S-menu, backed by the installed SearchBar addon.

from typing import Callable

from PySide import QtCore, QtGui, QtWidgets

UNAVAILABLE_PLACEHOLDER = "Search needs the SearchBar addon"
RESULT_LIST_HEIGHT = 200
TOOL_INFO_WIDTH = 260
RESULT_SCROLL_STEP = 3

_UNBOUNDED_WIDTH = 16777215
WHEEL_NOTCH = 120


def createSearchField(
    parent: QtWidgets.QWidget, height: int, onResultActivated: Callable[[], None]
) -> QtWidgets.QLineEdit:
    field = _createSearchBarField(parent, onResultActivated) or _createUnavailableField(parent)
    _stretchAcrossPanel(field, height)
    return field


def coversPoint(field: QtWidgets.QLineEdit, globalPosition: QtCore.QPoint) -> bool:
    """True when one of the search result windows is under the point.

    The S-menu is a Qt.Popup and therefore holds a mouse grab, so events over the
    result list — a separate top-level window — reach the menu instead of the list.
    """
    return any(
        _containsGlobally(window, globalPosition)
        for window in _floatingWidgets(field, ("listView", "extraInfo"))
    )


def resultAt(field: QtWidgets.QLineEdit, globalPosition: QtCore.QPoint) -> dict:
    index = _resultIndexAt(field, globalPosition)
    if index is None:
        return None

    import GetItemGroups

    groupId = int(index.model().itemData(index.siblingAtColumn(2))[0])
    return GetItemGroups.globalGroups[groupId] if groupId >= 0 else None


def activateResultAt(field: QtWidgets.QLineEdit, globalPosition: QtCore.QPoint) -> None:
    index = _resultIndexAt(field, globalPosition)
    if index is None:
        return

    # SearchBar's own click handler asks the list whether it is under the mouse,
    # which the S-menu's popup grab makes it answer with False.
    import SearchBox

    SearchBox.SearchBox.selectResult(field, None, index)


def hideToolInfo(field: QtWidgets.QLineEdit) -> None:
    extraInfo = _floatingWidget(field, "extraInfo")
    if extraInfo is not None:
        extraInfo.hide()


def hoverResultAt(field: QtWidgets.QLineEdit, globalPosition: QtCore.QPoint) -> None:
    resultList = _floatingWidget(field, "listView")
    if resultList is None or not resultList.isVisible():
        return
    index = _resultIndexAt(field, globalPosition)
    if index is None:
        hideToolInfo(field)
        return
    resultList.setCurrentIndex(index)
    field.showExtraInfo()


def scrollResults(field: QtWidgets.QLineEdit, globalPosition: QtCore.QPoint, angleDelta: int) -> bool:
    resultList = _floatingWidget(field, "listView")
    if resultList is None or not _containsGlobally(resultList, globalPosition):
        return False
    scrollBar = resultList.verticalScrollBar()
    scrollBar.setValue(scrollBar.value() - _scrollSteps(angleDelta))
    return True


def hideResults(field: QtWidgets.QLineEdit) -> None:
    for window in _floatingWidgets(field, ("listView", "extraInfo")):
        window.hide()


def _resultIndexAt(field: QtWidgets.QLineEdit, globalPosition: QtCore.QPoint) -> QtCore.QModelIndex:
    resultList = _floatingWidget(field, "listView")
    if resultList is None or not _containsGlobally(resultList, globalPosition):
        return None
    index = resultList.indexAt(resultList.viewport().mapFromGlobal(globalPosition))
    return index if index.isValid() else None


def _createSearchBarField(
    parent: QtWidgets.QWidget, onResultActivated: Callable[[], None]
) -> QtWidgets.QLineEdit:
    try:
        import GetItemGroups
        import IndentedItemDelegate
        import SearchBox
        import SearchBoxLight
    except ImportError:
        return None

    field = SearchBoxLight.SearchBoxLight(
        getItemGroups=GetItemGroups.getItemGroups,
        getToolTip=GetItemGroups.getToolTip,
        getItemDelegate=IndentedItemDelegate.IndentedItemDelegate,
        parent=parent,
    )
    SearchBox.SearchBox.lazyInit(field)
    _pinFloatingWidgetsToField(field)
    _showToolInfoOnHoverOnly(field)
    _showResultsOnlyWhenTyping(field)
    field.resultSelected.connect(lambda index, groupId: onResultActivated())
    field.resultSelected.connect(GetItemGroups.onResultSelected)
    return field


def _createUnavailableField(parent: QtWidgets.QWidget) -> QtWidgets.QLineEdit:
    field = QtWidgets.QLineEdit(parent)
    field.setPlaceholderText(UNAVAILABLE_PLACEHOLDER)
    field.setEnabled(False)
    return field


def _stretchAcrossPanel(field: QtWidgets.QLineEdit, height: int) -> None:
    # SearchBoxLight pins itself to 200px so its clear button cannot resize it;
    # in the S-menu the field has to follow the panel width instead. Its width
    # hint is ignored as well, so the panel is sized by the grid alone and the
    # grid keeps its spacing instead of stretching to a wider field.
    field.setMinimumWidth(0)
    field.setMaximumWidth(_UNBOUNDED_WIDTH)
    field.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)
    field.setFixedHeight(height)


def _pinFloatingWidgetsToField(field: QtWidgets.QLineEdit) -> None:
    # SearchBar derives the field's screen position by summing the geometry of
    # every ancestor, which double-counts the main window the S-menu popup is
    # parented to and drops the result list far below the field.
    resultList = field.__dict__["listView"]
    extraInfo = field.__dict__["extraInfo"]

    def setFloatingWidgetsGeometry() -> None:
        below = field.mapToGlobal(QtCore.QPoint(0, field.height()))
        available = _screenAt(below).availableGeometry()
        width = max(field.width(), resultList.sizeHint().width())
        left = max(available.left(), min(below.x(), available.right() - width))
        top = below.y()
        if top + RESULT_LIST_HEIGHT > available.bottom():
            top = field.mapToGlobal(QtCore.QPoint(0, 0)).y() - RESULT_LIST_HEIGHT
        resultList.setGeometry(left, top, width, RESULT_LIST_HEIGHT)

        roomOnRight = available.right() - (left + width)
        if roomOnRight >= min(TOOL_INFO_WIDTH, left - available.left()):
            infoLeft = left + width
            infoWidth = min(TOOL_INFO_WIDTH, roomOnRight)
        else:
            infoWidth = min(TOOL_INFO_WIDTH, left - available.left())
            infoLeft = left - infoWidth
        extraInfo.setGeometry(infoLeft, top, infoWidth, RESULT_LIST_HEIGHT)

    field.setFloatingWidgetsGeometry = setFloatingWidgetsGeometry


def _showToolInfoOnHoverOnly(field: QtWidgets.QLineEdit) -> None:
    resultList = field.__dict__["listView"]
    extraInfo = field.__dict__["extraInfo"]

    def showExtraInfo() -> None:
        hasInfo = extraInfo.layout().count() > 0
        if hasInfo and _containsGlobally(resultList, QtGui.QCursor.pos()):
            extraInfo.show()
        else:
            extraInfo.hide()

    field.showExtraInfo = showExtraInfo


def _showResultsOnlyWhenTyping(field: QtWidgets.QLineEdit) -> None:
    # Opening the S-menu focuses the field, and SearchBar shows its whole tool
    # list on focus; here the list belongs to the query, not to the menu.
    import SearchBox

    def showList() -> None:
        if field.text():
            SearchBox.SearchBox.showList(field)
        else:
            SearchBox.SearchBox.hideList(field)

    field.showList = showList
    field.textChanged.connect(lambda text: showList())


def _scrollSteps(angleDelta: int) -> int:
    steps = int(round(angleDelta / WHEEL_NOTCH * RESULT_SCROLL_STEP))
    if steps != 0 or angleDelta == 0:
        return steps
    return RESULT_SCROLL_STEP if angleDelta > 0 else -RESULT_SCROLL_STEP


def _floatingWidget(field: QtWidgets.QLineEdit, name: str) -> QtWidgets.QWidget:
    # SearchBoxLight synthesizes a method for every unknown attribute, so its
    # windows are only recognizable by bypassing __getattr__ entirely.
    candidate = field.__dict__.get(name)
    return candidate if isinstance(candidate, QtWidgets.QWidget) else None


def _floatingWidgets(field: QtWidgets.QLineEdit, names: tuple) -> list:
    windows = (_floatingWidget(field, name) for name in names)
    return [window for window in windows if window is not None]


def _containsGlobally(widget: QtWidgets.QWidget, globalPosition: QtCore.QPoint) -> bool:
    return widget.isVisible() and widget.rect().contains(widget.mapFromGlobal(globalPosition))


def _screenAt(point: QtCore.QPoint) -> QtGui.QScreen:
    return QtGui.QGuiApplication.screenAt(point) or QtGui.QGuiApplication.primaryScreen()
