from enum import Enum

from area import Region


# 1280x720p
class SearchPattern(Enum):
    ITEM_OWNED = Region(480, 510, 100, 40)
    ITEM_NAME = Region(50, 480, 430, 70)
    
    EQUIPMENT_OWNED = Region(530, 595, 90, 30)  # plus 5 for y (for ocr to detect it)
    EQUIPMENT_NAME = Region(60, 560, 420, 80)

    #
    AP = Region(560, 10, 105, 30)
    CREDITS = Region(770, 10, 140, 30)
    PYROXENE = Region(965, 10, 105, 30)
