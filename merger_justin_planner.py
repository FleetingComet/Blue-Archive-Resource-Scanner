import json

from config import Config


# def merge_equipment():
if __name__ == "__main__":
    with open(Config.MERGER["to_file"], "r") as file:
        previous_data = json.load(file)

    with open(Config.OUTPUT_FILES["converter_justin"], "r", encoding="utf-8") as f:
        new_resources = json.load(f)

    # Ensure new_resources["characters"] exists and is a list
    if "characters" not in new_resources or not isinstance(new_resources["characters"], list):
        new_resources["characters"] = []

    # Add 'target' field to every character if missing (Default: MAX for all)
    for char in new_resources["characters"]:
        if isinstance(char, dict) and "target" not in char:
            char["target"] = {
                "level": "90",
                "ue_level": "50",
                "bond": "23",
                "ex": "5",
                "basic": "10",
                "passive": "10",
                "sub": "10",
                "gear1": "9",
                "gear2": "9",
                "gear3": "9",
                "star": 5,
                "ue": 3,
            }

    previous_data["characters"] = new_resources["characters"]

    owned_materials = previous_data.get("owned_materials", {})
    # Only merge the 'owned_materials' part of new_resources, not the whole object
    merged_materials = {**owned_materials, **new_resources.get("owned_materials", {})}

    previous_data["owned_materials"] = merged_materials

    with open(Config.MERGER["output"], "w") as file:
        json.dump(previous_data, file, indent=2)

    print(f"Resources have been successfully merged into {Config.MERGER['output']}.")
