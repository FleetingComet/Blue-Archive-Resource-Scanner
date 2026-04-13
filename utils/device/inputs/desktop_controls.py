import pyautogui

from area import Location, Region, Size

# pyautogui.FAILSAFE = False

class DesktopControls:
    """Window-aware input helper using pyautogui."""

    def __init__(self, window_capture) -> None:
        self.wc = window_capture

    def _to_screen(self, loc: Location) -> tuple[int, int]:
        return self.wc.region.x + loc.x, self.wc.region.y + loc.y

    def tap(self, loc: Location, *, duration_ms: int = 50) -> None:
        pyautogui.click(*self._to_screen(loc))

    def tap_xy(self, x: int, y: int, *, duration_ms: int = 50) -> None:
        scaled = self._scale_from_base(Location(x, y))
        sx, sy = self._to_screen(scaled)
        pyautogui.click(sx, sy)
        # self.tap(Location(x, y), duration_ms=duration_ms)

    def tap_center(self, region: Region, *, duration_ms: int = 50) -> None:
        self.tap(region.center, duration_ms=duration_ms)

    def tap_test(self, x: int, y: int, *, duration_ms: int = 50) -> None:
        to_click = self.test_translate_from_base_resolution(
            x, y, Size(pyautogui.size().width, pyautogui.size().height)
        )
        print(f"TO CLICK : {to_click}")
        pyautogui.click(*self._to_screen(Location(x, y)), duration=duration_ms)

        # pyautogui.size()
    def _scale_from_base(self, loc: Location, base: Size = Size(1280, 720)) -> Location:
        scale_x = self.wc.region.width  / base.width
        scale_y = self.wc.region.height / base.height
        return Location(int(loc.x * scale_x), int(loc.y * scale_y))

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

    def test_translate_from_base_resolution(
        self,
        x: int,
        y: int,
        base_resolution: Size = Size(1280, 720),
    ) -> Location:
        scale_x = self.wc.region.width / base_resolution.width
        scale_y = self.wc.region.height / base_resolution.height
        print(f"Scale: {scale_x = } {scale_y = }")
        print(f"Base Reso: {base_resolution.width = } {base_resolution.height = }")
        print(f"Self Window Capture: {self.wc.region.width = } {self.wc.region.height = }")
        print(f"Original {x = }, {y = }")
        print(f"Result x= {x * scale_x}, y= {y * scale_y}")

        return Location(
            x=int(x * scale_x),
            y=int(y * scale_y),
        )
