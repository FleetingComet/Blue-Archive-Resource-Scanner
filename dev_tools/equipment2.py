import json
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


def process_json(data: List[dict]) -> List[Equipment]:
    equipment_list = []
    for item in data:
        try:
            # Validate and convert JSON data to Equipment object
            equipment = Equipment(
                id=int(item["id"]),
                category=item["category"],
                rarity=Rarity(item["rarity"]),
                tier=int(item["tier"]),
                icon=item["icon"],
                name=item["name"],
            )
            equipment_list.append(equipment)
        except (KeyError, ValueError) as e:
            pass
    return equipment_list


def save_json(equipment_list: List[Equipment], output_file: str):
    # Convert Equipment objects to dictionaries and save to a JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    **asdict(equipment),
                    "rarity": equipment.rarity.value,  # Convert Rarity enum to string (Serialize)
                }
                for equipment in equipment_list
            ],
            f,
            indent=4,
        )


def group_equipment_by_category(
    equipment_list: dict[Equipment], name_to_category_map: dict
) -> dict:
    grouped_data = defaultdict(dict)

    for item in equipment_list:
        category = item.category
        key = item.id if category == "Exp" else item.tier

        if category not in grouped_data:
            grouped_data[category] = {}

        # Get the value from name_to_category_map or set to 0 if not found
        value = name_to_category_map.get(item.name, 0)

        # Special case for WeaponExpGrowth categories
        if "WeaponExpGrowth" in category:
            # Extract the last character part of the icon
            # (e.g., '2' from 'equipment_icon_weaponexpgrowtha_2')
            icon_key = item.icon.split("_")[-1]
            grouped_data[category][int(icon_key) + 1] = value
        else:
            # Default assignment for non-WeaponExpGrowth categories
            grouped_data[category][key] = value

    return grouped_data


if __name__ == "__main__":
    main_json_file = "equipment_processed.json"
    name_to_category_json_file = "owned_counts.json"
    output_file = "final_values.json"

    # Load main equipment JSON
    with open(main_json_file, "r", encoding="utf-8") as f:
        equipment_data = json.load(f)

    # Load name-to-category mapping JSON
    with open(name_to_category_json_file, "r", encoding="utf-8") as f:
        name_to_category_map = json.load(f)

    # Process main JSON to create Equipment objects
    equipment_objects = process_json(equipment_data)

    # Group equipment by category
    grouped_output = group_equipment_by_category(
        equipment_objects, name_to_category_map
    )

    # Save the grouped output to a new JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(grouped_output, f, indent=4)

    print(f"Grouped data saved to {output_file}")
