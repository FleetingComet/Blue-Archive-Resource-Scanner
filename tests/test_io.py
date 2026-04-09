from pathlib import Path

from utils.data.io import read_json, update_count, update_student, write_json


class TestIO:
    def test_read_write_roundtrip(self, tmp_path: Path):
        path = tmp_path / "test.json"
        data = {"a": 1, "b": [2, 3]}

        write_json(path, data)
        loaded = read_json(path)

        assert loaded == data

    def test_read_missing_file(self, tmp_path: Path):
        path = tmp_path / "missing.json"
        assert read_json(path) == {}

    def test_update_count(self, tmp_path: Path):
        path = tmp_path / "counts.json"
        update_count(path, "Item A", 10)
        update_count(path, "Item B", 5)

        data = read_json(path)
        assert data["Item A"] == 10
        assert data["Item B"] == 5

    def test_update_student(self, tmp_path: Path):
        path = tmp_path / "students.json"
        stats = {"level": "80", "star": 3}
        update_student(path, "Shiroko", stats)

        data = read_json(path)
        assert data["characters"]["Shiroko"]["current"] == stats
