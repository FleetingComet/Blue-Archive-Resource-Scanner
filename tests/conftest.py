import pytest

@pytest.fixture
def tmp_config(tmp_path):
    class TempConfig:
        EQUIPMENT_PROCESSED_FILE = tmp_path / "equipment.json"
        OWNED_COUNTS_FILE = tmp_path / "owned.json"
        ITEMS_PROCESSED_FILE = tmp_path / "items.json"
        STUDENTS_PROCESSED_FILE = tmp_path / "students.json"
        OWNED_STUDENTS_FILE = tmp_path / "student_owned.json"
        
    return TempConfig()