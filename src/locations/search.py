from enum import Enum

from src.core.area import Region
from src.locations.common import AspectRegion, by, cx, cy


# 1280x720p
class SearchPattern(Enum):
    class EQUIPMENT(Enum):
        # NAME = Region(50, 560, 420, 70)
        NAME = AspectRegion(
            standard=lambda: cy(cx(Region(-582, 197, 422, 83))),
            wide_18_9=lambda: cy(cx(Region(-656, 177, 476, 92))),
            max_wide=lambda: cy(cx(Region(-713, 173, 488, 92))),
        )

        # OWNED = Region(530, 590, 75, 40)
        OWNED = AspectRegion(
            standard=lambda: cy(cx(Region(-107, 234, 90, 36))),
            wide_18_9=lambda: cy(cx(Region(-121, 219, 102, 40))),
            max_wide=lambda: cy(cx(Region(-163, 215, 104, 40))),
        )

    class ITEM(Enum):
        # NAME = Region(55 - 5, 480 - 5, 430, 70)
        NAME = AspectRegion(
            standard=lambda: cy(cx(Region(-588, 117, 431, 80))),
            wide_18_9=lambda: cy(cx(Region(-661, 87, 485, 89))),
            max_wide=lambda: cy(cx(Region(-719, 80, 498, 91))),
        )
        # OWNED = Region(480, 510, 100, 40)
        OWNED = AspectRegion(
            standard=lambda: cy(cx(Region(-154, 152, 90, 34))),
            wide_18_9=lambda: cy(cx(Region(-173, 126, 101, 39))),
            max_wide=lambda: cy(cx(Region(-218, 119, 105, 40))),
        )

    # AP = Region(475, 20, 102, 35)  # -10 from true value idk why
    AP = AspectRegion(
        standard=lambda: cy(cx(Region(-106, -342, 87, 35))),
        wide_18_9=lambda: cy(cx(Region(-119, -337, 98, 36))),
        max_wide=lambda: cy(cx(Region(-83, -338, 102, 39))),
    )
    # CREDIT = Region(660, 20, 150, 35)  # -10
    CREDIT = AspectRegion(
        standard=lambda: cy(cx(Region(58, -342, 150, 36))),
        wide_18_9=lambda: cy(cx(Region(67, -339, 169, 38))),
        max_wide=lambda: cy(cx(Region(108, -337, 174, 37))),
    )
    # PYROXENE = Region(860, 20, 100, 35)
    PYROXENE = AspectRegion(
        standard=lambda: cy(cx(Region(255, -340, 113, 33))),
        wide_18_9=lambda: cy(cx(Region(288, -338, 125, 39))),
        max_wide=lambda: cy(cx(Region(336, -337, 129, 38))),
    )


class StudentSearchPattern(Enum):
    STUDENT_NAME = AspectRegion(
        standard=lambda: by(Region(72, -170, 188, 44)),
        wide_18_9=lambda: by(Region(81, -191, 212, 50)),
        max_wide=lambda: by(Region(85, -196, 219, 51)),
    )

    LEVEL = AspectRegion(
        standard=lambda: by(Region(31, -124, 49, 18)),
        wide_18_9=lambda: by(Region(35, -138, 55, 19)),
        max_wide=lambda: by(Region(37, -144, 58, 23)),
    )

    BOND_LEVEL = AspectRegion(
        standard=lambda: by(Region(40, -160, 31, 25)),
        wide_18_9=lambda: by(Region(45, -180, 35, 30)),
        max_wide=lambda: by(Region(50, -184, 34, 29)),
    )

    STAR_QUANTITY = AspectRegion(
        standard=lambda: by(Region(260, -154, 78, 24)),
        wide_18_9=lambda: by(Region(295, -173, 85, 28)),
        max_wide=lambda: by(Region(305, -178, 88, 28)),
    )

    UNIQUE_EQUIPMENT_STAR_QUANTITY = AspectRegion(
        standard=lambda: cy(cx(Region(361, 149, 88, 21))),
        wide_18_9=lambda: cy(cx(Region(409, 168, 96, 24))),
        max_wide=lambda: cy(cx(Region(421, 174, 99, 22))),
    )  # Exclusive Weapon
    UNIQUE_EQUIPMENT_LEVEL = AspectRegion(
        standard=lambda: cy(cx(Region(139, 95, 65, 20))),
        wide_18_9=lambda: cy(cx(Region(156, 108, 72, 21))),
        max_wide=lambda: cy(cx(Region(162, 111, 71, 21))),
    )  # Exclusive Weapon Level

    class SKILL(Enum):
        EX = AspectRegion(
            standard=lambda: cy(Region(686, 42, 86, 22)),
            wide_18_9=lambda: cy(Region(772, 47, 96, 25)),
            max_wide=lambda: cy(Region(836, 48, 99, 25)),
        )

        BASIC = AspectRegion(
            standard=lambda: cy(Region(796, 42, 80, 22)),
            wide_18_9=lambda: cy(Region(895, 47, 89, 25)),
            max_wide=lambda: cy(Region(963, 48, 91, 25)),
        )

        ENHANCED = AspectRegion(
            standard=lambda: cy(Region(901, 42, 80, 22)),
            wide_18_9=lambda: cy(Region(1014, 47, 89, 25)),
            max_wide=lambda: cy(Region(1085, 48, 92, 25)),
        )

        SUB = AspectRegion(
            standard=lambda: cy(Region(1008, 42, 80, 22)),
            wide_18_9=lambda: cy(Region(1133, 47, 90, 25)),
            max_wide=lambda: cy(Region(1208, 48, 92, 25)),
        )

    class GEAR_SLOT(Enum):
        """
        Gear 1 to 3 and Bond Gear
        """

        GEAR_1 = AspectRegion(
            standard=lambda: cy(cx(Region(43, 256, 48, 15))),
            wide_18_9=lambda: cy(cx(Region(48, 288, 51, 17))),
            max_wide=lambda: cy(cx(Region(50, 296, 62, 19))),
        )
        GEAR_2 = AspectRegion(
            standard=lambda: cy(cx(Region(136, 256, 49, 15))),
            wide_18_9=lambda: cy(cx(Region(153, 288, 56, 17))),
            max_wide=lambda: cy(cx(Region(158, 296, 54, 18))),
        )

        GEAR_3 = AspectRegion(
            standard=lambda: cy(cx(Region(229, 256, 45, 15))),
            wide_18_9=lambda: cy(cx(Region(257, 288, 52, 17))),
            max_wide=lambda: cy(cx(Region(265, 296, 56, 17))),
        )

    class TALENT(Enum):
        """
        HP, ATK = Top Row
        DEF (Not Used), HEALING = Bottom Row
        ...
        HP, DEF = LEFT COLUMN
        ATK, HEALING = RIGHT COLUMN
        """

        HP = AspectRegion(
            standard=lambda: cy(cx(Region(44, -135, 206, 34))),
            wide_18_9=lambda: cy(cx(Region(49, -152, 233, 39))),
            max_wide=lambda: cy(cx(Region(51, -156, 237, 39))),
        )

        ATK = AspectRegion(
            standard=lambda: cy(cx(Region(250, -135, 203, 33))),
            wide_18_9=lambda: cy(cx(Region(282, -152, 228, 39))),
            max_wide=lambda: cy(cx(Region(290, -156, 235, 39))),
        )
        HEALING = AspectRegion(
            standard=lambda: cy(cx(Region(250, -99, 203, 33))),
            wide_18_9=lambda: cy(cx(Region(282, -111, 228, 38))),
            max_wide=lambda: cy(cx(Region(290, -113, 235, 37))),
        )
