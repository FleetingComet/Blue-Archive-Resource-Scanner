import json

from src.utils.data.processors.item import ItemProcessor


def test_item_matching(path_config):
    items_data = [
        {"id": 120, "name": "Wolfsegg Iron Ore", "rarity": "N", "icon": "icon_120"},
        {"id": 121, "name": "Wolfsegg Steel", "rarity": "N", "icon": "icon_121"},
        {
            "id": 122,
            "name": "Low-Purity Wolfsegg Steel",
            "rarity": "R",
            "icon": "icon_122",
        },
        {
            "id": 123,
            "name": "High-Purity Wolfsegg Steel",
            "rarity": "SR",
            "icon": "icon_123",
        },
    ]
    owned_data = {"High Purity Wolfegg Steel": 2}

    # Write test files
    with open(path_config.items_processed, "w") as f:
        json.dump(items_data, f)

    with open(path_config.scanned_counts, "w") as f:
        json.dump(owned_data, f)

    processor = ItemProcessor()
    processor.process()

    # Verify output
    with open(processor.output_file) as f:
        result = json.load(f)

    assert result["123"] == 2  # Should match via rapidfuzz
