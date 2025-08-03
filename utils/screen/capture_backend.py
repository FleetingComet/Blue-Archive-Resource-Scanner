from config import Config
from utils.device.adb_controller import ADBController
from utils.device.adbscreencapture import ADBScreenCapture
from utils.screen.desktop_screenshot import DesktopScreenCapture
from utils.screen.screenshot_provider import ScreenshotProvider


def get_capture_backend(target: str) -> ScreenshotProvider:
    if target == "desktop":
        return DesktopScreenCapture(window_name="Blue Archive", capture_interval=0.5)
    elif target == "android":
        adb_controller = ADBController(host=Config.ADB_HOST, port=Config.ADB_PORT)
        return ADBScreenCapture(adb_controller, Config.CAPTURE_INTERVAL)
    else:
        raise ValueError("Unknown target platform")