"""Main window.

Shell: a command bar (context + quick actions), a notebook (Scanner, Data,
Tools), a persistent action bar carrying the scanner's Run and the selected
tool's Run, the log as a collapsible/maximizable bottom panel and a status bar
with state and live progress.

The scanner and the tools are executed from separate buttons that are always
reachable, so neither needs a tab change first. This module also owns the
shared plumbing: the queue bridging worker threads to Tk, the child-process
manager, the Data tab's unsaved-edit guards, hotkeys and the dependency check.
"""

from __future__ import annotations

import argparse
import json
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

import ttkbootstrap as ttk

from gui import folders, window_state
from gui.metadata import project_display_name
from gui.panels.about import show_about
from gui.panels.data_page import DataPage
from gui.panels.log import LogPanel
from gui.panels.overview import OverviewPage, platform_short, scanner_flags
from gui.panels.settings import DEFAULT_SCREENS, SettingsDialog
from gui.panels.status_bar import StatusBar
from gui.panels.tools_tab import ToolsTab
from gui.process import (
    ANSI_ESCAPE_RE,
    CONTROL_TAG,
    PROGRESS_TAG,
    ProcessManager,
    format_duration,
)
from gui.registry import SELECTABLE_SCREENS, TOOLS
from gui.theme import apply_title_bar, theme_mode, theme_name
from gui.ui import (
    MUTED,
    OUTCOME_STYLE,
    ActionBar,
    apply_muted,
    button,
    confirm,
    heading,
    show_error,
)
from src.core.config import AppSettings, Config
from src.core.paths import Path_Config
from src.utils.cli import cli as cli_module
from src.utils.cli.config_utils import load_screens_from_config, write_screen_config
from src.utils.device.adb.adb_controller import list_adb_devices

try:
    from pynput import keyboard
except Exception:  # noqa: BLE001 - no X11/Wayland session, or pynput not installed
    keyboard = None

MAIN_ENTRY = Path_Config.PROJECT_ROOT / "main.py"
WINDOW_TITLE = project_display_name()
TAB_SCANNER, TAB_DATA, TAB_TOOLS = 0, 1, 2
TAB_LABELS = (("Scanner", "radar"), ("Data", "table"), ("Tools", "tools"))

# Each pane keeps at least this many pixels; a collapsed log keeps its header.
MIN_PANE_HEIGHT = 140
COLLAPSED_LOG_HEIGHT = 44
LOG_PANE_SHARE = 0.3  # of the pane area, when no usable split was saved

# Queue pump: drain in batches (one widget update per batch, not per line) and
# poll faster only while output is flowing.
POLL_BUSY_MS, POLL_IDLE_MS = 30, 120
MAX_ITEMS_PER_POLL = 400  # keeps one poll short so the UI stays responsive

# Three explicit log states instead of a bare sash position: a position of 0
# once hid a pane for good, and none of these can express an invisible pane.
LOG_EXPANDED, LOG_MAXIMIZED, LOG_COLLAPSED = "expanded", "maximized", "collapsed"


