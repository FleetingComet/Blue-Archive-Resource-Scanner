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
    for item in data:
        try:
            # Validate and convert JSON data to Equipment object
            # equipment = Equipment(
            #     id=int(item["Id"]),
            #     category=item["Category"],
            #     rarity=Rarity(item["Rarity"]),
            #     tier=int(item["Tier"]),
            #     icon=item["Icon"],
            #     name=item["Name"],
            #     # desc=item["Desc"],
            # )
            equipment = Equipment(
                id=int(item["id"]),
                category=item["category"],
                rarity=Rarity(item["rarity"]),
                tier=int(item["tier"]),
                icon=item["icon"],
                name=item["name"],
                # desc=item["Desc"],
            )
            equipment_list.append(equipment)
        except (KeyError, ValueError) as e:
            # Skip invalid entries
            # print(f"Skipping invalid entry: {item} - {e}")
            # print("Skipping invalid entry")
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
    equipment_list: List[Equipment],
    name_to_category_map: dict
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
    grouped_output = group_equipment_by_category(equipment_objects, name_to_category_map)

    # Save the grouped output to a new JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(grouped_output, f, indent=4)

    print(f"Grouped data saved to {output_file}")

# if __name__ == "__main__":
#     input_file = "equipment.json"  # Input JSON file path
#     output_file = "equipment_processed.json"  # Output JSON file path

#     # Load JSON data from file
#     with open(input_file, "r", encoding="utf-8") as f:
#         data = json.load(f)

#     # Process data to filter valid Equipment objects
#     equipment_objects = process_json(data)

#     # Save processed data to a new JSON file
#     save_json(equipment_objects, output_file)

#     print(f"Processed data saved to {output_file}")
