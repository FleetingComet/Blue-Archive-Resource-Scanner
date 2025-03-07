from enum import Enum
from area import Location


class _StudentInfoButtons(Enum):
    PREVIOUS = Location(30, 380)
    NEXT = Location(1250, 380)


class StudentInfo(Enum):
    BUTTONS: _StudentInfoButtons = _StudentInfoButtons
