from enum import Enum

from src.core.area import Region


# # 1280x720p
class EntryPointButtons(Enum):
    MENU_TAB = Region(1200, 23, 50, 33)
    MENU_TAB_EQUIPMENT = Region(425, 310, 210, 60)
    MENU_TAB_ITEMS = Region(655, 310, 210,60)
    HOME = Region(1212, 5, 53, 40)
    STUDENTS = Region(285, 620, 78, 75) # or x:292 idk


class EntryPointTitles(Enum):
    PAGE = Region(100, 5, 220, 50)
    MENU_TAB = Region(415, 160, 415, 40)