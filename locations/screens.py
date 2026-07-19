from src.core.area import Location, Region


class StudentInfo:
    class BUTTONS:
        PREVIOUS: Location = Location(30, 380)
        NEXT: Location = Location(1250, 380)

class StudentList:
    FIRST_STUDENT: Region = Region(55, 200, 175, 195)


class Home:
    # MENU_BUTTON: Region = Region(1150, 25, 50, 30)
    MENU_REGION: Region = Region(1010, 0, 270, 70)


class Page:
    # HOME_BUTTON: Region = Region(1210, 5, 50, 38)
    MENU_REGION: Region = Region(1010, 0, 270, 70)