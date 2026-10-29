"""The Control Panel's theme configuration.

Uses ttkbootstrap's built-in 'bootstrap' theme family (bootstrap-light and
bootstrap-dark) without registering a custom theme, ensuring full compatibility
with the library's native palettes, backgrounds, and element styles.
"""

from __future__ import annotations

import sys

from ttkbootstrap import Theme

FAMILY = "rio"
LIGHT_THEME = f"{FAMILY}-light"
DARK_THEME = f"{FAMILY}-dark"


Theme(
    name=FAMILY,
    primary="#c81d25",
    secondary="#94a3b8",
    success="#10b981",
    info="#0284c7",
    warning="#d97706",
    danger="#dc2626",
    neutral="#8490a0",
    light={
        "background": "#f8fafc",
        "foreground": "#0f172a",
    },
    dark={
        "background": "#1d1d1d",
        "foreground": "#ffffff",
    },
).register()


def theme_name(dark: bool) -> str:
    """The registered variant for ``dark`` (the initial ``themename``)."""
    return DARK_THEME if dark else LIGHT_THEME


def theme_mode(dark: bool) -> str:
    """The ttkbootstrap mode word used by ``Window.theme_mode``."""
    return "dark" if dark else "light"


def apply_title_bar(window, dark: bool) -> None:
    """Ask the Windows compositor to paint the title bar to match the theme.

    Tk leaves the non-client area (the title bar) in the system light style even
    when the client area is dark. ``DWMWA_USE_IMMERSIVE_DARK_MODE`` is the
    documented Windows 10/11 switch; the attribute number changed once, so try
    both and ignore platforms/builds that do not support it. The call is purely
    cosmetic, so every failure is swallowed.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes

        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if not hwnd:
            return
        enabled = ctypes.c_int(1 if dark else 0)
        for attribute in (20, 19):  # new / pre-20H1 DWMWA_USE_IMMERSIVE_DARK_MODE
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                attribute,
                ctypes.byref(enabled),
                ctypes.sizeof(enabled),
            )
            if result == 0:
                break
    except Exception:  # noqa: BLE001 - cosmetic; old Windows or no DWM
        return
