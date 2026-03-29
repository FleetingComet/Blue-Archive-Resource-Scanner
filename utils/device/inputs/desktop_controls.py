import pyautogui
from area import Location, Region

pyautogui.FAILSAFE = False


class DesktopControls:
    """Window-aware input helper using pyautogui."""

    def __init__(self, window_capture) -> None:
        self.wc = window_capture

    def _to_screen(self, loc: Location) -> tuple[int, int]:
        return self.wc.region.x + loc.x, self.wc.region.y + loc.y

    def tap(self, loc: Location, *, duration_ms: int = 50) -> None:
        pyautogui.click(*self._to_screen(loc))

    def tap_xy(self, x: int, y: int, *, duration_ms: int = 50) -> None:
        self.tap(Location(x, y), duration_ms=duration_ms)

    def tap_center(self, region: Region, *, duration_ms: int = 50) -> None:
        self.tap(region.center, duration_ms=duration_ms)

    def tap_test(self, x: int, y: int, *, duration_ms: int = 50) -> None:
        pyautogui.click(*self._to_screen(Location(x, y)), duration=duration_ms)

    def swipe(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration_ms: int = 300,
    ) -> None:
        sx, sy = self._to_screen(Location(start_x, start_y))
        ex, ey = self._to_screen(Location(end_x, end_y))
        pyautogui.moveTo(sx, sy)
        pyautogui.dragTo(ex, ey, duration=duration_ms / 1000, button="left")

    def scroll(self, clicks: int) -> None:
        pyautogui.scroll(clicks)
