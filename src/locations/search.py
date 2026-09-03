from enum import Enum

from src.core.area import Region


# 1280x720p
class SearchPattern(Enum):
    class EQUIPMENT(Enum):
        NAME = Region(50, 560, 420, 70)
        OWNED = Region(530, 590, 75, 40)

    class ITEM(Enum):
        NAME = Region(55 - 5, 480 - 5, 430, 70)
        OWNED = Region(480, 510, 100, 40)

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

    class SKILL(Enum):
        EX = Region(670, 400, 85, 20)
        BASIC = Region(775, 400, 85, 20)
        ENHANCED = Region(880, 400, 85, 20)
        SUB = Region(985, 400, 85, 22)

    class SKILL_PHONE(Enum):
        EX = Region(54, 48, 85, 20).x_from_center(1565).y_from_center()
        BASIC = Region(179, 48, 85, 20).x_from_center(1565).y_from_center()
        ENHANCED = Region(300, 48, 85, 20).x_from_center(1565).y_from_center()
        SUB = Region(422, 48, 85, 22).x_from_center(1565).y_from_center()
        # EX = Region(54, 48, 85, 20).x_from_center(1565).y_from_center()
        # BASIC = Region(179, 48, 85, 20).x_from_center(1565).y_from_center()
        # ENHANCED = Region(300, 48, 85, 20).x_from_center(1565).y_from_center()
        # SUB = Region(422, 48, 85, 22).x_from_center(1565).y_from_center()

    # EX = Region(40, 400, 85, 20).x_from_center()
    # BASIC = Region(150, 400, 85, 20).x_from_center()
    # ENHANCED = Region(260, 400, 85, 20).x_from_center()
    # SUB = Region(365, 400, 85, 22).x_from_center()

    class GEAR_SLOT(Enum):
        """
        Gear 1 to 3 and Bond Gear
        """

        # GEAR_1 = Region(665 + 12, 600, 20, 25 + 5)  # ? +12 Xoffset, widthOffset +5
        # GEAR_2 = Region(755 + 12, 600, 20, 25 + 5)
        # GEAR_3 = Region(850 + 10, 600, 20, 25 + 5)  # ? idk
        # GEAR_BOND = Region(940 + 11, 600, 20, 25 + 4)  # ? idk

        # GEAR_1 = Region(676, 615, 29, 19)
        # GEAR_2 = Region(770, 615, 29, 19)
        # GEAR_3 = Region(864, 615, 29, 19)
        # # GEAR_BOND_TIER = Region(960, 615, 30, 20) #works idk why
        # GEAR_BOND = Region(957, 615, 29, 19)

        # GEAR_1 = Region(679, 616, 19, 16)
        # GEAR_2 = Region(772, 616, 19, 16)
        # GEAR_3 = Region(865, 616, 19, 16)
        # GEAR_BOND = Region(958, 616, 19, 16)

        GEAR_1 = Region(679, 616, 70, 16)
        GEAR_2 = Region(772, 616, 70, 16)
        GEAR_3 = Region(865, 616, 70, 16)
        GEAR_BOND = Region(958, 616, 70, 16)

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
