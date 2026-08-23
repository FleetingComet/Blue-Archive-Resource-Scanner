import time
from pathlib import Path

import requests
from rich.console import Console
from tenacity import Retrying, stop_after_attempt, wait_fixed

from src.core.config import Config, Path_Config
from src.utils.data.io import read_json, write_json

console = Console()


class DataSyncManager:
    """
    Manages syncing local data files with online sources.
    Falls back to local files if online is unavailable.
    """

    def __init__(self):
        self.BASE_URL = (
            "https://raw.githubusercontent.com/FleetingComet/BA-Scanner-Data/main/data"
        )

        self.DEFAULT_ONLINE_URLS = {
            "equipment": f"{self.BASE_URL}/equipment.json",
            "items": f"{self.BASE_URL}/items.json",
            "students": f"{self.BASE_URL}/students.json",
        }

        self.local_paths: dict[str, Path] = {
            "equipment": Path_Config.equipment_processed,
            "items": Path_Config.items_processed,
            "students": Path_Config.students_processed,
        }
        self.retries: int = Config.settings.adb_retries
        self.retry_backoff: float = 1.0

    def update_from_online(self):
        """
        Try to update local processed data files from online sources if available and different.
        If online is not available, fallback to local file.
        """

        # Allow caller to provide their own mapping via attribute or use defaults
        remote_sources = getattr(self, "remote_sources", self.DEFAULT_ONLINE_URLS)

        for key, url in remote_sources.items():
            local_path = self.local_paths.get(key)
            if not local_path:
                print(f"[DataSync] Unknown data key '{key}', skipping.")
                continue

            local_path = Path(local_path)
            tmp_path = local_path.with_suffix(local_path.suffix + ".tmp")

            # Try downloading with retries
            retries = getattr(self, "retries", 3)
            retry_backoff = getattr(self, "retry_backoff", 1.0)
            last_exc: Exception | None = None

            for attempt in Retrying(
                stop=stop_after_attempt(retries), wait=wait_fixed(retry_backoff)
            ):
                try:
                    response = requests.get(url, timeout=6)
                    response.raise_for_status()
                    remote_data = response.json()

                    local_data = read_json(local_path)

                    # Compare and write atomically if different
                    if local_data == remote_data:
                        console.print(
                            f"[bold blue][DataSync][/bold blue] Local {key} is up to date."
                        )
                    else:
                        write_json(tmp_path, remote_data)
                        tmp_path.replace(local_path)
                        console.print(f"[DataSync] Updated local {key} from {url}")

                    last_exc = None
                    break
                except requests.RequestException as exc:
                    last_exc = exc
                    wait = retry_backoff * attempt
                    console.print(
                        f"[DataSync] Attempt {attempt} failed for {key} ({exc}), retrying in {wait}s"
                    )
                    time.sleep(wait)
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    console.print(f"[DataSync] Unexpected error updating {key}: {exc}")
                    break

            if last_exc is not None:
                console.print(
                    f"[DataSync] Failed to update {key} after {retries} attempts. Using local {local_path}"
                )
