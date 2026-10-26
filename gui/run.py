"""Standalone Tkinter control panel for the Blue Archive Resource Scanner.

This is a windowed front-end for the exact same flow ``launch.py`` drives from
the terminal:

1. read + edit ``config/settings.json`` (``AppSettings`` via ``Config``) and
   ``config/screen_config.json`` (via ``write_screen_config``),
2. check that rapidocr + cv2 are importable (``launch.py`` does the same on
   first launch, but the result is reported in the log instead of prompting),
3. print the active settings (captured into the in-app log instead of stdout),
4. run ``main.py`` as a child process - with ``--offline`` when data sync is
   disabled - and stream everything it prints into the log panel,
5. run any exporter in ``tools/`` the same way (``python -m tools.<name>``).

It is *not* wired into ``launch.py``; run it directly:

    python gui/run.py [--debug]

The window itself lives in :mod:`gui.app`; this file only bootstraps the
environment so the package imports can find the project + Tcl/Tk.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: locate the project root and make ``src`` importable *before* the
# project modules are imported. ``python gui/run.py`` puts ``gui/`` on
# sys.path, not the repo root, so ``import src.*`` would otherwise fail.
# ---------------------------------------------------------------------------


def _locate_root() -> Path:
    path = Path(__file__).resolve()
    while not (path / "main.py").exists():
        if path.parent == path:
            raise RuntimeError("Could not locate project root.")
        path = path.parent
    return path


PROJECT_ROOT = _locate_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Tcl/Tk data directories, as used by the uv/embeddable Python distributions
# where Tk cannot locate init.tcl on its own. Only exported when the
# directories actually exist, so a normal install is left untouched.
for _env_var, _sub_dir in (("TCL_LIBRARY", "tcl8.6"), ("TK_LIBRARY", "tk8.6")):
    _tcl_dir = Path(sys.base_prefix) / "tcl" / _sub_dir
    if _tcl_dir.is_dir():
        os.environ[_env_var] = str(_tcl_dir)
del _env_var, _sub_dir, _tcl_dir

from gui.app import main

if __name__ == "__main__":
    main()
