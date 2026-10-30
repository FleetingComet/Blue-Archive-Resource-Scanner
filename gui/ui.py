"""Shared UI helpers: fonts, icon buttons, dialogs, the run bar and the page scaffold.

Needs ttkbootstrap 2.x (theme-aware ``icon=`` with Bootstrap Icons names).
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from tkinter import font as tkfont

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets.scrolled import ScrolledFrame, ScrolledText

__all__ = [
    "MONO_FONT",
    "MUTED",
    "OUTCOME_STYLE",
    "ActionBar",
    "CommandPreview",
    "Page",
    "ScrolledText",
    "apply_muted",
    "apply_role_styles",
    "ask_save_discard_cancel",
    "button",
    "center_on_parent",
    "confirm",
    "heading",
    "local_hotkey",
    "show_error",
]

MONO_FONT = ("Consolas" if sys.platform == "win32" else "DejaVu Sans Mono", 10)
MUTED = "Muted.TLabel"  # dim helper text; contrast follows the active theme

# Process outcome tag -> ttkbootstrap colour name (shared by every status text).
OUTCOME_STYLE = {
    "ok": "success",
    "warn": "warning",
    "error": "danger",
    "info": "info",
}


def heading(size: int = 14) -> tuple:
    """Bold variant of the theme's UI font (needs a running Tk root)."""
    return (tkfont.nametofont("TkDefaultFont").actual("family"), size, "bold")


def apply_role_styles(style: ttk.Style | None = None) -> None:
    """Configure toolbutton styles for student roles to ensure consistent text colors."""
    if style is None:
        style = ttk.Style()
    for name, color in (("Striker", "#ff2d51"), ("Special", "#4c6cb3")):
        for base in ("Toolbutton", "secondary.Toolbutton"):
            style_name = f"{name}.{base}"
            style.configure(style_name, foreground=color)
            style.map(
                style_name,
                foreground=[("disabled", style.colors.border), ("!disabled", color)],
            )


def apply_muted() -> None:
    """(Re)define muted and custom styles; runs at start and on theme switches."""
    style = ttk.Style()
    bg = style.colors.bg
    try:
        bg_lum = (int(bg[1:3], 16) + int(bg[3:5], 16) + int(bg[5:7], 16)) / 3
    except Exception:  # noqa: BLE001
        bg_lum = 0

    if bg_lum < 100:
        # Dark mode floor: clean slate silver (#9da8b6) so text is always legible
        muted_color = "#9da8b6"
    else:
        # Light mode floor: graphite (#5c6675)
        muted_color = "#5c6675"

    style.configure(MUTED, foreground=muted_color)
    apply_role_styles(style)


def button(
    master,
    text: str = "",
    icon: str | None = None,
    *,
    style: str = "outline",
    bootstyle: str | None = None,
    tip: str | None = None,
    command: Callable[[], None] | None = None,
    **options,
) -> ttk.Button:
    """A themed button with an optional Bootstrap icon and tooltip.

    No ``text`` makes it an icon-only button (give it a ``tip``). The icon
    colour follows the bootstyle, so it adapts to light/dark by itself.

    Normalizes hyphenated styles (e.g., 'primary-outline' -> 'primary outline').
    """
    if icon and not text:
        options["icon_only"] = True
    effective_style = (bootstyle or style).replace("-", " ")
    widget = ttk.Button(
        master,
        text=text,
        icon=icon,
        bootstyle=effective_style,
        command=command,
        **options,
    )
    if tip:
        ttk.ToolTip(widget, text=tip)
    return widget


def local_hotkey(action: Callable[[], object]):
    """Bind ``action`` to a dialog key without running the app's global one.

    The app registers its shortcuts with ``bind_all``, which also reaches the
    widgets of every other toplevel, so a dialog's own Esc/Ctrl+S would run
    both handlers. Returning ``"break"`` stops the event before the global
    binding (e.g. Esc closing a dialog must not also stop a running scan).
    """

    def handler(_event=None) -> str:
        action()
        return "break"

    return handler


