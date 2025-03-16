import json
from utils.data.student import StudentProcessor


def test_student_matching(tmp_config):
    # Setup test data
    students_data = [
        {"id": 10010, "name": "Shiroko"},
        {"id": 20027, "name": "Shiroko (Swimsuit)"},
        {"id": 10024, "name": "Shiroko (Cycling)"},
        {"id": 10100, "name": "Shiroko*Terror"},
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
                "target": {
                    "level": "90",
                    "ue_level": "50",
                    "bond": "1",
                    "ex": "5",
                    "basic": "10",
                    "passive": "10",
                    "sub": "10",
                    "gear1": "9",
                    "gear2": "9",
                    "gear3": "9",
                    "star": 5,
                    "ue": 3,
                },
                "eleph": {
                    "owned": "0",
                    "unlocked": True,
                    "cost": "5",
                    "purchasable": "",
                    "farm_nodes": "0",
                    "node_refresh": False,
                    "use_eligma": True,
                    "use_shop": False,
                },
                "enabled": True,
            },
        ]
    }

    # Write test files
    with open(tmp_config.STUDENTS_PROCESSED_FILE, "w") as f:
        json.dump(students_data, f)

    with open(tmp_config.OWNED_STUDENTS_FILE, "w") as f:
        json.dump(owned_students, f)

    # Run processor
    processor = StudentProcessor()
    processor.processed_file = tmp_config.STUDENTS_PROCESSED_FILE
    processor.owned_file = tmp_config.OWNED_STUDENTS_FILE
    processor.output_file = (
        tmp_config.STUDENTS_PROCESSED_FILE.parent / "students_output.json"
    )
    processor.process()

    # Verify output
    with open(processor.output_file) as f:
        result = json.load(f)

    # assert result["characters"][0]["id"] == "S001"
    print(result["characters"][0]["name"])
    assert result["characters"][0]["id"] == 10100  # Shiroko Terror ID
    assert result["characters"][0]["current"]["star"] == 5
    assert result["characters"][0]["current"]["ue"] == 2
    assert isinstance(result["characters"][0]["current"]["level"], str)
