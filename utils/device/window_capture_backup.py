from ctypes import windll

import numpy as np
import win32con
import win32gui
import win32ui

from area import Region, Size


class WindowCapture:
    def __init__(self, window_name=None):
        self.window_name = window_name
        self.hwnd = win32gui.FindWindow(None, window_name) if window_name else None
        if self.hwnd == 0:
            raise Exception(f"Window not found: {window_name}")

        self.update_window_bounds()

    def update_window_bounds(self):
        windll.user32.SetProcessDPIAware()
        rect = win32gui.GetWindowRect(self.hwnd)
        self.width = rect[2] - rect[0]
        self.height = rect[3] - rect[1]
        self.left = rect[0]
        self.top = rect[1]

        # account for the window border and titlebar and cut them off
        border_pixels = 8
        titlebar_pixels = 30
        # Final game region (crop window chrome)
        self.region = Region(
            x=self.left + border_pixels,
            y=self.top + titlebar_pixels,
            width=self.width - (border_pixels * 2),
            height=self.height - titlebar_pixels - border_pixels,
        )

    def get_screenshot(self) -> np.ndarray:
        self.update_window_bounds()

        hwindc = win32gui.GetWindowDC(self.hwnd)
        srcdc = win32ui.CreateDCFromHandle(hwindc)
        memdc = srcdc.CreateCompatibleDC()

        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(srcdc, self.width, self.height)
        memdc.SelectObject(bmp)

        memdc.BitBlt((0, 0), (self.width, self.height), srcdc, (0, 0), win32con.SRCCOPY)

        bmp_info = bmp.GetInfo()
        bmp_data = bmp.GetBitmapBits(True)

        img = np.frombuffer(bmp_data, dtype=np.uint8)
        img = img.reshape((self.height, self.width, 4))  # BGRA format

        srcdc.DeleteDC()
        memdc.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, hwindc)
        win32gui.DeleteObject(bmp.GetHandle())

        return img[..., :3]  # Convert BGRA to BGR

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
