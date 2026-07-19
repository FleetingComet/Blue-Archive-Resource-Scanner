from dataclasses import dataclass
from typing import Dict, List

from src.core.config import Config
from src.utils.data.base import BaseProcessor
from src.utils.data.text_matcher import find_closest


@dataclass
class Student:
    id: str
    name: str


class StudentProcessor(BaseProcessor):
    def __init__(self):
        self.dataclass = Student
        self.processed_file = Config.students_processed
        self.owned_file = Config.scanned_students
        self.output_file = Config.final_students

    def _get_student_id(self, name: str, db: List[Student], threshold=0.8) -> str:
        choices = [s.name for s in db]
        matched_name = find_closest(name, choices, threshold)
        if matched_name:
            for student in db:
                if student.name == matched_name:
                    return student.id
        return "N/A"

    def map_data(self, students: List[Student], owned_data: Dict) -> Dict:
        mapped = {"characters": []}
        for char in owned_data.get("characters", []):
            student_id = self._get_student_id(char["name"], students)
            mapped["characters"].append(
                {
                    "id": student_id,
                    "name": char["name"],
                    "current": self._process_stats(char.get("current", {})),
                }
            )
        return mapped

    def _process_stats(self, stats: Dict) -> Dict:
        processed = {}
        for k, v in stats.items():
            processed[k] = int(v) if k in ("star", "ue") else str(v)
        return processed
