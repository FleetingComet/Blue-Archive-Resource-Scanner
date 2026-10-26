"""Entry + Browse/Clear for a file or folder path.

Used by the tool pages (a tool's ``-f/--file`` argument) and by Settings (the
local artwork folder). The entry takes the free space while the buttons keep
their size, so a long path never moves them.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Sequence
from pathlib import Path
from tkinter import filedialog

import ttkbootstrap as ttk

from gui.registry import JSON_FILETYPES
from gui.ui import button
from src.core.paths import Path_Config

OPEN, SAVE, DIRECTORY = "open", "save", "dir"


class FileSelector(ttk.Frame):
    """A path entry with Browse… (and Clear) beside it."""

    def __init__(
        self,
        master,
        *,
        mode: str = OPEN,
        textvariable: tk.StringVar | None = None,
        filetypes: Sequence[tuple[str, str]] | None = None,
        title: str = "Select a file",
        label: str | None = None,
        on_change: Callable[[], None] | None = None,
        clearable: bool = True,
    ):
        super().__init__(master)
        self.mode = mode
        self.variable = textvariable if textvariable is not None else tk.StringVar()
        self._filetypes = list(filetypes or JSON_FILETYPES)
        self._title = title
        self._on_change = on_change

        if label:
            ttk.Label(self, text=label).pack(side="left", padx=(0, 8))
        self.entry = ttk.Entry(self, textvariable=self.variable)
        self.entry.pack(side="left", fill="x", expand=True)
        self._browse_button = button(
            self, "Browse…", "folder2-open", command=self.browse, tip=self._title
        )
        self._browse_button.pack(side="left", padx=(6, 0))
        self._clear_button = None
        if clearable:
            self._clear_button = button(
                self, "Clear", "x-lg", command=self.clear, tip="Clear this path"
            )
            self._clear_button.pack(side="left", padx=(4, 0))
        if on_change is not None:
            self.variable.trace_add("write", lambda *_a: on_change())

    # ------------------------------------------------------------------
    def get(self) -> str:
        return self.variable.get().strip()

    def set(self, value: str | Path | None) -> None:
        self.variable.set("" if value is None else str(value))

    def browse(self) -> None:
        initial = self._initial_directory()
        if self.mode == DIRECTORY:
            chosen = filedialog.askdirectory(
                parent=self, title=self._title, initialdir=str(initial)
            )
        elif self.mode == SAVE:
            chosen = filedialog.asksaveasfilename(
                parent=self,
                title=self._title,
                initialdir=str(initial),
                defaultextension=".json",
                filetypes=self._filetypes,
            )
        else:
            chosen = filedialog.askopenfilename(
                parent=self,
                title=self._title,
                initialdir=str(initial),
                filetypes=self._filetypes,
            )
        if chosen:
            self.set(chosen)

    def clear(self) -> None:
        self.set("")

    def set_enabled(self, enabled: bool) -> None:
        """Disable the entry and its buttons (they keep their size)."""
        state = "normal" if enabled else "disabled"
        self.entry.configure(state=state)
        self._browse_button.configure(state=state)
        if self._clear_button is not None:
            self._clear_button.configure(state=state)

    # ------------------------------------------------------------------
    def _initial_directory(self) -> Path:
        current = self.get()
        if current:
            path = Path(current).expanduser()
            if not path.is_absolute():
                path = Path_Config.PROJECT_ROOT / path
            return path if path.is_dir() else path.parent
        return Path_Config.PROJECT_ROOT
