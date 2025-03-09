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

    BOND_LEVEL = Region(40, 555, 30, 25)
    # BOND_LEVEL = Region(50, 555, 20, 25) # 

    STAR_QUANTITY = Region(260, 560, 80, 30)
    UNIQUE_EQUIPMENT_STAR_QUANTITY = Region(1030, 510, 60, 20) #Exclusive Weapon
    UNIQUE_EQUIPMENT_LEVEL = Region(779, 455, 61, 21) #Exclusive Weapon Level

    GEAR_1_TIER = Region(686, 617, 20, 15)
    GEAR_2_TIER = Region(779, 617, 20, 15)
    GEAR_3_TIER = Region(872, 617, 20, 15)
    # GEAR_BOND_TIER = Region(960, 615, 30, 20) #works idk why
    GEAR_BOND_TIER = Region(965, 617, 20, 15)

    SKILL_EX = Region(686, 403, 86, 20) #
    SKILL_BASIC = Region(796, 403, 79, 20)
    SKILL_ENHANCED = Region(901, 403, 80, 20)#
    SKILL_SUB = Region(1008, 403, 79, 20)