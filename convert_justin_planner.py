from itertools import chain
import json

from config import Config


def transform_equipment_data(grouped_data):
    transformed_data = {}

    # Mapping of WeaponExpGrowth categories to their respective names
    category_name_map = {
        "WeaponExpGrowthA": "Spring",
        "WeaponExpGrowthB": "Hammer",
        "WeaponExpGrowthC": "Barrel",
        "WeaponExpGrowthZ": "Needle",
    }

    for category, items in grouped_data.items():
        for key, value in items.items():
            # Format key based on category
            transformed_category = category_name_map.get(category, category)

            if category == "Exp":
                new_key = f"GXP_{key}"
            else:
                new_key = f"T{key}_{transformed_category}"

            # Assign the transformed key-value pair
            transformed_data[new_key] = value

    return transformed_data


def transform_item_data(item_data):
    transformed_data = {}

    for key, value in item_data.items():
        # Format key based on category
        transformed_data[key] = value

    return transformed_data


if __name__ == "__main__":
    with open(Config.EQUIPMENT_OUTPUT_FILE, "r", encoding="utf-8") as f:
        equipment_data = json.load(f)

    with open(Config.ITEMS_OUTPUT_FILE, "r", encoding="utf-8") as f:
        item_data = json.load(f)

    # Transform Data
    result_equipment = transform_equipment_data(equipment_data)
    result_item = transform_item_data(item_data)

    # Save the grouped output to a new JSON file
    with open(Config.CONVERTER_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            dict(
                chain.from_iterable(d.items() for d in (result_equipment, result_item))
            ),
            f,
            indent=4,
        )

    print(f"Converted data saved to {Config.CONVERTER_OUTPUT_FILE}")
