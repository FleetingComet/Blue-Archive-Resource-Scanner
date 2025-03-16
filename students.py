import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import List

import Levenshtein

from config import Config


@dataclass
class Student:
    id: int | str
    name: str


def process_json(data: List[dict]) -> List[Student]:
    student_list = []

    for item in data:
        try:
            item = Student(
                id=str(item["id"]),
                name=item["name"],
            )
            student_list.append(item)
        except (KeyError, ValueError):
            pass
    return student_list


def save_json(student_list: List[Student], output_file: str):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    **asdict(student),
                }
                for student in student_list
            ],
            f,
            indent=4,
            ensure_ascii=False,
        )


def get_id_for_character(name: str, known_db: list, threshold=0.8) -> str:
    best_match = None
    best_ratio = 0

    for entry in known_db:    
        ratio = Levenshtein.ratio(name, entry["name"])

        if ratio > best_ratio:
                print(best_ratio)
                best_ratio = ratio
                best_match = entry
        if best_ratio >= threshold and best_match is not None:
            # character["id"] = str(best_match["id"])
            return str(best_match["id"])
    #     else:
    #         character["id"] = "N/A"

    # return data


def map_items(data, student_list) -> dict:
     
    new_data = {"characters": []}

    for character in data.get("characters", []):
        new_char = {}
        name = character.get("name", "").strip()
        new_char["name"] = name
        new_char["id"] = get_id_for_character(name, student_list)
        
        # Process current stats: convert all values (except star) to strings.
        current = character.get("current", {})
        new_current = {}
        for key, value in current.items():
            if key == "star" or key == "ue":
                try:
                    new_current[key] = int(value)
                except (ValueError, TypeError):
                    new_current[key] = value
            else:
                new_current[key] = str(value)
        new_char["current"] = new_current

        
        new_data["characters"].append(new_char)
    return new_data


def process_items():
    # Load processed items JSON
    with open(Config.STUDENTS_PROCESSED_FILE, "r", encoding="utf-8") as f:
        student_data = json.load(f)

    # Load our own output JSON
    with open(Config.OWNED_STUDENTS_FILE, "r", encoding="utf-8") as f:
        name_to_map = json.load(f)

    # Process main JSON to create students object
    # student_objects = process_json(student_data)

    mapped_output = map_items(name_to_map, student_data)

    # # Save the grouped output to a new JSON file
    with open(Config.STUDENTS_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(mapped_output, f, indent=4)

    print(f"Data saved to {Config.STUDENTS_OUTPUT_FILE}")

if __name__ == "__main__":
    process_items()