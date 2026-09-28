from enum import Enum

from src.core.area import Region
from src.locations.common import AspectRegion, rx


class EntryPointButtons(Enum):
    MENU_TAB = AspectRegion(
        standard=lambda: rx(Region(-90, 11, 78, 47)),
        wide_18_9=lambda: rx(Region(-94, 10, 77, 55)),
        max_wide=lambda: rx(Region(-96, 9, 79, 56)),
    )

    HOME = AspectRegion(  # noqa: PIE796
        standard=lambda: rx(Region(-90, 11, 78, 47)),
        wide_18_9=lambda: rx(Region(-94, 10, 77, 55)),
        max_wide=lambda: rx(Region(-96, 9, 79, 56)),
    )


class EntryPointTitles(Enum):
    PAGE = Region(100, 5, 220, 50)
    MENU_TAB = Region(415, 160, 415, 40)
