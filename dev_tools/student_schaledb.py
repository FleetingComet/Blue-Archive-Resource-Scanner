import json
from dataclasses import asdict, dataclass
from typing import List


@dataclass
class Student:
    id: int
    name: str


def process_json(data: List[dict]) -> List[Student]:
    item_list = []
    for item in data.values():
        try:
            item = Student(
                id=int(item["Id"]),
                name=item["Name"],
            )
            item_list.append(item)
        except (KeyError, ValueError):
            pass
    return item_list


def save_json(item_list: List[Student], output_file: str):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    **asdict(item),
                }
                for item in item_list
            ],
            f,
            indent=4,
            ensure_ascii=False,
        )


if __name__ == "__main__":
    input_file = "students.min.json"
    output_file = "students_processed.json"

    # Load JSON data from file
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Process data to filter valid Equipment objects
    item_objects = process_json(data)

    # Save processed data to a new JSON file
    save_json(item_objects, output_file)

    print(f"Processed data saved to {output_file}")
