from enum import Enum


class ExtractionMode(Enum):
    # Text-based modes (OCR)
    NAME = "name"
    NUMBER = "number"
    MULTI_LINE_NAME = "multi_line_name"
    LEVEL = "level_indicator"
    SKILL_LEVEL = "skill_level_indicator"
    BOND_LEVEL = "number_in_circle"
    UE_LEVEL = "ue_level"
    TALENT = "talent"

    # Shape-based modes (Counting)
    STAR = "star"
    UE_STAR = "ue_star"

    # something
    GEAR = "gear"
