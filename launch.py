import argparse
import json
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

from src.constant import SCREEN_DEFAULTS, USER_FACING_SCREENS
from src.core.config import TargetPlatform

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
        from src.core.config import AppSettings

        validated = AppSettings(**settings)

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
                on_disk = json.load(f)
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
        json.dump(screens, f, indent=2)


def load_screens_from_config() -> list[str]:
    """Read enabled screens from screen_config.json."""
    if SCREEN_CONFIG.exists():
        try:
            with open(SCREEN_CONFIG, encoding="utf-8") as f:
                screens = json.load(f)
            return [name for name, cfg in screens.items() if cfg.get("enabled", False)]
        except Exception:
            pass
    return []


# Dependency Check
def check_dependencies():
    try:
        from rapidocr import RapidOCR  # noqa
        import cv2  # noqa

        console.print("[green]✓ Dependencies OK[/green]")
    except ImportError:
        console.print("[yellow]✗ Missing dependencies (rapidocr, cv2)[/yellow]")

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
                TargetPlatform.DESKTOP.value,
                "PC client / desktop window (Blue Archive PC app)",
            ),
            (
                TargetPlatform.EMULATOR.value,
                "Emulator on this PC  (MuMu Player 12, LDPlayer, BlueStacks …)",
            ),
            (
                TargetPlatform.DEVICE.value,
                "Real Android phone / tablet over USB or Wi-Fi",
            ),
        ],
        default=previous.get("target_platform", TargetPlatform.EMULATOR.value),
    )

    adb_host, adb_port, adb_retries = "127.0.0.1", 16384, 5

    if mode == "emulator":
        console.print("[dim]MuMu → 16384 | LD/BlueStacks → 5555[/dim]")
        adb_port = IntPrompt.ask("ADB port", default=previous.get("adb_port", 16384))
        adb_retries = IntPrompt.ask(
            "ADB Retries", default=previous.get("adb_retries", 5)
        )

    elif mode == "device":
        console.print("[yellow]Tip: Enable wireless ADB[/yellow]")
        adb_host = ask(
            "Device IP address", default=previous.get("adb_host", "192.168.1.100")
        )
        adb_port = IntPrompt.ask("ADB port", default=previous.get("adb_port", 5555))

    header("Step 2 - Scan Targets")

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
    wait_mult = FloatPrompt.ask(
        "Wait multiplier", default=previous.get("wait_multiplier", 1.0)
    )
    wait_screen_nav_multiplier = FloatPrompt.ask(
        "Multiplier specifically for screen navigation delays (use for slower screen loads)",
        default=previous.get("wait_screen_nav_multiplier", 1.0),
    )

    if mode != "emulator" and mode != "device":
        capture_interval = FloatPrompt.ask(
            "Seconds between captures", default=previous.get("capture_interval", 0.5)
        )

    header("Step 4 - Network")
    enable_sync = Confirm.ask(
        "Enable online data sync? (Download latest item/student data)",
        default=previous.get("enable_sync", False),
    )

    return {
        "target_platform": mode,
        "adb_host": adb_host,
        "adb_port": adb_port,
        "adb_retries": adb_retries,
        "screens": chosen,
        "wait_multiplier": wait_mult,
        "wait_screen_nav_multiplier": wait_screen_nav_multiplier,
        "capture_interval": capture_interval,
        "enable_sync": enable_sync,
        "debug_mode": debug_mode,
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

    args = _parse_args()

    global debug_mode
    debug_mode = args.debug
    force_edit = args.edit

    previous_settings = load_settings()
    first_launch = not previous_settings
    from_config = load_screens_from_config()
    if from_config:
        previous_settings["screens"] = from_config

    if force_edit:
        # User explicitly asked to reconfigure
        if previous_settings:
            console.print(
                "[dim]Edit mode - previous settings loaded as defaults.[/dim]\n"
            )
        settings = run_wizard(previous_settings)
        save_settings(settings)
    elif first_launch:
        # No saved settings yet - must run wizard
        console.print("[dim]First launch - let's get you set up.[/dim]\n")
        check_dependencies()
        settings = run_wizard(previous_settings)
        save_settings(settings)
    else:
        # Saved settings exist and no --edit flag - use them silently
        console.print("[green]Using saved settings.[/green]\n")
        console.print("[dim]Run with -e / --edit to change them.\n")
        settings = previous_settings
        if debug_mode:
            settings["debug_mode"] = debug_mode

    launch(settings)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-e",
        "--edit",
        action="store_true",
        help="Re-run the setup wizard.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
