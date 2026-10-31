"""Scrolling log panel with header controls and a level filter.

Every entry (up to ``MAX_LOG_LINES``) is kept in ``_entries`` and the ones the
level filter allows are rendered, so changing the filter re-renders instead of
only affecting new lines. Copy/Save work on what is currently shown. Live
progress is not shown here; it goes to the status bar.
"""

from __future__ import annotations

import time
import tkinter as tk
from collections.abc import Callable
from pathlib import Path

import ttkbootstrap as ttk

from gui import folders
from gui.process import ANSI_ESCAPE_RE, TAG_SEVERITY
from gui.ui import MONO_FONT, MUTED, ScrolledText, button, heading
from src.core.paths import Path_Config

MAX_LOG_LINES = 4000
TRIM_SLACK = 400  # trim in one go once this far over, not on every line
INSERT_CHUNK = 500  # entries per Text.insert call
LOG_BG, LOG_FG = "#10161d", "#d7dde5"

# Level filter label -> the lowest severity that is shown.
LEVEL_FILTERS = {"All": 0, "Debug+": 10, "Info+": 20, "Warning+": 30, "Error": 40}

# The log is dark in both themes (it is monospaced child output).
TAG_COLOURS = {
    "info": LOG_FG,
    "plain": LOG_FG,
    "debug": "#7c8798",
    "dim": "#7c8798",
    "cmd": "#7fd1ff",
    "ok": "#79d17f",
    "warn": "#e8c07d",
    "error": "#ff7b72",
    "report": "#8fb8d8",
    "header": "#7fd1ff",
}