def center_on_parent(window, parent, *, y_fraction: int = 3) -> None:
    """Centre a toplevel over ``parent`` (or the screen) and keep it on-screen."""
    window.update_idletasks()
    width, height = _window_size(window)
    if parent is not None and parent.winfo_ismapped() and parent.winfo_width() > 1:
        left, top = parent.winfo_rootx(), parent.winfo_rooty()
        parent_w, parent_h = parent.winfo_width(), parent.winfo_height()
    else:
        left = top = 0
        parent_w, parent_h = window.winfo_screenwidth(), window.winfo_screenheight()
    x = left + max(0, (parent_w - width) // 2)
    y = top + max(0, (parent_h - height) // y_fraction)
    x = min(max(0, x), max(0, window.winfo_screenwidth() - width))
    y = min(max(0, y), max(0, window.winfo_screenheight() - height))
    window.geometry(f"{width}x{height}+{x}+{y}")


def _window_size(window) -> tuple[int, int]:
    """The toplevel's size, from its geometry if set, else its requested size."""
    size = str(window.geometry()).split("+", 1)[0]
    try:
        width, height = (int(part) for part in size.split("x"))
    except ValueError:
        width = height = 0
    if width <= 1 or height <= 1:
        width, height = window.winfo_reqwidth(), window.winfo_reqheight()
    return width, height


def confirm(
    parent, title: str, message: str, *, yes: str = "Yes", style: str = "danger"
) -> bool:
    """Theme-aware yes/no question; True when ``yes`` was chosen."""
    answer = Messagebox.yesno(
        message,
        title,
        parent=parent,
        buttons=["No:secondary", f"{yes}:{style}"],
        localize=False,
    )
    return answer == yes


def ask_save_discard_cancel(
    parent,
    title: str,
    message: str,
    *,
    save: str = "Save",
    discard: str = "Discard",
) -> str:
    """Tri-state guard for unsaved work.

    Returns ``"save"``, ``"discard"`` or ``"cancel"`` - cancelling also covers
    a dismissed window, so callers can treat anything unknown as "cancel".
    """
    answer = Messagebox.yesnocancel(
        message,
        title,
        parent=parent,
        buttons=[f"{discard}:danger", f"{save}:success"],
        localize=False,
    )
    if answer == save:
        return "save"
    if answer == discard:
        return "discard"
    return "cancel"


def show_error(parent, title: str, message: str) -> None:
    Messagebox.show_error(message, title, parent=parent)


class ActionBar(ttk.Frame):
    """The window's persistent run controls.

    Two independent run buttons - the scanner and the selected tool - plus the
    single Stop that applies to whichever of them is running. Keeping both here
    (instead of inside a tab) means a scan never needs a tab change first, and
    "run a tool" can never be mistaken for "run the scanner".
    """

    def __init__(self, master, *, on_run_scanner, on_run_tool, on_stop):
        super().__init__(master, padding=(10, 6))
        self.scanner_run = button(
            self,
            "Run Scanner",
            "radar",
            style="primary",
            command=on_run_scanner,
            tip="Run main.py with the saved settings (F5) - works from any tab",
        )
        self.stop = button(
            self,
            "Stop",
            "stop-fill",
            style="danger",
            command=on_stop,
            tip="Stop the running command (F2 / Esc)",
        )
        self.stop.configure(state="disabled")
        self.tool_label = ttk.Label(self, text="Tool:", style=MUTED)
        # A fixed width keeps the scanner controls still while the selected
        # tool (and therefore this button's caption) changes.
        self.tool_run = button(
            self,
            "Run tool",
            "play-fill",
            style="success",
            command=on_run_tool,
            width=20,
            tip="Run the tool selected in the Tools tab (F6)",
        )
        self.hint = ttk.Label(
            self, text="F5 scanner  ·  F6 tool  ·  F2 / Esc stop", style=MUTED
        )

        self.scanner_run.pack(side="left")
        self.stop.pack(side="left", padx=(6, 0))
        ttk.Separator(self, orient="vertical").pack(side="left", fill="y", padx=14)
        self.tool_label.pack(side="left", padx=(0, 6))
        self.tool_run.pack(side="left")
        self.hint.pack(side="right")

    def set_tool(self, tool) -> None:
        self.tool_run.configure(text=f"Run {tool.label}")

    def set_running(self, running: bool) -> None:
        self.scanner_run.configure(state="disabled" if running else "normal")
        self.tool_run.configure(state="disabled" if running else "normal")
        self.stop.configure(state="normal" if running else "disabled")


class Page(ttk.Frame):
    """A scrolling page with a title, a subtitle and stacked cards.

    Subclasses add content with :meth:`card`; the scrollbar only appears when
    the content overflows, and :meth:`footer` pins a bar underneath.
    """

    def __init__(self, master, title: str, subtitle: str = ""):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        scroll = ScrolledFrame(self, auto_hide=True, padding=(22, 18))
        scroll.grid(row=0, column=0, sticky="nsew")
        self._scroll = scroll

        self.title_row = ttk.Frame(scroll)
        self.title_row.pack(fill="x")
        ttk.Label(self.title_row, text=title, font=heading(17)).pack(side="left")
        ttk.Separator(scroll, orient="horizontal").pack(fill="x", pady=(11, 12))
        if subtitle:
            ttk.Label(
                scroll,
                text=subtitle,
                style=MUTED,
                wraplength=800,
                justify="left",
            ).pack(anchor="w", pady=(0, 15))

    def footer(self) -> ttk.Frame:
        """A bar pinned under the scrolling area (always visible)."""
        bar = ttk.Frame(self, padding=(18, 8))
        bar.grid(row=1, column=0, sticky="ew")
        return bar

    def card(self, title: str) -> ttk.Labelframe:
        frame = ttk.Labelframe(self._scroll, text=title, padding=(16, 12))
        frame.pack(fill="x", pady=(0, 14))
        frame.columnconfigure(1, weight=1)
        return frame

    def command_card(self) -> tuple[ttk.Labelframe, CommandPreview]:
        card = self.card("Command")
        preview = CommandPreview(card)
        preview.grid(row=0, column=0, columnspan=2, sticky="ew")
        return card, preview


class CommandPreview(ttk.Entry):
    """Read-only (but selectable/copyable) one-line command display."""

    def __init__(self, master):
        super().__init__(master, font=MONO_FONT, state="readonly")

    def set(self, text: str) -> None:
        self.configure(state="normal")
        self.delete(0, "end")
        self.insert(0, text)
        self.configure(state="readonly")
