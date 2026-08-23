import subprocess
import sys

from rich.prompt import Confirm, FloatPrompt, IntPrompt

from src.constant import USER_FACING_SCREENS
from src.core.config import AppSettings, TargetPlatform
from src.utils.cli.cli import ask, choose, console, header
from src.utils.cli.config_utils import load_screens_from_config


def check_dependencies():
    try:
        from rapidocr import RapidOCR  # noqa
        import cv2  # noqa

        console.print("[green]✓ Dependencies OK[/green]")
    except ImportError:
        console.print("[yellow]✗ Missing dependencies (rapidocr, cv2)[/yellow]")
        if Confirm.ask("Install now?"):
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                check=True,
            )
        else:
            sys.exit(1)


def run_wizard(previous: AppSettings) -> tuple[AppSettings, list[str]]:
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
        default=previous.target_platform,
    )

    adb_host, adb_port, adb_retries = (
        previous.adb_host,
        previous.adb_port,
        previous.adb_retries,
    )

    if mode == TargetPlatform.EMULATOR.value:
        console.print("[dim]MuMu → 16384 | LD/BlueStacks → 5555[/dim]")
        adb_port = IntPrompt.ask("ADB port", default=previous.adb_port)
        adb_retries = IntPrompt.ask("ADB Retries", default=previous.adb_retries)
    elif mode == TargetPlatform.DEVICE.value:
        console.print("[yellow]Tip: Enable wireless ADB[/yellow]")
        adb_host = ask(
            "Device IP address", default=previous.adb_host or "192.168.1.100"
        )
        adb_port = IntPrompt.ask("ADB port", default=previous.adb_port or 5555)

    header("Step 2 - Scan Targets")
    previously_enabled = load_screens_from_config() or USER_FACING_SCREENS
    chosen = [
        s
        for s in USER_FACING_SCREENS
        if Confirm.ask(f"Scan [cyan]{s}[/cyan]?", default=s in previously_enabled)
    ]
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
    wait_mult = FloatPrompt.ask("Wait multiplier", default=previous.wait_multiplier)
    wait_screen_nav_multiplier = FloatPrompt.ask(
        "Multiplier specifically for screen navigation delays (use for slower screen loads)",
        default=previous.wait_screen_nav_multiplier,
    )

    header("Step 4 - Network")
    enable_sync = Confirm.ask(
        "Enable online data sync? (Download the latest community-maintained data.)",
        default=previous.enable_sync,
    )

    settings = AppSettings(
        target_platform=mode,
        adb_host=adb_host,
        adb_port=adb_port,
        adb_retries=adb_retries,
        wait_multiplier=wait_mult,
        wait_screen_nav_multiplier=wait_screen_nav_multiplier,
        enable_sync=enable_sync,
        debug=previous.debug,
    )

    return settings, chosen