class LogPanel(ttk.Frame):
    def __init__(
        self,
        master,
        *,
        on_toggle_maximize: Callable[[], None],
        on_toggle_collapse: Callable[[], None],
        on_open_folder: Callable[[str], None],
    ):
        super().__init__(master, padding=(6, 4))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._entries: list[tuple[str, str]] = []  # (text, tag), unfiltered
        self._collapsed = False
        self.autoscroll = tk.BooleanVar(value=True)
        # The child no longer stamps its own lines, so the panel is the one
        # source of timestamps.
        self.timestamps = tk.BooleanVar(value=True)
        self.level = tk.StringVar(value="All")

        self._build_header(on_toggle_maximize, on_toggle_collapse, on_open_folder)

        # height=5 is only the requested height; the pane decides the real one.
        self._view = ScrolledText(self, auto_hide=True, hbar=True, height=5, padding=0)
        self._view.grid(row=1, column=0, sticky="nsew")
        self._text: tk.Text = self._view.text
        self._text.configure(
            wrap="none",
            state="disabled",
            font=MONO_FONT,
            background=LOG_BG,
            foreground=LOG_FG,
            insertbackground=LOG_FG,
            relief="flat",
            padx=6,
            pady=4,
        )
        for tag, colour in TAG_COLOURS.items():
            self._text.tag_configure(tag, foreground=colour)
        self._text.tag_configure("header", font=(MONO_FONT[0], MONO_FONT[1], "bold"))

    def _build_header(self, maximize, collapse, open_folder) -> None:
        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        ttk.Label(header, text="LOG", style=MUTED, font=heading(9)).pack(
            side="left", padx=(2, 10)
        )
        combo = ttk.Combobox(
            header,
            textvariable=self.level,
            values=list(LEVEL_FILTERS),
            state="readonly",
            width=9,
        )
        combo.pack(side="left")
        combo.bind("<<ComboboxSelected>>", lambda _e: self._rerender())
        ttk.Checkbutton(
            header,
            text="Timestamps",
            variable=self.timestamps,
            bootstyle="round toggle",
        ).pack(side="left", padx=(12, 0))
        ttk.Checkbutton(
            header,
            text="Autoscroll",
            variable=self.autoscroll,
            bootstyle="round toggle",
        ).pack(side="left", padx=(12, 0))

        # Packed right-to-left, so they read: Clear Copy Save Logs | Max Hide
        self._collapse_button = button(
            header,
            "",
            "chevron-down",
            command=collapse,
            tip="Collapse the log (Ctrl+L)",
        )
        self._collapse_button.pack(side="right")
        button(
            header, "", "arrows-fullscreen", command=maximize, tip="Maximize the log"
        ).pack(side="right", padx=4)
        button(
            header,
            "Logs",
            "folder2-open",
            command=lambda: open_folder(folders.LOGS),
            tip="Open the logs folder",
        ).pack(side="right", padx=(0, 4))
        button(
            header,
            "Save",
            "floppy-fill",
            command=self.save_to_file,
            tip="Save the shown log to logs/",
        ).pack(side="right", padx=(0, 4))
        button(
            header, "Copy", "clipboard", command=self.copy_all, tip="Copy the shown log"
        ).pack(side="right", padx=(0, 4))
        button(
            header,
            "Clear",
            "trash3-fill",
            style="danger",
            command=self.clear,
            tip="Clear the log",
        ).pack(side="right", padx=(0, 4))

    # ------------------------------------------------------------------
    def set_collapsed(self, collapsed: bool) -> None:
        """Hide the log body, leaving only the header row."""
        if collapsed == self._collapsed:
            return
        self._collapsed = collapsed
        (self._view.grid_remove if collapsed else self._view.grid)()
        self._collapse_button.configure(
            icon="chevron-up" if collapsed else "chevron-down"
        )

    def focus_text(self) -> None:
        self._text.focus_set()

    def append(self, text: str, tag: str = "info") -> None:
        self.append_many([(text, tag)])

    def append_many(self, items: list[tuple[str, str]]) -> None:
        """Append entries with one widget update (the app batches queue drains)."""
        stamp = f"[{time.strftime('%H:%M:%S')}] " if self.timestamps.get() else ""
        minimum = LEVEL_FILTERS[self.level.get()]
        shown: list[str] = []  # alternating text, tag for Text.insert
        for text, tag in items:
            if "\x1b" in text:  # catch-all for stray styling codes
                text = ANSI_ESCAPE_RE.sub("", text)
            if not text:
                continue
            tag = tag if tag in TAG_COLOURS else "info"
            line = stamp + text
            self._entries.append((line, tag))
            if (TAG_SEVERITY.get(tag) or minimum) >= minimum:
                shown += (line + "\n", tag)
        # Keep the backing store bounded even if the current severity filter
        # hides every new message. Otherwise it grows forever until the user
        # changes the filter or a matching entry arrives.
        overflow = max(0, len(self._entries) - MAX_LOG_LINES)
        if overflow and overflow <= TRIM_SLACK:
            overflow = 0
        dropped = self._entries[:overflow] if overflow else []
        if overflow:
            del self._entries[:overflow]
        if not shown and not dropped:
            return

        widget = self._text
        widget.configure(state="normal")
        for start in range(0, len(shown), INSERT_CHUNK * 2):
            widget.insert("end", *shown[start : start + INSERT_CHUNK * 2])
        if dropped:
            visible = sum(self._passes_filter(tag) for _, tag in dropped)
            if visible:
                widget.delete("1.0", f"{visible + 1}.0")
        widget.configure(state="disabled")
        if self.autoscroll.get():
            widget.see("end")

    def clear(self) -> None:
        self._entries.clear()
        self._rerender()

    def copy_all(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self._text.get("1.0", "end-1c"))
        self.append("Log copied to clipboard.", "dim")

    def save_to_file(self) -> Path | None:
        """Write the log currently shown to a timestamped file in ``logs/``."""
        Path_Config.ensure_directories()
        path = Path_Config.LOGS_DIR / f"gui_log_{time.strftime('%Y%m%d-%H%M%S')}.txt"
        try:
            path.write_text(self._text.get("1.0", "end-1c") + "\n", encoding="utf-8")
        except OSError as exc:
            self.append(f"Could not write the log file: {exc}", "error")
            return None
        self.append(f"Log written to {path}", "dim")
        return path

    # ------------------------------------------------------------------
    def _passes_filter(self, tag: str) -> bool:
        severity = TAG_SEVERITY.get(tag)
        return severity is None or severity >= LEVEL_FILTERS[self.level.get()]

    def _rerender(self) -> None:
        """Repaint from ``_entries`` (after a filter change or Clear)."""
        widget = self._text
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        parts = [
            part
            for text, tag in self._entries
            if self._passes_filter(tag)
            for part in (text + "\n", tag)
        ]
        for start in range(0, len(parts), INSERT_CHUNK * 2):
            widget.insert("end", *parts[start : start + INSERT_CHUNK * 2])
        widget.configure(state="disabled")
        if self.autoscroll.get():
            widget.see("end")
