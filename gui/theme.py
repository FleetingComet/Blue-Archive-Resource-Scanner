"""The Control Panel's ttkbootstrap 2.x theme family.

ttkbootstrap 2.0 replaced the separate pre-2.0 themes (``flatly``, ``darkly``,
...) with *theme families*: one set of accent colours generates a contrast-checked
``<name>-light`` and ``<name>-dark`` variant.  Declaring the family once keeps
the light and dark modes in sync (the same blue accent and the same semantic
success/warning/danger colours) and avoids the deprecation warnings the old
theme names produce.

The module is imported by :mod:`gui.app` before the root window exists;
``Theme.register()`` supports that and queues the variants until Tk starts.
"""

from __future__ import annotations

import sys

from ttkbootstrap.style import Theme

FAMILY = "bluearchive"
LIGHT_THEME = f"{FAMILY}-light"
DARK_THEME = f"{FAMILY}-dark"

Theme(
    name=FAMILY,
    primary="#4c8dff",
    success="#2fb56f",
    info="#4cc2ff",
    warning="#f2b134",
    danger="#e05a5a",
    neutral="#8a97a8",
    # A soft blue-tinted paper in light mode and a navy charcoal in dark mode.
    # The generated ramps pick the remaining surfaces, borders and hover states.
    light={"background": "#f4f7fb", "foreground": "#1b2733"},
    dark={"background": "#161c25", "foreground": "#e7edf5"},
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
    when the client area is dark.  ``DWMWA_USE_IMMERSIVE_DARK_MODE`` is the
    documented Windows 10/11 switch; the attribute number changed once, so try
    both and ignore platforms/builds that do not support it.  The call is purely
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
