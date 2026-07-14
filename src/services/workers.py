from pathlib import Path
from typing import TypedDict

import cv2

from locations.search import StudentSearchPattern
from src.utils.ocr.extract import (
    extract_from_region,
    extract_item_name,
    extract_owned_count,
)


class ItemResult(TypedDict):
    name: str | None
    count: str | None


def item_ocr_worker(img_path: Path, grid_type: str) -> ItemResult:
    """Worker for Equipment/Items"""
    img = cv2.imread(str(img_path))
    if img is None:
        return None

    return {
        "name": extract_item_name(img, grid_type),
        "count": extract_owned_count(img, grid_type),
    }


def student_ocr_worker(img_path: Path):
    """Runs full student OCR on a single saved screenshot."""
    image = cv2.imread(str(img_path))
    if image is None:
        return None

    return {
        "Name": extract_from_region(
            image,
            StudentSearchPattern.STUDENT_NAME.value,
            image_type="name",
        ),
        "Level": extract_from_region(
            image,
            StudentSearchPattern.LEVEL.value,
            image_type="level_indicator",
        ),
        "Bond Level": extract_from_region(
            image,
            StudentSearchPattern.BOND_LEVEL.value,
            image_type="number_in_circle",
        ),
        "Rarity": extract_from_region(
            image,
            StudentSearchPattern.STAR_QUANTITY.value,
            image_type="star",
        ),
        "Gear 1 Tier": extract_from_region(
            image,
            StudentSearchPattern.GEAR_1_TIER.value,
            image_type="gear",
        ),
        "Gear 2 Tier": extract_from_region(
            image,
            StudentSearchPattern.GEAR_2_TIER.value,
            image_type="gear",
        ),
        "Gear 3 Tier": extract_from_region(
            image,
            StudentSearchPattern.GEAR_3_TIER.value,
            image_type="gear",
        ),
        "Gear Bond Tier": extract_from_region(
            image,
            StudentSearchPattern.GEAR_BOND_TIER.value,
            image_type="gear",
        ),
        "Unique Equipment Star Quantity": extract_from_region(
            image,
            StudentSearchPattern.UNIQUE_EQUIPMENT_STAR_QUANTITY.value,
            image_type="ue_star",
        ),
        "Unique Equipment Level": extract_from_region(
            image,
            StudentSearchPattern.UNIQUE_EQUIPMENT_LEVEL.value,
            image_type="ue_level",
        ),
        "Skill EX": extract_from_region(
            image,
            StudentSearchPattern.SKILL_EX.value,
            image_type="skill_level_indicator",
        ),
        "Skill Basic": extract_from_region(
            image,
            StudentSearchPattern.SKILL_BASIC.value,
            image_type="skill_level_indicator",
        ),
        "Skill Enhanced": extract_from_region(
            image,
            StudentSearchPattern.SKILL_ENHANCED.value,
            image_type="skill_level_indicator",
        ),
        "Skill Sub": extract_from_region(
            image,
            StudentSearchPattern.SKILL_SUB.value,
            image_type="skill_level_indicator",
        ),
        "Talent_ATK": extract_from_region(
            image,
            StudentSearchPattern.TALENT.ATK.value,
            image_type="talent",
        ),
        "Talent_HP": extract_from_region(
            image,
            StudentSearchPattern.TALENT.HP.value,
            image_type="talent",
        ),
        "Talent_HEALING": extract_from_region(
            image,
            StudentSearchPattern.TALENT.HEALING.value,
            image_type="talent",
        ),
    }
