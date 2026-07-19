from dataclasses import dataclass
from typing import Dict, List

from src.core.config import Config
from src.utils.data.base import BaseProcessor
from src.utils.data.text_matcher import find_closest


@dataclass
class Item:
    id: int
    name: str


class ItemProcessor(BaseProcessor):
    def __init__(self):
        self.dataclass = Item
        self.processed_file = Config.equipment_processed
        self.owned_file = Config.scanned_counts
        self.output_file = Config.final_items

    def _get_closest_value(
        self, name: str, name_map: Dict[str, int], threshold=0.8
    ) -> int:
        if not isinstance(name_map, dict) or not name_map:
            return 0
        matched = find_closest(name, list(name_map.keys()), threshold)
        return name_map.get(matched, 0) if matched else 0

    def map_data(self, items: List[Item], name_map: Dict) -> Dict:
        # return {item.id: name_map.get(item.name, 0) for item in items}
        return {item.id: self._get_closest_value(item.name, name_map) for item in items}
