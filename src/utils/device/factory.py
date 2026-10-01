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
        if not settings.adb_serial:
            raise ValueError(
                "adb_serial is empty - re-run the wizard with -e / --edit."
            )
        logger.info(f"ADB target: {settings.adb_serial}")
        return ADBDevice(serial=settings.adb_serial)
    raise ValueError(f"Unknown target_platform: {settings.target_platform!r}")
