from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

import Levenshtein

from config import Config
from utils.data.base import BaseProcessor


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
        self.processed_file = Config.PROCESSED_DATA["equipment"]
        self.owned_file = Config.OWNED["counts"]
        self.output_file = Config.OUTPUT_FILES["equipment"]

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

        return name_map[best_match] if best_ratio >= threshold else 0

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
