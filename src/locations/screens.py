from enum import Enum

from src.core.area import Location, Region
from src.locations.common import AspectLocation, AspectRegion, cx, cy, rx


class StudentInfo:
    class BUTTONS(Enum):
        # PREVIOUS: Location = Location(30, 380)
        PREVIOUS: Location = AspectLocation(
            standard=lambda: cy(Location(22, 24)),
            wide_18_9=lambda: cy(Location(21, 27)),
            max_wide=lambda: cy(Location(31, 28)),
        )
        # NEXT: Location = Location(1250, 380)
        NEXT: Location = AspectLocation(
            standard=lambda: cy(rx(Location(-22, 24))),
            wide_18_9=lambda: cy(rx(Location(-21, 27))),
            max_wide=lambda: cy(rx(Location(-30, 28))),
        )


class StudentList(Enum):
    # FIRST_STUDENT: Region = Region(55, 200, 175, 195)
    FIRST_STUDENT: Region = AspectRegion(
        standard=lambda: cy(cx(Region(-588, -160, 176, 198))),
        wide_18_9=lambda: cy(cx(Region(-660, -136, 196, 223))),
        max_wide=lambda: cy(cx(Region(-678, -129, 202, 228))),
    )


class Home:
    # MENU_BUTTON: Region = Region(1150, 25, 50, 30)
    MENU_REGION: Region = Region(1010, 0, 270, 70)


class Page:
    # HOME_BUTTON: Region = Region(1210, 5, 50, 38)
    MENU_REGION: Region = Region(1010, 0, 270, 70)
