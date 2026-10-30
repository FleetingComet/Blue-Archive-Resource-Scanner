from pathlib import Path


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
        self.IMAGES_DIR = self.ASSETS_DIR / "images"
        self.TEMPLATES_DIR = self.IMAGES_DIR / "templates"

        self.equipment_processed = self.DATA_DIR / "equipment_processed.json"
        self.items_processed = self.DATA_DIR / "items_processed.json"
        self.students_processed = self.DATA_DIR / "students_processed.json"
        self.currency_processed = self.DATA_DIR / "currency_processed.json"

        self.scanned_counts = self.OWNED_DIR / "scanned_counts.json"
        self.scanned_currencies = self.OWNED_DIR / "scanned_currencies.json"
        self.scanned_students = self.OWNED_DIR / "scanned_students.json"

        self.final_equipment = self.OUTPUT_DIR / "equipment_final_values.json"
        self.final_items = self.OUTPUT_DIR / "items_final_values.json"
        self.final_students = self.OUTPUT_DIR / "students_final_values.json"
        self.final_currencies = self.OUTPUT_DIR / "currencies_final_values.json"

        # Justin Planner
        self.justin_planner_data = self.INPUT_DIR / "justin_data.json"
        self.justin_planner_merged_output = self.OUTPUT_DIR / "justin_data_final.json"

        self.SETTINGS_FILE = self.CONFIG_DIR / "settings.json"

        # GUI-only: user-supplied artwork (same tree as schaledb's paths).
        self.local_images = self.IMAGES_DIR / "local"
        # GUI-only: downloaded artwork is kept with the local art (not under
        # output/) so clearing the scanner's output never deletes the cache.
        self.icon_cache = self.local_images

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
