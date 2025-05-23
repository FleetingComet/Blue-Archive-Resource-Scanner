from itertools import chain
import json

from config import Config


class JustinPlannerConverter:
    def __init__(self, config):
        self.config = config

    def transform_equipment_data(self, grouped_data):
        transformed_data = {}
        category_name_map = {
            "WeaponExpGrowthA": "Spring",
            "WeaponExpGrowthB": "Hammer",
            "WeaponExpGrowthC": "Barrel",
            "WeaponExpGrowthZ": "Needle",
        }
        for category, items in grouped_data.items():
            for key, value in items.items():
                transformed_category = category_name_map.get(category, category)
                if category == "Exp":
                    new_key = f"GXP_{key}"
                else:
                    new_key = f"T{key}_{transformed_category}"
                transformed_data[new_key] = value
        return transformed_data

    def transform_item_data(self, item_data):
        transformed_data = {}
        for key, value in item_data.items():
            transformed_data[key] = value
        return transformed_data

    def transform_student_data(self, item_data):
        transformed_data = {"characters": []}
        for char in item_data.get("characters", []):
            new_char = {}
            new_char["id"] = str(char.get("id", ""))
            new_char["name"] = char.get("name", "")
            current = char.get("current", {})
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
            transformed_data["characters"].append(new_char)
        return transformed_data

    def run(self):
        with open(self.config.OUTPUT_FILES["equipment"], "r", encoding="utf-8") as f:
            equipment_data = json.load(f)
        with open(self.config.OUTPUT_FILES["items"], "r", encoding="utf-8") as f:
            item_data = json.load(f)
        with open(self.config.OUTPUT_FILES["students"], "r", encoding="utf-8") as f:
            students_data = json.load(f)
        result_equipment = self.transform_equipment_data(equipment_data)
        result_item = self.transform_item_data(item_data)
        result_student = self.transform_student_data(students_data)
        output = {
            "characters": result_student["characters"],
            "owned_materials": {**result_equipment, **result_item}
        }
        with open(self.config.OUTPUT_FILES["converter_justin"], "w", encoding="utf-8") as f:
            json.dump(
                output,
                f,
                indent=4,
            )
        print(f"Justin planner data exported to {self.config.OUTPUT_FILES['converter_justin']}")


if __name__ == "__main__":
    converter = JustinPlannerConverter(Config)
    converter.run()
