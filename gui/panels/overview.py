"""Overview page: what the scanner is about to do.

Re-reads the saved configuration whenever it is shown (``refresh``), so it
never displays a stale one. Running is done from the command bar.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

import ttkbootstrap as ttk

from gui.registry import SELECTABLE_SCREENS
from gui.ui import MUTED, Page, button
from src.core.config import Config, TargetPlatform
from src.utils.cli.config_utils import load_screens_from_config

# platform value -> (long label, short label for the bars)
PLATFORMS = {
    TargetPlatform.DESKTOP.value: ("PC client / desktop window", "desktop"),
    TargetPlatform.EMULATOR.value: ("Emulator on this PC (ADB)", "emulator"),
    TargetPlatform.DEVICE.value: ("Android device over ADB", "device"),
}

CONFIG_FIELDS = (
    ("platform", "Target platform"), ("serial", "ADB serial"),
    ("wait", "Wait multiplier"), ("nav", "Screen navigation multiplier"),
    ("sync", "Data sync"), ("language", "Game language"), ("debug", "Debug logging"),
)  # fmt: skip


def scanner_flags(sync_enabled: bool) -> list[str]:
    """Extra ``main.py`` arguments for a scanner run (shared with the app)."""
    return [] if sync_enabled else ["--offline"]


def platform_short(value: str) -> str:
    return PLATFORMS.get(value, (value, value))[1]


class OverviewPage(Page):
    def __init__(
        self,
        master,
        *,
        on_edit_settings: Callable[[], None],
    ):
        super().__init__(
            master,
            "Scanner",
            "Drives the open game client, reads the inventory screens and "
            "refreshes output/ with planner-ready values.",
        )

        _card, self._preview = self.command_card()

        card = self.card("Active configuration")
        self._values = {}
        for row, (key, label) in enumerate(CONFIG_FIELDS):
            ttk.Label(card, text=label).grid(row=row, column=0, sticky="w", pady=2)
            self._values[key] = ttk.Label(card)
            self._values[key].grid(row=row, column=1, sticky="w", padx=(16, 0), pady=2)
        button(
            card,
            "Settings…",
            "gear-fill",
            command=on_edit_settings,
            tip="Edit these values (Ctrl+,)",
        ).grid(row=len(CONFIG_FIELDS), column=0, columnspan=2, sticky="w", pady=(8, 0))

        card = self.card("Scan targets")
        self._summary = ttk.Label(card, style=MUTED)
        self._summary.grid(row=0, column=0, columnspan=2, sticky="w")
        self._targets = ttk.Frame(card)
        self._targets.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))
        # Built once: refreshes only change the text/colour, so the card never
        # changes height or reflows.
        self._target_labels: dict = {}
        for index, screen in enumerate(SELECTABLE_SCREENS):
            label = ttk.Label(self._targets)
            label.grid(
                row=index // 2, column=index % 2, sticky="w", padx=(0, 28), pady=1
            )
            self._target_labels[screen] = label
        ttk.Label(
            card,
            text="When a scan finishes, its JSON output is opened in the Data tab for review.",
            style=MUTED,
            wraplength=640,
            justify="left",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def refresh(self) -> None:
        settings = Config.settings
        platform = settings.target_platform.value
        serial = settings.adb_serial or "not set"
        if platform == TargetPlatform.DESKTOP.value:
            serial = "not used in desktop mode"

        text = {
            "platform": PLATFORMS.get(platform, (platform,))[0],
            "serial": serial,
            "wait": f"{settings.wait_multiplier:.2f}x",
            "nav": f"{settings.wait_screen_nav_multiplier:.2f}x",
            "sync": (
                "Enabled" if settings.enable_sync else "Disabled (main.py --offline)"
            ),
            "language": settings.language,
            "debug": "On" if settings.debug else "Off",
        }
        for key, value in text.items():
            self._values[key].configure(text=value)

        command = [
            Path(sys.executable).name,
            "main.py",
            *scanner_flags(settings.enable_sync),
        ]
        self._preview.set(" ".join(command))

        enabled = load_screens_from_config()
        count = sum(s.value in enabled for s in SELECTABLE_SCREENS)
        note = "" if count else "  ·  nothing will be scanned until one is enabled"
        self._summary.configure(
            text=f"{count} of {len(SELECTABLE_SCREENS)} enabled{note}"
        )
        for screen, label in self._target_labels.items():
            on = screen.value in enabled
            label.configure(
                text=("✓  " if on else "–  ") + screen.value,
                bootstyle="success" if on else "secondary",
            )
