# SMenuForFreeCad

A SolidWorks-style "S-menu" for FreeCAD: press a trigger key to pop up a
fixed grid of commands at the cursor, with a search bar attached that any
typing routes into, drag-and-drop pinning from search results into the
grid, and Alt+drag rearranging of pinned commands. Workspaces
(Sketcher, PartDesign, Assembly, ...) can each get their own set of
pinned commands, or share one default set.

Status: grid size is configurable, the grid opens at the cursor, search
works, search results can be dragged onto a grid cell to pin them, and
Alt+drag rearranges pinned commands. Pinned commands run on click and
are stored per palette.

Search reuses the [SearchBar](https://github.com/APEbbers/SearchBar)
addon's search field, but searches the S-menu's own index: every command
FreeCAD has registered, taken live from the command registry rather than
from SearchBar's cached scrape of the toolbars. If SearchBar is not
installed, the S-menu still opens and the field is shown disabled —
install SearchBar through the Addon Manager to enable search.

## Usage

Set the grid size, the cell size, the cell outlines and the trigger key
under **Edit -> Preferences -> SMenu**; all of them are global and apply
in every workspace.

The grid opens on its own; results appear only once you type. Hovering a
result shows its details beside the list, clicking one runs it.

Drag a result onto a grid cell to pin it there; click a pinned cell to
run it. Dropping on an occupied cell replaces what was there. **Alt+drag**
a pinned command to move it, which swaps it with whatever occupies the
target cell — dropping on an empty cell just moves it. Alt+drag it out of
the menu to unpin it; the ghost icon fades once the drop would remove it.

## Workspace palettes

Pins live in a palette. The **Workspaces** list in the preferences page
decides which palette a workbench uses: a checked workbench gets its own,
starting out empty; every unchecked one shares the default palette, so
editing the grid from any of them changes the grid in all of them.
Unchecking a workbench puts it back on the default palette and leaves its
own palette untouched, ready for when it is checked again.

The grid size and the search bar are global — only the pins differ
between palettes.

A command only shows up in search while its workbench is loaded, since
that is when FreeCAD registers it. A pin keeps working regardless: it
stores the command name, not the workbench.

## Layout

- `InitGui.py` - thin bootstrap FreeCAD loads at startup; registers the
  workbench and installs the global event filter from `smenu/setup.py`.
- `smenu/` - actual implementation package (importlib-reloadable during
  dev, see `dev/reload.py`).
  - `setup.py` - install/teardown of the global trigger-key event filter.
  - `widget.py` - the grid + search popup widget.
  - `commands.py` - a command's label, icon, tooltip and execution,
    addressed by command name.
  - `index.py` - the searchable command index built from FreeCAD's
    command registry, in the group shape SearchBar's box expects.
  - `drag.py` - the in-flight drag: its ghost icon and drop threshold.
  - `search.py` - the search field: builds SearchBar's `SearchBoxLight`
    over `index.py`, stretches it across the panel, routes clicks on its
    result list past the popup's mouse grab, and replaces its key handler
    so fast typing keeps its order.
  - `config.py` - persisted settings (grid size, trigger key, palettes
    and which workspace uses which) via FreeCAD's parameter store.
  - `preferences.py` - the preferences page class registered with
    FreeCAD; loads `Preferences.ui` and reads/writes through `config.py`.
- `Resources/icons/` - workbench + UI icons.
- `Resources/ui/Preferences.ui` - preferences page layout, loaded by
  `smenu/preferences.py`.
- `dev/reload.py` - reload `smenu/` modules and reinstall the event filter
  without restarting FreeCAD.
- `package.xml` - Addon Manager metadata.

## Credits

No code from other addons is copied into this repo. `smenu/search.py`
integrates with the [SearchBar](https://github.com/APEbbers/SearchBar)
addon at runtime, importing its installed `SearchBox`, `SearchBoxLight`
and `IndentedItemDelegate` modules to reuse its search field and result
list instead of reimplementing them; SearchBar must be installed
separately (see Addon Manager) and keeps its own license.

## Dev setup

This repo is symlinked into FreeCAD's Mod directory so edits here take
effect without reinstalling:

```
ln -s ~/Desktop/SMenuForFreeCad ~/.var/app/org.freecad.FreeCAD/data/FreeCAD/v1-1/Mod/SMenuForFreeCad
```

Restart FreeCAD after pulling/editing `InitGui.py` or workbench
registration. For changes inside `smenu/`, run `dev/reload.py` from the
FreeCAD Python console instead of restarting.
