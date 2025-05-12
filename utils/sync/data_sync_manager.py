from email.mime import base
from config import Config
import hashlib
import requests


class DataSyncManager:
    """
    Manages syncing local data files with online sources.
    Falls back to local files if online is unavailable.
    """

    def is_same_content(self, file_path, new_bytes: bytes) -> bool:
        """
        Check if the file at file_path has the same content as new_bytes.
        """
        if not file_path.exists():
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
        If online is not available, fallback to local file. Uses the online URL for this session if successful.
        """

        base_url = (
            "https://raw.githubusercontent.com/FleetingComet/BA-Scanner-Data/main/data"
        )

        online_urls = {
            "equipment": f"{base_url}/equipment.json",
            "items": f"{base_url}/items.json",
            "students": f"{base_url}/students.json",
        }
        for key, url in online_urls.items():
            local_path = Config.PROCESSED_DATA[key]
            try:
                response = requests.get(url, timeout=5)
                if response.ok:
                    online_content = response.content
                    if self.is_same_content(local_path, online_content):
                        print(f"[Config] Local {key} cache is up to date.")
                    else:
                        self.write_file(local_path, online_content)
                        print(f"[Config] Updated local {key} cache from online.")
                    Config.swap_processed_data(key, url)
                else:
                    print(
                        f"[Config] Online {key} data not available, using local file {local_path}"
                    )
            except Exception as e:
                print(
                    f"[Config] Could not fetch online {key} data: {e}. Using local file {local_path}"
                )
