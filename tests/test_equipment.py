import json

from src.utils.data.processors.equipment import EquipmentProcessor


def test_equipment_processing(path_config):
    # Setup test data
    equipment_data = [
        {
            "id": 1,
            "category": "WeaponExpGrowthA",
            "rarity": "SR",
            "tier": 3,
            "icon": "icon_weaponexpgrowtha_2",
            "name": "Growth Stone A",
        }
    ]

    owned_data = {"Growth Stone": 5, "Groeth Stone A": 3}  # Intentional typo

    # Write test files
    with open(path_config.equipment_processed, "w") as f:
        json.dump(equipment_data, f)

    with open(path_config.scanned_counts, "w") as f:
        json.dump(owned_data, f)

    processor = EquipmentProcessor()
    processor.process()

    # Verify output
    with open(processor.output_file) as f:
        result = json.load(f)

    assert "WeaponExpGrowthA" in result
    assert result["WeaponExpGrowthA"]["3"] == 3  # Should match with typo via rapidfuzz
