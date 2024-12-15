import json

from config import Config

def transform_data(grouped_data):
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

if __name__ == "__main__":
    with open(Config.CONVERTER_INPUT_FILE, "r", encoding="utf-8") as f:
        equipment_data = json.load(f)
        
    # Transform Data
    result = transform_data(equipment_data)
        
    # Save the grouped output to a new JSON file
    with open(Config.CONVERTER_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)

    print(f"Converted data saved to {Config.CONVERTER_OUTPUT_FILE}")