def _clamp_split(saved: object, height: int) -> int:
    """Log pane height for ``height``, keeping both panes usable."""
    if height <= 2 * MIN_PANE_HEIGHT:
        return max(0, height // 2)
    low, high = MIN_PANE_HEIGHT, height - MIN_PANE_HEIGHT
    if isinstance(saved, int) and low <= saved <= high:
        return saved
    return min(max(int(height * LOG_PANE_SHARE), low), high)


def _command_label(cmd: list[str]) -> str:
    """Short form of a command line for the status bar."""
    parts = cmd[1:]
    if parts and parts[0].endswith(".py"):
        parts = [Path(parts[0]).name, *parts[1:]]
    return " ".join(parts)


class ControlPanel(ttk.Window):
    """Top-level window wiring the panels and the background work together."""

    def __init__(self, debug: bool = False):
        self._saved = window_state.load()
        # The remote artwork root lives in gui_state.json (not AppSettings), and
        # must be in place before the Data tab's image service starts loading.
        self._dark = self._saved.get("theme") == "dark"
        super().__init__(themename=theme_name(self._dark), title=WINDOW_TITLE)
        apply_muted()
        # A Tk toplevel has no parent HWND until it is mapped, so defer the
        # title-bar colour until the window is actually viewable (the toggle
        # path can call it directly because the window is already up).
        self.after(100, self._apply_title_bar_when_ready)
        self.minsize(1000, 660)
        self.geometry("1200x820")

        # Worker threads / child processes feed this; the Tk loop drains it.
        # Items are (text, tag); with CONTROL_TAG the text is a callable (run
        # on the Tk thread) or the process manager's "__done__" message.
        self._log_queue: queue.Queue[tuple[object, str]] = queue.Queue()
        self._processes = ProcessManager(self._queue_log)
        self._hotkey_listener = None
        self._settings_dialog: SettingsDialog | None = None
        self._about_open = False
        self._debug_preset = debug  # presets the debug checkbox when Settings opens

        self._run_started = 0.0
        self._elapsed_job: str | None = None
        self._poll_job: str | None = None
        self._log_state = LOG_EXPANDED
        self._log_height: int | None = None  # expanded height in pixels
        self._running_tool: str | None = None  # key of the tool being run, if any
        self._running_kind: str | None = None  # "scanner" | "tool"
        self._data_dirty = False

        self._build_ui()
        self._bind_keys()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._poll_queue()
        self._append_log(WINDOW_TITLE, "header")
        self._append_log(f"Project root: {Path_Config.PROJECT_ROOT}", "dim")
        self._append_log(f"Python: {sys.executable}", "dim")
        self._append_log(
            "Hotkeys: F5 scanner · F6 tool · F2/Esc stop · Ctrl+1/2/3 tabs · Ctrl+, settings "
            "· Ctrl+O output · Ctrl+L log",
            "dim",
        )
        self._start_hotkey_listener()
        self._check_dependencies()
        self.after(50, self._restore_window_state)

    # ------------------------------------------------------------------
    # UI composition
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        bar = ttk.Frame(self, padding=(20, 12, 20, 10))
        bar.grid(row=0, column=0, sticky="ew")
        brand = ttk.Frame(bar)
        brand.pack(side="left")
        ttk.Label(
            brand,
            text=WINDOW_TITLE,
            bootstyle="info",
            font=heading(9),
        ).pack(anchor="w")
        # ttk.Label(brand, text=WINDOW_TITLE, font=heading(16)).pack(
        #     anchor="w", pady=(2, 0)
        # )
        self._context = ttk.Label(brand, style=MUTED)
        self._context.pack(anchor="w", pady=(3, 0))
        # Packed right-to-left: reads "Output  About  Settings  Theme".
        self._theme_button = button(
            bar,
            "",
            self._theme_icon(),
            command=self._toggle_theme,
            tip="Switch light / dark theme",
        )
        self._theme_button.pack(side="right")
        button(
            bar,
            "Settings",
            "gear-fill",
            command=self._open_settings,
            tip="Open settings (Ctrl+,)",
        ).pack(side="right", padx=6)
        button(
            bar,
            "About",
            "info-circle-fill",
            command=self._open_about,
            tip="About this application",
        ).pack(side="right", padx=(0, 6))
        button(
            bar,
            "Output",
            "folder2-open",
            command=lambda: self._open_folder(folders.OUTPUT),
            tip="Open the output folder (Ctrl+O)",
        ).pack(side="right")

        ttk.Separator(self, orient="horizontal").grid(row=0, column=0, sticky="sew")
        panes = ttk.Panedwindow(self, orient="vertical")
        panes.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 4))
        self._panes = panes

        # Main area: the Scanner / Data / Tools notebook, with the action bar
        # pinned under it. The action bar is never hidden - both Run buttons
        # stay reachable from any tab.
        main = ttk.Frame(panes)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(0, weight=1)
        self._main = main

        self._tabs = ttk.Notebook(main)
        self._tabs.grid(row=0, column=0, sticky="nsew")
        self.overview_page = OverviewPage(
            self._tabs, on_edit_settings=self._open_settings
        )
        self.data_page = DataPage(
            self._tabs,
            on_post=self._post,
            on_log=self._queue_log,
            on_dirty_changed=self._on_data_dirty_changed,
            on_file_changed=self._on_data_file_changed,
        )
        self.tools_tab = ToolsTab(
            self._tabs,
            tools=TOOLS,
            on_change=self._on_tool_changed,
            on_notice=self._queue_log,
            active_file=self.data_page.active_path,
            on_open_in_data=self._open_in_data,
        )
        for page, (label, _icon) in zip(
            (self.overview_page, self.data_page, self.tools_tab), TAB_LABELS
        ):
            self._tabs.add(page, text=f" {label}", compound="left")
        self._refresh_tab_icons()
        self._tabs.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self.action_bar = ActionBar(
            main,
            on_run_scanner=self._run_scanner,
            on_run_tool=self._run_tool,
            on_stop=self._processes.stop,
        )
        self.action_bar.grid(row=1, column=0, sticky="ew")

        panes.add(main, weight=3)
        self.log_panel = LogPanel(
            panes,
            on_toggle_maximize=lambda: self._toggle_log(LOG_MAXIMIZED),
            on_toggle_collapse=lambda: self._toggle_log(LOG_COLLAPSED),
            on_open_folder=self._open_folder,
        )
        panes.add(self.log_panel, weight=2)

        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=2, column=0, sticky="ew")

        self.tools_tab.show(TOOLS[0].key)
        self.overview_page.refresh()
        self._refresh_context()

    def _bind_keys(self) -> None:
        # bind_all so the hotkeys work no matter which widget has focus.
        bindings = {
            "<F5>": self._run_scanner,
            "<F6>": self._run_tool,
            "<F2>": self._processes.stop,
            "<Escape>": self._escape,
            "<Control-s>": self._save_data,
            "<Control-comma>": self._open_settings,
            "<Control-l>": self._focus_log,
            "<Control-o>": lambda: self._open_folder(folders.OUTPUT),
            "<Control-Key-1>": lambda: self._tabs.select(TAB_SCANNER),
            "<Control-Key-2>": lambda: self._tabs.select(TAB_DATA),
            "<Control-Key-3>": lambda: self._tabs.select(TAB_TOOLS),
        }
        for sequence, action in bindings.items():
            self.bind_all(sequence, lambda _e, action=action: action())

    def _escape(self) -> None:
        if (
            self._settings_dialog is None
        ):  # while Settings is open, Esc closes it instead
            self._processes.stop()

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------
    def _theme_icon(self) -> str:
        return "sun-fill" if self._dark else "moon-stars-fill"

    def _apply_title_bar_when_ready(self) -> None:
        """Apply the title-bar colour once Tk has a parent HWND for the window."""
        if not self.winfo_exists():
            return
        if not self.winfo_viewable():
            self.after(80, self._apply_title_bar_when_ready)
            return
        apply_title_bar(self, self._dark)

    def _toggle_theme(self) -> None:
        self._dark = not self._dark
        self.configure(cursor="watch")  # rebuilding the theme takes a moment
        self.update_idletasks()
        # ``theme_mode`` switches inside the registered family; both variants
        # come from the same accent tokens (see gui/theme.py).
        self.theme_mode = theme_mode(self._dark)
        # Things the theme engine does not recolour on its own.
        apply_muted()
        self.tools_tab.tool_list.restyle()
        self.data_page.restyle_cards()
        self._refresh_tab_icons()
        self._theme_button.configure(icon=self._theme_icon())
        apply_title_bar(self, self._dark)
        self.configure(cursor="")

    def _refresh_tab_icons(self) -> None:
        for index, (_label, icon) in enumerate(TAB_LABELS):
            self._tabs.tab(index, image=ttk.Icon(icon, 16))

    # ------------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------------
    @property
    def _tab(self) -> int:
        return self._tabs.index("current")

    def _on_tab_changed(self, _event=None) -> None:
        if self._tab == TAB_TOOLS:
            self._sync_tool_button()
            # The Data tab may have opened another file since the last look.
            self.tools_tab.refresh_files()

    def _on_tool_changed(self, tool) -> None:
        self.action_bar.set_tool(tool)

    def _sync_tool_button(self) -> None:
        self.action_bar.set_tool(self.tools_tab.tool)

    def _refresh_context(self) -> None:
        """Push the saved configuration into the top bar + status bar."""
        settings = Config.settings
        platform = platform_short(settings.target_platform.value)
        count = len(load_screens_from_config())
        sync = "data sync on" if settings.enable_sync else "offline"
        self._context.configure(
            text=f"{platform} · {count}/{len(SELECTABLE_SCREENS)} screens · {sync}"
        )
        self.status_bar.set_context(f"{platform} · {count} screens")

    def _focus_log(self) -> None:
        if self._log_state == LOG_COLLAPSED:
            self._set_log_state(LOG_EXPANDED)
        self.log_panel.focus_text()

    # ------------------------------------------------------------------
    # Settings and About dialogs
    # ------------------------------------------------------------------
    def _open_settings(self) -> None:
        if self._settings_dialog is not None:
            self._settings_dialog.lift()
            return
        self._settings_dialog = SettingsDialog(
            self,
            on_save=self._apply_settings,
            on_detect=self._detect_devices,
            on_open_folder=self._open_folder,
            on_closed=self._settings_closed,
            debug=self._debug_preset,
        )
        self._debug_preset = False

    def _settings_closed(self) -> None:
        self._settings_dialog = None

    def _open_about(self) -> None:
        if self._about_open:
            return
        self._about_open = True
        show_about(
            self,
            on_closed=lambda: setattr(self, "_about_open", False),
            on_open_folder=self._open_folder,
        )

    def _apply_settings(
        self,
        settings: AppSettings,
        screens: list,
    ) -> None:
        """Persist settings and refresh the GUI."""
        if not screens:
            screens = list(DEFAULT_SCREENS)
            self._append_log(
                "No scan targets selected - defaulting to Equipment + Items.",
                "warn",
            )

        Config.save(settings)
        write_screen_config(screens)

        self._append_log(
            "Saved config/settings.json and config/screen_config.json",
            "ok",
        )

        self.data_page.apply_image_settings(settings)

        self._append_log(
            f"Images: local only - "
            f"{settings.local_image_dir or Path_Config.local_images}",
            "dim",
        )

        self._refresh_context()
        self.overview_page.refresh()

    # ------------------------------------------------------------------
    # Running commands
    # ------------------------------------------------------------------
    def _busy(self) -> bool:
        """True when a run (or the Settings dialog) makes a new run unsafe."""
        if self._processes.running:
            self._append_log("A command is already running - stop it first.", "warn")
            return True
        return self._settings_dialog is not None

    def _run_scanner(self) -> None:
        if self._busy():
            return
        if not load_screens_from_config():
            self._append_log(
                "No scan targets selected - defaulting to Equipment + Items.", "warn"
            )
            write_screen_config(list(DEFAULT_SCREENS))
            self.overview_page.refresh()
        self._log_scanner_settings()
        cmd = [
            sys.executable,
            str(MAIN_ENTRY),
            *scanner_flags(Config.settings.enable_sync),
        ]
        self._start_process("Scanner", cmd, tool_key=None, kind="scanner")

    def _run_tool(self) -> None:
        if self._busy():
            return
        tool = self.tools_tab.tool
        page = self.tools_tab.page()
        if problem := page.validate():
            page.tkraise()
            self._tabs.select(TAB_TOOLS)
            self._append_log(f"{tool.label}: {problem}", "error")
            show_error(self, f"{tool.label} - invalid argument", problem)
            return
        if missing := page.missing_inputs():
            names = "\n".join(f"• {path}" for path in missing)
            if not confirm(
                self,
                "Missing input",
                f"{tool.label} reads files that do not exist yet:\n\n{names}\n\nRun it anyway?",
                yes="Run anyway",
            ):
                return
        if not self.data_page.prompt_save_before(f"running {tool.label}"):
            return
        self._start_process(tool.label, page.command(), tool_key=tool.key, kind="tool")

    def _log_scanner_settings(self) -> None:
        """The pre-launch report launch.py prints. capture() keeps styling
        codes on a real terminal, so they are stripped before logging."""
        try:
            with cli_module.console.capture() as capture:
                cli_module.print_settings()
            self._append_log(
                ANSI_ESCAPE_RE.sub("", capture.get()).rstrip("\n"), "report"
            )
        except Exception as exc:  # noqa: BLE001 - reporting must never block a run
            self._append_log(f"Could not render settings summary: {exc}", "warn")

    def _start_process(
        self, label: str, cmd: list[str], tool_key: str | None, *, kind: str
    ) -> None:
        Path_Config.ensure_directories()
        if not self._processes.start(label, cmd):
            return
        self._run_started = time.time()
        self._running_tool = tool_key
        self._running_kind = kind
        self.status_bar.set_progress("")
        self.status_bar.set_command(_command_label(cmd))
        self._set_running(True)
        self._tick(label)

    def _set_running(self, running: bool) -> None:
        self.action_bar.set_running(running)

    def _tick(self, label: str) -> None:
        """Live ``● Running: <label> (elapsed)`` in the status bar and title."""
        if not self._processes.running:
            return
        elapsed = format_duration(time.time() - self._run_started)
        self.status_bar.set_state(f"● Running: {label} ({elapsed})", "warning")
        self.title(f"● {label} {elapsed} — {WINDOW_TITLE}")
        self._elapsed_job = self.after(1000, self._tick, label)

    def _on_process_finished(self, text: str, tag: str) -> None:
        if self._elapsed_job is not None:
            self.after_cancel(self._elapsed_job)
            self._elapsed_job = None
        self._set_running(False)
        self.status_bar.set_progress("")
        self._refresh_title()
        self.status_bar.set_state(f"● {text}", OUTCOME_STYLE.get(tag, "success"))

        tool_key, self._running_tool = self._running_tool, None
        kind, self._running_kind = self._running_kind, None
        if tool_key is not None:
            self.tools_tab.page(tool_key).set_last_run(text, tag)
        elif kind == "scanner" and tag == "ok":
            # A successful scan: point the Data tab at what it produced.
            self.data_page.on_scan_completed(self._run_started)
        if self.focus_displayof() is None:  # long scans: nudge if in the background
            self.bell()

    # ------------------------------------------------------------------
    # Data tab glue
    # ------------------------------------------------------------------
    def _on_data_dirty_changed(self, dirty: bool) -> None:
        self._data_dirty = dirty
        self._refresh_title()

    def _on_data_file_changed(self) -> None:
        """Keep the tool pages' "open in the Data tab" marker in step."""
        tools = getattr(self, "tools_tab", None)
        if tools is not None:
            tools.refresh_files()

    def _open_in_data(self, path: Path) -> None:
        """Open ``path`` in the Data tab (used by the Tools tab's file rows)."""
        if self.data_page.open_path(path):
            self._tabs.select(TAB_DATA)

    def _refresh_title(self) -> None:
        if self._processes.running:
            return
        self.title(
            f"● Unsaved data — {WINDOW_TITLE}" if self._data_dirty else WINDOW_TITLE
        )

    def _save_data(self) -> None:
        if not self.data_page.has_unsaved_edits():
            return
        self._tabs.select(TAB_DATA)
        self.data_page.save()

    # ------------------------------------------------------------------
    # ADB detection and the dependency check (worker threads)
    # ------------------------------------------------------------------
    def _detect_devices(self) -> None:
        self._append_log("Querying `adb devices`…", "dim")

        def work() -> None:
            try:
                devices = list_adb_devices()
            except Exception as exc:  # noqa: BLE001
                self._queue_log(f"ADB detection failed: {exc}", "error")
                return
            if not devices:
                self._queue_log(
                    "No ADB targets found. Start the emulator, or run `adb connect <host:port>` first.",
                    "warn",
                )
                return
            ready = next(
                (serial for serial, state in devices if state == "device"), None
            )
            for serial, state in devices:
                self._queue_log(
                    f"  • {serial}  ({state})", "ok" if state == "device" else "warn"
                )
            serials = [serial for serial, _ in devices]
            self._post(
                lambda: self._settings_dialog
                and self._settings_dialog.set_detected_devices(serials, ready)
            )

        threading.Thread(target=work, daemon=True).start()

    def _check_dependencies(self) -> None:
        """Mirror launch.py's check, reporting into the log (a GUI has no
        stdin to answer a prompt)."""
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

        def work() -> None:
            try:
                result = subprocess.run(
                    [sys.executable, "-c", "import cv2, rapidocr"],
                    check=False,
                    cwd=str(Path_Config.PROJECT_ROOT),
                    capture_output=True,
                    text=True,
                    creationflags=flags,
                )
            except OSError as exc:
                self._queue_log(f"Dependency check failed: {exc}", "warn")
                return
            if result.returncode == 0:
                self._queue_log("Dependencies OK (rapidocr, cv2).", "ok")
            else:
                self._queue_log(
                    "Missing dependencies (rapidocr / cv2). Run "
                    "`pip install -r requirements.txt` before scanning.",
                    "error",
                )

        threading.Thread(target=work, daemon=True).start()

    def _start_hotkey_listener(self) -> None:
        """Global F2 (works while the game window has focus), like launch.py."""
        if keyboard is None:
            self._append_log(
                "pynput unavailable - F2 is disabled here, use the Stop button.", "warn"
            )
            return

        def on_press(key) -> None:
            if key == keyboard.Key.f2:
                self._post(self._processes.stop)

        try:
            self._hotkey_listener = keyboard.Listener(on_press=on_press)
            self._hotkey_listener.start()
        except Exception as exc:  # noqa: BLE001 - hook may be blocked by the OS
            self._hotkey_listener = None
            self._append_log(f"Could not start the F2 hook ({exc}).", "warn")
            return
        self._append_log(
            "The global F2 hook is active and stops a running command from any window.",
            "dim",
        )

    # ------------------------------------------------------------------
    # Log plumbing
    # ------------------------------------------------------------------
    def _queue_log(self, text: str, tag: str = "info") -> None:
        """Thread-safe: hand one (text, tag) item to the Tk main loop."""
        self._log_queue.put((text, tag))

    def _post(self, action) -> None:
        """Thread-safe: run ``action()`` on the Tk main loop."""
        self._log_queue.put((action, CONTROL_TAG))

    def _append_log(self, text: str, tag: str = "info") -> None:
        self.log_panel.append(text, tag)

    def _poll_queue(self) -> None:
        """Drain the queue in one batch: a single log update for all the lines,
        and only the newest progress frame (older ones are already stale)."""
        logs: list[tuple[str, str]] = []
        progress: str | None = None
        handled = 0

        def flush() -> None:
            nonlocal progress
            if logs:
                self.log_panel.append_many(logs)
                logs.clear()
            if progress is not None:
                self.status_bar.set_progress(progress)
                progress = None

        try:
            while handled < MAX_ITEMS_PER_POLL:
                text, tag = self._log_queue.get_nowait()
                handled += 1
                if tag == PROGRESS_TAG:
                    progress = text
                elif tag != CONTROL_TAG:
                    logs.append((text, tag))
                else:
                    flush()  # control actions see everything that came before them
                    self._run_control(text)
        except queue.Empty:
            pass
        except Exception as exc:  # noqa: BLE001 - a dead pump freezes every button
            self._append_log(f"Log pump error: {exc}", "error")
        finally:
            flush()
            delay = (
                POLL_BUSY_MS
                if handled >= MAX_ITEMS_PER_POLL
                else (POLL_IDLE_MS if not handled else 60)
            )
            # Tracked so _on_close can cancel it (avoids "invalid command name").
            self._poll_job = self.after(delay, self._poll_queue)

    def _run_control(self, message) -> None:
        if callable(message):
            message()
        elif message.startswith("__done__"):  # the process manager's finish message
            done = json.loads(message.removeprefix("__done__"))
            self._on_process_finished(done["text"], done["tag"])

    def _open_folder(self, key: str) -> None:
        if error := folders.open_folder(key):
            self._append_log(error, "error")

    # ------------------------------------------------------------------
    # Log pane layout
    # ------------------------------------------------------------------
    def _toggle_log(self, state: str) -> None:
        """Header buttons: enter ``state``, or return to expanded if already in it."""
        self._set_log_state(LOG_EXPANDED if self._log_state == state else state)

    def _set_log_state(self, state: str) -> None:
        if self._log_state == LOG_EXPANDED and state != LOG_EXPANDED:
            self._log_height = self._current_log_height()
        self._log_state = state
        self._apply_log_layout()

    def _apply_log_layout(self) -> None:
        """Put the paned window into the current log state."""
        has_main = str(self._main) in self._panes.panes()
        if self._log_state == LOG_MAXIMIZED:
            if has_main:
                self._panes.forget(self._main)  # the log becomes the only pane
        elif not has_main:
            self._panes.insert(0, self._main, weight=3)
        self.log_panel.set_collapsed(self._log_state == LOG_COLLAPSED)
        self._place_sash()

    def _place_sash(self, attempts: int = 10) -> None:
        """Set the split; Tk ignores a sash set before the panes have a size,
        so retry until the window has been laid out."""
        if self._log_state == LOG_MAXIMIZED:
            return
        self.update_idletasks()
        height = self._panes.winfo_height()
        if height < 2 * MIN_PANE_HEIGHT:
            if attempts:
                self.after(100, self._place_sash, attempts - 1)
            return
        if self._log_state == LOG_COLLAPSED:
            log_height = COLLAPSED_LOG_HEIGHT
        else:
            log_height = _clamp_split(self._log_height, height)
        self._panes.sashpos(0, height - log_height)

    def _current_log_height(self) -> int | None:
        """Height of the log pane right now (the saved one if not measurable)."""
        height = self._panes.winfo_height()
        if height > 1 and len(self._panes.panes()) == 2:
            return height - self._panes.sashpos(0)
        return self._log_height

    # ------------------------------------------------------------------
    # Window state persistence
    # ------------------------------------------------------------------
    def _save_window_state(self) -> None:
        self.update_idletasks()
        if self._log_state == LOG_EXPANDED:
            self._log_height = self._current_log_height()
        data: dict[str, object] = {
            "geometry": self.geometry(),
            "tab": self._tab,
            "tool": self.tools_tab.current,
            "log_state": self._log_state,
            "theme": "dark" if self._dark else "light",
        }
        # Only a split keeping both panes usable is worth saving.
        height = self._panes.winfo_height()
        if (
            isinstance(self._log_height, int)
            and MIN_PANE_HEIGHT <= self._log_height <= height - MIN_PANE_HEIGHT
        ):
            data["split"] = self._log_height
        active = self.data_page.active_path()
        if active is not None:
            data["data_file"] = str(active)
        window_state.save(data)

    def _restore_window_state(self) -> None:
        data = self._saved
        geometry = data.get("geometry")
        if isinstance(geometry, str) and geometry:
            fitted = window_state.fit_geometry(
                geometry, window_state.desktop_bounds(self)
            )
            if fitted is None:
                self._append_log(
                    f"Ignored an unreadable window geometry: {geometry!r}", "warn"
                )
            else:
                if fitted != geometry:
                    self._append_log(
                        f"Window geometry {geometry} was off-screen; opened at {fitted}.",
                        "warn",
                    )
                self.geometry(fitted)

        if isinstance(data.get("tool"), str):
            self.tools_tab.show(data["tool"])
        if data.get("tab") in (TAB_SCANNER, TAB_DATA, TAB_TOOLS):
            self._tabs.select(data["tab"])
        remembered = data.get("data_file")
        preferred = (
            Path(remembered) if isinstance(remembered, str) and remembered else None
        )
        self.data_page.load_initial(preferred)

        state = data.get("log_state")
        self._log_state = (
            state
            if state in (LOG_EXPANDED, LOG_MAXIMIZED, LOG_COLLAPSED)
            else LOG_EXPANDED
        )
        split = data.get("split")
        self._log_height = split if isinstance(split, int) else None
        self._apply_log_layout()

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------
    def _on_close(self) -> None:
        if (
            self._settings_dialog is not None
            and not self._settings_dialog.request_close()
        ):
            return
        if self.data_page.has_unsaved_edits() and not self.data_page.prompt_save_before(
            "closing"
        ):
            return
        if self._processes.running and not confirm(
            self,
            "Command running",
            "A command is still running. Stop it and quit?",
            yes="Stop and quit",
        ):
            return

        self._processes.stop(user_initiated=False)
        self._save_window_state()
        for job in (self._poll_job, self._elapsed_job):
            if job is not None:
                self.after_cancel(job)
        if self._hotkey_listener is not None:
            self._hotkey_listener.stop()
        self.destroy()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tkinter front-end for the Blue Archive Resource Scanner."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Preset the debug checkbox in Settings (still needs Save).",
    )
    args = parser.parse_args()
    Path_Config.ensure_directories()
    ControlPanel(debug=args.debug).mainloop()


if __name__ == "__main__":
    main()
