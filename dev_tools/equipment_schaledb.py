from collections import defaultdict
from dataclasses import asdict, dataclass
from enum import Enum
import json
from typing import List


class Rarity(Enum):
    N = "N"
    R = "R"
    SR = "SR"
    SSR = "SSR"


@dataclass
class Equipment:
    id: int
    category: str
    rarity: Rarity
    tier: int
    icon: str
    name: str
    # desc: str


def process_json(data: List[dict]) -> List[Equipment]:
    equipment_list = []
    for item in data.values():
        try:
            # Validate and convert JSON data to Equipment object
            equipment = Equipment(
                id=int(item["Id"]),
                category=item["Category"],
                rarity=Rarity(item["Rarity"]),
                tier=int(item["Tier"]),
                icon=item["Icon"],
                name=item["Name"],
                # desc=item["Desc"],
            )
            equipment_list.append(equipment)
        except (KeyError, ValueError):
            pass
    return equipment_list


def save_json(equipment_list: List[Equipment], output_file: str):
    # Convert Equipment objects to dictionaries and save to a JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    **asdict(equipment),
                    "rarity": equipment.rarity.value,  # Convert Rarity enum to string
                }
                for equipment in equipment_list
            ],
            f,
            indent=4,
        )


def group_equipment_by_category(
    equipment_list: List[Equipment], name_to_category_map: dict
) -> dict:
    grouped_data = defaultdict(dict)

    print(f"{equipment_list}")

    for equipment in equipment_list:
        # Find the category and its corresponding value
        mapped_value = name_to_category_map.get(equipment.name)
        print(f"{equipment.name}: {mapped_value}")
        if mapped_value:
            # Add the mapped value to the category
            category = equipment.category
            grouped_data[category][equipment.tier] = mapped_value
        else:
            # Default to tier if no mapping exists
            grouped_data[equipment.category][equipment.tier] = equipment.tier

    return grouped_data

if __name__ == "__main__":
    input_file = "equipment.json"
    output_file = "equipment_processed.json"

    # Load JSON data from file
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Process data to filter valid Equipment objects
    equipment_objects = process_json(data)

    # Save processed data to a new JSON file
    save_json(equipment_objects, output_file)

    print(f"Processed data saved to {output_file}")
