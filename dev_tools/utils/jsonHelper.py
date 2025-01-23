import json
import os


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
