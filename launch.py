import argparse
import subprocess
import sys
from threading import Event

from pynput import keyboard
from rich.console import Console
from rich.panel import Panel

from src.constant import USER_FACING_SCREENS
from src.core.config import Config, Path_Config
from src.utils.cli.cli import print_settings
from src.utils.cli.config_utils import load_screens_from_config, write_screen_config
from src.utils.cli.wizard import check_dependencies, run_wizard

console = Console()

# Paths
MAIN_ENTRY = Path_Config.PROJECT_ROOT / "main.py"


# Launch
def launch(screens: list[str]):
    """Launch the scanner with given settings."""

    write_screen_config(screens)

    print_settings()

    console.print("\n[bold green]▶ Starting Scanner...[/bold green]\n")

    cmd = [sys.executable, str(MAIN_ENTRY)]
    if not Config.settings.enable_sync:
        cmd.append("--offline")

    stop_event = Event()

    def on_press(key):
        if key == keyboard.Key.f2:  # to be configurable later
            stop_event.set()
            return False  # stop pynput listener

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    try:
        process = subprocess.Popen(cmd)

        while process.poll() is None:
            if stop_event.is_set():
                console.print("[yellow]\nScan interrupted.[/yellow]")
                process.terminate()
                break

            stop_event.wait(0.1)

        process.wait()

    except KeyboardInterrupt:
        console.print("[yellow]\nScan interrupted.[/yellow]")
        process.terminate()
        process.wait()

    except subprocess.CalledProcessError as e:
        console.print("[red]\nScanner crashed. Check logs.[/red]")
        sys.exit(e.returncode)

    finally:
        listener.stop()
        listener.join()


# Entry
def main():
    console.print(
        Panel(
            "[bold cyan]Blue Archive Resource Scanner[/bold cyan]",
            border_style="cyan",
        )
    )

    args = _parse_args()
    Path_Config.ensure_directories()

    first_launch = not Path_Config.SETTINGS_FILE.exists()
    previous_settings = Config.settings

    if args.edit:
        # User explicitly asked to reconfigure
        console.print("[dim]Edit mode - previous settings loaded as defaults.[/dim]\n")
        settings, screens = run_wizard(previous=previous_settings)
        Config.save(settings)
    elif first_launch:
        # No saved settings yet - must run wizard
        console.print("[dim]First launch - let's get you set up.[/dim]\n")
        check_dependencies()
        settings, screens = run_wizard(previous=previous_settings)
        Config.save(settings)
    else:
        # Saved settings exist and no --edit flag - use them silently
        console.print("[green]Using saved settings.[/green]\n")
        console.print("[dim]Run with -e / --edit to change them.\n")
        settings = previous_settings
        screens = load_screens_from_config() or USER_FACING_SCREENS

    settings = settings.model_copy(update={"debug": args.debug})
    Config.save(settings)
    launch(screens)


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
