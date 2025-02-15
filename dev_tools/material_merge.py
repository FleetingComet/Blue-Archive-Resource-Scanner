from itertools import chain
import json
from config import Config


def merge_materials():
    # Load processed items JSON
    with open(Config.EQUIPMENT_OUTPUT_FILE, "r", encoding="utf-8") as f:
        equipment_data = json.load(f)

    # Load our own output JSON
    with open(Config.ITEMS_OUTPUT_FILE, "r", encoding="utf-8") as f:
        item_data = json.load(f)

    # Save the grouped output to a new JSON file
    with open(Config.OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            dict(chain.from_iterable(d.items() for d in (equipment_data, item_data))),
            f,
            indent=4,
        )

    print(f"Data saved to {Config.OUTPUT_FILE}")
