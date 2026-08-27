from src.core.config import Path_Config
from src.utils.data.processors.base import BaseProcessor
from src.utils.data.shapes import Student
from src.utils.data.text_matcher import find_closest


class StudentProcessor(BaseProcessor):
    def __init__(self):
        self.dataclass = Student
        self.processed_file = Path_Config.students_processed
        self.owned_file = Path_Config.scanned_students
        self.output_file = Path_Config.final_students

    def _get_student_id(
        self, name: str, name_to_id: dict[str, str], threshold=0.8
    ) -> str:
        # Exact match
        if name in name_to_id:
            return name_to_id[name]

        # Fuzzy match
        matched_name = find_closest(name, name_to_id.keys(), threshold)
        return name_to_id.get(matched_name, "N/A") if matched_name else "N/A"

    def map_data(self, students: list[Student], owned_data: dict) -> dict:
        # Build O(1) lookup map
        name_to_id = {s.name: str(s.id) for s in students}

        mapped = {"characters": []}
        for char in owned_data.get("characters", []):
            student_id = self._get_student_id(char["name"], name_to_id)
            mapped["characters"].append(
                {
                    "id": student_id,
                    "name": char["name"],
                    "current": self._process_stats(char.get("current", {})),
                }
            )
        return mapped

    def _process_stats(self, stats: dict) -> dict:
        processed = {}
        for k, v in stats.items():
            processed[k] = int(v) if k in ("star", "ue") else str(v)
        return processed
