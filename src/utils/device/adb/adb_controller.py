import logging
import platform
import re
import subprocess
import threading
import time

import cv2
import numpy as np


def list_adb_devices() -> list[tuple[str, str]]:
    """
    Return [(serial, state), ...] as reported by `adb devices`.
    state is usually 'device', 'offline', 'unauthorized'.
    """
    try:
        result = subprocess.run(
            "adb devices",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        return []

    devices: list[tuple[str, str]] = []
    for line in result.stdout.splitlines()[1:]:  # skip "List of devices attached"
        line = line.strip()
        if not line:
            continue
        parts = re.split(r"\s+", line)
        if len(parts) >= 2:
            devices.append((parts[0], parts[1]))
    return devices


class ADBController:
    _instance = None  # Singleton instance
    _lock = threading.Lock()
    latest_screenshot = None

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance of ADBController exists (Singleton Pattern)."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    # Mumu port : 16384
    def __init__(self, serial: str):
        """
        Two modes:
          - Physical/USB device: pass `serial` (e.g. '123456789A123456').
          - Emulator or TCP:   pass `host` + `port` (or leave defaults).
        If `serial` is set, `host:port` are ignored for `-s` targeting,
        but `adb connect` is still attempted if the serial looks like host:port.
        """
        if not serial or not serial.strip():
            raise ValueError("ADBController requires a non-empty serial/target.")
        self.serial = serial.strip()
        self.logger = logging.getLogger(__name__)

    @property
    def device_id(self) -> str:
        """The value passed to `adb -s <device_id>`."""
        return self.serial

    def _is_tcp_serial(self) -> bool:
        """True if the serial looks like 'host:port' (an emulator)."""
        return bool(self.serial and re.match(r"^[\w\.\-]+:\d+$", self.serial))

    def connect(self, retries: int = 3, delay: float = 2.0) -> bool:
        """
        Ensure the target is reachable.
          - If `serial` is a USB serial -> verify it appears in `adb devices`.
          - If `serial` is 'host:port' or `serial` is None -> `adb connect host:port`.
        """
        is_tcp = self._is_tcp_target()

        for attempt in range(1, retries + 1):
            state = dict(list_adb_devices()).get(self.serial)
            if state == "device":
                self.logger.info(f"Device {self.serial} ready.")
                return True
            if state == "unauthorized":
                self.logger.error(
                    f"Device {self.serial} is unauthorized. "
                    "Accept the USB debugging prompt on the phone."
                )
                return False
            self.logger.warning(
                f"Attempt {attempt}: device {self.serial} not found "
                f"(state={state!r})."
            )
            # For TCP targets, try `adb connect` first.
            if is_tcp:
                try:
                    result = subprocess.run(
                        f"adb connect {self.serial}",
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=10,
                        check=False,
                    )
                    output = result.stdout.lower()
                    self.logger.info(
                        f"adb connect {self.serial} (attempt {attempt}): {output.strip()}"
                    )
                    if "connected" in output or "already connected" in output:
                        return True

                except subprocess.TimeoutExpired:
                    self.logger.error(
                        f"ADB connect {self.serial} attempt {attempt} timed out."
                    )
                except subprocess.SubprocessError as e:
                    self.logger.error(
                        f"Failed to connect to ADB (attempt {attempt}): {e}"
                    )

            if attempt < retries:
                time.sleep(delay)

        self.logger.error(f"Could not reach ADB target: {self.serial}")
        return False

    def execute_command(self, command: str) -> bool:
        """Execute an ADB shell command."""
        try:
            subprocess.run(f"adb -s {self.device_id} {command}", shell=True, check=True)
            return True
        except subprocess.SubprocessError as e:
            self.logger.error(f"Failed to execute ADB command: {e}")
            return False

    def capture_screenshot(self) -> np.ndarray | None:
        """
        Capture a screenshot from the device and return it as an OpenCV image held in memory.

        Returns:
            np.ndarray: The captured image if successful, or None otherwise.
        """
        logger = self.logger
        try:
            # On Unix-like hosts, redirect screencap stderr into /dev/null to avoid
            # malformed PNGs caused by stray stderr output (e.g. AMD GPU bug).
            # Thanks to execv@discord
            if (
                platform.system() == "Windows"
            ):  # Windows (NT-family) idk if os.name="nt" works
                logger.debug("Windows (NT-family) detected")
                command = f"adb -s {self.device_id} exec-out screencap -p"
            else:
                logger.debug("Unix-like system detected")
                command = f"adb -s {self.device_id} exec-out 'screencap -p 2>/dev/null'"
            logger.debug(f"ADBController: Running command: {command}")
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=False,
                timeout=8,
                check=False,
            )
            if result.returncode == 0:
                # Convert the byte output to an OpenCV image.
                image_data = np.frombuffer(result.stdout, dtype=np.uint8)
                img = cv2.imdecode(image_data, cv2.IMREAD_UNCHANGED)
                ADBController.latest_screenshot = img
                logger.debug("ADBController: Screenshot captured successfully.")
                return img

            logger.error(f"Failed to capture screenshot: {result.stderr}")
            return None
        except subprocess.TimeoutExpired:
            logger.error("ADBController: capture_screenshot timed out.")
            return None
        except subprocess.SubprocessError as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None

    @classmethod
    def get_latest_screenshot(cls) -> np.ndarray | None:
        """Returns the latest captured screenshot or None."""
        return cls.latest_screenshot
