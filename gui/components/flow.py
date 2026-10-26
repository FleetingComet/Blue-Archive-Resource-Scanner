"""A tiny flow layout: widgets pack left-to-right and wrap onto new rows.

Tk's ``pack``/``grid`` cannot wrap, and a filter toolbar with a variable
number of categories otherwise overflows a narrow pane.  This frame measures
its children and places them row by row whenever the available width changes.
It is intentionally small: it does not manage children's geometry options
beyond ``place`` and it does not grow wider than its parent.
"""

from __future__ import annotations

import tkinter as tk

import ttkbootstrap as ttk


class FlowFrame(ttk.Frame):
    """Lay children out in wrapping rows, left aligned."""

    def __init__(
        self,
        master,
        *,
        spacing: int = 8,
        row_spacing: int = 6,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self._spacing = max(0, int(spacing))
        self._row_spacing = max(0, int(row_spacing))
        self._items: list[tk.Widget] = []
        self._width = 0
        self._height = 0
        self._job: str | None = None
        self.bind("<Configure>", self._on_configure)

    # -- content -------------------------------------------------------
    def add(self, widget: tk.Widget) -> None:
        if widget not in self._items:
            self._items.append(widget)
        self._schedule()

    def remove(self, widget: tk.Widget) -> None:
        if widget in self._items:
            self._items.remove(widget)
        try:
            widget.place_forget()
        except tk.TclError:
            pass
        self._schedule()

    def set_items(self, widgets: list[tk.Widget]) -> None:
        for widget in self._items:
            if widget not in widgets:
                try:
                    widget.place_forget()
                except tk.TclError:
                    pass
        self._items = list(widgets)
        self._schedule()

    def items(self) -> list[tk.Widget]:
        return list(self._items)

    def refresh(self) -> None:
        """Re-measure after a child's caption (and therefore width) changed."""
        self._schedule()

    # -- layout --------------------------------------------------------
    def _on_configure(self, event: tk.Event) -> None:
        if event.widget is not self or event.width == self._width:
            return
        self._width = event.width
        self._schedule()

    def _schedule(self) -> None:
        if self._job is not None:
            return
        self._job = self.after_idle(self._reflow)

    def _reflow(self) -> None:
        self._job = None
        if not self.winfo_exists():
            return
        width = self.winfo_width()
        if width <= 1:  # not mapped yet: wait for the first Configure
            return

        # A freshly built container (the filter dropdown frame) can still report
        # its fallback request size of 1x1 until Tk has run its geometry pass.
        # Measuring in that state laid every new filter button out one pixel
        # wide, which looked exactly like "the filters disappeared" after
        # loading another file.  Flush only when a child still looks unmeasured.
        items = [widget for widget in self._items if widget.winfo_exists()]
        if any(
            widget.winfo_reqwidth() <= 1 or widget.winfo_reqheight() <= 1
            for widget in items
        ):
            self.update_idletasks()
            # The idle flush can run a queued relayout that replaces the items;
            # only place widgets that are still alive and still current.
            items = [widget for widget in self._items if widget.winfo_exists()]

        x = 0
        y = 0
        row_height = 0
        max_height = 0
        for widget in items:
            widget_width = max(1, widget.winfo_reqwidth())
            widget_height = max(1, widget.winfo_reqheight())
            if x and x + widget_width > width:
                y += row_height + self._row_spacing
                x = 0
                row_height = 0
            widget.place(x=x, y=y, width=widget_width, height=widget_height)
            x += widget_width + self._spacing
            row_height = max(row_height, widget_height)
            max_height = max(max_height, y + row_height)

        height = max(1, max_height)
        if height != self._height:
            self._height = height
            self.configure(height=height)
