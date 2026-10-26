"""Child-process plumbing: output cleaning, level tagging, ProcessManager.

The :class:`ProcessManager` runs *one* child process at a time and streams
its stdout into a caller-supplied sink (the app's log queue). It also
escalates a user stop from ``terminate()`` to ``kill()`` if the child does
not exit in time.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time

# Reserved log tag for control messages (see gui.app._handle_log_item).
CONTROL_TAG = "__control__"

# Reserved log tag for the child's live progress frames (see gui.app).
PROGRESS_TAG = "progress"

# Prefix the child writes in front of every progress frame. The child side
# lives in gui/_child_bootstrap/sitecustomize.py - keep the two in sync.
PROGRESS_PREFIX = "__progress__"

# Width GUI children render at. Rich wraps to the console width, and a pipe
# reports none (80), which broke long messages across several log lines.
CHILD_CONSOLE_WIDTH = 200

# Seconds between terminate() and the kill() escalation.
STOP_KILL_DELAY_S = 5.0

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")

LEVEL_TAGS = {
    "DEBUG": "debug",
    "INFO": "info",
    "WARNING": "warn",
    "ERROR": "error",
    "CRITICAL": "error",
}
LEVEL_RE = re.compile(r"\b(DEBUG|INFO|WARNING|ERROR|CRITICAL)\b")

# Severity of the level tags, for the log panel's level filter. Tags missing
# from this map are not log levels (a colour-rich message, a traceback body,
# the panel's own notices) and are never filtered out.
TAG_SEVERITY = {"debug": 10, "info": 20, "warn": 30, "error": 40}

# Child output that is not a log record at all: plain prints, CLI help, table
# output. It carries no level, so the panel's level filter always shows it.
PLAIN_TAG = "plain"
TRACEBACK_RE = re.compile(
    r"(Traceback \(most recent call last\)|\b\w*Error\b|\bException\b)"
)

# ANSI SGR (Select Graphic Rendition) sequences, e.g. "\x1b[31m".
_SGR_RE = re.compile(r"\x1b\[([0-9;]*)m")

# Basic foreground codes -> log tag. 2 is rich's "dim" attribute; 30/90 are
# black/grey (also reads as dim).
_BASIC_FG_TAGS: dict[int, str] = {
    2: "dim",
    30: "dim",
    90: "dim",
    31: "error",
    91: "error",
    32: "ok",
    92: "ok",
    33: "warn",
    93: "warn",
    34: "cmd",
    94: "cmd",
    35: "report",
    95: "report",
    36: "cmd",
    96: "cmd",
}

# Classic VGA-16 approximations for the low end of the 256-colour palette.
_VGA16 = (
    (0, 0, 0),
    (170, 0, 0),
    (0, 170, 0),
    (170, 85, 0),
    (0, 0, 170),
    (170, 0, 170),
    (0, 170, 170),
    (170, 170, 170),
    (85, 85, 85),
    (255, 85, 85),
    (85, 255, 85),
    (255, 255, 85),
    (85, 85, 255),
    (255, 85, 255),
    (85, 255, 255),
    (255, 255, 255),
)


def _nearest_tag(red: int, green: int, blue: int) -> str | None:
    """Map an RGB colour to the closest log tag (white stays neutral)."""
    low, high = min(red, green, blue), max(red, green, blue)
    if high - low <= 28:  # greyscale
        return "dim" if (red + green + blue) / 3 < 200 else None
    if blue == high:
        return "report" if red >= green and red > 100 else "cmd"
    if red == high and green >= blue:
        return "warn" if green > 60 else "error"
    if green == high:
        return "ok"
    return "error"


def _xterm256_to_rgb(index: int) -> tuple[int, int, int]:
    if index < 16:
        return _VGA16[index % 16]
    if index < 232:
        slot = index - 16
        return tuple(
            0 if channel == 0 else 55 + channel * 40
            for channel in (slot // 36, (slot % 36) // 6, slot % 6)
        )  # type: ignore[return-value]
    grey = 8 + (index - 232) * 10
    return grey, grey, grey


def _first_style_tag(raw: str) -> str | None:
    """Return the log tag of the first definite colour in ``raw``'s SGR codes.

    Neutral codes (bold, reset, default foreground) are skipped so a line
    styled ``[bold green]text[/][default]plain`` still resolves to ``ok``.
    """
    for match in _SGR_RE.finditer(raw):
        parts = match.group(1).split(";")
        index, count = 0, len(parts)
        while index < count:
            try:
                code = int(parts[index] or "0")
            except ValueError:
                break
            if code in (38, 48) and index + 1 < count:
                mode = parts[index + 1]
                if mode == "5" and index + 2 < count:  # 38;5;N
                    if code == 38 and (
                        tag := _nearest_tag(
                            *_xterm256_to_rgb(int(parts[index + 2] or "0"))
                        )
                    ):
                        return tag
                    index += 3
                    continue
                if mode == "2" and index + 4 < count:  # 38;2;R;G;B
                    if code == 38 and (
                        tag := _nearest_tag(
                            *(
                                int(value or "0")
                                for value in parts[index + 2 : index + 5]
                            )
                        )
                    ):
                        return tag
                    index += 5
                    continue
                index += 1
                continue
            tag = _BASIC_FG_TAGS.get(code)
            if tag is not None:
                return tag
            index += 1
    return None


def clean_output_line(raw: str) -> tuple[str | None, str | None]:
    """Normalise one line of child output.

    Returns ``(text, style_tag)``: ``\\r`` progress redraws collapse to their
    last segment, all ANSI escape sequences are removed, blank lines become
    ``(None, None)``, and ``style_tag`` is the log tag for the first colour
    styled onto the line (``None`` when colourless).
    """
    style_tag = _first_style_tag(raw)
    text = ANSI_ESCAPE_RE.sub("", raw)
    segments = [segment for segment in text.split("\r") if segment.strip()]
    return (segments[-1].rstrip() if segments else None), style_tag


def tag_for_output_line(line: str) -> str:
    """Pick a log tag for one line of child output.

    A line carrying no level and no colour is not a log record, so it gets
    ``PLAIN_TAG`` and the panel's level filter never hides it.
    """
    match = LEVEL_RE.search(line)
    if match:
        return LEVEL_TAGS[match.group(1)]
    if TRACEBACK_RE.search(line):
        return "error"
    return PLAIN_TAG


def child_env() -> dict[str, str]:
    """Env for children: UTF-8 + unbuffered output, and ANSI colours forced on
    so the log panel can colourize what Rich/`cli` intended to print.

    ``PYTHONPATH`` points at ``gui/_child_bootstrap`` so Python loads its
    ``sitecustomize.py``, which disables Rich's legacy-Windows console mode
    (that mode colours via the Win32 API and sends no ANSI codes down a pipe)
    and routes Rich's live frames to the panel's status row.

    ``COLUMNS`` widens the child's Rich console: a pipe reports no size, so
    Rich would otherwise wrap messages at 80 columns and split them over
    several log lines.
    """
    bootstrap_dir = _project_root() / "gui" / "_child_bootstrap"
    existing = os.environ.get("PYTHONPATH", "")
    paths = [str(bootstrap_dir)]
    if existing:
        paths.append(existing)
    return {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONUNBUFFERED": "1",
        "FORCE_COLOR": "1",
        "COLUMNS": str(CHILD_CONSOLE_WIDTH),
        "BA_SCANNER_GUI": "1",
        "PYTHONPATH": os.pathsep.join(paths),
    }


def popen_creationflags() -> int:
    """No stray console window when the panel is launched with pythonw."""
    if sys.platform == "win32":
        return subprocess.CREATE_NO_WINDOW
    return 0


def format_duration(seconds: float) -> str:
    """Human duration: ``12s``, ``2m 34s``, ``1h 2m 3s``."""
    total = int(seconds)
    if total >= 3600:
        return f"{total // 3600}h {(total % 3600) // 60}m {total % 60}s"
    if total >= 60:
        return f"{total // 60}m {total % 60}s"
    return f"{total}s"


def outcome(
    label: str, code: int | None, stopped: bool, seconds: float
) -> tuple[str, str]:
    """``(text, tag)`` describing how a command ended.

    The single source of the wording: the log line and the page's "Last run"
    result both come from here.
    """
    suffix = f" after {format_duration(seconds)}" if seconds else ""
    if stopped:
        return f"{label} stopped by user{suffix}.", "warn"
    if code == 0:
        return f"{label} finished successfully{suffix}.", "ok"
    return f"{label} exited with code {code}{suffix}.", "error"


class ProcessManager:
    """Run one child at a time and stream its output line by line.

    ``emit`` is the thread-safe sink every message goes through (the app's
    log queue). Finishing always emits a ``__done__`` control message carrying
    ``{"label", "code", "stopped"}`` as JSON, so the app can reset its UI and
    show the outcome on the Tk main loop.
    """

    def __init__(self, emit):
        self._emit = emit
        self._process: subprocess.Popen | None = None
        self._label = ""
        self._started = 0.0
        self._user_stopped = False
        self._kill_timer: threading.Timer | None = None

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def start(self, label: str, cmd: list[str]) -> bool:
        """Start ``cmd``; returns False (logging why) when nothing was started."""
        if self.running:
            self._emit(
                f"{self._label} is still running - stop it before starting a new command.",
                "warn",
            )
            return False

        self._cancel_kill_timer()
        self._emit(f"$ {' '.join(cmd)}", "cmd")

        try:
            self._process = subprocess.Popen(
                cmd,
                cwd=str(_project_root()),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=child_env(),
                creationflags=popen_creationflags(),
            )
        except OSError as exc:
            self._emit(f"Failed to start {label}: {exc}", "error")
            self._process = None
            return False

        self._label = label
        self._started = time.time()
        self._user_stopped = False
        threading.Thread(target=self._pump, args=(self._process,), daemon=True).start()
        return True

    def stop(self, *, user_initiated: bool = True) -> None:
        """Terminate the child, escalating to kill() after a grace period."""
        process = self._process
        if process is None or process.poll() is not None:
            return
        self._cancel_kill_timer()
        if user_initiated:
            self._user_stopped = True
        self._emit("Stopping… (terminating the child process)", "warn")
        try:
            process.terminate()
        except OSError as exc:
            self._emit(f"Could not stop {self._label}: {exc}", "error")
            return
        self._kill_timer = threading.Timer(STOP_KILL_DELAY_S, self._force_kill)
        self._kill_timer.daemon = True
        self._kill_timer.start()

    def _force_kill(self) -> None:
        process = self._process
        if process is None or process.poll() is not None:
            return
        self._emit(
            f"{self._label} did not exit within {int(STOP_KILL_DELAY_S)}s - killing it.",
            "warn",
        )
        try:
            process.kill()
        except OSError as exc:
            self._emit(f"Could not kill {self._label}: {exc}", "error")

    def _cancel_kill_timer(self) -> None:
        if self._kill_timer is not None:
            self._kill_timer.cancel()
            self._kill_timer = None

    def _pump(self, process: subprocess.Popen) -> None:
        """Worker thread: forward the child's stdout into the emit sink."""
        previous_tag = "info"
        try:
            if process.stdout is not None:
                for raw in process.stdout:
                    if raw.startswith(PROGRESS_PREFIX):
                        # A live progress frame: the panel paints it on the
                        # status row instead of adding a log line.
                        frame, _ = clean_output_line(raw[len(PROGRESS_PREFIX) :])
                        self._emit(frame or "", PROGRESS_TAG)
                        continue

                    line, style_tag = clean_output_line(raw)
                    if line is None:
                        continue
                    if LEVEL_RE.search(line):
                        # A log record: its own level is more useful than the
                        # colour Rich styled it with (and the level filter
                        # needs to know it).
                        tag = tag_for_output_line(line)
                    elif style_tag is not None:
                        # The child explicitly coloured this line - honour it.
                        tag = style_tag
                    else:
                        tag = tag_for_output_line(line)
                        # Keep indented traceback bodies on the error colour.
                        if previous_tag == "error" and line[:1] in (" ", "\t"):
                            tag = "error"
                    previous_tag = tag
                    self._emit(line, tag)
        finally:
            self._cancel_kill_timer()
            code = process.wait()
            self._process = None
            text, tag = outcome(
                self._label, code, self._user_stopped, time.time() - self._started
            )
            self._emit(text, tag)
            # The app shows the same text on the page that started the run.
            self._emit("__done__" + json.dumps({"text": text, "tag": tag}), CONTROL_TAG)


def _project_root():
    from src.core.paths import Path_Config

    return Path_Config.PROJECT_ROOT
