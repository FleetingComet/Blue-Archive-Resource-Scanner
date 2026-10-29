"""Settings: the form (``SettingsPage``) and the modal window that hosts it.

Nothing here writes to disk by itself: ``save`` validates the form and hands
the result to the app, which persists it.
"""

from __future__ import annotations

import sys
import tkinter as tk
from collections.abc import Callable
from pathlib import Path

import ttkbootstrap as ttk

from gui import folders, icons, window_state
from gui.components.file_selector import DIRECTORY, FileSelector
from gui.registry import LANGUAGES, SELECTABLE_SCREENS
from gui.ui import MUTED, Page, button, confirm, local_hotkey, show_error
from src.constant import Screen
from src.core.config import AppSettings, Config, ImageMode, TargetPlatform
from src.core.paths import Path_Config
from src.utils.cli.config_utils import load_screens_from_config

# Screens used when nothing is selected (mirrors the launcher's default).
DEFAULT_SCREENS = (Screen.EQUIPMENT, Screen.ITEMS)
DEFAULT_WAIT, DEFAULT_NAV_WAIT = "1.0", "2.0"

PLATFORM_CHOICES = [
    (
        TargetPlatform.EMULATOR,
        "Emulator on this PC (MuMu Player 12, LDPlayer, BlueStacks)",
    ),
    (TargetPlatform.DEVICE, "Real Android phone / tablet over USB or Wi-Fi"),
]
if sys.platform == "win32":  # desktop mode uses Windows-only APIs
    PLATFORM_CHOICES.insert(
        0, (TargetPlatform.DESKTOP, "PC client / desktop window (Blue Archive PC app)")
    )


