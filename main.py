import argparse
import logging
from typing import Set

from src.core.config import Config
from src.core.navigator import ScreenNavigator
from src.core.state import ScreenState
from src.utils.data.equipment import EquipmentProcessor
from src.utils.data.item import ItemProcessor
from src.utils.data.student import StudentProcessor
from src.utils.device.factory import create_device
from src.utils.device.interfaces import DeviceController
from src.utils.sync.data_sync_manager import DataSyncManager

logger = logging.getLogger("BA-Scanner")


def run_post_processing(visited_screens: Set[str]):
    """
    Only runs processors if the corresponding screen
    was actually successfully scanned.
    """
    processor_map = {
        "Equipment": EquipmentProcessor,
        "Items": ItemProcessor,
        "Students": StudentProcessor,
    }

    for screen_name, ProcessorClass in processor_map.items():
        if screen_name in visited_screens:
            try:
                logger.info(f"Post-processing {screen_name} data...")
                ProcessorClass().process()
            except Exception as e:
                logger.error(f"Failed to process {screen_name}: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--offline", action="store_true", help="Skip data sync and any network calls"
    )
    args = parser.parse_args()

    Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Sync Data
    # Sync if CLI is NOT offline AND settings say Enable Sync is True
    if not args.offline and Config.settings.enable_sync:
        try:
            DataSyncManager().update_from_online()
        except Exception:
            pass

    # Create device controller based on platform
    device = create_device(Config.settings)

    if not device.connect(Config.ADB_RETRIES):
        logger.error("❌ Failed to connect to ADB.")
        exit(1)

    mainpage(device)


def mainpage(device: DeviceController):
    """
    Handles navigation and starts the matching process.
    Logic:
      - If the current screen is None (meaning we're either on Home or on a Page),
        if we're on a Page then a. go Home if that certain screen is finished, b. start immediately.
      - Then loop through each screen defined.
      - Skip already visited screens.
      - If not on the target screen, navigate to it.
        For "Students" and "Student", these are accessed without using the Menu Tab.
      - If navigation is successful, call the matching process (or get info).
    """
    navigator = ScreenNavigator(device)
    state = ScreenState(navigator)

    if state.run():
        run_post_processing(state.visited)
    else:
        logger.warning("⚠️ Matching process failed or was interrupted.")


if __name__ == "__main__":
    main()
