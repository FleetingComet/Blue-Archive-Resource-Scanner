from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from src.core.config import Config
from src.utils.data.base import BaseProcessor
from src.utils.data.text_matcher import find_closest


class Rarity(Enum):
    N = "N"
    R = "R"
    SR = "SR"
    SSR = "SSR"


@dataclass
class Equipment:
    id: int
    category: str
    rarity: Rarity
    tier: int
    icon: str
    name: str


class EquipmentProcessor(BaseProcessor):
    def __init__(self):
        self.dataclass = Equipment
        self.processed_file = Config.equipment_processed
        self.owned_file = Config.scanned_counts
        self.output_file = Config.final_equipment

    def _get_closest_value(
        self, name: str, name_map: Dict[str, int], threshold=0.8
    ) -> int:
        if not isinstance(name_map, dict) or not name_map:
            return 0
        choices = list(name_map.keys())
        matched = find_closest(name, choices, threshold)
        return name_map.get(matched, 0) if matched else 0

    def map_data(self, equipment_list: List[Equipment], name_map: Dict) -> Dict:
        grouped = defaultdict(dict)
        for item in equipment_list:
            category = item.category
            key = item.id if category == "Exp" else item.tier
            # value = name_map.get(item.name, 0)
            value = self._get_closest_value(item.name, name_map)

            if "WeaponExpGrowth" in category:
                icon_key = int(item.icon.split("_")[-1]) + 1
                grouped[category][icon_key] = value
            else:
                grouped[category][key] = value
        return grouped
