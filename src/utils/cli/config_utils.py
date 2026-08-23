from rich.console import Console

from src.constant import SCREEN_DEFAULTS, USER_FACING_SCREENS
from src.core.config import Path_Config
from src.utils.data.io import read_json, write_json

SCREEN_CONFIG = Path_Config.CONFIG_DIR / "screen_config.json"
console = Console()


def load_screens_from_config() -> list[str]:
    """Read enabled screens from screen_config.json."""
    if not SCREEN_CONFIG.exists():
        return []

    try:
        screens = read_json(SCREEN_CONFIG)
    except ValueError:
        return []

    return [
        name
        for name, cfg in screens.items()
        if cfg.get("enabled", False) and name in USER_FACING_SCREENS
    ]


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
    enabled_screens = [*enabled_screens]

    if "Students" in enabled_screens and "Student" not in enabled_screens:
        enabled_screens.append("Student")

    # Start from code-level defaults
    screens: dict = {
        name: {**defaults, "enabled": False}
        for name, defaults in SCREEN_DEFAULTS.items()
    }

    # Merge existing file values (preserves menu_location, grid_type, etc.)
    if SCREEN_CONFIG.exists():
        try:
            on_disk = read_json(SCREEN_CONFIG)
        except ValueError as exc:
            console.print(
                f"[yellow]Warning: could not read existing screen config - {exc}[/yellow]"
            )
            on_disk = {}

        for name, disk_values in on_disk.items():
            if name in screens:
                # Overlay all keys except "enabled" - that is ours to set
                for k, v in disk_values.items():
                    if k != "enabled":
                        screens[name][k] = v
            else:
                # Unknown screen added manually - keep it untouched
                screens[name] = disk_values

    # Apply the launcher's enabled choices
    for name in screens:  # noqa: PLC0206
        screens[name]["enabled"] = name in enabled_screens

    write_json(SCREEN_CONFIG, screens)