class SettingsPage(Page):
    def __init__(
        self,
        master,
        *,
        on_save: Callable[[AppSettings, list[Screen], dict], None],
        on_detect: Callable[[], None],
        on_open_folder: Callable[[str], None],
    ):
        super().__init__(
            master,
            "Settings",
            "Writes config/settings.json and config/screen_config.json, the files launch.py uses.",
        )
        self._on_save = on_save
        self.dirty = False
        self._loading = False

        self.platform = tk.StringVar(value=TargetPlatform.EMULATOR.value)
        self.serial = tk.StringVar()
        self.retries = tk.StringVar()
        self.wait = tk.StringVar()
        self.nav = tk.StringVar()
        self.sync = tk.BooleanVar()
        self.debug = tk.BooleanVar()
        self.language = tk.StringVar(value=LANGUAGES[0])
        self.image_mode = tk.StringVar(value=ImageMode.HYBRID.value)
        self.local_dir = tk.StringVar()
        self.asset_base = tk.StringVar()
        self.screens = {s: tk.BooleanVar() for s in SELECTABLE_SCREENS}

        self._dirty_label = ttk.Label(self.title_row, bootstyle="warning")
        self._dirty_label.pack(side="left", padx=12)

        self._build_platform()
        self._build_adb(on_detect)
        self._build_images()
        self._build_performance()
        self._build_targets()
        self._build_extras()

        self.actions = footer = self.footer()
        self._save = button(
            footer,
            "Save",
            "check-lg",
            style="success",
            command=self.save,
            tip="Save (Ctrl+S)",
        )
        self._revert = button(
            footer,
            "Revert",
            "arrow-counterclockwise",
            style="warning",
            command=self.reload,
            tip="Discard unsaved edits",
        )
        self._save.pack(side="left")
        self._revert.pack(side="left", padx=6)
        button(
            footer,
            "Config folder",
            "folder2-open",
            command=lambda: on_open_folder(folders.CONFIG),
            tip="Open the config folder",
        ).pack(side="left", padx=(12, 0))

        for var in (
            self.platform,
            self.serial,
            self.retries,
            self.wait,
            self.nav,
            self.language,
            self.sync,
            self.debug,
            self.image_mode,
            self.local_dir,
            self.asset_base,
            *self.screens.values(),
        ):
            var.trace_add("write", self._mark_dirty)
        self.platform.trace_add("write", lambda *_: self._toggle_platform())
        self.image_mode.trace_add("write", self._images_changed)
        self.asset_base.trace_add("write", self._images_changed)
        self.reload()

    # ------------------------------------------------------------------
    # Form
    # ------------------------------------------------------------------
    def _spin(
        self, card, row: int, label: str, var, low, high, step=1, fmt=None
    ) -> None:
        ttk.Label(card, text=label).grid(row=row, column=0, sticky="w", pady=3)
        ttk.Spinbox(
            card,
            from_=low,
            to=high,
            increment=step,
            format=fmt,
            width=7,
            textvariable=var,
        ).grid(row=row, column=1, sticky="w", padx=(12, 0), pady=3)

    def _build_platform(self) -> None:
        self._platform_card = card = self.card("Target platform")
        for row, (platform, text) in enumerate(PLATFORM_CHOICES):
            ttk.Radiobutton(
                card, text=text, value=platform.value, variable=self.platform
            ).grid(row=row, column=0, columnspan=3, sticky="w", pady=2)

    def _build_adb(self, on_detect) -> None:
        self._adb_card = card = self.card("ADB connection")
        ttk.Label(
            card, text="MuMu: 16384  ·  LDPlayer / BlueStacks: 5555", style=MUTED
        ).grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(card, text="Serial (host:port or USB serial)").grid(
            row=1, column=0, sticky="w", pady=3
        )
        # Editable: doubles as a dropdown of the last detected devices.
        self._serial_combo = ttk.Combobox(card, textvariable=self.serial, width=26)
        self._serial_combo.grid(row=1, column=1, sticky="w", padx=(12, 0), pady=3)
        button(
            card,
            "Detect",
            "search",
            command=on_detect,
            tip="List connected ADB devices",
        ).grid(row=1, column=2, padx=(8, 0))
        self._spin(card, 2, "Connect retries", self.retries, 1, 50)

    def _build_images(self) -> None:
        card = self.card("Images")
        ttk.Label(
            card,
            text="Artwork shown on the Data tab (student portraits, item and equipment icons, school crests).",
            style=MUTED,
            wraplength=560,
            justify="left",
        ).grid(row=0, column=0, columnspan=3, sticky="w")
        modes = (
            (
                ImageMode.DISABLED,
                "Disabled - placeholders only; no disk or network access",
            ),
            (ImageMode.LOCAL, "Local only - read the folder below; never download"),
            (
                ImageMode.HYBRID,
                "Hybrid - local folder first, schaledb.com when a file is missing",
            ),
        )
        for row, (mode, text) in enumerate(modes, start=1):
            ttk.Radiobutton(
                card, text=text, value=mode.value, variable=self.image_mode
            ).grid(row=row, column=0, columnspan=3, sticky="w", pady=2)

        row = len(modes) + 1
        ttk.Label(card, text="Local artwork folder").grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(8, 2)
        )
        self._local_selector = FileSelector(
            card,
            mode=DIRECTORY,
            textvariable=self.local_dir,
            title="Select the local artwork folder",
            on_change=self._images_changed,
        )
        self._local_selector.grid(row=row + 1, column=0, columnspan=3, sticky="ew")
        self._images_status = ttk.Label(
            card, style=MUTED, wraplength=560, justify="left"
        )
        self._images_status.grid(
            row=row + 2, column=0, columnspan=3, sticky="w", pady=(4, 0)
        )
        button(
            card,
            "Use default folder",
            "arrow-counterclockwise",
            command=self._default_images_dir,
            tip="assets/images/local next to the scanner",
        ).grid(row=row + 3, column=0, columnspan=3, sticky="w", pady=(6, 0))

        base_row = row + 4
        ttk.Label(card, text="Remote asset base URL").grid(
            row=base_row, column=0, columnspan=3, sticky="w", pady=(12, 2)
        )
        ttk.Entry(card, textvariable=self.asset_base).grid(
            row=base_row + 1, column=0, columnspan=2, sticky="ew"
        )
        button(
            card,
            "Reset",
            "arrow-counterclockwise",
            command=lambda: self.asset_base.set(""),
            tip="Back to https://schaledb.com/images/",
        ).grid(row=base_row + 1, column=2, sticky="w", padx=(8, 0))
        ttk.Label(
            card,
            text="Where downloaded artwork is read from (hybrid mode). "
            "Leave blank for schaledb; it is saved in config/gui_state.json, "
            "not in the scanner's settings.",
            style=MUTED,
            wraplength=560,
            justify="left",
        ).grid(row=base_row + 2, column=0, columnspan=3, sticky="w", pady=(4, 0))

    def _default_images_dir(self) -> None:
        self.local_dir.set(str(Path_Config.local_images))

    def _resolved_images_dir(self) -> Path:
        raw = self.local_dir.get().strip()
        if not raw:
            return Path_Config.local_images
        path = Path(raw).expanduser()
        return path if path.is_absolute() else Path_Config.PROJECT_ROOT / path

    def _images_changed(self, *_args) -> None:
        """Update the mode-dependent hint and disable the folder while off."""
        try:
            mode = ImageMode(self.image_mode.get())
        except ValueError:
            mode = ImageMode.HYBRID
        enabled = mode is not ImageMode.DISABLED
        self._local_selector.set_enabled(enabled)
        folder = self._resolved_images_dir()
        remote = icons.normalize_base_url(self.asset_base.get())
        try:
            exists = folder.is_dir()
        except OSError:
            exists = False
        if mode is ImageMode.DISABLED:
            text = "No artwork is loaded; cards keep their placeholders."
        elif mode is ImageMode.LOCAL:
            text = (
                f"Using {folder}. Missing or unreadable files show a placeholder."
                if exists
                else f"{folder} does not exist yet - cards will show placeholders."
            )
        elif exists:
            text = (
                f"Using {folder}, then {remote} for anything missing. "
                "Downloads are cached in that folder."
            )
        else:
            text = (
                f"{folder} does not exist - everything is downloaded from {remote} "
                "and cached in that folder."
            )
        self._images_status.configure(text=text)

    def _build_performance(self) -> None:
        card = self.card("Performance")
        ttk.Label(
            card,
            text="1.0 = normal  ·  1.5 = 50% slower  ·  2.0 = double the waits. "
            "Raise navigation first if screens are misread.",
            style=MUTED,
        ).grid(row=0, column=0, columnspan=3, sticky="w")
        self._spin(card, 1, "Wait multiplier", self.wait, 0.1, 10.0, 0.1, "%.1f")
        self._spin(
            card, 2, "Screen navigation multiplier", self.nav, 0.1, 10.0, 0.1, "%.1f"
        )
        button(
            card,
            "Reset",
            "arrow-counterclockwise",
            command=self._reset_waits,
            tip="Back to 1.0 / 2.0",
        ).grid(row=1, column=2, rowspan=2, padx=(8, 0))

    def _build_targets(self) -> None:
        card = self.card("Scan targets")
        for index, screen in enumerate(SELECTABLE_SCREENS):
            ttk.Checkbutton(card, text=str(screen), variable=self.screens[screen]).grid(
                row=index // 2, column=index % 2, sticky="w", padx=(0, 28), pady=2
            )
        buttons = ttk.Frame(card)
        buttons.grid(
            row=(len(SELECTABLE_SCREENS) + 1) // 2,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(8, 0),
        )
        for text, icon, state in (
            ("Select all", "check2-all", True),
            ("Clear all", "x-circle", False),
        ):
            button(
                buttons,
                text,
                icon,
                command=lambda s=state: [v.set(s) for v in self.screens.values()],
            ).pack(side="left", padx=(0, 6))

    def _build_extras(self) -> None:
        card = self.card("Data, language & debug")
        ttk.Checkbutton(
            card,
            text="Enable online data sync (download community data on start)",
            variable=self.sync,
            bootstyle="round toggle",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Checkbutton(
            card,
            text="Debug mode (verbose logging)",
            variable=self.debug,
            bootstyle="round toggle",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Label(card, text="Game language").grid(
            row=2, column=0, sticky="w", pady=(8, 0)
        )
        ttk.Combobox(
            card,
            textvariable=self.language,
            values=LANGUAGES,
            state="readonly",
            width=6,
        ).grid(row=2, column=1, sticky="w", padx=(12, 0), pady=(8, 0))
        ttk.Label(
            card,
            text="Used to recognise the menu tab (en / jp / kr / zh).",
            style=MUTED,
        ).grid(row=3, column=0, columnspan=2, sticky="w")

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------
    def _set_dirty(self, dirty: bool) -> None:
        self.dirty = dirty
        self._dirty_label.configure(text="● unsaved changes" if dirty else "")
        state = "normal" if dirty else "disabled"
        self._save.configure(state=state)
        self._revert.configure(state=state)

    def _mark_dirty(self, *_args) -> None:
        if not self._loading:
            self._set_dirty(True)

    def reload(self) -> None:
        """Fill the form from the saved configuration (discards edits)."""
        settings = Config.settings
        enabled = load_screens_from_config() or list(SELECTABLE_SCREENS)
        self._loading = True
        try:
            self.platform.set(settings.target_platform.value)
            self.serial.set(settings.adb_serial or "")
            self.retries.set(str(settings.adb_retries))
            self.wait.set(str(settings.wait_multiplier))
            self.nav.set(str(settings.wait_screen_nav_multiplier))
            self.sync.set(settings.enable_sync)
            self.debug.set(settings.debug)
            self.language.set(
                settings.language if settings.language in LANGUAGES else LANGUAGES[0]
            )
            self.image_mode.set(settings.image_mode.value)
            self.local_dir.set(settings.local_image_dir or "")
            self.asset_base.set(window_state.asset_base_url())
            for screen, var in self.screens.items():
                var.set(screen in enabled)
        finally:
            self._loading = False
        self._toggle_platform()
        self._images_changed()
        self._set_dirty(False)

    def _toggle_platform(self) -> None:
        """Desktop mode does not use ADB: keep the card, but disable its fields."""
        desktop = self.platform.get() == TargetPlatform.DESKTOP.value
        self._adb_card.configure(
            text=(
                "ADB connection (not used in desktop mode)"
                if desktop
                else "ADB connection"
            )
        )
        state = "disabled" if desktop else "normal"
        for child in self._adb_card.winfo_children():
            try:
                child.configure(state=state)
            except tk.TclError:  # a widget without a state option
                pass

    def _reset_waits(self) -> None:
        self.wait.set(DEFAULT_WAIT)
        self.nav.set(DEFAULT_NAV_WAIT)

    def set_detected_devices(self, serials: list[str], selected: str | None) -> None:
        self._serial_combo.configure(values=serials)
        if selected:
            self.serial.set(selected)

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    def collect(self) -> tuple[AppSettings, list[Screen], dict]:
        """Validate the form into ``(settings, screens, gui_state)``; raises
        ValueError with one line per problem. Screens may be empty (the app
        picks the default)."""
        problems: list[str] = []

        def number(var, label: str, cast, minimum):
            try:
                value = cast(var.get())
            except ValueError:
                problems.append(
                    f"{label} must be a {'whole ' if cast is int else ''}number."
                )
                return None
            if value < minimum:
                problems.append(
                    f"{label} must be at least {minimum}."
                    if cast is int
                    else f"{label} must be greater than 0."
                )
                return None
            return value

        platform = TargetPlatform(self.platform.get())
        serial = self.serial.get().strip()
        if platform is not TargetPlatform.DESKTOP and not serial:
            problems.append(
                "An ADB serial (host:port) is required for emulator / device mode."
            )
        base = self.asset_base.get().strip()
        if not icons.valid_base_url(base):
            problems.append(
                "The remote asset base URL must start with http:// or https:// "
                "(leave it blank for the default)."
            )
        retries = number(self.retries, "Connect retries", int, 1)
        wait = number(self.wait, "Wait multiplier", float, 1e-9)
        nav = number(self.nav, "Screen navigation multiplier", float, 1e-9)
        if problems:
            raise ValueError("\n".join(f"• {p}" for p in problems))

        settings = AppSettings(
            target_platform=platform,
            adb_serial=serial,  # "" rather than None: the validator rejects None
            adb_retries=retries,
            wait_multiplier=wait,
            wait_screen_nav_multiplier=nav,
            enable_sync=self.sync.get(),
            language=self.language.get(),
            debug=self.debug.get(),
            image_mode=ImageMode(self.image_mode.get()),
            local_image_dir=self.local_dir.get().strip(),
        )
        gui_state = {"asset_base_url": icons.normalize_base_url(base) if base else ""}
        return settings, [s for s, var in self.screens.items() if var.get()], gui_state

    def save(self) -> bool:
        """Validate and hand the values to the app; True when saved."""
        try:
            settings, screens, gui_state = self.collect()
        except ValueError as exc:
            show_error(self, "Invalid settings", str(exc))
            return False
        self._on_save(settings, screens, gui_state)
        self._set_dirty(False)
        return True


class SettingsDialog(ttk.Toplevel):
    """Modal settings window. ``on_closed`` runs once it has been destroyed."""

    def __init__(
        self,
        parent,
        *,
        on_save: Callable[[AppSettings, list[Screen], dict], None],
        on_detect: Callable[[], None],
        on_open_folder: Callable[[str], None],
        on_closed: Callable[[], None],
        debug: bool = False,
    ):
        super().__init__(
            title="Settings", master=parent, transient=parent, minsize=(640, 480)
        )
        self._on_closed = on_closed
        self.page = SettingsPage(
            self, on_save=on_save, on_detect=on_detect, on_open_folder=on_open_folder
        )
        self.page.pack(fill="both", expand=True)
        button(
            self.page.actions,
            "Close",
            "x-lg",
            command=self.request_close,
            tip="Close (Esc)",
        ).pack(side="right")
        if debug:  # presets the checkbox; it still needs an explicit Save
            self.page.debug.set(True)

        self.protocol("WM_DELETE_WINDOW", self.request_close)
        self.bind("<Escape>", local_hotkey(self.request_close))
        self.bind(
            "<Control-s>", local_hotkey(lambda: self.page.dirty and self.page.save())
        )

        # Centre over the main window, within the screen.
        self.update_idletasks()
        width = 680
        height = min(720, self.winfo_screenheight() - 120)
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - width) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - height) // 3)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.grab_set()
        self.focus_set()

    @property
    def dirty(self) -> bool:
        return self.page.dirty

    def set_detected_devices(self, serials: list[str], selected: str | None) -> None:
        self.page.set_detected_devices(serials, selected)

    def request_close(self) -> bool:
        """Close, asking first when there are unsaved edits; False if cancelled."""
        if self.page.dirty and not confirm(
            self,
            "Unsaved settings",
            "Discard the unsaved changes and close?",
            yes="Discard",
        ):
            return False
        self.grab_release()
        self.destroy()
        self._on_closed()
        return True
