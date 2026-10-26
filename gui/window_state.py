"""Persisted window state: geometry, page, log layout and theme.

Stored in ``config/gui_state.json``; every field is optional and validated on
load, so a missing or damaged file just means defaults.
"""

from __future__ import annotations

import json
import re
import sys
import tkinter as tk

from src.core.paths import Path_Config

STATE_FILE = Path_Config.CONFIG_DIR / "gui_state.json"
VISIBLE_MARGIN = 80  # how much of a restored window must be on the desktop


def load() -> dict:
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save(data: dict) -> None:
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass  # best-effort


def asset_base_url(data: dict | None = None) -> str:
    """The saved remote artwork base (blank = the schaledb default)."""
    state = load() if data is None else data
    value = state.get("asset_base_url")
    return value if isinstance(value, str) else ""


def save_field(key: str, value: object) -> None:
    """Merge one value into the saved state without touching the rest."""
    data = load()
    data[key] = value
    save(data)


def desktop_bounds(root: tk.Misc) -> tuple[int, int, int, int]:
    """Desktop ``(x, y, width, height)``, spanning every monitor when known."""
    if sys.platform == "win32":
        try:
            import ctypes

            metrics = ctypes.windll.user32.GetSystemMetrics
            x, y, width, height = metrics(76), metrics(77), metrics(78), metrics(79)
            if width > 0 and height > 0:
                return x, y, width, height
        except Exception:  # noqa: BLE001, S110 - fall back to Tk's own view
            pass
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


def fit_geometry(geometry: str, bounds: tuple[int, int, int, int]) -> str | None:
    """Fit ``geometry`` to the desktop; None if it cannot be parsed.

    A saved position can point at a monitor that is gone, which looks exactly
    like the GUI failing to start. Sizes are clamped and an unreachable
    position is replaced by a centred one.
    """
    match = re.fullmatch(r"(\d+)x(\d+)(?:([+-]\d+)([+-]\d+))?", geometry.strip())
    if match is None:
        return None

    origin_x, origin_y, screen_w, screen_h = bounds
    width = min(max(int(match.group(1)), 400), screen_w)
    height = min(max(int(match.group(2)), 300), screen_h)
    if match.group(3) is None:
        return f"{width}x{height}"

    x, y = int(match.group(3)), int(match.group(4))
    reachable = (
        origin_x + VISIBLE_MARGIN < x + width
        and x < origin_x + screen_w - VISIBLE_MARGIN
        and origin_y + VISIBLE_MARGIN < y + height
        and y < origin_y + screen_h - VISIBLE_MARGIN
    )
    if not reachable:
        x = origin_x + max(0, (screen_w - width) // 2)
        y = origin_y + max(0, (screen_h - height) // 3)
    # Tk wants "-1100" (not "+-1100") for a monitor left of the origin.
    return f"{width}x{height}{x:+d}{y:+d}"
