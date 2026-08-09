from enum import Enum
from pathlib import Path

from pydantic import BaseModel

from src.utils.data.io import read_json, write_json


class TargetPlatform(str, Enum):
    EMULATOR = "emulator"
    DEVICE = "device"
    DESKTOP = "desktop"


class AppSettings(BaseModel):
    """User-adjustable settings saved in config/settings.json"""

    # ADB Settings
    adb_host: str = "127.0.0.1"  # or "localhost"
    adb_port: int = 16384  # Default MuMu Player 12 port
    adb_retries: int = 3  # Retries the connection up to retries times (default 3).

    wait_multiplier: float = 1.0
    wait_screen_nav_multiplier: float = 2.0
    capture_interval: float = 0.5  # seconds between captures

    enable_sync: bool = False
    target_platform: TargetPlatform = TargetPlatform.EMULATOR

    debug_mode: bool = False


class ConfigManager:
    """The project's source of truth for paths and settings."""

    def __init__(self):
        self.PROJECT_ROOT = self._locate_root()

        # Directory Structure
        self.ASSETS_DIR = self.PROJECT_ROOT / "assets"
        self.INPUT_DIR = self.PROJECT_ROOT / "input"
        self.OUTPUT_DIR = self.PROJECT_ROOT / "output"
        self.CONFIG_DIR = self.PROJECT_ROOT / "config"
        self.LOGS_DIR = self.PROJECT_ROOT / "logs"
        self.OWNED_DIR = self.OUTPUT_DIR / "owned"
        self.DATA_DIR = self.ASSETS_DIR / "data"

        self.equipment_processed = self.DATA_DIR / "equipment_processed.json"
        self.items_processed = self.DATA_DIR / "items_processed.json"
        self.students_processed = self.DATA_DIR / "students_processed.json"

        self.scanned_counts = self.OWNED_DIR / "scanned_counts.json"
        self.scanned_currencies = self.OWNED_DIR / "scanned_currencies.json"
        self.scanned_students = self.OWNED_DIR / "scanned_students.json"

        self.final_equipment = self.OUTPUT_DIR / "equipment_final_values.json"
        self.final_items = self.OUTPUT_DIR / "items_final_values.json"
        self.final_students = self.OUTPUT_DIR / "students_final_values.json"

        # Justin Planner
        self.justin_planner_data = self.INPUT_DIR / "justin_data.json"
        self.justin_planner_merged_output = self.OUTPUT_DIR / "justin_data_final.json"

        self.settings: AppSettings = self.load_settings()
        # Map settings to class attributes for backward compatibility with utils
        self.WAIT_TIME_MULTIPLIER = self.settings.wait_multiplier
        self.WAIT_TIME_SCREEN_NAV_MULTIPLIER = self.settings.wait_screen_nav_multiplier
        self.ADB_RETRIES = self.settings.adb_retries
        self.DEBUG = self.settings.debug_mode

        self._ensure_directories()

    def _locate_root(self) -> Path:
        path = Path(__file__).resolve()
        while not (path / "main.py").exists():
            if path.parent == path:
                raise RuntimeError("Could not locate project root.")
            path = path.parent
        return path

    def _ensure_directories(self):
        """Create required folders (logic folders that might stay empty for a while)."""
        for folder in [self.OUTPUT_DIR, self.CONFIG_DIR, self.LOGS_DIR, self.OWNED_DIR]:
            folder.mkdir(parents=True, exist_ok=True)

    def load_settings(self) -> AppSettings:
        path = Path(self.CONFIG_DIR / "settings.json")

        data = read_json(path)
        if data:
            try:
                return AppSettings(**data)
            except Exception:
                pass
        return AppSettings()

    def save_settings(self, settings: AppSettings):
        self.settings = settings
        path = self.CONFIG_DIR / "settings.json"
        write_json(path, settings.model_dump())


# Global instance
Config = ConfigManager()
