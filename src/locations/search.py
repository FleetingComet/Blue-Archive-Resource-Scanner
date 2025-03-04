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

    # At Level up tab
    # LEVEL = Region(760, 230, 90, 25)
    # EXP_BAR = Region(950, 230, 242, 25)

    # BOND_LEVEL = Region(30, 555, 40, 25)
    BOND_LEVEL = Region(50, 555, 20, 25) # 

    GEAR_1_TIER = Region(680, 615, 30, 20)
    GEAR_2_TIER = Region(775, 615, 30, 20)
    GEAR_3_TIER = Region(865, 615, 30, 20)
    GEAR_BOND_TIER = Region(960, 615, 30, 20)
    # GEAR_1_TIER = Region(686, 616, 20, 16)
    # GEAR_2_TIER = Region(779, 616, 20, 16)
    # GEAR_3_TIER = Region(872, 616, 20, 16)
    # GEAR_BOND_TIER = Region(974, 616, 20, 16)

    # + 3 offset for y and - 5 height
    # + 10 offset for x and - 15 width
    SKILL_EX = Region(695, 403, 70, 20) #
    SKILL_BASIC = Region(795, 403, 85, 20)
    SKILL_ENHANCED = Region(910, 403, 70, 20)#
    SKILL_SUB = Region(1010, 403, 85, 20)
    # SKILL_EX = Region(703, 404, 42, 17)
    # SKILL_BASIC = Region(812, 404, 42, 17)
    # SKILL_ENHANCED = Region(917, 404, 42, 17)
    # SKILL_SUB = Region(1025, 404, 42, 17)
