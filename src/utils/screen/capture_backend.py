import platform

from src.core.config import Config
from src.utils.device.adb_controller import ADBController
from src.utils.device.adbscreencapture import ADBScreenCapture
from src.utils.device.inputs.adb_input import ADBInputController
from src.utils.device.inputs.desktop_input import DesktopInputController
from src.utils.device.inputs.input_controller import InputController
from src.utils.device.window_capture import WindowCapture
from src.utils.screen.desktop_screenshot import (
    DesktopScreenCapture,
)
from src.utils.screen.screenshot_provider import ScreenshotProvider


def get_capture_backend(target: str) -> ScreenshotProvider:
    """Returns screenshot provider for the target platform."""

    if target == "desktop":
        return DesktopScreenCapture(window_name="Blue Archive", capture_interval=0.5)
    elif target in ["emulator", "device"]:
        adb_controller = ADBController(host=Config.ADB_HOST, port=Config.ADB_PORT)
        return ADBScreenCapture(adb_controller, Config.CAPTURE_INTERVAL)
    else:
        raise ValueError("Unknown target platform")


def get_input_controller(target: str, window_capture=None) -> InputController:
    """Returns input controller for the target platform."""
    if target == "desktop":
        if window_capture is None:
            window_capture = _get_window_capture_backend("Blue Archive")
        return DesktopInputController(window_capture)
    elif target in ["emulator", "device"]:
        adb_controller = ADBController(host=Config.ADB_HOST, port=Config.ADB_PORT)
        return ADBInputController(adb_controller)
    else:
        raise ValueError(f"Unknown target platform: {target}")


def get_desktop_components(window_name: str = "Blue Archive"):
    """
    Factory for Desktop mode - returns shared WindowCapture instance
    for both screenshot and input to avoid duplication.
    """
    window_capture = _get_window_capture_backend(window_name)
    screencap = DesktopScreenCapture(window_name=window_name, capture_interval=0.5)
    # Pass the same window_capture to screencap
    screencap.window_capture_backend = window_capture
    input_controller = DesktopInputController(window_capture)
    return screencap, input_controller, window_capture


def _get_window_capture_backend(window_name: str):
    """Function that returns the right window capture backend."""
    if platform.system() == "Windows":
        return WindowCapture(window_name)
    else:
        from src.utils.device.window_capture_mss import WindowCaptureMSS

        return WindowCaptureMSS(window_name)


def get_adb_components():
    """
    Factory for ADB mode - returns shared ADBController instance
    for both screenshot and input to avoid duplication.
    """
    adb_controller = ADBController(host=Config.ADB_HOST, port=Config.ADB_PORT)
    screencap = ADBScreenCapture(adb_controller, Config.CAPTURE_INTERVAL)
    input_controller = ADBInputController(adb_controller)
    return screencap, input_controller, adb_controller
