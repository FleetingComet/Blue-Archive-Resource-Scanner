from collections import defaultdict

from src.core.config import Path_Config
from src.utils.data.processors.base import BaseProcessor
from src.utils.data.shapes import Equipment


class EquipmentProcessor(BaseProcessor):
    def __init__(self):
        self.dataclass = Equipment
        self.processed_file = Path_Config.equipment_processed
        self.owned_file = Path_Config.scanned_counts
        self.output_file = Path_Config.final_equipment

    def map_data(self, equipment_list: list[Equipment], name_map: dict) -> dict:
        grouped = defaultdict(dict)
        for item in equipment_list:
            category = item.category
            key = item.id if category == "Exp" else item.tier
            # value = name_map.get(item.name, 0)
            value = self.get_closest_value(item.name, name_map)

            if "WeaponExpGrowth" in category:
                icon_key = int(item.icon.split("_")[-1]) + 1
                grouped[category][icon_key] = value
            else:
                grouped[category][key] = value
        return grouped
