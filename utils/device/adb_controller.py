import logging
import subprocess
import threading
import time
from typing import Optional

import cv2
import numpy as np


class ADBController:
    _instance = None  # Singleton instance
    _lock = threading.Lock()
    latest_screenshot = None

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance of ADBController exists (Singleton Pattern)."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ADBController, cls).__new__(cls)
        return cls._instance

    def __init__(self, host: str = "localhost", port: int = 16384):
        """Mumu port : 16384"""
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__)

    def connect(self, retries: int = 3, delay: float = 2.0) -> bool:
        """
        Connect to ADB device, retrying if necessary.
        Returns True if connected, False otherwise.
        """
        for attempt in range(1, retries + 1):
            try:
                result = subprocess.run(
                    f"adb connect {self.host}:{self.port}",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                output = result.stdout.lower()
                if (
                    "connected" in output
                    or "already connected" in output
                    or "unable to connect" not in output
                ):
                    self.logger.info(f"ADB connect attempt {attempt}: {output.strip()}")
                    return True
                else:
                    self.logger.warning(
                        f"ADB connect attempt {attempt} failed: {output.strip()}"
                    )
            except subprocess.TimeoutExpired:
                self.logger.error(f"ADB connect attempt {attempt} timed out.")
            except subprocess.SubprocessError as e:
                self.logger.error(f"Failed to connect to ADB (attempt {attempt}): {e}")
            if attempt < retries:
                time.sleep(delay)
        return False

    def execute_command(self, command: str) -> bool:
        """Execute an ADB shell command."""
        try:
            subprocess.run(
                f"adb -s {self.host}:{self.port} {command}", shell=True, check=True
            )
            return True
        except subprocess.SubprocessError as e:
            self.logger.error(f"Failed to execute ADB command: {e}")
            return False

    def capture_screenshot(self) -> Optional[np.ndarray]:
        """
        Capture a screenshot from the device and return it as an OpenCV image held in memory.

        Returns:
            np.ndarray: The captured image if successful, or None otherwise.
        """
        logger = self.logger
        try:
            command = f"adb -s {self.host}:{self.port} exec-out screencap -p"
            logger.debug(f"ADBController: Running command: {command}")
            result = subprocess.run(
                command, shell=True, capture_output=True, text=False, timeout=8
            )
            if result.returncode == 0:
                # Convert the byte output to an OpenCV image.
                image_data = np.frombuffer(result.stdout, dtype=np.uint8)
                img = cv2.imdecode(image_data, cv2.IMREAD_UNCHANGED)
                ADBController.latest_screenshot = img
                logger.debug("ADBController: Screenshot captured successfully.")
                return img
            else:
                logger.error(f"Failed to capture screenshot: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            logger.error("ADBController: capture_screenshot timed out.")
            return None
        except subprocess.SubprocessError as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None

    @classmethod
    def get_latest_screenshot(cls) -> Optional[np.ndarray]:
        """Returns the latest captured screenshot or None."""
        return cls.latest_screenshot
