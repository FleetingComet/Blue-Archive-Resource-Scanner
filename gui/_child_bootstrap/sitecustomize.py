"""sitecustomize for scanner children started by the GUI.

Loaded automatically (via ``PYTHONPATH``) in every child process the GUI
spawns. It only activates when the GUI is the parent (``BA_SCANNER_GUI`` set),
so plain terminal runs are untouched.

Why:
- On Windows, when Rich's stdout is a pipe, ``GetConsoleMode`` fails and Rich
  falls back to legacy Win32 rendering - colors are then applied to the real
  console and the pipe receives plain text. The GUI needs ANSI codes in the
  pipe to colorize its log panel, so legacy mode is disabled here and
  ``FORCE_COLOR`` (set by the GUI) forces colors on.
- ``FORCE_COLOR`` also makes Rich treat the pipe as a terminal, so live widgets
  (``Progress``, ``Status``) animate: they repaint their frame in place many
  times a second, which a log widget cannot show. Those frames are sent down
  the GUI's progress channel instead (see ``PROGRESS_PREFIX`` in
  ``gui/process.py``): the panel paints them on one live status row and the log
  below stays records-only.
"""

import functools
import os
import sys
import threading

# Keep in sync with gui/process.py. This file runs before the project is
# importable, so the constant is repeated rather than imported.
_PROGRESS_PREFIX = "__progress__"


def _force_ansi_console() -> None:
    try:
        import rich.console

        # Windows: never fall back to the legacy Win32 renderer, which
        # bypasses the pipe and makes colours invisible to the log.
        rich.console.detect_legacy_windows = lambda: False  # type: ignore[assignment]
    except Exception:  # noqa: BLE001, S110 - never break the child over this
        pass


def _send_frame(frame: str) -> None:
    """Hand one progress frame to the GUI in a single, self-contained write."""
    try:
        sys.stdout.write(f"{_PROGRESS_PREFIX}{frame}\n")
        sys.stdout.flush()
    except Exception:  # noqa: BLE001, S110 - the GUI must never break a scan
        pass


class _FrameThread(threading.Thread):
    """Repaint a live widget at its own rate, the way a terminal would."""

    def __init__(self, live, refresh_per_second: float) -> None:
        super().__init__(daemon=True)
        self._live = live
        self._interval = 1.0 / refresh_per_second
        self._done = threading.Event()

    def stop(self) -> None:
        self._done.set()

    def run(self) -> None:
        while not self._done.wait(self._interval):
            self._live.refresh()


def _send_live_frames_to_gui() -> None:
    """Route ``Live`` repaints to the GUI's status row instead of stdout.

    ``Live`` (and therefore ``Progress``/``Status``) normally repaints its
    frame in place through render hooks and cursor moves; a pipe has neither,
    so every repaint used to arrive as a log line. Rendering the frame to text
    and pushing it down the progress channel keeps the animation (the panel
    updates one row) and keeps the log free of it.
    """
    import rich.live

    def frame(self) -> str:
        options = self.console.options
        lines = self.console.render_lines(self.renderable, options, pad=False)
        return " ".join(
            "".join(segment.text for segment in line) for line in lines
        ).strip()

    def start(self, refresh: bool = False) -> None:
        # No hidden cursor, stdout redirection or render hooks: only the
        # frames pushed below reach the GUI.
        if self._started:
            return
        self._started = True
        if refresh:
            self.refresh()
        if self.auto_refresh:
            self._refresh_thread = _FrameThread(self, self.refresh_per_second)
            self._refresh_thread.start()

    def stop(self) -> None:
        if not self._started:
            return
        self._started = False
        thread, self._refresh_thread = self._refresh_thread, None
        if thread is not None:
            thread.stop()
        if self.transient:
            _send_frame("")  # clear the status row
        else:
            self.refresh()

    def refresh(self) -> None:
        _send_frame(frame(self))

    rich.live.Live.start = start
    rich.live.Live.stop = stop
    rich.live.Live.refresh = refresh


def _drop_child_timestamps() -> None:
    """Let the panel own the timestamps.

    Rich stamps every record with its own clock, and the panel prefixes its
    time too, so each line carried two times. The panel's "Timestamps" toggle
    is the single source of truth; the scanner's file log keeps its format.
    """
    import rich.logging

    original_init = rich.logging.RichHandler.__init__

    @functools.wraps(original_init)
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("show_time", False)
        original_init(self, *args, **kwargs)

    rich.logging.RichHandler.__init__ = __init__


if os.environ.get("BA_SCANNER_GUI") == "1":
    _force_ansi_console()
    _drop_child_timestamps()
    _send_live_frames_to_gui()
