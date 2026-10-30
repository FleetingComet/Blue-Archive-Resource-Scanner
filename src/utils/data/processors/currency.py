from src.core.paths import Path_Config
from src.utils.data.processors.base import BaseProcessor
from src.utils.data.shapes import Currency


class CurrencyProcessor(BaseProcessor):
    def __init__(self):
        self.dataclass = Currency
        self.processed_file = Path_Config.currency_processed
        self.owned_file = Path_Config.scanned_currencies
        self.output_file = Path_Config.final_currencies

    def map_data(self, currencies: list[Currency], name_map: dict) -> dict:
        scanned_keys = {
            1: "Credit",
            2: "Pyroxene",
            5: "Ap",
        }

        valid_ids = {currency.id for currency in currencies}

        return {
            currency_id: name_map[key]
            for currency_id, key in scanned_keys.items()
            if currency_id in valid_ids and key in name_map
        }
