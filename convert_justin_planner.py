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


def transform_student_data(item_data):
    """
    Transforms student data into the desired export format.
    
    Expected input (example):
    {
        "characters": [
            {
                "name": "Wakamo",
                "current": {
                    "level": 90,
                    "bond": 24,
                    "ex": 5,
                    "basic": 10,
                    "passive": 10,
                    "sub": 10,
                    "gear1": 9,
                    "gear2": 9,
                    "gear3": 9,
                    "gear_bond": 2,
                    "ue_level": 50,
                    "ue": 3,
                    "star": 5
                }
            },
            ...
        ]
    }
    
    Desired output (example):
    {
        "characters": [
            {
                "id": "10033",
                "name": "Wakamo",
                "current": {
                    "level": "90",
                    "bond": "25",
                    "ex": "5",
                    "basic": "10",
                    "passive": "10",
                    "sub": "10",
                    "gear1": "9",
                    "gear2": "9",
                    "gear3": "9",
                    "gear_bond": "2",
                    "ue_level": "50",
                    "ue": 3,
                    "star": 5
                }
            },
            ...
        ]
    }
    """
    transformed_data = {"characters": []}
    
    for char in item_data.get("characters", []):
        new_char = {}
        # Copy the name unchanged.
        new_char["name"] = char.get("name", "")
        
        # Process the "current" stats.
        current = char.get("current", {})
        new_current = {}
        for key, value in current.items():
            if key == "star" or key=="ue":
                # Keep "star" and "ue" as an integer.
                try:
                    new_current[key] = int(value)
                except (ValueError, TypeError):
                    new_current[key] = value
            else:
                # Convert other values to strings.
                new_current[key] = str(value)
        new_char["current"] = new_current
        
        # new_char["target"] = {} 
        # new_char["eleph"] = {} 
        # new_char["enabled"] = False
        
        transformed_data["characters"].append(new_char)
    
    return transformed_data



if __name__ == "__main__":
    with open(Config.OUTPUT_FILES["equipment"], "r", encoding="utf-8") as f:
        equipment_data = json.load(f)

    with open(Config.OUTPUT_FILES["items"], "r", encoding="utf-8") as f:
        item_data = json.load(f)

    with open(Config.OUTPUT_FILES["students"], "r", encoding="utf-8") as f:
        students_data = json.load(f)

    # Transform Data
    result_equipment = transform_equipment_data(equipment_data)
    result_item = transform_item_data(item_data)
    result_student = transform_student_data(students_data)

    # Save the grouped output to a new JSON file
    with open(Config.OUTPUT_FILES["converter_justin"], "w", encoding="utf-8") as f:
        json.dump(
            dict(
                chain.from_iterable(d.items() for d in (result_equipment, result_item, result_student))
            ),
            f,
            indent=4,
        )

    print(f"Converted data saved to {Config.OUTPUT_FILES["converter_justin"]}")
