from enum import Enum
from area import Location, Region


# # 1280x720p
class EntryPointButtons(Enum):
    MENU_TAB = Location(1220, 40)
    MENU_TAB_EQUIPMENT = Location(540, 380)
    MENU_TAB_ITEMS = Location(770, 380)
    HOME = Location(1235, 20)
    STUDENTS = Location(330, 650)


class EntryPointTitles(Enum):
    PAGE = Region(100, 5, 220, 50)
    MENU_TAB = Region(410, 200, 420, 40)