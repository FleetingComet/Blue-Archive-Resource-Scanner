from enum import Enum
from area import Location
from typing import Type


class _StudentInfoButtons(Enum):
    PREVIOUS: Type[Location] = Location(30, 380)
    NEXT: Type[Location] = Location(1250, 380)


class StudentInfo(Enum):
    BUTTONS: Type[_StudentInfoButtons] = _StudentInfoButtons
