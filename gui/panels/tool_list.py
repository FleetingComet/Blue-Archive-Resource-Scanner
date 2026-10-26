"""The tool-selection pane of the Tools tab.

A Treeview gives selection highlighting and Up/Down keyboard navigation for
free; each tool carries its Bootstrap icon.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

import ttkbootstrap as ttk

from gui.registry import Tool


class ToolList(ttk.Frame):
    """Calls ``on_select(key)`` when the user picks a tool."""

    def __init__(
        self, master, *, tools: Iterable[Tool], on_select: Callable[[str], None]
    ):
        super().__init__(master)
        self._tools = list(tools)
        self._on_select = on_select
        self._current: str | None = None
        self._icons: dict[str, str] = {}

        self._tree = ttk.Treeview(self, show="tree", selectmode="browse", padding=4)
        self._tree.column("#0", width=190, stretch=True)
        self._tree.pack(fill="both", expand=True)
        for tool in self._tools:
            self._tree.insert("", "end", iid=tool.key, text=f"  {tool.label}")
        self.restyle()
        self._tree.bind("<<TreeviewSelect>>", self._changed)

    def restyle(self) -> None:
        """Row height and icon colours are per-theme: run again after a switch."""
        ttk.Style().configure("Treeview", rowheight=34)
        for tool in self._tools:
            self._icons[tool.key] = ttk.Icon(tool.icon, 18)
            self._tree.item(tool.key, image=self._icons[tool.key])

    def select(self, key: str) -> None:
        """Highlight ``key`` (the callback only fires for user clicks)."""
        self._current = key
        self._tree.selection_set(key)

    def _changed(self, _event) -> None:
        selected = self._tree.selection()
        if selected and selected[0] != self._current:
            self._current = selected[0]
            self._on_select(self._current)
