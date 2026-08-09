from src.core.config import Config
from src.utils.data.base import BaseProcessor
from src.utils.data.shapes import Item


class ItemProcessor(BaseProcessor):
    def __init__(self):
        self.dataclass = Item
        self.processed_file = Config.items_processed
        self.owned_file = Config.scanned_counts
        self.output_file = Config.final_items

    def map_data(self, items: list[Item], name_map: dict) -> dict:
        # return {item.id: name_map.get(item.name, 0) for item in items}
        return {item.id: self.get_closest_value(item.name, name_map) for item in items}
