from src.core.paths import Path_Config
from src.utils.data.processors.base import BaseProcessor
from src.utils.data.shapes import Currency, Item


class CurrencyProcessor(BaseProcessor):
    def __init__(self):
        self.dataclass = Currency
        self.processed_file = Path_Config.currency_processed
        self.owned_file = Path_Config.scanned_currencies
        self.output_file = Path_Config.final_currencies

    def map_data(self, items: list[Item], name_map: dict) -> dict:
        return {item.id: self.get_closest_value(item.name, name_map) for item in items}
