from typing import TypedDict

import numpy as np

from locations.search import StudentSearchPattern
from src.enums.ExtractionMode import ExtractionMode
from src.utils.ocr.extract import (
    extract_from_region,
    extract_item_name,
    extract_owned_count,
)


class ItemResult(TypedDict):
    name: str | None
    count: str | None


def item_ocr_worker(image: np.ndarray, grid_type: str) -> ItemResult:
    """Worker for Equipment/Items"""
    if image is None:
        return None

    return {
        "name": extract_item_name(image, grid_type),
        "count": extract_owned_count(image, grid_type),
    }


def student_ocr_worker(image: np.ndarray):
    """Runs full student OCR on a single saved screenshot."""
    if image is None:
        return None

    return {
        "Name": extract_from_region(
            image,
            StudentSearchPattern.STUDENT_NAME.value,
            mode=ExtractionMode.NAME,
        ),
        "Level": extract_from_region(
            image,
            StudentSearchPattern.LEVEL.value,
            mode=ExtractionMode.LEVEL,
        ),
        "Bond Level": extract_from_region(
            image,
            StudentSearchPattern.BOND_LEVEL.value,
            mode=ExtractionMode.BOND_LEVEL,
        ),
        "Rarity": extract_from_region(
            image,
            StudentSearchPattern.STAR_QUANTITY.value,
            mode=ExtractionMode.STAR,
        ),
        "Gear 1 Tier": extract_from_region(
            image,
            StudentSearchPattern.GEAR_SLOT.GEAR_1.value,
            mode=ExtractionMode.GEAR,
        ),
        "Gear 2 Tier": extract_from_region(
            image,
            StudentSearchPattern.GEAR_SLOT.GEAR_2.value,
            mode=ExtractionMode.GEAR,
        ),
        "Gear 3 Tier": extract_from_region(
            image,
            StudentSearchPattern.GEAR_SLOT.GEAR_3.value,
            mode=ExtractionMode.GEAR,
        ),
        "Gear Bond Tier": extract_from_region(
            image,
            StudentSearchPattern.GEAR_SLOT.GEAR_BOND.value,
            mode=ExtractionMode.GEAR,
        ),
        "Unique Equipment Star Quantity": extract_from_region(
            image,
            StudentSearchPattern.UNIQUE_EQUIPMENT_STAR_QUANTITY.value,
            mode=ExtractionMode.UE_STAR,
        ),
        "Unique Equipment Level": extract_from_region(
            image,
            StudentSearchPattern.UNIQUE_EQUIPMENT_LEVEL.value,
            mode=ExtractionMode.UE_LEVEL,
        ),
        "Skill EX": extract_from_region(
            image,
            StudentSearchPattern.SKILL.EX.value,
            mode=ExtractionMode.SKILL_LEVEL,
        ),
        "Skill Basic": extract_from_region(
            image,
            StudentSearchPattern.SKILL.BASIC.value,
            mode=ExtractionMode.SKILL_LEVEL,
        ),
        "Skill Enhanced": extract_from_region(
            image,
            StudentSearchPattern.SKILL.ENHANCED.value,
            mode=ExtractionMode.SKILL_LEVEL,
        ),
        "Skill Sub": extract_from_region(
            image,
            StudentSearchPattern.SKILL.SUB.value,
            mode=ExtractionMode.SKILL_LEVEL,
        ),
        "Talent_ATK": extract_from_region(
            image,
            StudentSearchPattern.TALENT.ATK.value,
            mode=ExtractionMode.TALENT,
        ),
        "Talent_HP": extract_from_region(
            image,
            StudentSearchPattern.TALENT.HP.value,
            mode=ExtractionMode.TALENT,
        ),
        "Talent_HEALING": extract_from_region(
            image,
            StudentSearchPattern.TALENT.HEALING.value,
            mode=ExtractionMode.TALENT,
        ),
    }
