import json

from config import Config


# def merge_equipment():
if __name__ == "__main__":
    with open(Config.MERGER_TO_FILE, "r") as file:
        previous_data = json.load(file)

    with open(Config.MERGER_INPUT_FILE, "r", encoding="utf-8") as f:
        new_resources = json.load(f)

    owned_materials = previous_data.get("owned_materials", {})
    
    merged_materials = {**owned_materials, **new_resources}

    previous_data["owned_materials"] = merged_materials

    with open(Config.MERGER_OUTPUT_FILE, "w") as file:
        json.dump(previous_data, file, indent=2)

    print("Resources have been successfully merged into 'owned_materials'.")
