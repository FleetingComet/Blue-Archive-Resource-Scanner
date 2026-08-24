"""
Centralized wait/delay logic for the scanner.

  wait(seconds, nav=False)
      Sleeps `seconds`, scaled by Config.settings.wait_multiplier
      (and also wait_screen_nav_multiplier if nav=True).

  wait_until(condition, timeout=5.0, interval=0.2, nav=False)
      Polls `condition()` every `interval` seconds until it returns True
      or `timeout` is reached. Use this instead of a fixed sleep whenever
      you can actually check "did the thing I'm waiting for happen yet?"
      (e.g. "has the screen changed", "did the button appear").
      Returns True if the condition was met, False if it timed out.

Usage:
    from src.utils.wait_utils import wait, wait_until

    wait(2.0, nav=True)

    changed = wait_until(lambda: navigator.at_home(), timeout=5)
    if not changed:
        logger.warning("Never reached Home screen.")
"""

import logging
import time

from src.core.config import Config

logger = logging.getLogger("BA-Scanner")


def _multiplier(nav: bool) -> float:
    mult = Config.settings.wait_multiplier
    if nav:
        mult *= Config.settings.wait_screen_nav_multiplier
    return mult


def wait(seconds: float, nav: bool = False) -> None:
    """Sleep for `seconds`, scaled by the configured wait multipliers."""
    duration = seconds * _multiplier(nav)
    logger.debug(
        f"[dim]wait: sleeping {duration:.2f}s (base={seconds}, nav={nav})[/dim]"
    )
    time.sleep(duration)


def wait_until(
    condition,
    timeout: float = 5.0,
    interval: float = 0.2,
    nav: bool = False,
) -> bool:
    """
    Poll `condition()` (a zero-arg callable returning bool) until it's True
    or `timeout` seconds pass. Both timeout and interval are scaled by the
    same wait multipliers as `wait()`.

    Returns:
        True if `condition()` became True, False if it timed out.
    """
    mult = _multiplier(nav)
    deadline = time.monotonic() + timeout * mult
    scaled_interval = interval * mult

    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(scaled_interval)

    logger.debug(f"[yellow]wait_until: timed out after {timeout}s[/yellow]")
    return False
