# Persisted settings: grid size, trigger key, and the per-workspace command palettes.

import FreeCAD as App
import FreeCADGui as Gui

PARAMETER_PATH = "User parameter:BaseApp/Preferences/Mod/SMenuForFreeCad"
PALETTE_GROUP = "Pinned"
OWN_PALETTE_GROUP = "OwnPalette"
DEFAULT_PALETTE = "Default"
FALLBACK_WORKSPACE = "Global"

DEFAULT_GRID_ROWS = 3
DEFAULT_GRID_COLUMNS = 4
MIN_GRID_EXTENT = 1
MAX_GRID_EXTENT = 12
DEFAULT_CELL_SIZE = 28
MIN_CELL_SIZE = 16
MAX_CELL_SIZE = 96
DEFAULT_TRIGGER_KEY = "S"

WORKSPACE_SUFFIX = "Workbench"


def getGridRows() -> int:
    return _clampGridExtent(_parameters().GetInt("GridRows", DEFAULT_GRID_ROWS))


def getGridColumns() -> int:
    return _clampGridExtent(_parameters().GetInt("GridColumns", DEFAULT_GRID_COLUMNS))


def setGridRows(rows: int) -> None:
    _parameters().SetInt("GridRows", _clampGridExtent(rows))


def setGridColumns(columns: int) -> None:
    _parameters().SetInt("GridColumns", _clampGridExtent(columns))


def getCellSize() -> int:
    return _clampCellSize(_parameters().GetInt("CellSize", DEFAULT_CELL_SIZE))


def setCellSize(size: int) -> None:
    _parameters().SetInt("CellSize", _clampCellSize(size))


def getShowCellFrames() -> bool:
    return _parameters().GetBool("ShowCellFrames", True)


def setShowCellFrames(showCellFrames: bool) -> None:
    _parameters().SetBool("ShowCellFrames", showCellFrames)


def getTriggerKey() -> str:
    return _parameters().GetString("TriggerKey", DEFAULT_TRIGGER_KEY) or DEFAULT_TRIGGER_KEY


def setTriggerKey(key: str) -> None:
    _parameters().SetString("TriggerKey", key)


def getActiveWorkspace() -> str:
    workbench = Gui.activeWorkbench()
    return workbench.name() if workbench is not None else FALLBACK_WORKSPACE


def listWorkspaces() -> list[tuple[str, str]]:
    workspaces = [(name, _workspaceLabel(name)) for name in Gui.listWorkbenches()]
    return sorted(workspaces, key=lambda workspace: workspace[1].lower())


def hasOwnPalette(workspace: str) -> bool:
    return _ownPaletteParameters().GetBool(workspace or FALLBACK_WORKSPACE, False)


def setHasOwnPalette(workspace: str, hasOwnPalette: bool) -> None:
    _ownPaletteParameters().SetBool(workspace or FALLBACK_WORKSPACE, hasOwnPalette)


def getActivePalette() -> str:
    return getPaletteFor(getActiveWorkspace())


def getPaletteFor(workspace: str) -> str:
    return workspace if hasOwnPalette(workspace) else DEFAULT_PALETTE


def getPinnedCommand(palette: str, row: int, column: int) -> str:
    return _paletteParameters(palette).GetString(_cellKey(row, column), "")


def setPinnedCommand(palette: str, row: int, column: int, commandName: str) -> None:
    _paletteParameters(palette).SetString(_cellKey(row, column), commandName)


def clearPinnedCommand(palette: str, row: int, column: int) -> None:
    _paletteParameters(palette).RemString(_cellKey(row, column))


def _parameters():
    return App.ParamGet(PARAMETER_PATH)


def _paletteParameters(palette: str):
    return _parameters().GetGroup(PALETTE_GROUP).GetGroup(palette or DEFAULT_PALETTE)


def _ownPaletteParameters():
    return _parameters().GetGroup(OWN_PALETTE_GROUP)


def _clampGridExtent(extent: int) -> int:
    return max(MIN_GRID_EXTENT, min(MAX_GRID_EXTENT, extent))


def _clampCellSize(size: int) -> int:
    return max(MIN_CELL_SIZE, min(MAX_CELL_SIZE, size))


def _cellKey(row: int, column: int) -> str:
    return "Cell{0}x{1}".format(row, column)


def _workspaceLabel(workspace: str) -> str:
    workbench = Gui.listWorkbenches().get(workspace)
    menuText = getattr(workbench, "MenuText", "")
    if menuText:
        return menuText
    return workspace[: -len(WORKSPACE_SUFFIX)] if workspace.endswith(WORKSPACE_SUFFIX) else workspace
