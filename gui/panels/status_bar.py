"""Bottom status bar: state, running command, live progress, context.

The child's live progress frame lands here (not in the log) so it stays
visible while the log is collapsed or maximized.

Each field has a fixed character width (and ellipsis truncation), so a longer
state message or command can never push the neighbouring fields sideways.
"""

from __future__ import annotations

import ttkbootstrap as ttk

from gui.process import ANSI_ESCAPE_RE
from gui.ui import MONO_FONT, MUTED

STATE_WIDTH = 30
COMMAND_WIDTH = 36
PROGRESS_WIDTH = 28
CONTEXT_WIDTH = 34


def _shorten(text: str, width: int) -> str:
    text = " ".join(str(text).split())  # keep it one line
    return text if len(text) <= width else f"{text[: width - 1]}…"


class StatusBar(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=(10, 4))
        self._state = ttk.Label(
            self, text="● Idle", bootstyle="success", width=STATE_WIDTH
        )
        self._command = ttk.Label(self, style=MUTED, width=COMMAND_WIDTH)
        self._progress = ttk.Label(
            self, bootstyle="info", font=MONO_FONT, width=PROGRESS_WIDTH
        )
        self._context = ttk.Label(self, style=MUTED, width=CONTEXT_WIDTH, anchor="e")
        self._state.grid(row=0, column=0, sticky="w")
        self._command.grid(row=0, column=1, sticky="w", padx=(12, 0))
        self._progress.grid(row=0, column=2, sticky="w", padx=(12, 0))
        self._context.grid(row=0, column=3, sticky="e")
        self.columnconfigure(3, weight=1)

    def set_state(self, text: str, colour: str = "success") -> None:
        self._state.configure(text=_shorten(text, STATE_WIDTH), bootstyle=colour)

    def set_command(self, text: str) -> None:
        self._command.configure(text=_shorten(text, COMMAND_WIDTH))

    def set_progress(self, text: str) -> None:
        """Show one live progress frame (``""`` clears it)."""
        clean = ANSI_ESCAPE_RE.sub("", text)
        self._progress.configure(text=_shorten(clean, PROGRESS_WIDTH))

    def set_context(self, text: str) -> None:
        self._context.configure(text=_shorten(text, CONTEXT_WIDTH))
