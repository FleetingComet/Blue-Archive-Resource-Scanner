from enum import Enum

from area import Region


# 1280x720p
class SearchPattern(Enum):
    ITEM_OWNED = Region(480, 510, 100, 40)
    ITEM_NAME = Region(55, 480, 430, 70)  # plus 5 for x (to avoid ')

    EQUIPMENT_OWNED = Region(530, 595, 90, 30)  # plus 5 for y (for ocr to detect it)
    EQUIPMENT_NAME = Region(60, 560, 420, 80)

    #
    AP = Region(560, 10, 105, 30)
    CREDITS = Region(770, 10, 140, 30)
    PYROXENE = Region(965, 10, 105, 30)


class StudentSearchPattern(Enum):
    STUDENT_NAME = Region(70, 550, 190, 35)
    LEVEL = Region(30, 585, 50, 30)
    BOND_LEVEL = Region(30, 555, 40, 25)

    GEAR_1_TIER = Region(680, 615, 30, 20)
    GEAR_2_TIER = Region(775, 615, 30, 20)
    GEAR_3_TIER = Region(865, 615, 30, 20)
    GEAR_BOND_TIER = Region(960, 615, 30, 20)

    SKILL_EX = Region(685, 400, 85, 25)
    SKILL_BASIC = Region(795, 400, 85, 25)
    SKILL_EMHAMCED = Region(900, 400, 85, 25)
    SKILL_SUB = Region(1010, 400, 85, 25)
