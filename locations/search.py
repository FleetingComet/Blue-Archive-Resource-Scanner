from enum import Enum

from src.core.area import Region


# 1280x720p
class SearchPattern(Enum):
    ITEM_OWNED = Region(480, 510, 100, 40)
    ITEM_NAME = Region(55 - 5, 480 - 5, 430, 70)
    # ITEM_NAME = Region(50, 470, 432, 70)  # plus 5 for x (to avoid ')

    EQUIPMENT_OWNED = Region(530, 595, 90, 30)  # plus 5 for y (for ocr to detect it)
    EQUIPMENT_NAME = Region(60, 560, 420, 80)

    AP = Region(475, 20, 102, 35)  # -10 from true value idk why
    CREDIT = Region(660, 20, 150, 35)  # -10
    PYROXENE = Region(860, 20, 100, 35)


class StudentSearchPattern(Enum):
    STUDENT_NAME = Region(65, 550, 185, 40)
    LEVEL = Region(30, 585, 45, 30)

    BOND_LEVEL = Region(30, 550, 35, 35)

    STAR_QUANTITY = Region(245, 560, 82, 25)
    UNIQUE_EQUIPMENT_STAR_QUANTITY = Region(977, 504, 93, 22)  # Exclusive Weapon
    UNIQUE_EQUIPMENT_LEVEL = Region(775, 450, 61, 21)  # Exclusive Weapon Level

    SKILL_EX = Region(686, 402, 80, 20)
    SKILL_BASIC = Region(796, 403, 80, 20)
    SKILL_ENHANCED = Region(901, 403, 80, 20)
    SKILL_SUB = Region(1008, 402, 79, 22)

    class GEAR_SLOT(Enum):
        """
        Gear 1 to 3 and Bond Gear
        """

        GEAR_1 = Region(665 + 12, 600, 20, 25 + 5)  # ? +12 Xoffset, widthOffset +5
        GEAR_2 = Region(755 + 12, 600, 20, 25 + 5)
        GEAR_3 = Region(850 + 10, 600, 20, 25 + 5)  # ? idk
        GEAR_BOND = Region(940 + 11, 600, 20, 25 + 4)  # ? idk

    class TALENT(Enum):
        """
        HP, ATK = Top Row
        DEF (Not Used), HEALING = Bottom Row
        ...
        HP, DEF = LEFT COLUMN
        ATK, HEALING = RIGHT COLUMN
        """

        HP = Region(675, 225, 215, 35)
        ATK = Region(890, 225, 215, 35)
        HEALING = Region(890, 260, 205, 35)
