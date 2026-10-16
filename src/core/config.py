from enum import Enum

from pydantic import BaseModel, field_validator, model_validator
from rich.console import Console

from src.core.paths import Path_Config, PathConfig
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
    adb_serial: str = (
        None  # e.g. "123456789A123456" or "localhost:16384" or "127.0.0.1:16384", 16384 is default MuMu Player 12 port
    )
    adb_retries: int = 3  # Retries the connection up to retries times (default 3).

    wait_multiplier: float = 1.0
    wait_screen_nav_multiplier: float = 2.0

    enable_sync: bool = False
    target_platform: TargetPlatform = TargetPlatform.EMULATOR

    language: str = "en"
    debug: bool = False

    @model_validator(mode="before")
    @classmethod
    def _strip_legacy_adb(cls, data):
        if isinstance(data, dict):
            # Old configs stored adb_host/adb_port — synthesise adb_serial once.
            if not data.get("adb_serial") and data.get("adb_host"):
                data["adb_serial"] = f"{data['adb_host']}:{data['adb_port']}"
            data.pop("adb_host", None)
            data.pop("adb_port", None)
        return data

    @field_validator("adb_serial")
    @classmethod
    def _clean_serial(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


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
