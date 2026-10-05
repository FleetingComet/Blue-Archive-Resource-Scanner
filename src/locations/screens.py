from enum import Enum

from src.core.area import Location, Region
from src.locations.common import AspectLocation, AspectRegion, cxy, cy, rx


class StudentInfo:
    class BUTTONS(Enum):
        PREVIOUS: AspectLocation = AspectLocation(
            standard=lambda: cy(Location(22, 24)),
            wide_18_9=lambda: cy(Location(21, 27)),
            max_wide=lambda: cy(Location(31, 28)),
        )
        NEXT: AspectLocation = AspectLocation(
            standard=lambda: cy(rx(Location(-22, 24))),
            wide_18_9=lambda: cy(rx(Location(-21, 27))),
            max_wide=lambda: cy(rx(Location(-30, 28))),
        )


class StudentList(Enum):
    FIRST_STUDENT: AspectRegion = AspectRegion(
        standard=lambda: cxy(Region(-588, -160, 176, 198)),
        wide_18_9=lambda: cxy(Region(-660, -136, 196, 223)),
        max_wide=lambda: cxy(Region(-678, -129, 202, 228)),
    )


class Home:
    MENU_REGION = rx(Region(-270, 0, 270, 70))


class Page:
    MENU_REGION = rx(Region(-270, 0, 270, 70))
