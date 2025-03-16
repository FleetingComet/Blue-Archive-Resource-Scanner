from dataclasses import dataclass
from typing import Dict, List

import Levenshtein

from config import Config
from utils.data.base import BaseProcessor


@dataclass
class Item:
    id: int
    name: str


class ItemProcessor(BaseProcessor):
    def __init__(self):
        self.dataclass = Item
        self.processed_file = Config.PROCESSED_DATA["items"]
        self.owned_file = Config.OWNED["counts"]
        self.output_file = Config.OUTPUT_FILES["items"]

    def _get_closest_value(
        self, name: str, name_map: Dict[str, int], threshold=0.8
    ) -> int:
        best_match = None
        best_ratio = 0

        for map_name in name_map:
            ratio = Levenshtein.ratio(name, map_name)
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = map_name

        return name_map.get(best_match, 0) if best_ratio >= threshold else 0

    def map_data(self, items: List[Item], name_map: Dict) -> Dict:
        # return {item.id: name_map.get(item.name, 0) for item in items}
        return {item.id: self._get_closest_value(item.name, name_map) for item in items}
