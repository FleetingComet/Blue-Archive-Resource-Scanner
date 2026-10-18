import json

from src.utils.data.processors.student import StudentProcessor


def _student(id: int, name: str, order: int) -> dict:
    """Minimal dummy record satisfying every ``Student`` dataclass field."""
    return {
        "id": id,
        "name": name,
        "DefaultOrder": order,
        "SquadType": "Main",
        "BulletType": "Pierce",
        "ArmorType": "Light",
        "School": "Abydos",
        "Club": "Foreclosure Task Force",
        "hasBondGear": False,
        "StarGrade": 3,
        "StyleId": None,
        "LinkedCharacterId": None,
    }


def test_student_matching(path_config):
    students_data = [
        _student(10010, "Shiroko", 1),
        _student(20027, "Shiroko (Swimsuit)", 2),
        _student(10024, "Shiroko (Cycling)", 3),
        _student(10100, "Shiroko*Terror", 4),
    ]
    owned_students = {
        "characters": [
            {
                "name": "Shiroko Terror",
                "current": {
                    "level": "81",
                    "ue_level": "40",
                    "bond": "1",
                    "ex": "1",
                    "basic": "1",
                    "passive": "0",
                    "sub": "0",
                    "gear1": "9",
                    "gear2": "9",
                    "gear3": "9",
                    "star": 5,
                    "ue": 2,
                },
            },
        ]
    }

    # Write test files
    with open(path_config.students_processed, "w") as f:
        json.dump(students_data, f)

    with open(path_config.scanned_students, "w") as f:
        json.dump(owned_students, f)

    processor = StudentProcessor()
    processor.process()

    # Verify output
    with open(processor.output_file) as f:
        result = json.load(f)

    assert result["characters"][0]["name"] == "Shiroko Terror"
    # IDs are serialized as strings so they survive as JSON object keys
    assert result["characters"][0]["id"] == "10100"  # Shiroko Terror ID
    assert result["characters"][0]["current"]["star"] == 5
    assert result["characters"][0]["current"]["ue"] == 2
    assert isinstance(result["characters"][0]["current"]["level"], str)
