import subprocess
import logging


class ADBController:
    """Mumu port : 16384"""
    def __init__(self, host: str = "127.0.0.1", port: int = 16384):
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__)

    def connect(self) -> bool:
        """Connect to ADB device."""
        try:
            result = subprocess.run(
                f"adb connect {self.host}:{self.port}",
                shell=True,
                capture_output=True,
                text=True,
            )
            return "connected" in result.stdout.lower()
        except subprocess.SubprocessError as e:
            self.logger.error(f"Failed to connect to ADB: {e}")
            return False

    def execute_command(self, command: str) -> bool:
        """Execute an ADB shell command."""
        try:
            subprocess.run(f"adb -s {self.host}:{self.port} {command}", shell=True, check=True)
            return True
        except subprocess.SubprocessError as e:
            self.logger.error(f"Failed to execute ADB command: {e}")
            return False
    def capture_screenshot(self, save_path: str) -> bool:
        """
        Capture a screenshot from the device and save it to the specified path.

        Args:
            save_path (str): Path to save the screenshot.
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            command = f"adb -s {self.host}:{self.port} exec-out screencap -p > {save_path}"
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True
            )
            if result.returncode == 0:
                self.logger.info(f"Screenshot saved to {save_path}")
                return True
            else:
                self.logger.error(f"Failed to capture screenshot: {result.stderr}")
                return False
        except subprocess.SubprocessError as e:
            self.logger.error(f"Error capturing screenshot: {e}")
            return False
