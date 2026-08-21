from os import environ
from pathlib import Path
from sys import base_prefix

from src.constant import SCREEN_DEFAULTS, USER_FACING_SCREENS
from src.core.config import TargetPlatform
from src.utils.data.io import read_json, write_json

environ["TCL_LIBRARY"] = str(Path(base_prefix) / "tcl" / "tcl8.6")
environ["TK_LIBRARY"] = str(Path(base_prefix) / "tcl" / "tk8.6")

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


def locate_root() -> Path:
    path = Path(__file__).resolve()
    while not (path / "main.py").exists():
        if path.parent == path:
            raise RuntimeError("Could not locate project root.")
        path = path.parent
    return path


BASE_DIR = locate_root()
SETTINGS_FILE = BASE_DIR / "config" / "settings.json"
SCREEN_CONFIG = BASE_DIR / "config" / "screen_config.json"


class SettingsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Blue Archive Resource Scanner - Settings")
        self.resizable(False, False)

        self.platform_var = tk.StringVar(value=TargetPlatform.EMULATOR.value)
        self.adb_host_var = tk.StringVar(value="192.168.1.100")
        self.adb_port_var = tk.StringVar(value="16384")
        self.adb_retries_var = tk.StringVar(value="5")
        self.wait_mult_var = tk.StringVar(value="1.0")
        self.wait_nav_mult_var = tk.StringVar(value="1.0")
        self.capture_interval_var = tk.StringVar(value="0.5")
        self.enable_sync_var = tk.BooleanVar(value=False)
        self.debug_var = tk.BooleanVar(value=False)

        self.screen_vars = {s: tk.BooleanVar(value=False) for s in USER_FACING_SCREENS}

        self.eval("tk::PlaceWindow . center")

        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        # Main container
        container = ttk.Frame(self, padding="10")
        container.pack(fill="both", expand=True)

        # Step 1: Setup
        step1 = ttk.LabelFrame(container, text="Step 1 - Setup", padding="10")
        step1.pack(fill="x", pady=(0, 10))

        ttk.Radiobutton(
            step1,
            text="PC client / desktop window",
            value=TargetPlatform.DESKTOP.value,
            variable=self.platform_var,
            command=self._toggle_platform_fields,
        ).pack(anchor="w")
        ttk.Radiobutton(
            step1,
            text="Emulator on this PC (MuMu, LDPlayer, BlueStacks)",
            value=TargetPlatform.EMULATOR.value,
            variable=self.platform_var,
            command=self._toggle_platform_fields,
        ).pack(anchor="w")
        ttk.Radiobutton(
            step1,
            text="Real Android phone / tablet over USB or Wi-Fi",
            value=TargetPlatform.DEVICE.value,
            variable=self.platform_var,
            command=self._toggle_platform_fields,
        ).pack(anchor="w")

        # ADB Frame
        self.adb_frame = ttk.Frame(step1)
        self.adb_frame.pack(fill="x", pady=(10, 0))

        ttk.Label(
            self.adb_frame,
            text="Tip: MuMu -> 16384 | LD/BlueStacks -> 5555",
            foreground="gray",
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        self.lbl_host = ttk.Label(self.adb_frame, text="Device IP address:")
        self.ent_host = ttk.Entry(
            self.adb_frame, textvariable=self.adb_host_var, width=20
        )
        self.lbl_host.grid(row=1, column=0, sticky="w", pady=2)
        self.ent_host.grid(row=1, column=1, sticky="w", padx=(5, 0), pady=2)

        self.lbl_port = ttk.Label(self.adb_frame, text="ADB port:")
        self.ent_port = ttk.Entry(
            self.adb_frame, textvariable=self.adb_port_var, width=10
        )
        self.lbl_port.grid(row=2, column=0, sticky="w", pady=2)
        self.ent_port.grid(row=2, column=1, sticky="w", padx=(5, 0), pady=2)

        self.lbl_retries = ttk.Label(self.adb_frame, text="ADB retries:")
        self.ent_retries = ttk.Entry(
            self.adb_frame, textvariable=self.adb_retries_var, width=10
        )
        self.lbl_retries.grid(row=3, column=0, sticky="w", pady=2)
        self.ent_retries.grid(row=3, column=1, sticky="w", padx=(5, 0), pady=2)

        # Desktop specific frame
        self.desktop_frame = ttk.Frame(step1)
        self.desktop_frame.pack(fill="x", pady=(10, 0))
        self.lbl_capture = ttk.Label(
            self.desktop_frame, text="Seconds between captures:"
        )
        self.ent_capture = ttk.Entry(
            self.desktop_frame, textvariable=self.capture_interval_var, width=8
        )
        self.lbl_capture.grid(row=0, column=0, sticky="w", pady=2)
        self.ent_capture.grid(row=0, column=1, sticky="w", padx=(5, 0), pady=2)

        # Step 2: Scan Targets
        step2 = ttk.LabelFrame(container, text="Step 2 - Scan Targets", padding="10")
        step2.pack(fill="x", pady=(0, 10))

        for s in USER_FACING_SCREENS:
            ttk.Checkbutton(step2, text=s, variable=self.screen_vars[s]).pack(
                anchor="w"
            )

        btn_frame = ttk.Frame(step2)
        btn_frame.pack(fill="x", pady=(5, 0))
        ttk.Button(
            btn_frame, text="Select All", command=lambda: self._set_all_screens(True)
        ).pack(side="left", padx=(0, 5))
        ttk.Button(
            btn_frame, text="Clear All", command=lambda: self._set_all_screens(False)
        ).pack(side="left")

        # Step 3: Performance
        step3 = ttk.LabelFrame(container, text="Step 3 - Performance", padding="10")
        step3.pack(fill="x", pady=(0, 10))

        ttk.Label(
            step3,
            text="1.0 = normal speed  |  1.5 = 50% slower  |  2.0 = double wait",
            foreground="gray",
        ).pack(anchor="w", pady=(0, 5))

        perf_row1 = ttk.Frame(step3)
        perf_row1.pack(fill="x")
        ttk.Label(perf_row1, text="Wait multiplier:").pack(side="left")
        ttk.Spinbox(
            perf_row1,
            from_=0.1,
            to=10.0,
            increment=0.1,
            textvariable=self.wait_mult_var,
            width=8,
        ).pack(side="left", padx=(5, 0))

        perf_row2 = ttk.Frame(step3)
        perf_row2.pack(fill="x", pady=(5, 0))
        ttk.Label(perf_row2, text="Screen navigation wait multiplier:").pack(side="left")
        ttk.Spinbox(
            perf_row2,
            from_=0.1,
            to=10.0,
            increment=0.1,
            textvariable=self.wait_nav_mult_var,
            width=8,
        ).pack(side="left", padx=(5, 0))

        # Step 4: Network & Debug
        step4 = ttk.LabelFrame(container, text="Step 4 - Network & Debug", padding="10")
        step4.pack(fill="x", pady=(0, 10))

        ttk.Checkbutton(
            step4, text="Enable online data sync", variable=self.enable_sync_var
        ).pack(anchor="w")
        ttk.Checkbutton(step4, text="Debug mode", variable=self.debug_var).pack(
            anchor="w"
        )

        # Bottom Buttons
        bottom = ttk.Frame(container)
        bottom.pack(fill="x")
        ttk.Button(bottom, text="Save Settings", command=self._save_settings).pack(
            side="right"
        )
        ttk.Button(bottom, text="Cancel", command=self.destroy).pack(
            side="right", padx=(0, 5)
        )

    def _toggle_platform_fields(self):
        mode = self.platform_var.get()

        # Hide all optional fields first
        self.lbl_host.grid_remove()
        self.ent_host.grid_remove()
        self.lbl_port.grid_remove()
        self.ent_port.grid_remove()
        self.lbl_retries.grid_remove()
        self.ent_retries.grid_remove()
        self.lbl_capture.grid_remove()
        self.ent_capture.grid_remove()

        if mode == TargetPlatform.EMULATOR.value:
            self.lbl_port.grid(row=2, column=0, sticky="w", pady=2)
            self.ent_port.grid(row=2, column=1, sticky="w", padx=(5, 0), pady=2)
            self.lbl_retries.grid(row=3, column=0, sticky="w", pady=2)
            self.ent_retries.grid(row=3, column=1, sticky="w", padx=(5, 0), pady=2)
        elif mode == TargetPlatform.DEVICE.value:
            self.lbl_host.grid(row=1, column=0, sticky="w", pady=2)
            self.ent_host.grid(row=1, column=1, sticky="w", padx=(5, 0), pady=2)
            self.lbl_port.grid(row=2, column=0, sticky="w", pady=2)
            self.ent_port.grid(row=2, column=1, sticky="w", padx=(5, 0), pady=2)
        elif mode == TargetPlatform.DESKTOP.value:
            self.lbl_capture.grid(row=0, column=0, sticky="w", pady=2)
            self.ent_capture.grid(row=0, column=1, sticky="w", padx=(5, 0), pady=2)

    def _set_all_screens(self, state: bool):
        for var in self.screen_vars.values():
            var.set(state)

    def _load_settings(self):
        settings = read_json(SETTINGS_FILE)

        if settings:
            self.platform_var.set(
                settings.get("target_platform", TargetPlatform.EMULATOR.value)
            )
            self.adb_host_var.set(settings.get("adb_host", "192.168.1.100"))
            self.adb_port_var.set(str(settings.get("adb_port", 16384)))
            self.adb_retries_var.set(str(settings.get("adb_retries", 5)))
            self.wait_mult_var.set(str(settings.get("wait_multiplier", 1.0)))
            self.wait_nav_mult_var.set(
                str(settings.get("wait_screen_nav_multiplier", 1.0))
            )
            self.capture_interval_var.set(str(settings.get("capture_interval", 0.5)))
            self.enable_sync_var.set(settings.get("enable_sync", False))
            self.debug_var.set(settings.get("debug_mode", False))

        # Load screen config to populate checkbuttons
        enabled_screens = self._load_screens_from_config()
        for s in USER_FACING_SCREENS:
            self.screen_vars[s].set(s in enabled_screens)

        # Trigger UI toggle after loading
        self._toggle_platform_fields()

    def _load_screens_from_config(self) -> list:
        screens = read_json(SCREEN_CONFIG)
        if not screens:
            return []

        return [
            name
            for name, cfg in screens.items()
            if cfg.get("enabled", False) and name in USER_FACING_SCREENS
        ]

    def _save_settings(self):
        # Assemble dictionary from UI
        chosen_screens = [s for s, var in self.screen_vars.items() if var.get()]
        if not chosen_screens:
            chosen_screens = ["Equipment", "Items"]
            messagebox.showinfo(
                "Defaulting",
                "No scan targets selected. Defaulting to Equipment + Items.",
            )

        try:
            settings_data = {
                "target_platform": self.platform_var.get(),
                "adb_host": self.adb_host_var.get(),
                "adb_port": int(self.adb_port_var.get()),
                "adb_retries": int(self.adb_retries_var.get()),
                "wait_multiplier": float(self.wait_mult_var.get()),
                "wait_screen_nav_multiplier": float(self.wait_nav_mult_var.get()),
                "capture_interval": float(self.capture_interval_var.get()),
                "enable_sync": self.enable_sync_var.get(),
                "debug_mode": self.debug_var.get(),
            }
        except ValueError:
            messagebox.showerror(
                "Invalid Input", "Please ensure numeric fields contain valid numbers."
            )
            return

        write_json(SETTINGS_FILE, settings_data)

        self._write_screen_config(chosen_screens)

        messagebox.showinfo("Success", "Settings saved successfully!")
        self.destroy()

    def _write_screen_config(self, enabled_screens: list):
        # Auto-include "Student" if "Students" is checked
        if "Students" in enabled_screens and "Student" not in enabled_screens:
            enabled_screens.append("Student")

        screens = {
            name: {**defaults, "enabled": False}
            for name, defaults in SCREEN_DEFAULTS.items()
        }

        on_disk = read_json(SCREEN_CONFIG)
        for name, disk_values in on_disk.items():
            if name in screens:
                for k, v in disk_values.items():
                    if k != "enabled":
                        screens[name][k] = v
            else:
                screens[name] = disk_values

        for name in screens:  # noqa: PLC0206
            screens[name]["enabled"] = name in enabled_screens

        write_json(SCREEN_CONFIG, screens)


if __name__ == "__main__":
    app = SettingsApp()
    app.mainloop()
