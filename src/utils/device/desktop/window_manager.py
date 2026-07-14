import mss
import numpy as np
import win32con
import win32gui
from windows_capture import Frame, InternalCaptureControl, WindowsCapture

from src.core.area import Region, Size


class WindowManager:
    # Windows-only constants for stripping the border/titlebar from the
    # window rect so captured pixels line up with in-game coordinates.
    BORDER_PX = 8
    TITLEBAR_PX = 30

    def __init__(self, window_name: str):
        self.window_name = window_name
        self.hwnd = self._find_window()
        # what we work on
        self.base_res = Size(1280, 720)
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

        # Find where the (0,0) of the game area is on the monitor
        point = win32gui.ClientToScreen(self.hwnd, (0, 0))

        if w <= 0 or h <= 0:
            # Fallback for minimized windows
            return Region(0, 0, 1280, 720)

        return Region(x=point[0], y=point[1], width=w, height=h)

        # full = Region(x=left, y=top, width=right - left, height=bottom - top)
        # Windows standard border/titlebar offsets
        # return Region(
        #     x=full.x + self.BORDER_PX,
        #     y=full.y + self.TITLEBAR_PX,
        #     width=full.width - (2 * self.BORDER_PX),
        #     height=full.height - self.TITLEBAR_PX - self.BORDER_PX,
        # )

    def get_screenshot(self) -> np.ndarray:
        """Try the first capture method, fallback to MSS."""
        try:
            return self._capture()
        except Exception:
            return self._capture_mss()

    def _capture(self):
        client = self.get_client_region()
        capture = WindowsCapture(window_name=self.window_name)
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

        left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
        full_width = right - left
        full_height = bottom - top

        # Crop offsets
        offset_x = (full_width - client.width) // 2
        # Usually, borders are equal on left/right, and the remainder is on top
        offset_y = full_height - client.height - offset_x

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

    def scale_coords(self, x: int, y: int):
        """Translates 1280x720 relative coords to absolute screen coords."""
        client_region = self.get_client_region()
        scale_x = client_region.width / self.base_res.width
        scale_y = client_region.height / self.base_res.height
        # return Region(
        #     x=int(client_region.x + (x * scale_x)),
        #     y=int(client_region.y + (y * scale_y)),
        #     width=int(client_region.width * scale_x),
        #     height=int(client_region.height * scale_y),
        # )

        return int(client_region.x + (x * scale_x)), int(
            client_region.y + (y * scale_y)
        )
