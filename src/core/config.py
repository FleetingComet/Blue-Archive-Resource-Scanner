import json
from pathlib import Path

from pydantic import BaseModel


class UserSettings(BaseModel):
    # ADB Settings
    adb_host: str = "127.0.0.1"  # or "localhost"
    adb_port: int = 16384  # Default MuMu Player 12 port

    # increase this if your device is laggy (eg. 1.1 or 1.8 or 2)
    wait_multiplier: float = 1.0
    # Multiplier specifically for screen navigation delays (use for slower screen loads)
    wait_screen_nav_multiplier: float = 2.0
    capture_interval: float = 0.5  # seconds between captures
    enable_sync: bool = False
    target_platform: str = "emulator"  # emulator, desktop, device

    adb_retries: int = 3  # Retries the connection up to retries times (default 3).


class Config:
    # --- Directories ---
    BASE_DIR = Path(__file__).parent

    path = Path(__file__).resolve()

    while not (path / "main.py").exists():
        if path.parent == path:
            raise RuntimeError("Could not locate project root.")
        path = path.parent

    PROJECT_ROOT = path
    ASSETS_DIR = PROJECT_ROOT / "assets"
    OUTPUT_DIR = PROJECT_ROOT / "output"
    CONFIG_DIR = PROJECT_ROOT / "config"
    LOGS_DIR = PROJECT_ROOT / "logs"

    def __init__(self):
        # Ensure directories exist
        for dir_path in [self.OUTPUT_DIR, self.CONFIG_DIR, self.LOGS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)

        self.settings: UserSettings = self.load_settings()
        # Map settings to class attributes for backward compatibility with utils
        self.ADB_HOST = self.settings.adb_host
        self.ADB_PORT = self.settings.adb_port
        self.WAIT_TIME_MULTIPLIER = self.settings.wait_multiplier
        self.WAIT_TIME_SCREEN_NAV_MULTIPLIER = self.settings.wait_screen_nav_multiplier
        self.CAPTURE_INTERVAL = self.settings.capture_interval
        self.ADB_RETRIES = self.settings.adb_retries

        # File Paths
        self.SCREENSHOTS_DIR = self.PROJECT_ROOT / "screenshots"
        self.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        self.SCREENSHOT_PATH = self.SCREENSHOTS_DIR / "latest_screenshot.png"

        self.OWNED_DIR = self.OUTPUT_DIR / "owned"
        self.OWNED_DIR.mkdir(parents=True, exist_ok=True)

        self.OWNED = {
            "counts": self.OWNED_DIR / "scanned_counts.json",
            "students": self.OWNED_DIR / "scanned_students.json",
            "currencies": self.OWNED_DIR / "scanned_currencies.json",
        }

        self.PROCESSED_DATA = {
            "equipment": self.ASSETS_DIR / "data" / "equipment_processed.json",
            "items": self.ASSETS_DIR / "data" / "items_processed.json",
            "students": self.ASSETS_DIR / "data" / "students_processed.json",
        }

        self.OUTPUT_FILES = {
            "equipment": self.OUTPUT_DIR / "equipment_final_values.json",
            "items": self.OUTPUT_DIR / "items_final_values.json",
            "students": self.OUTPUT_DIR / "students_final_values.json",
            "converter_justin": self.OUTPUT_DIR / "converted_to_justin_planner.json",
            "merger": self.OUTPUT_DIR / "justin_data_final.json",
        }

    def load_settings(self) -> UserSettings:
        settings_file = Path(self.CONFIG_DIR / "settings.json")

        if settings_file.exists():
            try:
                data = json.loads(settings_file.read_text(encoding="utf-8"))
                return UserSettings(**data)
            except Exception:
                pass
        return UserSettings()

    def save_settings(self, settings: UserSettings):
        settings_file = self.CONFIG_DIR / "settings.json"
        settings_file.write_text(settings.model_dump_json(indent=4), encoding="utf-8")


# Global instance
Config = Config()
