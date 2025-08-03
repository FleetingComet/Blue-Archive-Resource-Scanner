import numpy as np
import win32gui
from windows_capture import WindowsCapture, Frame, InternalCaptureControl
from area import Region, Size


class WindowCapture:
    def __init__(self, window_name: str):
        self.window_name = window_name
        self.hwnd = self._find_window()

        self.border = 8
        self.titlebar = 30
        self.full_region = self._get_window_region()

        # Final client region (excluding border + titlebar)
        self.region = Region(
            x=self.full_region.x + self.border,
            y=self.full_region.y + self.titlebar,
            width=self.full_region.width - (2 * self.border),
            height=self.full_region.height - self.titlebar - self.border,
        )

    def _find_window(self):
        hwnd = win32gui.FindWindow(None, self.window_name)
        if not hwnd:
            raise RuntimeError(f"Window '{self.window_name}' not found.")
        return hwnd

    def _get_window_region(self):
        l, t, r, b = win32gui.GetWindowRect(self.hwnd)
        return Region(x=l, y=t, width=r - l, height=b - t)

    def get_screenshot(self) -> np.ndarray:
        capture = WindowsCapture(window_name=self.window_name)
        result = {"frame": None}

        @capture.event
        def on_frame_arrived(frame: Frame, control: InternalCaptureControl):
            img = frame.convert_to_bgr().frame_buffer
            result["frame"] = img
            control.stop()

        @capture.event
        def on_closed():
            pass  # Required even if you don't use it

        capture.start()

        if result["frame"] is None:
            return np.zeros((self.region.height, self.region.width, 3), dtype=np.uint8)

        # Optional: crop only to client area if needed
        img = result["frame"]
        offset_x = self.region.x - self.full_region.x
        offset_y = self.region.y - self.full_region.y

        return img[
            offset_y : offset_y + self.region.height,
            offset_x : offset_x + self.region.width,
        ]

    def translate_from_base_resolution(
        self,
        base_region: Region,
        base_resolution: Size = Size(1280, 720),
    ) -> Region:
        scale_x = self.region.width / base_resolution.width
        scale_y = self.region.height / base_resolution.height

        return Region(
            x=int(base_region.x * scale_x),
            y=int(base_region.y * scale_y),
            width=int(base_region.width * scale_x),
            height=int(base_region.height * scale_y),
        )
