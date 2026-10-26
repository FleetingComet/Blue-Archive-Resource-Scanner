"""Tkinter control panel for the Blue Archive Resource Scanner.

Package layout:

- ``gui.run`` - thin entry point (``python gui/run.py``), bootstraps
  ``sys.path``/Tcl and starts the app.
- ``gui.app`` - the top-level window; composes the panels and owns the shared
  plumbing (log queue, child-process manager, hotkeys, dependency checks,
  unsaved-data guards).
- ``gui.ui`` - shared widgets and helpers (``ActionBar``, ``Page``, dialogs,
  fonts, the muted style).
- ``gui.registry`` - the runnable exporter/tool definitions and their real
  ``argparse`` options.
- ``gui.scanner_files`` - the scanner's JSON outputs and the processors behind
  them (used by the Data tab).
- ``gui.metadata`` - project name/version/description/links/dependencies read
  from ``pyproject.toml`` (the About dialog).
- ``gui.dependencies`` - the installed dependencies and their licenses.
- ``gui.gamedata`` - name/rarity lookups into ``assets/data/*_processed.json``
  (turns the scanner's bare item IDs and equipment tiers into readable names).
- ``gui.icons`` - asset identifiers for the game artwork (schaledb-relative
  paths), the remote URL builder, and star rows from ``assets/images/star``.
- ``gui.services`` - shared services; ``image_service`` is the one place that
  resolves local/remote artwork, caches it and decodes it off the UI thread.
- ``gui.components`` - reusable widgets: ``CardGrid``/``AssetCard``/
  ``StudentCard``, ``DataTable``, ``ImageView`` and ``FileSelector``.
- ``gui.folders`` - ``Path_Config`` folders and a cross-platform opener.
- ``gui.window_state`` - persisted geometry/tab/log layout/theme.
- ``gui.process`` - subprocess handling + output cleaning/tagging.
- ``gui.panels`` - the major UI regions:

  - ``overview`` - the Scanner tab (what the config will do).
  - ``data_page`` - the Data tab (inspect/correct scanned JSON, re-process).
  - ``tools_tab`` + ``tool_list`` + ``tool_page`` - the Tools tab.
  - ``log`` - the collapsible log panel.
  - ``status_bar`` - state/command/progress/context.
  - ``settings`` - the modal Settings dialog.
  - ``about`` - the About dialog.
"""

from __future__ import annotations
