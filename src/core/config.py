from enum import Enum
from pathlib import Path

from pydantic import BaseModel
from rich.console import Console

from src.utils.data.io import read_json, write_json

console = Console()


class TargetPlatform(str, Enum):
    EMULATOR = "emulator"
    DEVICE = "device"
    DESKTOP = "desktop"


class OCREngine(str, Enum):
    RAPIDOCR = "rapidocr"


class AppSettings(BaseModel):
    """User-adjustable settings saved in config/settings.json"""

    # ADB Settings
    adb_host: str = "127.0.0.1"  # or "localhost"
    adb_port: int = 16384  # Default MuMu Player 12 port
    adb_retries: int = 3  # Retries the connection up to retries times (default 3).

    wait_multiplier: float = 1.0
    wait_screen_nav_multiplier: float = 2.0

    enable_sync: bool = False
    target_platform: TargetPlatform = TargetPlatform.EMULATOR

    debug: bool = False


class PathConfig:
    """The project's source of truth for paths."""

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

        self.SETTINGS_FILE = self.CONFIG_DIR / "settings.json"

    def _locate_root(self) -> Path:
        path = Path(__file__).resolve()
        while not (path / "main.py").exists():
            if path.parent == path:
                raise RuntimeError("Could not locate project root.")
            path = path.parent
        return path

    def ensure_directories(self):
        """Create required folders (logic folders that might stay empty for a while)."""
        for folder in [self.OUTPUT_DIR, self.CONFIG_DIR, self.LOGS_DIR, self.OWNED_DIR]:
            folder.mkdir(parents=True, exist_ok=True)


Path_Config = PathConfig()


class ConfigManager:
    """The project's source of truth for settings."""

    _instance = None

    @classmethod
    def get(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = cls(path_config=Path_Config)
        return cls._instance

    def __init__(self, path_config: PathConfig):
        self._path_config = path_config
        self.settings: AppSettings = self.load()
        self.OCR_ENGINE = OCREngine.RAPIDOCR.value  # for future

    def load(self) -> AppSettings:
        data = read_json(self._path_config.SETTINGS_FILE)

        if not data:
            return AppSettings()

        try:
            return AppSettings(**data)
        except Exception as e:  # noqa: BLE001
            console.print(f"[yellow]Invalid settings ({e}) — using defaults[/yellow]")
            return AppSettings()

    def save(self, settings: AppSettings):
        self.settings = settings
        write_json(self._path_config.SETTINGS_FILE, self.settings.model_dump())


# Global instance
Config = ConfigManager.get()
