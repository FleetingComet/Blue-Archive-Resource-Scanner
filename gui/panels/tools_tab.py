"""The Tools tab: a tool list on the left, the selected tool's page on the right.

Pages are built the first time a tool is shown (most sessions only use one or
two). Running is done from the window's action bar, which knows the tool this
tab has selected. This module also owns the HTML ↔ Text grouping transfer,
because it is the only place that can see both pages at once.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

import ttkbootstrap as ttk

from gui.panels.tool_list import ToolList
from gui.panels.tool_page import ToolPage
from gui.registry import Tool


class ToolsTab(ttk.Frame):
    """Calls ``on_change(tool)`` whenever the selected tool changes."""

    def __init__(
        self,
        master,
        *,
        tools: Iterable[Tool],
        on_change: Callable[[Tool], None],
        on_notice: Callable[[str, str], None] | None = None,
        active_file: Callable[[], Path | None] | None = None,
        on_open_in_data: Callable[[Path], None] | None = None,
    ):
        super().__init__(master)
        self._tools = {tool.key: tool for tool in tools}
        self._pages: dict[str, ToolPage] = {}
        self._on_change = on_change
        self._on_notice = on_notice
        self._active_file = active_file
        self._on_open_in_data = on_open_in_data
        self.current: str | None = None

        panes = ttk.Panedwindow(self, orient="horizontal")
        panes.pack(fill="both", expand=True)
        self.tool_list = ToolList(
            panes, tools=self._tools.values(), on_select=self.show
        )
        self._host = ttk.Frame(panes)
        self._host.columnconfigure(0, weight=1)
        self._host.rowconfigure(0, weight=1)
        panes.add(self.tool_list, weight=0)  # keeps its width on resize
        panes.add(self._host, weight=1)

    @property
    def tool(self) -> Tool:
        return self._tools[self.current]

    def page(self, key: str | None = None) -> ToolPage:
        key = key or self.current
        if key not in self._pages:
            self._pages[key] = ToolPage(
                self._host,
                self._tools[key],
                on_copy_grouping=self._copy_grouping_callback(key),
                copy_grouping_label=self._copy_grouping_label(key),
                on_notice=self._on_notice,
                active_file=self._active_file,
                on_open_in_data=self._on_open_in_data,
            )
            self._pages[key].grid(row=0, column=0, sticky="nsew")
        return self._pages[key]

    def show(self, key: str) -> None:
        if key not in self._tools:
            key = next(iter(self._tools))
        page = self.page(key)
        page.tkraise()
        page.refresh_files()
        self.current = key
        self.tool_list.select(key)
        self._on_change(self._tools[key])

    def refresh_files(self) -> None:
        """Re-check the input files of every page built so far.

        Called when the Tools tab is shown and whenever the Data tab loads or
        saves a file, so "open in the Data tab" never goes stale.
        """
        for page in self._pages.values():
            page.refresh_files()

    # ------------------------------------------------------------------
    # Grouping transfer between the report tools
    # ------------------------------------------------------------------
    def _grouping_partners(self, key: str) -> list[Tool]:
        return [
            t
            for t in self._tools.values()
            if t.key != key and t.group_option is not None
        ]

    def _copy_grouping_label(self, key: str) -> str:
        partners = self._grouping_partners(key)
        if not partners:
            return "Copy grouping from…"
        return f"Copy grouping from {partners[0].label}"

    def _copy_grouping_callback(self, key: str) -> Callable[[], None] | None:
        partners = self._grouping_partners(key)
        if not partners:
            return None
        source = partners[0]
        return lambda: self.copy_grouping(source.key, key)

    def copy_grouping(self, source_key: str, dest_key: str) -> None:
        """Copy the grouping set from one report tool to the other.

        Values are transferred by name, so a dimension the destination does not
        support is reported instead of being silently dropped.
        """
        if source_key not in self._tools or dest_key not in self._tools:
            return
        fields = self.page(source_key).grouping_fields()
        kept, dropped = self.page(dest_key).set_grouping(fields)
        source_label = self._tools[source_key].label
        dest_label = self._tools[dest_key].label

        summary = ", ".join(kept) if kept else "no grouping (flat list)"
        self.page(dest_key).set_grouping_notice(
            f"Copied from {source_label}: {summary}"
        )
        if self._on_notice is not None:
            self._on_notice(
                f"Copied grouping from {source_label} to {dest_label}: {summary}", "ok"
            )
            if dropped:
                self._on_notice(
                    f"{dest_label} does not support: {', '.join(dropped)} - those were not copied.",
                    "warn",
                )
