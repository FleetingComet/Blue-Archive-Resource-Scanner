from dataclasses import dataclass

from src.core.config import Config
from src.utils.data.base import BaseProcessor


@dataclass
class Item:
    id: int
    name: str
    category: str


class ItemProcessor(BaseProcessor):
    def __init__(self):
        self.dataclass = Item
        self.processed_file = Config.equipment_processed
        self.owned_file = Config.scanned_counts
        self.output_file = Config.final_items

    def map_data(self, items: list[Item], name_map: dict) -> dict:
        # return {item.id: name_map.get(item.name, 0) for item in items}
        return {item.id: self._get_closest_value(item.name, name_map) for item in items}
