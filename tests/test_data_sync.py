import json

import requests

from src.utils.sync.data_sync_manager import DataSyncManager


class DummyResp:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise requests.RequestException(f"status {self.status_code}")

    def json(self):
        return self._payload


def test_update_from_online_writes_file(monkeypatch, path_config):
    # Prepare a sample payload and the sandboxed destination file
    sample_payload = {"test": 1}
    equipment_file = path_config.equipment_processed

    # Mock requests.get to return our payload
    def fake_get(url, timeout=6):
        return DummyResp(sample_payload, 200)

    monkeypatch.setattr("requests.get", fake_get)

    mgr = DataSyncManager()
    # Override the local path and remote source for equipment only
    mgr.local_paths = {"equipment": equipment_file}
    mgr.remote_sources = {"equipment": "https://example.com/equipment_processed.json"}
    mgr.retries = 1
    mgr.retry_backoff = 0

    mgr.update_from_online()

    assert equipment_file.exists()
    assert json.loads(equipment_file.read_text(encoding="utf-8")) == sample_payload
