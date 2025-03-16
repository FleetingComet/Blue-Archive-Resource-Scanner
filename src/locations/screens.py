from area import Location, Region


class StudentInfoButtons:
    PREVIOUS = Location(30, 380)
    NEXT = Location(1250, 380)


class StudentInfo:
    BUTTONS = StudentInfoButtons


class StudentList:
    FIRST_STUDENT = Location(150, 290)


class Home:
    MENU_BUTTON = Region(1200, 25, 50, 30)


class Page:
    HOME_BUTTON = Region(1210, 5, 50, 38)
