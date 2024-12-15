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
    OWNED_COUNTS_FILE = "owned_counts.json"
    EQUIPMENT_PROCESSED_FILE = "assets/data/equipment_processed.json"
    
    OUTPUT_FILE = "final_values.json"
    CONVERTER_INPUT_FILE = OUTPUT_FILE
    CONVERTER_OUTPUT_FILE = "justin_planner.json"
    
    @staticmethod
    def get_screenshot_path():
        return Config.SCREENSHOT_PATH
