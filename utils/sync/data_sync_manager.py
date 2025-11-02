from pathlib import Path
from config import Config
import hashlib
import requests
import time
from typing import Dict, Optional


class DataSyncManager:
    """
    Manages syncing local data files with online sources.
    Falls back to local files if online is unavailable.
    """

    def is_same_content(self, file_path, new_bytes: bytes) -> bool:
        """
        Check if the file at file_path has the same content as new_bytes.
        """
        if not Path(file_path).exists():
            return False
        with open(file_path, "rb") as f:
            local_content = f.read()
        return (
            hashlib.sha256(local_content).digest() == hashlib.sha256(new_bytes).digest()
        )

    def write_file(self, file_path, data: bytes) -> None:
        """
        Write data to file, creating directories if necessary.
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(data)

    def update_from_online(self):
        """
        Try to update local processed data files from online sources if available and different.
        If online is not available, fallback to local file.
        """

        base_url = (
            "https://raw.githubusercontent.com/FleetingComet/BA-Scanner-Data/main/data"
        )

        default_online_urls = {
            "equipment": f"{base_url}/equipment.json",
            "items": f"{base_url}/items.json",
            "students": f"{base_url}/students.json",
        }

        # Allow caller to provide their own mapping via attribute or use defaults
        remote_sources = getattr(self, "remote_sources", default_online_urls)

        for key, url in remote_sources.items():
            local_path = Path(Config.PROCESSED_DATA[key])
            tmp_path = local_path.with_suffix(local_path.suffix + ".tmp")

            # Try downloading with retries
            retries = getattr(self, "retries", 3)
            retry_backoff = getattr(self, "retry_backoff", 1.0)
            last_exc: Optional[Exception] = None
            for attempt in range(1, retries + 1):
                try:
                    response = requests.get(url, timeout=6)
                    response.raise_for_status()
                    content = response.content

                    # Compare and write atomically if different
                    if self.is_same_content(local_path, content):
                        print(f"[DataSync] Local {key} is up to date.")
                    else:
                        tmp_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(tmp_path, "wb") as fh:
                            fh.write(content)
                        tmp_path.replace(local_path)
                        print(f"[DataSync] Updated local {key} from {url}")
                    last_exc = None
                    break
                except requests.RequestException as exc:
                    last_exc = exc
                    wait = retry_backoff * attempt
                    print(
                        f"[DataSync] Attempt {attempt} failed for {key} ({exc}), retrying in {wait}s"
                    )
                    time.sleep(wait)
                except Exception as exc:
                    last_exc = exc
                    print(f"[DataSync] Unexpected error updating {key}: {exc}")
                    break

            if last_exc is not None:
                print(
                    f"[DataSync] Failed to update {key} after {retries} attempts. Using local {local_path}"
                )
