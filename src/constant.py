# Screen Config
# Screens the user explicitly toggles in the wizard.
# "Student" is excluded - it is a sub-screen of "Students" and is
# enabled/disabled automatically alongside it.
SCREEN_DEFAULTS = {
    "Currencies": {
        "menu_location": "currencies",
        "grid_type": "currencies",
        "uses_menu_tab": False,
        "grid_config": None,  # No grid scanning for currencies
    },
    "Equipment": {
        "menu_location": "menu_equipment",
        "grid_type": "Equipment",
        "uses_menu_tab": True,
        "grid_config": {
            "start_x": 690,
            "start_y": 160,
            "item_width": 110,
            "item_height": 90,
            "cols_per_row": 5,
            "rows_per_page": 5,
            "y_padding": 11,
            "swipe_distance": 450,
            "end_y": 660,
        },
    },
    "Items": {
        "menu_location": "menu_items",
        "grid_type": "Items",
        "uses_menu_tab": True,
        "grid_config": {
            "start_x": 690,
            "start_y": 160,
            "item_width": 110,
            "item_height": 90,
            "cols_per_row": 5,
            "rows_per_page": 5,
            "y_padding": 11,
            "swipe_distance": 450,
            "end_y": 560,
        },
    },
    "Students": {
        "menu_location": "menu_students",
        "grid_type": "Students",
        "uses_menu_tab": False,
        "grid_config": None,  # No grid scanning for students list
    },
    "Student": {
        "menu_location": "first_student",
        "grid_type": "Student",
        "uses_menu_tab": False,
        "grid_config": None,  # Individual student info, no grid
    },
}

USER_FACING_SCREENS = ["Equipment", "Items", "Students", "Currencies"]
