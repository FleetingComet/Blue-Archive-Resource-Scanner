
import os

from utils.adb_controller import ADBController


screenshots_dir = "screenshots"
screenshot_path = os.path.join(screenshots_dir, "latest_screenshot.png")

adb_controller = ADBController()

if not adb_controller.capture_screenshot(screenshot_path):
    print("Failed to capture screenshot.")