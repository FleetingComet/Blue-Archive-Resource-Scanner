# Screen Config
# Screens the user explicitly toggles in the wizard.
# "Student" is excluded - it is a sub-screen of "Students" and is
# enabled/disabled automatically alongside it.
from pathlib import Path

from src.core.area import Size

SCREEN_DEFAULTS = {
    "Currencies": {
        "menu_location": "currencies",
        "grid_type": "currencies",
        "uses_menu_tab": False,
    },
    "Equipment": {
        "menu_location": "menu_equipment",
        "grid_type": "Equipment",
        "uses_menu_tab": True,
    },
    "Items": {
        "menu_location": "menu_items",
        "grid_type": "Items",
        "uses_menu_tab": True,
    },
    "Students": {
        "menu_location": "menu_students",
        "grid_type": "Students",
        "uses_menu_tab": False,
        "skip_if_visited": ["Student"],
    },
    "Student": {
        "menu_location": "first_student",
        "grid_type": "Student",
        "uses_menu_tab": False,
    },
}

USER_FACING_SCREENS = ["Equipment", "Items", "Students", "Currencies"]
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