import json

from utils.data.equipment import EquipmentProcessor


def test_equipment_processing(tmp_config):
    # Setup test data
    equipment_data = [{
        "id": 1,
        "category": "WeaponExpGrowthA",
        "rarity": "SR",
        "tier": 3,
        "icon": "icon_weaponexpgrowtha_2",
        "name": "Growth Stone A"
    }]
    
    owned_data = {"Growth Stone": 5, "Groeth Stone A": 3}  # Intentional typo
    
    # Write test files
    with open(tmp_config.EQUIPMENT_PROCESSED_FILE, 'w') as f:
        json.dump(equipment_data, f)
    
    with open(tmp_config.OWNED_COUNTS_FILE, 'w') as f:
        json.dump(owned_data, f)
    
    # Run processor
    processor = EquipmentProcessor()
    processor.processed_file = tmp_config.EQUIPMENT_PROCESSED_FILE
    processor.owned_file = tmp_config.OWNED_COUNTS_FILE
    processor.output_file = tmp_config.EQUIPMENT_PROCESSED_FILE.parent / "output.json"
    processor.process()
    
    # Verify output
    with open(processor.output_file) as f:
        result = json.load(f)
    
    assert "WeaponExpGrowthA" in result
    assert result["WeaponExpGrowthA"]["3"] == 3  # Should match with typo via Levenshtein