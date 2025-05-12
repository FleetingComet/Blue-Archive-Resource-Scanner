from dataclasses import dataclass
from typing import Dict, List

import Levenshtein

from config import Config
from utils.data.base import BaseProcessor


@dataclass
class Student:
    id: str
    name: str


class StudentProcessor(BaseProcessor):
    def __init__(self):
        self.dataclass = Student
        self.processed_file = Config.PROCESSED_DATA["students"]
        self.owned_file = Config.OWNED["students"]
        self.output_file = Config.OUTPUT_FILES["students"]

    def _get_student_id(self, name: str, db: List[Student], threshold=0.8) -> str:
        # print(f"_get_student_id name: {name}")
        best_match = max(
            ((Levenshtein.ratio(name, s.name), s) for s in db),
            key=lambda x: x[0], # I forgot to set the key to select ratio because it's (Ratio, Student Object)
            default=(0, None),
        )
        return (
            best_match[1].id if best_match[0] >= threshold and best_match[1] else "N/A"
        )

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
