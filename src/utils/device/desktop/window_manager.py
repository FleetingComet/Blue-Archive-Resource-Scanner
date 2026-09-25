from ctypes import windll

import mss
import numpy as np
import win32con
import win32gui
from windows_capture import Frame, InternalCaptureControl, WindowsCapture

from src.core.area import Region


class WindowManager:
    PROCESS_PER_MONITOR_DPI_AWARE = 2

    def __init__(self, window_name: str):
        self.window_name = window_name
        # https://learn.microsoft.com/en-us/windows/win32/api/shellscalingapi/ne-shellscalingapi-process_dpi_awareness
        try:
            windll.shcore.SetProcessDpiAwareness(self.PROCESS_PER_MONITOR_DPI_AWARE)
        except Exception:  # noqa: BLE001
            try:
                windll.user32.SetProcessDPIAware(self.PROCESS_PER_MONITOR_DPI_AWARE)
            except Exception:  # noqa: BLE001, S110
                pass

        self.hwnd = self._find_window()
        self._last_known_region: Region | None = None
        self._bring_to_front()

    def _find_window(self):
        hwnd = win32gui.FindWindow(None, self.window_name)
        if not hwnd:
            raise RuntimeError(f"Window '{self.window_name}' not found.")
        return hwnd

    def _bring_to_front(self):
        if win32gui.IsIconic(self.hwnd):  # Check if minimized
            win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(self.hwnd)

    def get_client_region(self) -> Region:
        """Returns the inner region of the window (minus borders)."""
        # left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
        _, _, w, h = win32gui.GetClientRect(self.hwnd)

        if w <= 0 or h <= 0:
            if self._last_known_region is not None:
                return self._last_known_region

            self._bring_to_front()
            _, _, w, h = win32gui.GetClientRect(self.hwnd)
            if w <= 0 or h <= 0:
                raise RuntimeError(
                    f"'{self.window_name}' has no visible client area "
                    "(minimized?) and no prior region to fall back on."
                )

        # Find where the (0,0) of the game area is on the monitor
        point = win32gui.ClientToScreen(self.hwnd, (0, 0))
        region = Region(x=point[0], y=point[1], width=w, height=h)
        self._last_known_region = region

        return region

    def get_screenshot(self) -> np.ndarray:
        """Try the first capture method, fallback to MSS."""
        try:
            return self._capture()
        except Exception:  # noqa: BLE001
            return self._capture_mss()

    def _capture(self):
        client = self.get_client_region()
        # capture = WindowsCapture(window_name=self.window_name, cursor_capture=False)
        capture = WindowsCapture(
            window_hwnd=self.hwnd, cursor_capture=False, draw_border=False
        )

        image = None

        @capture.event
        def on_frame_arrived(frame: Frame, control: InternalCaptureControl):
            nonlocal image
            image = frame.convert_to_bgr().frame_buffer
            control.stop()

        @capture.event
        def on_closed():
            pass  # Required even if you don't use it

        capture.start()

        if image is None:
            return np.zeros((client.height, client.width, 3), dtype=np.uint8)

        img_h, img_w = image.shape[:2]

        diff_w = max(img_w - client.width, 0)
        diff_h = max(img_h - client.height, 0)

        offset_x = max(diff_w // 2, 0)
        offset_y = max(diff_h - 1, 0)

        return image[
            offset_y : offset_y + client.height, offset_x : offset_x + client.width
        ].copy()

    def _capture_mss(self):
        reg = self.get_client_region()
        with mss.mss() as sct:
            monitor = {
                "top": reg.y,
                "left": reg.x,
                "width": reg.width,
                "height": reg.height,
            }
            return np.array(sct.grab(monitor))[:, :, :3]
