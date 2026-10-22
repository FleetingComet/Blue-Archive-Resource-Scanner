import ctypes
import logging
import threading
import time
from ctypes import windll, wintypes

import cv2
import mss
import numpy as np
import pywintypes
import win32con
import win32gui
from windows_capture import Frame, InternalCaptureControl, WindowsCapture

from src.core.area import Region, Size
from src.utils.device.interfaces import DeviceUnavailableError

logger = logging.getLogger("BA-Scanner")

BASE_RES = Size(1280, 720)
UNITY_WINDOW_CLASS = "UnityWndClass"
DWMWA_EXTENDED_FRAME_BOUNDS = 9
DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
CAPTURE_TIMEOUT_S = 2.0
FOCUS_WAIT_S = 60


def set_dpi_awareness():
    """
    Make window rects, captures and clicks all use physical pixels.
    Must run before pyautogui is imported: it calls SetProcessDPIAware()
    (system-aware) at import time, and the first awareness call wins.
    """
    # https://learn.microsoft.com/en-us/windows/win32/hidpi/dpi-awareness-context
    try:
        windll.user32.SetProcessDpiAwarenessContext(
            ctypes.c_void_p(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)
        )
    except AttributeError:  # Older than Windows 10 1703
        windll.shcore.SetProcessDpiAwareness(2)


def find_game_window(title: str, window_class: str | None = None) -> int:
    """
    Visible top-level window with exactly this title, preferring Unity's player
    window. Pass window_class to accept only that kind of window.
    """
    matches = []

    def collect(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd) == title:
            matches.append(hwnd)
        return True

    win32gui.EnumWindows(collect, None)
    if window_class is not None:
        matches = [h for h in matches if win32gui.GetClassName(h) == window_class]
    if not matches:
        raise DeviceUnavailableError(
            f"Window '{title}' not found. Is the game running?"
        )

    unity = [h for h in matches if win32gui.GetClassName(h) == UNITY_WINDOW_CLASS]
    return (unity or matches)[0]


def crop_to_client(image: np.ndarray, frame: Region, client: Region) -> np.ndarray:
    """Cut the client area out of a capture of the whole window frame."""
    x, y = client.x - frame.x, client.y - frame.y
    crop = image[y : y + client.height, x : x + client.width]
    if (
        x < 0
        or y < 0
        or image.shape[:2] != (frame.height, frame.width)
        or crop.shape[:2] != (client.height, client.width)
    ):
        raise RuntimeError(
            f"Capture {image.shape[1]}x{image.shape[0]} does not match the "
            f"{frame.width}x{frame.height} window, or the window moved."
        )
    return crop


def to_base_resolution(image: np.ndarray) -> np.ndarray:
    """Scale a client-area capture to the 1280x720 every search region is measured in."""
    h, w = image.shape[:2]
    if (w, h) == (BASE_RES.width, BASE_RES.height):
        return image
    interpolation = cv2.INTER_AREA if w > BASE_RES.width else cv2.INTER_CUBIC
    return cv2.resize(
        image, (BASE_RES.width, BASE_RES.height), interpolation=interpolation
    )


class WindowManager:
    def __init__(self, window_name: str):
        self.window_name = window_name
        self.hwnd = find_game_window(window_name)
        self.window_class = win32gui.GetClassName(self.hwnd)

    def _ensure_window(self):
        """Re-find the window if the game was restarted, never a different kind of window."""
        if not win32gui.IsWindow(self.hwnd):
            self.hwnd = find_game_window(self.window_name, self.window_class)

    def activate(self):
        """
        Restore and focus the game window, since clicks land on whatever is on top.
        Windows may refuse to hand focus to a background process. Then wait for
        the user to click the game window, which also pauses the scan meanwhile.
        """
        self._ensure_window()
        if win32gui.IsIconic(self.hwnd):
            win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
        if win32gui.GetForegroundWindow() == self.hwnd:
            return

        try:
            win32gui.SetForegroundWindow(self.hwnd)
        except pywintypes.error:
            pass

        deadline = time.monotonic() + FOCUS_WAIT_S
        if win32gui.GetForegroundWindow() != self.hwnd:
            logger.warning(f"Click the '{self.window_name}' window to continue.")
        while win32gui.GetForegroundWindow() != self.hwnd:
            if time.monotonic() > deadline:
                raise DeviceUnavailableError(f"'{self.window_name}' did not get focus.")
            time.sleep(0.2)

    def get_client_region(self) -> Region:
        """The game area (client area) of the window, in screen coordinates."""
        self._ensure_window()
        if win32gui.IsIconic(self.hwnd):
            raise RuntimeError(f"'{self.window_name}' is minimized.")

        _, _, w, h = win32gui.GetClientRect(self.hwnd)
        if w <= 0 or h <= 0:
            raise RuntimeError(f"'{self.window_name}' has no visible game area.")

        x, y = win32gui.ClientToScreen(self.hwnd, (0, 0))
        return Region(x=x, y=y, width=w, height=h)

    def _frame_bounds(self) -> Region:
        """
        Window bounds as Windows Graphics Capture sees them. GetWindowRect also
        counts the invisible resize borders, which would shift the crop.
        """
        rect = wintypes.RECT()
        failed = windll.dwmapi.DwmGetWindowAttribute(
            wintypes.HWND(self.hwnd),
            DWMWA_EXTENDED_FRAME_BOUNDS,
            ctypes.byref(rect),
            ctypes.sizeof(rect),
        )
        if failed:
            rect.left, rect.top, rect.right, rect.bottom = win32gui.GetWindowRect(
                self.hwnd
            )
        return Region(
            rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top
        )

    def get_screenshot(self) -> np.ndarray:
        """Client area at its native size. Try WGC first, fall back to MSS."""
        try:
            return self._capture()
        except DeviceUnavailableError:
            raise
        except Exception as e:  # noqa: BLE001
            logger.debug(f"WGC capture failed ({e}), falling back to MSS.")
            return self._capture_mss()

    def _capture(self) -> np.ndarray:
        self.get_client_region()  # Fail fast (minimized) before starting a session
        capture = WindowsCapture(cursor_capture=False, window_hwnd=self.hwnd)
        image = None
        arrived = threading.Event()

        @capture.event
        def on_frame_arrived(frame: Frame, control: InternalCaptureControl):
            nonlocal image
            # The buffer is native memory that is reused after this callback returns
            image = frame.convert_to_bgr().frame_buffer.copy()
            arrived.set()
            control.stop()

        @capture.event
        def on_closed():
            pass  # Required even if you don't use it

        # ponytail: one capture session per screenshot, keep a session open if capture latency matters
        control = capture.start_free_threaded()
        got_frame = arrived.wait(CAPTURE_TIMEOUT_S)
        if not got_frame:
            control.stop()
            raise RuntimeError("No frame arrived from Windows Graphics Capture.")
        control.wait()

        # Read both rects together, the window may have moved during the session
        client, frame = self.get_client_region(), self._frame_bounds()
        return crop_to_client(image, frame, client)

    def _capture_mss(self) -> np.ndarray:
        """Grabs screen pixels, so the game window has to be on top."""
        self.activate()
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
        scale_x = client_region.width / BASE_RES.width
        scale_y = client_region.height / BASE_RES.height
        return int(client_region.x + (x * scale_x)), int(
            client_region.y + (y * scale_y)
        )

    def owns_point(self, x: int, y: int) -> bool:
        """True if a click at this screen point would reach the game window."""
        hwnd = win32gui.WindowFromPoint((x, y))
        return bool(hwnd) and win32gui.GetAncestor(hwnd, win32con.GA_ROOT) == self.hwnd
