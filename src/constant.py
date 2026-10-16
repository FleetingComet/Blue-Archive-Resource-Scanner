from enum import StrEnum
from pathlib import Path

from src.core.area import Size


class Screen(StrEnum):
    """
    Navigable UI screens.

    Values are the exact keys used in ``config/screen_config.json`` and in
    scan output, so they stay JSON/str-compatible while making typos fail
    loudly instead of silently disabling a screen.
    """

    CURRENCIES = "Currencies"
    EQUIPMENT = "Equipment"
    ITEMS = "Items"
    STUDENTS = "Students"
    STUDENT = "Student"  # sub-screen of STUDENTS


# Screen Config
# Screens the user explicitly toggles in the wizard.
# Screen.STUDENT is excluded - it is a sub-screen of Screen.STUDENTS and is
# enabled/disabled automatically alongside it.
SCREEN_DEFAULTS = {
    Screen.CURRENCIES: {
        "menu_location": "currencies",
        "grid_type": "currencies",
        "uses_menu_tab": False,
    },
    Screen.EQUIPMENT: {
        "menu_location": "menu_equipment",
        "grid_type": Screen.EQUIPMENT,
        "uses_menu_tab": True,
    },
    Screen.ITEMS: {
        "menu_location": "menu_items",
        "grid_type": Screen.ITEMS,
        "uses_menu_tab": True,
    },
    Screen.STUDENTS: {
        "menu_location": "menu_students",
        "grid_type": Screen.STUDENTS,
        "uses_menu_tab": False,
        "skip_if_visited": [Screen.STUDENT],
    },
    Screen.STUDENT: {
        "menu_location": "first_student",
        "grid_type": Screen.STUDENT,
        "uses_menu_tab": False,
    },
}

USER_FACING_SCREENS = [
    Screen.EQUIPMENT,
    Screen.ITEMS,
    Screen.STUDENTS,
    Screen.CURRENCIES,
]
SCRIPT_SIZE: Size = Size(1280, 720)

TEMPLATE_BUTTONS = {
    "menu_students": Path("assets/images/templates/Icons/student_page.png"),
    "menu_equipment": Path("assets/images/templates/Icons/equipment_page.png"),
    "menu_items": Path("assets/images/templates/Icons/item_page.png"),
}

MENU_TAB_KEYWORDS: dict[str, tuple[str, ...]] = {
    "en": ("menu",),
    "jp": ("メニュー",),
    "kr": ("메뉴",),
    "zh": ("菜单", "選單"),
}
