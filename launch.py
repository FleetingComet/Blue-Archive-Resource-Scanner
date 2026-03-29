#!/usr/bin/env python3
import json
import sys
import subprocess
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text

console = Console()

# Paths
BASE_DIR = Path(__file__).parent
SETTINGS_FILE = BASE_DIR / "config" / "settings.json"
SCREEN_CONFIG = BASE_DIR / "config" / "screen_config.json"
MAIN_ENTRY = BASE_DIR / "main.py"


# Helpers
def header(title: str):
    console.print(
        Panel(
            Text(title, style="bold cyan"),
            border_style="cyan",
            expand=False,
        )
    )


def ask(prompt: str, default: str = "") -> str:
    return Prompt.ask(prompt, default=default)


def ask_int(prompt: str, default: int) -> int:
    while True:
        val = Prompt.ask(prompt, default=str(default))
        try:
            return int(val)
        except ValueError:
            console.print("[red]Please enter a valid number.[/red]")


def ask_float(prompt: str, default: float) -> float:
    while True:
        val = Prompt.ask(prompt, default=str(default))
        try:
            return float(val)
        except ValueError:
            console.print("[red]Please enter a valid decimal number.[/red]")


def choose(prompt: str, options: list, default: str = "") -> str:
    console.print(f"\n[bold]{prompt}[/bold]")

    table = Table(show_header=False, box=None)
    table.add_column("Index", style="cyan")
    table.add_column("Option")

    default_index = 1

    for i, (key, label) in enumerate(options, 1):
        marker = "▶ " if key == default else "  "
        if key == default:
            default_index = i
        table.add_row(f"{i}", f"{marker}{label}")

    console.print(table)

    while True:
        raw = Prompt.ask("Enter number", default=str(default_index))
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(options):
                return options[idx - 1][0]

        console.print(f"[red]Choose between 1 and {len(options)}[/red]")


# Config of Script
def save_settings(settings: dict):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        from config import UserSettings

        validated = UserSettings(**settings)

        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            f.write(validated.model_dump_json(indent=4))

        console.print(f"[dim]Saved → {SETTINGS_FILE}[/dim]")

    except Exception as e:
        console.print(f"[red]Error saving settings:[/red] {e}")


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


# Screen Config
SCREEN_DEFAULTS = {
    "Currencies": {
        "menu_location": "currencies",
        "grid_type": "currencies",
        "uses_menu_tab": False,
        "grid_config": None,  # No grid scanning for currencies
    },
    "Equipment": {
        "menu_location": "menu_equipment",
        "grid_type": "Equipment",
        "uses_menu_tab": True,
        "grid_config": {
            "start_x": 690,
            "start_y": 160,
            "item_width": 110,
            "item_height": 90,
            "cols_per_row": 5,
            "rows_per_page": 5,
            "y_padding": 11,
            "swipe_distance": 450,
            "end_y": 660,
        },
    },
    "Items": {
        "menu_location": "menu_items",
        "grid_type": "Items",
        "uses_menu_tab": True,
        "grid_config": {
            "start_x": 690,
            "start_y": 160,
            "item_width": 110,
            "item_height": 90,
            "cols_per_row": 5,
            "rows_per_page": 5,
            "y_padding": 11,
            "swipe_distance": 450,
            "end_y": 560,
        },
    },
    "Students": {
        "menu_location": "menu_students",
        "grid_type": "Students",
        "uses_menu_tab": False,
        "grid_config": None,  # No grid scanning for students list
    },
    "Student": {
        "menu_location": "first_student",
        "grid_type": "Student",
        "uses_menu_tab": False,
        "grid_config": None,  # Individual student info, no grid
    },
}

# Screens the user explicitly toggles in the wizard.
# "Student" is excluded - it is a sub-screen of "Students" and is
# enabled/disabled automatically alongside it.
USER_FACING_SCREENS = ["Equipment", "Items", "Students", "Currencies"]


def write_screen_config(enabled_screens: list[str]) -> None:
    """
    Update the ``enabled`` flag in config/screen_config.json.

    Strategy - three-way merge:
      1. Start from SCREEN_DEFAULTS (guarantees all keys are always present).
      2. Overlay whatever is already in the file (preserves manual edits to
         menu_location, grid_type, uses_menu_tab, etc.).
      3. Apply the launcher\'s enabled/disabled choices on top.

    This means the file is never left with missing keys, and values the user
    or a developer edited by hand are never silently clobbered.
    """
    # Start from code-level defaults
    screens: dict = {
        name: {**defaults, "enabled": False}
        for name, defaults in SCREEN_DEFAULTS.items()
    }

    # Merge existing file values (preserves menu_location, grid_type, etc.)
    if SCREEN_CONFIG.exists():
        try:
            with open(SCREEN_CONFIG) as f:
                on_disk = json.load(f).get("screens", {})
            for name, disk_values in on_disk.items():
                if name in screens:
                    # Overlay all keys except "enabled" - that is ours to set
                    for k, v in disk_values.items():
                        if k != "enabled":
                            screens[name][k] = v
                else:
                    # Unknown screen added manually - keep it untouched
                    screens[name] = disk_values
        except Exception as exc:
            console.print(
                f"[yellow]Warning: could not read existing screen config - {exc}[/yellow]"
            )

    # Apply the launcher's enabled choices
    for name in screens:
        screens[name]["enabled"] = name in enabled_screens

    SCREEN_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with open(SCREEN_CONFIG, "w") as f:
        json.dump({"screens": screens}, f, indent=2)


