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


# Settings
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
            ("emulator", "Emulator (MuMu, LD, BlueStacks)"),
            ("desktop", "PC Client"),
            ("device", "Android Phone (WiFi/USB)"),
        ],
        default=previous.get("target_platform", "emulator"),
    )

    adb_host, adb_port = "127.0.0.1", 16384

    if mode == "emulator":
        console.print("[dim]MuMu → 16384 | LD/BlueStacks → 5555[/dim]")
        adb_port = ask_int("ADB port", previous.get("adb_port", 16384))

    elif mode == "device":
        console.print("[yellow]Tip: Enable wireless ADB[/yellow]")
        adb_host = ask("Device IP", previous.get("adb_host", "192.168.1.100"))
        adb_port = ask_int("ADB port", previous.get("adb_port", 5555))

    header("Step 2 - Scan Targets")

    screens = ["Equipment", "Items", "Students", "Currencies"]
    chosen = []

    for s in screens:
        if Confirm.ask(
            f"Scan [cyan]{s}[/cyan]?", default=s in previous.get("screens", screens)
        ):
            chosen.append(s)

    if not chosen:
        chosen = ["Equipment", "Items"]

    header("Step 3 - Performance")
    wait_mult = ask_float("Wait multiplier", previous.get("wait_multiplier", 1.0))

    header("Step 4 - Network")
    offline = not Confirm.ask(
        "Enable online sync?",
        default=not previous.get("offline_mode", False),
    )

    return {
        "target_platform": mode,
        "adb_host": adb_host,
        "adb_port": adb_port,
        "screens": chosen,
        "wait_multiplier": wait_mult,
        "offline_mode": offline,
    }


# Launch
def launch(settings: dict):
    save_settings(settings)

    SCREEN_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with open(SCREEN_CONFIG, "w") as f:
        json.dump(
            {"screens": {s: {"enabled": True} for s in settings["screens"]}},
            f,
            indent=2,
        )

    console.print("\n[bold green]▶ Starting Scanner...[/bold green]\n")

    cmd = [sys.executable, str(MAIN_ENTRY)]
    if settings["offline_mode"]:
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

    check_dependencies()
    previous = load_settings()

    if "--saved" in sys.argv and previous:
        console.print("[green]Using saved settings.[/green]\n")
        launch(previous)
        return

    if previous:
        console.print("[dim]Press Enter to keep previous values.[/dim]\n")

    settings = run_wizard(previous)
    launch(settings)


if __name__ == "__main__":
    main()
