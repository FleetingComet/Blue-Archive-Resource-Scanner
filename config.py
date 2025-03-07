import os


class Config:
    # ADB Settings
    ADB_HOST = "localhost"
    ADB_PORT = 16384  # Default MuMu Player 12 port

    # increase this if your device is laggy (eg. 1.1 or 1.8 or 2)
    WAIT_TIME_MULTIPLIER: float = 1.0

    # Screenshot paths
    SCREENSHOTS_DIR = "screenshots"
    SCREENSHOT_FILENAME = "latest_screenshot.png"
    SCREENSHOT_PATH = os.path.join(SCREENSHOTS_DIR, SCREENSHOT_FILENAME)

    # File paths for data handling
    OWNED_COUNTS_FILE = "output/owned_counts.json"
    OWNED_STUDENTS_FILE = "output/owned_students.json"
    EQUIPMENT_PROCESSED_FILE = "assets/data/equipment_processed.json"
    ITEMS_PROCESSED_FILE = "assets/data/items_processed.json"

    EQUIPMENT_OUTPUT_FILE = "output/equipment_final_values.json"
    ITEMS_OUTPUT_FILE = "output/items_final_values.json"

    CONVERTER_OUTPUT_FILE = "output/justin_planner.json"

    MERGER_INPUT_FILE = CONVERTER_OUTPUT_FILE
    MERGER_TO_FILE = "input/justin_data.json"
    MERGER_OUTPUT_FILE = "output/justin_data_final.json"

    @staticmethod
    def get_screenshot_path():
        return Config.SCREENSHOT_PATH
