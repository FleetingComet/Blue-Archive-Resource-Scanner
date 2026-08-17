import re

from src.utils.ocr.text_util import normalize_skill_value, normalize_value


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
        "talent_atk": normalize_value(student_data.get("Talent_ATK", 0)),
        "talent_hp": normalize_value(student_data.get("Talent_HP", 0)),
        "talent_healing": normalize_value(student_data.get("Talent_HEALING", 0)),
    }

    return name, current_data


def get_talent_level(text: str):
    """
    Extract the number after "Lv."

    Args:
        text (str): extract text from ocr

    Returns:
        _str_: stripped text
    """
    match = re.search(r"\[?\s*Lv\.?\s*(\d+)", text, re.IGNORECASE)
    return str(match.group(1)) if match else None
