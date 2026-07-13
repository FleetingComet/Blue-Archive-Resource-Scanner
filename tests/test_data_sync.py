from pathlib import Path
import requests

from src.utils.sync.data_sync_manager import DataSyncManager
from src.core.config import Config


class DummyResp:
    def __init__(self, content: bytes, status_code: int = 200):
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise requests.RequestException(f"status {self.status_code}")


def test_update_from_online_writes_file(monkeypatch, tmp_path: Path):
    # Prepare a temporary local path in config
    sample_content = b'{"test": 1}'
    local_dir = tmp_path / "assets" / "data"
    local_dir.mkdir(parents=True)
    equipment_file = local_dir / "equipment_processed.json"

    # Temporarily override Config.PROCESSED_DATA for the test
    orig = Config.PROCESSED_DATA
    Config.PROCESSED_DATA = {"equipment": equipment_file}

    # Mock requests.get to return our content
    def fake_get(url, timeout=6):
        return DummyResp(sample_content, 200)

    monkeypatch.setattr("requests.get", fake_get)

    mgr = DataSyncManager()
    # Override online_urls to only include equipment and point to a dummy URL
    mgr.remote_sources = {"equipment": "https://example.com/equipment_processed.json"}
    mgr.retries = 1
    mgr.retry_backoff = 0

    mgr.update_from_online()

    assert equipment_file.exists()
    assert equipment_file.read_bytes() == sample_content

    # cleanup
    Config.PROCESSED_DATA = orig
