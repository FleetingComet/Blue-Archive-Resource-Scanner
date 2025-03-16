from pathlib import Path

from typed_dict import MergerDict, OutputFilesDict, OwnedDict, ProcessedDataDict


class Config:
    # ADB Settings
    ADB_HOST = "localhost"
    ADB_PORT = 16384  # Default MuMu Player 12 port

    # increase this if your device is laggy (eg. 1.1 or 1.8 or 2)
    WAIT_TIME_MULTIPLIER: float = 1.0

    # Base Directories
    BASE_DIR = Path(__file__).parent
    ASSETS_DIR = BASE_DIR / "assets"
    OUTPUT_DIR = BASE_DIR / "output"
    INPUT_DIR = BASE_DIR / "input"
    OWNED_DIR = BASE_DIR / OUTPUT_DIR / "owned"
    SCREENSHOTS_DIR = BASE_DIR / "screenshots"
    SCREENSHOT_FILENAME = "latest_screenshot.png"
    SCREENSHOT_PATH = SCREENSHOTS_DIR / SCREENSHOT_FILENAME

    OWNED: OwnedDict = {
        "counts": OWNED_DIR / "scanned_counts.json",
        "students": OWNED_DIR / "scanned_students.json",
        "currencies": OWNED_DIR / "scanned_currencies.json",
    }

    PROCESSED_DATA: ProcessedDataDict = {
        "equipment": ASSETS_DIR / "data/equipment_processed.json",
        "items": ASSETS_DIR / "data/items_processed.json",
        "students": ASSETS_DIR / "data/students_processed.json",
    }

    OUTPUT_FILES: OutputFilesDict = {
        "equipment": OUTPUT_DIR / "equipment_final_values.json",
        "items": OUTPUT_DIR / "items_final_values.json",
        "students": OUTPUT_DIR / "students_final_values.json",
        # Take all 3 above and construct them according to justin planner data structure
        # planning to support other tools in the future
        "converter_justin": OUTPUT_DIR / "converted_to_justin_planner.json",
        "merger": OUTPUT_DIR / "justin_data_final.json",
    }

    MERGER: MergerDict = {
        "input": OUTPUT_DIR / "converted_to_justin_planner.json",
        "to_file": INPUT_DIR / "justin_data.json",
        "output": OUTPUT_DIR / "justin_data_final.json",
    }

    # # File paths for data handling
    # OWNED_COUNTS_FILE = "output/owned/scanned_counts.json"
    # OWNED_STUDENTS_FILE = "output/owned/scanned_students.json"
    # OWNED_CURRENCIES_FILE = "output/owned/scanned_currencies.json"

    # EQUIPMENT_PROCESSED_FILE = "assets/data/equipment_processed.json"
    # ITEMS_PROCESSED_FILE = "assets/data/items_processed.json"
    # STUDENTS_PROCESSED_FILE = "assets/data/students_processed.json"

    # EQUIPMENT_OUTPUT_FILE = "output/equipment_final_values.json"
    # ITEMS_OUTPUT_FILE = "output/items_final_values.json"
    # STUDENTS_OUTPUT_FILE = "output/students_final_values.json"

    # CONVERTER_OUTPUT_FILE = "output/justin_planner.json"

    # MERGER_INPUT_FILE = CONVERTER_OUTPUT_FILE
    # MERGER_TO_FILE = "input/justin_data.json"
    # MERGER_OUTPUT_FILE = "output/justin_data_final.json"

    @staticmethod
    def get_screenshot_path():
        return Config.SCREENSHOT_PATH
