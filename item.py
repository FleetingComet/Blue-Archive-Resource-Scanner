import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import List

from config import Config


@dataclass
class Item:
    id: int
    name: str


def process_json(data: List[dict]) -> List[Item]:
    item_list = []

    for item in data:
        try:
            item = Item(
                id=int(item["id"]),
                name=item["name"],
            )
            item_list.append(item)
        except (KeyError, ValueError):
            pass
    return item_list


def save_json(item_list: List[Item], output_file: str):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    **asdict(item),
                }
                for item in item_list
            ],
            f,
            indent=4,
            ensure_ascii=False,
        )


def map_items(item_list: dict[Item], name_to_category_map: dict) -> dict:
    grouped_data = defaultdict(dict)

    for item in item_list:
        key = item.id

        # Get the value from name_to_category_map or set to 0 if not found
        value = name_to_category_map.get(item.name, 0)
        grouped_data[key] = value

    return grouped_data


def process_items():
    # Load processed items JSON
    with open(Config.ITEMS_PROCESSED_FILE, "r", encoding="utf-8") as f:
        material_data = json.load(f)

    # Load our own output JSON
    with open(Config.OWNED_COUNTS_FILE, "r", encoding="utf-8") as f:
        name_to_map = json.load(f)

    # Process main JSON to create Equipment objects
    item_objects = process_json(material_data)

    # Group equipment by category
    mapped_output = map_items(item_objects, name_to_map)

    # Save the grouped output to a new JSON file
    with open(Config.ITEMS_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(mapped_output, f, indent=4)

    print(f"Data saved to {Config.ITEMS_OUTPUT_FILE}")
