from pathlib import Path

import requests
from rich.console import Console
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_fixed

from src.core.config import Config
from src.core.paths import Path_Config
from src.utils.data.io import read_json, write_json

console = Console()


class DataSyncManager:
    """
    Synchronizes local JSON datasets with BA-Scanner-Data.
    Keeps existing local files when remote sources are unavailable.
    """

    BASE_URL = (
        "https://raw.githubusercontent.com/"
        "FleetingComet/BA-Scanner-Data/main/data"
    )  # fmt: skip

    def __init__(self):
        self.local_paths: dict[str, Path] = {
            "equipment": Path_Config.equipment_processed,
            "items": Path_Config.items_processed,
            "students": Path_Config.students_processed,
            "currency": Path_Config.currency_processed,
        }

        self.DEFAULT_ONLINE_URLS = {
            key: f"{self.BASE_URL}/{key}.json" for key in self.local_paths
        }

        self.retries: int = Config.settings.data_sync_retries
        self.retry_backoff: float = 1.0

    def update_from_online(self) -> bool:
        """Sync datasets and return True if all updates succeed."""

        # Allow caller to provide their own mapping via attribute or use defaults
        remote_sources = getattr(self, "remote_sources", self.DEFAULT_ONLINE_URLS)

        all_successful = True

        with requests.Session() as session:
            for key, url in remote_sources.items():
                local_path = self.local_paths.get(key)

                if local_path is None:
                    console.print(f"[yellow][DataSync] Unknown dataset: {key}[/yellow]")
                    all_successful = False
                    continue

                local_path = Path(local_path)
                tmp_path = local_path.with_suffix(local_path.suffix + ".tmp")

                try:
                    for attempt in Retrying(
                        stop=stop_after_attempt(max(1, self.retries)),
                        wait=wait_fixed(max(0, self.retry_backoff)),
                        retry=retry_if_exception_type(requests.RequestException),
                        reraise=True,
                    ):
                        with attempt:
                            response = session.get(url, timeout=15)
                            response.raise_for_status()
                            remote_data = response.json()

                    if not isinstance(remote_data, (dict, list)):
                        raise TypeError(f"Unexpected JSON type for {key}")

                    if not remote_data:
                        raise ValueError(f"Remote dataset {key} is empty")

                    local_data = None

                    if local_path.is_file():
                        try:
                            local_data = read_json(local_path)
                        except (OSError, ValueError) as exc:
                            console.print(
                                f"[yellow][DataSync] Could not read "
                                f"local {key}: {exc}[/yellow]"
                            )

                    if local_data == remote_data:
                        console.print(f"[blue][DataSync] {key} is up to date.[/blue]")
                        continue

                    local_path.parent.mkdir(parents=True, exist_ok=True)

                    try:
                        write_json(tmp_path, remote_data)
                        tmp_path.replace(local_path)
                    finally:
                        tmp_path.unlink(missing_ok=True)

                    console.print(f"[green][DataSync] Updated {key}.[/green]")

                except (
                    requests.RequestException,
                    ValueError,
                    OSError,
                ) as exc:
                    all_successful = False
                    console.print(
                        f"[red][DataSync] Failed to update {key}: " f"{exc}[/red]"
                    )
                    console.print(
                        f"[yellow][DataSync] Using local file: "
                        f"{local_path}[/yellow]"
                    )

        return all_successful
