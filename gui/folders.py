"""Project folders the GUI can open, and a cross-platform opener.

Folders are offered where they are relevant (output next to a result, logs
next to the log, config next to the preferences) rather than in one menu.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from src.core.paths import Path_Config

OUTPUT = "output"
LOGS = "logs"
CONFIG = "config"
PROJECT = "project"


def folder_path(key: str) -> Path:
    return {
        OUTPUT: Path_Config.OUTPUT_DIR,
        LOGS: Path_Config.LOGS_DIR,
        CONFIG: Path_Config.CONFIG_DIR,
        PROJECT: Path_Config.PROJECT_ROOT,
    }[key]


def open_folder(key: str) -> str | None:
    """Open the folder in the file manager; returns an error text or None."""
    target = folder_path(key)
    try:
        target.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(str(target))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])
    except OSError as exc:
        return f"Could not open {target}: {exc}"
    return None


def reveal(path: Path) -> str | None:
    """Open the file's folder, selecting the file where the OS supports it."""
    path = Path(path)
    if not path.exists():
        return (
            open_folder(OUTPUT)
            if path.parent == Path_Config.OUTPUT_DIR
            else _open_directory(path.parent)
        )
    try:
        if sys.platform == "win32":
            subprocess.Popen(["explorer", "/select,", str(path)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path.parent)])
    except OSError as exc:
        return f"Could not open the location of {path.name}: {exc}"
    return None


def _open_directory(target: Path) -> str | None:
    try:
        target.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(str(target))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])
    except OSError as exc:
        return f"Could not open {target}: {exc}"
    return None
