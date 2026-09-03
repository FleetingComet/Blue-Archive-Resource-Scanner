import logging

from src.core.config import AppSettings, TargetPlatform
from src.utils.device.adb.adb_device import ADBDevice
from src.utils.device.desktop.desktop_device import DesktopDevice
from src.utils.device.interfaces import DeviceController

logger = logging.getLogger("BA-Scanner")


def create_device(settings: AppSettings) -> DeviceController:
    platform_ = settings.target_platform
    if isinstance(platform_, TargetPlatform):
        platform_ = platform_.value

    if platform_ == TargetPlatform.DESKTOP.value:
        logger.info("Desktop mode selected.")
        return DesktopDevice()
    if platform_ in (TargetPlatform.EMULATOR.value, TargetPlatform.DEVICE.value):
        return ADBDevice(
            host=settings.adb_host,
            port=settings.adb_port,
        )
    raise ValueError(f"Unknown target_platform: {settings.target_platform!r}")
