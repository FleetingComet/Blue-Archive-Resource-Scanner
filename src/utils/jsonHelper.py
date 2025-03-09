import json
import os

from src.utils.text_util import normalize_value, normalize_skill_value


def load_json(json_path):
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            return json.load(f)
    return {}


def save_json(json_path, data):
    with open(json_path, "w") as f:
        json.dump(data, f, indent=4)


def update_owned_counts(json_path: str, category: str, tier: str, owned_count: int):
    """
    Update the owned counts JSON file with new data.

    Args:
        json_path (str): Path to the owned counts JSON file.
        category (str): The category (e.g., 'Shoes').
        tier (str): The tier (e.g., 't3').
        owned_count (int): The owned count (e.g., 999).
    """
    # Load existing data
    data = load_json(json_path)

    # Update the specific category and tier
    if category not in data:
        data[category] = {}
    data[category][tier] = owned_count

    save_json(json_path, data)


def update_name_owned_counts(json_path: str, name: str, owned_count: int):
    """
    Update the owned counts JSON file with new data.

    Args:
        json_path (str): Path to the owned counts JSON file.
        name (str): The name of the item (e.g., 'Gothic Leather Wristwatch Blueprint').
        owned_count (int): The owned count (e.g., 999).
    """
    # Load existing data
    data = load_json(json_path)

    if name not in data:
        data[name] = {}
    data[name] = owned_count

    save_json(json_path, data)


def update_character_data(json_path: str, name: str, current_data: dict):
    """
    Add or update a character entry in the JSON file under the 'characters' key.

    Args:
        json_path (str): Path to the JSON file.
        name (str): The character's name (e.g., "Iori").
        current_data (dict): A dictionary containing the character's current data.
                            Example:
                            {
                              "level": "81",
                              "ue_level": "0",
                              "bond": "15",
                              "ex": "4",
                              "basic": "8",
                              "passive": "7",
                              "sub": "7",
                              "gear1": "9",
                              "gear2": "9",
                              "gear3": "8",
                              "star": 5,
                              "ue": 1
                            }
    """
    # Load the existing data
    data = load_json(json_path)

    # Ensure "characters" is a list in the JSON
    if "characters" not in data:
        data["characters"] = []

    # Search for an existing character entry by name
    for char in data["characters"]:
        if char.get("name") == name:
            # Update the 'current' data
            char["current"] = current_data
            break
    else:
        # If not found, append a new entry
        data["characters"].append({"name": name, "current": current_data})

    # Save the updated data back to the JSON
    save_json(json_path, data)


def map_student_data_to_character(student_data):
    """
    Transform the extracted student_data into the structure needed
    for the 'characters' JSON entry.

    Returns a tuple of (name, current_data) where current_data is a dict.
    """
    # Extract the character's name
    name = student_data.get("Name", "Unknown")

    current_data = {
        "level": normalize_value(student_data.get("Level", 1)),
        "bond": normalize_value(student_data.get("Bond Level", 1)),
        "ex": normalize_skill_value(student_data.get("Skill EX", 1), 5),
        "basic": normalize_skill_value(student_data.get("Skill Basic", 1), 10),
        "passive": normalize_skill_value(student_data.get("Skill Enhanced", 0), 10),
        "sub": normalize_skill_value(student_data.get("Skill Sub", 0), 10),
        "gear1": normalize_value(student_data.get("Gear 1 Tier", 1)),
        "gear2": normalize_value(student_data.get("Gear 2 Tier", 1)),
        "gear3": normalize_value(student_data.get("Gear 3 Tier", 1)),
        "gear_bond": normalize_value(student_data.get("Gear Bond Tier", 0)),
        "ue_level": normalize_value(student_data.get("Unique Equipment Level", 0)),
        "ue": normalize_value(student_data.get("Unique Equipment Star Quantity", 1)),
        "star": normalize_value(student_data.get("Rarity", 1)),
    }

    return name, current_data
