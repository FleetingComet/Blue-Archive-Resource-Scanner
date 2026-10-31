"""Reliable mouse-wheel routing for ttkbootstrap's scrolling containers.

ttkbootstrap's ``ScrolledFrame`` adds its wheel bind-tag on ``<Enter>`` and
removes it on ``<Leave>``; crossing into a child fires that ``<Leave>``, so a
wheel over a card (or any child) can stop scrolling.  Widget-level bindings
also clash with the tag and scroll twice.

``WheelRouter`` installs one bind-tag on the container and every descendant,
independently of hover state.  The handler consumes the event, so a grid never
scrolls twice.  New children can be attached at any time (cards are built
lazily), and widgets that disappear simply take their binding with them.
"""

from __future__ import annotations

import sys
import tkinter as tk
from collections.abc import Callable

import ttkbootstrap as ttk

_WHEEL_SEQUENCES = ("<MouseWheel>", "<Button-4>", "<Button-5>")
_SKIP_TYPES = (ttk.Scrollbar, ttk.Progressbar)


class WheelRouter:
    """Send wheel gestures over any descendant to one scrolling widget."""

    def __init__(
        self,
        scroll,
        *,
        units: int = 3,
        on_scroll: Callable[[], None] | None = None,
    ):
        self._scroll = scroll
        self._units = max(1, int(units))
        self._on_scroll = on_scroll
        self._tag = f"WheelRouter{id(self)}"
        self._bound = False
        # ttkbootstrap's own tag is hover-dependent and double-scrolls with us.
        disable = getattr(scroll, "disable_scrolling", None)
        if callable(disable):
            disable()

    # -- registration --------------------------------------------------
    def attach(self, widget: tk.Misc) -> None:
        """Route wheel events from ``widget`` and its descendants."""
        self.attach_tree(widget)

    def attach_tree(self, widget: tk.Misc) -> None:
        """Route wheel events from ``widget`` and all current descendants."""
        self._bind_once()
        self._attach_one(widget)
        for child in _children(widget):
            self.attach_tree(child)

    def close(self) -> None:
        """Unregister this router's Tcl class bindings during teardown."""
        if not self._bound:
            return
        for sequence in _WHEEL_SEQUENCES:
            try:
                self._scroll.unbind_class(self._tag, sequence)
            except tk.TclError:
                pass
        self._bound = False

    def _bind_once(self) -> None:
        if self._bound:
            return
        for sequence in _WHEEL_SEQUENCES:
            self._scroll.bind_class(self._tag, sequence, self._on_wheel, "+")
        self._bound = True

    def _attach_one(self, widget: tk.Misc) -> None:
        if isinstance(widget, _SKIP_TYPES):
            return
        try:
            tags = list(widget.bindtags())
        except tk.TclError:
            return
        if self._tag in tags:
            return
        tags.insert(1, self._tag)  # after the widget's own binding
        try:
            widget.bindtags(tuple(tags))
        except tk.TclError:
            pass

    # -- events --------------------------------------------------------
    def _on_wheel(self, event: tk.Event) -> str:
        steps = _steps(event)
        if steps:
            self._scroll.yview_scroll(steps * self._units, "units")
            if self._on_scroll is not None:
                self._on_scroll()
        return "break"

    # -- helpers used by card grids -----------------------------------
    def content_fits(self) -> bool:
        try:
            first, last = self._scroll.yview()
        except (tk.TclError, TypeError):
            return False
        return first <= 0.0 and last >= 1.0

    def view_fraction(self) -> tuple[float, float]:
        try:
            first, last = self._scroll.yview()
            return float(first), float(last)
        except (tk.TclError, TypeError, ValueError):
            return 0.0, 1.0

    def scroll_to_top(self) -> None:
        try:
            self._scroll.yview_moveto(0)
        except tk.TclError:
            pass

    def scroll_to_widget(self, widget: tk.Misc) -> None:
        """Bring ``widget`` into view, keeping a little breathing room above.

        The content frame of a ``ScrolledFrame`` is positioned at the canvas
        origin, so the widget's own y offset is already the canvas coordinate.
        """
        try:
            widget.update_idletasks()
            canvas = getattr(self._scroll, "_canvas", None)
            content = canvas.bbox("all") if canvas is not None else None
            total = max(1, content[3] - content[1]) if content else 0
            if total <= 0:
                return
            top = max(0, widget.winfo_y() - 8)
            self._scroll.yview_moveto(min(1.0, top / total))
        except (tk.TclError, TypeError):
            pass


def _children(widget: tk.Misc):
    try:
        return widget.winfo_children()
    except tk.TclError:
        return []


def _steps(event: tk.Event) -> int:
    """Mouse-wheel notches for Windows, macOS and X11 events."""
    number = getattr(event, "num", None)
    if number == 4:
        return -1
    if number == 5:
        return 1
    delta = int(getattr(event, "delta", 0) or 0)
    if delta == 0:
        return 0
    if sys.platform == "win32":
        return -1 if delta > 0 else 1
    # macOS reports small pixel deltas; X11 may report either sign convention.
    return -1 if delta > 0 else 1
