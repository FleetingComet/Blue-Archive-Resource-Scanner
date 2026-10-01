from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

from src.constant import USER_FACING_SCREENS
from src.core.config import Config, TargetPlatform
from src.utils.cli.config_utils import load_screens_from_config
from src.utils.device.adb.adb_controller import list_adb_devices

console = Console()

_MANUAL_SENTINEL = "__manual__"


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
    """Interactive choice from a list of (key, label) pairs."""
    console.print(f"\n[bold]{prompt}[/bold]")

    table = Table(show_header=False, box=None)
    table.add_column("Index", style="cyan")
    table.add_column("Option")

    default_index = 1

    for i, (key, label) in enumerate(options, 1):
        marker = "▶ " if key == default else "  "
        style = "bold cyan" if key == default else "white"
        if key == default:
            default_index = i

        table.add_row(f"{i}", f"[{style}]{marker}{label}[/{style}]")

    console.print(table)

    if default:
        console.print(f"[dim]Default: {default}[/dim]")

    while True:
        # raw = Prompt.ask("Enter number", default=str(default_index)).strip()
        raw = IntPrompt.ask("Enter number", default=default_index)
        # if raw.isdigit():
        idx = int(raw)
        if 1 <= idx <= len(options):
            return options[idx - 1][0]

        console.print(f"[red]Choose between 1 and {len(options)}[/red]")


def ask_for_device(mode: str, previous: str | None = None) -> str:
    """
    Returns a target string (USB serial or host:port).
    """
    devices = list_adb_devices()
    prev = (previous or "").strip()
    manual_default = prev or (
        "localhost:16384" if mode == TargetPlatform.EMULATOR.value else ""
    )

    console.print("\n[bold]Detected ADB targets[/bold]")
    if devices:
        for serial, state in devices:
            color = "green" if state == "device" else "yellow"
            console.print(f"  [dim]•[/dim] [{color}]{serial}[/{color}]  ({state})")
    else:
        console.print(
            "  [yellow]None found.[/yellow] [dim]"
            "Start the emulator or run `adb connect <host:port>` first.[/dim]"
        )

    options: list[tuple[str, str]] = []
    for serial, state in devices:
        color = "green" if state == "device" else "yellow"
        options.append((serial, f"[{color}]{serial}[/{color}]  ({state})"))
    options.append(
        (
            _MANUAL_SENTINEL,
            f"Enter manually  [dim](e.g. {manual_default or 'host:port'})[/dim]",
        )
    )

    default_key = _MANUAL_SENTINEL
    for serial, _ in devices:
        if serial == prev:
            default_key = serial
            break

    chosen = choose("Select a target", options, default=default_key)

    if chosen == _MANUAL_SENTINEL:
        return ask(
            "Serial (e.g. 123456789A123456) or host:port (e.g. localhost:16384)",
            default=manual_default,
        ).strip()

    return chosen


def print_settings() -> None:
    """Pretty-print the active configuration before launch."""
    s = Config.settings

    def _status(enabled: bool) -> str:
        return "[bold green]Enabled[/bold green]" if enabled else "[dim]Disabled[/dim]"

    def _speed_hint(mult: float) -> str:
        if mult == 1.0:
            return "normal"
        if mult < 1.0:
            return "fast"
        if mult <= 1.5:
            return "moderate"
        if mult <= 2.0:
            return "slow"
        return "very slow"

    table = Table(show_header=False, box=None, padding=(0, 2), expand=False)
    table.add_column("key", style="cyan", justify="right", no_wrap=True)
    table.add_column("sep", style="dim", no_wrap=True, width=1)
    table.add_column("val", justify="left", no_wrap=True)

    # Platform & connection
    table.add_row("[bold cyan]PLATFORM & CONNECTION[/bold cyan]", "", "")
    table.add_row("Target Platform", ">", s.target_platform.name)
    if s.target_platform.name.lower() != "desktop":
        kind = "TCP" if ":" in s.adb_serial else "USB"
        table.add_row("ADB Endpoint", ">", f"{s.adb_serial} [dim]({kind})[/dim]")
        table.add_row("ADB Retries", ">", str(s.adb_retries))

    # Performance
    table.add_row("[bold cyan]PERFORMANCE[/bold cyan]", "", "")
    table.add_row(
        "Wait Multiplier",
        ">",
        f"[white]{s.wait_multiplier:.2f}x[/white] [dim]({_speed_hint(s.wait_multiplier)})[/dim]",
    )
    table.add_row(
        "Screen Navigation Multiplier",
        ">",
        f"[white]{s.wait_screen_nav_multiplier:.2f}x[/white] [dim]({_speed_hint(s.wait_screen_nav_multiplier)})[/dim]",
    )

    # Features
    table.add_row("[bold cyan]FEATURES[/bold cyan]", "", "")
    table.add_row("Data Sync", ">", _status(s.enable_sync))

    # Screens table
    enabled_screens = load_screens_from_config() or list(USER_FACING_SCREENS)
    total = len(USER_FACING_SCREENS)
    active = len(enabled_screens)

    scan = Table(
        show_header=True,
        header_style="bold cyan",
        box=None,
        padding=(0, 2),
        expand=True,
    )
    scan.add_column("#", style="dim", justify="right", width=3)
    scan.add_column("Screen", style="white", ratio=1)
    scan.add_column("Status", justify="right", no_wrap=True)

    for i, name in enumerate(USER_FACING_SCREENS, 1):
        is_on = name in enabled_screens
        scan.add_row(
            f"{i:02d}",
            name,
            "[bold green]Enabled[/bold green]" if is_on else "[dim]Disabled[/dim]",
        )

    body = Group(table, Text(""), scan)
    console.print(
        Panel(
            body,
            title="[bold cyan]Current Settings[/bold cyan]",
            subtitle=f"[dim]Enabled: {active}/{total} screens[/dim]",
            border_style="cyan",
            padding=(1, 2),
            expand=False,
        )
    )