def load_screens_from_config() -> list[str]:
    """Read enabled screens from screen_config.json."""
    if SCREEN_CONFIG.exists():
        try:
            with open(SCREEN_CONFIG, encoding="utf-8") as f:
                screens = json.load(f).get("screens", {})
            return [name for name, cfg in screens.items() if cfg.get("enabled", False)]
        except Exception:
            pass
    return []


# Dependency Check
def check_dependencies():
    try:
        import pytesseract  # noqa
        import cv2  # noqa

        console.print("[green]✓ Dependencies OK[/green]")
    except ImportError:
        console.print("[yellow]✗ Missing dependencies (tesseract, cv2)[/yellow]")

        if Confirm.ask("Install now?"):
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
            )
        else:
            sys.exit(1)


# Wizard
def run_wizard(previous: dict) -> dict:
    header("Step 1 - Setup")

    mode = choose(
        "How are you running Blue Archive?",
        [
            (
                "emulator",
                "Emulator on this PC  (MuMu Player 12, LDPlayer, BlueStacks …)",
            ),
            ("desktop", "PC client / desktop window (Blue Archive PC app)"),
            ("device", "Real Android phone / tablet over USB or Wi-Fi"),
        ],
        default=previous.get("target_platform", "emulator"),
    )

    adb_host, adb_port = "127.0.0.1", 16384

    if mode == "emulator":
        console.print("[dim]MuMu → 16384 | LD/BlueStacks → 5555[/dim]")
        adb_port = ask_int("ADB port", previous.get("adb_port", 16384))

    elif mode == "device":
        console.print("[yellow]Tip: Enable wireless ADB[/yellow]")
        adb_host = ask("Device IP address", previous.get("adb_host", "192.168.1.100"))
        adb_port = ask_int("ADB port", previous.get("adb_port", 5555))

    header("Step 2 - Scan Targets")

    # screens = ["Equipment", "Items", "Students", "Currencies"]
    screens = previous.get("screens", USER_FACING_SCREENS)
    chosen: list[str] = []

    for s in USER_FACING_SCREENS:
        if Confirm.ask(
            f"Scan [cyan]{s}[/cyan]?", default=s in previous.get("screens", screens)
        ):
            chosen.append(s)

    if not chosen:
        chosen = ["Equipment", "Items"]
        console.print(
            "[yellow]Nothing selected, defaulting to Equipment + Items[/yellow]"
        )

    header("Step 3 - Performance")
    console.print(
        "\n[bold]Wait-time multiplier[/bold] - increase if your device/emulator is slow.\n"
    )
    console.print(
        "[dim]1.0 = normal speed  |  1.5 = 50 % slower  |  2.0 = double wait[/dim]\n"
    )
    wait_mult = ask_float("Wait multiplier", previous.get("wait_multiplier", 1.0))

    header("Step 4 - Network")
    enable_sync = Confirm.ask(
        "Enable online data sync? (Download latest item/student data)",
        default=previous.get("enable_sync", False),
    )

    return {
        "target_platform": mode,
        "adb_host": adb_host,
        "adb_port": adb_port,
        "screens": chosen,
        "wait_multiplier": wait_mult,
        "enable_sync": enable_sync,
    }


# Launch
def launch(settings: dict):
    """Launch the scanner with given settings."""

    save_settings(settings)

    write_screen_config(settings["screens"])

    console.print("\n[bold green]▶ Starting Scanner...[/bold green]\n")

    cmd = [sys.executable, str(MAIN_ENTRY)]
    if not settings.get("enable_sync", False):
        cmd.append("--offline")

    try:
        with console.status("[cyan]Running scanner...[/cyan]", spinner="dots"):
            subprocess.run(cmd, check=True)

    except KeyboardInterrupt:
        console.print("[yellow]\nScan interrupted.[/yellow]")
    except subprocess.CalledProcessError as e:
        console.print("[red]\nScanner crashed. Check logs.[/red]")
        sys.exit(e.returncode)


# Entry
def main():
    console.print(
        Panel(
            "[bold cyan]Blue Archive Resource Scanner[/bold cyan]",
            border_style="cyan",
        )
    )

    force_edit = _parse_args()
    previous = load_settings()
    first_launch = not previous

    if force_edit:
        # User explicitly asked to reconfigure
        if previous:
            console.print(
                "[dim]Edit mode - previous settings loaded as defaults.[/dim]\n"
            )
        settings = run_wizard(previous)
        save_settings(settings)
    elif first_launch:
        # No saved settings yet - must run wizard
        console.print("[dim]First launch - let's get you set up.[/dim]\n")
        check_dependencies()
        settings = run_wizard(previous)
        save_settings(settings)
    else:
        # Saved settings exist and no --edit flag - use them silently
        console.print("[green]Using saved settings.[/green]\n")
        console.print("[dim]Run with -e / --edit to change them.\n")
        from_config = load_screens_from_config()
        if from_config:
            previous["screens"] = from_config
        settings = previous

    launch(settings)


def _parse_args() -> bool:
    """
    Return True if the user wants to re-run the wizard.

    Default behaviour (no flags):
      - Settings file exists  → skip wizard, use saved settings.
      - Settings file missing → run wizard (first launch).

    Flags that force the wizard to run:
      --edit / -e   re-configure even when saved settings exist.
    """
    edit_flags = {"--edit", "-e"}
    return bool(edit_flags & set(sys.argv[1:]))


if __name__ == "__main__":
    main()
