import mss
import numpy as np
import win32con
import win32gui

from area import Location, Region, Size


class WindowCaptureMSS:
    def __init__(self, window_name):
        self.window_name = window_name
        self.hwnd = self._find_window()
        self._bring_to_front()

        # These are the screen coordinates of the top-left corner of the captured window
        full_region = self._get_window_region()

        # Account for the window border and titlebar and cut them off (Windows-specific values [Windows 10/11])
        window_border_pixels = 8
        window_titlebar_pixels = 30
        # Final game region (crop window)
        self.region = Region(
            x=full_region.x + window_border_pixels,
            y=full_region.y + window_titlebar_pixels,
            width=full_region.width - (window_border_pixels * 2),
            height=full_region.height - window_titlebar_pixels - window_border_pixels,
        )

    def _find_window(self):
        hwnd = win32gui.FindWindow(None, self.window_name)
        if not hwnd:
            raise Exception(f"Window '{self.window_name}' not found.")
        return hwnd

    def _bring_to_front(self):
        win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(self.hwnd)

    def _get_window_region(self) -> Region:
        left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
        return Region(x=left, y=top, width=right - left, height=bottom - top)

    def get_screenshot(self) -> np.ndarray:
        with mss.mss() as sct:
            img = sct.grab(
                {
                    "top": self.region.y,
                    "left": self.region.x,
                    "width": self.region.width,
                    "height": self.region.height,
                }
            )
            return np.array(img)[:, :, :3]  # RGB only

    def get_screen_position(self, obj: Location | Region) -> Location | Region:
        """
        Convert a game-relative coordinate to a screen coordinate
        by adding the window region's top-left offset.
        """
        if isinstance(obj, Location):
            return obj + self.region.location  # uses Location.__add__
        elif isinstance(obj, Region):
            return obj + self.region  # uses Region.__add__
        else:
            raise TypeError(f"Unsupported type: {type(obj).__name__}")

    def translate_from_base_resolution(
        self, base_region: Region, base_resolution=Size(1280, 720)
    ) -> Region:
        # No more subtraction here — region is already cropped
        actual_width = self.region.width
        actual_height = self.region.height

        scale_x = actual_width / base_resolution.width
        scale_y = actual_height / base_resolution.height

        return Region(
            x=int(base_region.x * scale_x),
            y=int(base_region.y * scale_y),
            width=int(base_region.width * scale_x),
            height=int(base_region.height * scale_y),
        )
