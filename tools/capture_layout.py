"""Capture the game screen and draw the scan regions on it, to check they line up.

Navigate the game by hand, then pick the screen you are on. Nothing is clicked.
Uses the device from config/settings.json (PC window or ADB), so emulator and
PC captures can be compared side by side.

Usage: python -m tools.capture_layout
"""

from datetime import datetime
from enum import EnumType

import cv2

from locations.entrypoint import EntryPointButtons, EntryPointTitles
from locations.screens import Home, StudentInfo, StudentList
from locations.search import SearchPattern, StudentSearchPattern
from src.core.area import Location, Region
from src.core.config import Config
from src.services.scanners.grids import EQUIPMENT_GRID, ITEMS_GRID
from src.utils.device.factory import create_device

OUT_DIR = Config.OUTPUT_DIR / "layout"


def regions_of(enum_cls: EnumType, prefix: str = "") -> dict:
    """Every region in an Enum, including the nested Enum classes."""
    found = {f"{prefix}{m.name}": m.value for m in enum_cls}
    for name, value in vars(enum_cls).items():
        if isinstance(value, EnumType):
            found |= regions_of(value, f"{prefix}{name}.")
    return found


LAYOUTS = {
    "home": {
        "AP": SearchPattern.AP.value,
        "CREDIT": SearchPattern.CREDIT.value,
        "PYROXENE": SearchPattern.PYROXENE.value,
        "MENU_REGION": Home.MENU_REGION,
        "MENU_TAB": EntryPointButtons.MENU_TAB.value,
        "STUDENTS": EntryPointButtons.STUDENTS.value,
    },
    "menu": {
        "MENU_TAB_TITLE": EntryPointTitles.MENU_TAB.value,
        "MENU_TAB_EQUIPMENT": EntryPointButtons.MENU_TAB_EQUIPMENT.value,
        "MENU_TAB_ITEMS": EntryPointButtons.MENU_TAB_ITEMS.value,
    },
    "equipment": {
        "PAGE_TITLE": EntryPointTitles.PAGE.value,
        "GRID": EQUIPMENT_GRID,
        **regions_of(SearchPattern.EQUIPMENT),
        "HOME": EntryPointButtons.HOME.value,
    },
    "items": {
        "PAGE_TITLE": EntryPointTitles.PAGE.value,
        "GRID": ITEMS_GRID,
        **regions_of(SearchPattern.ITEM),
        "HOME": EntryPointButtons.HOME.value,
    },
    "students": {
        "PAGE_TITLE": EntryPointTitles.PAGE.value,
        "FIRST_STUDENT": StudentList.FIRST_STUDENT,
    },
    "student": {
        "PAGE_TITLE": EntryPointTitles.PAGE.value,
        **regions_of(StudentSearchPattern),
        "PREVIOUS": StudentInfo.BUTTONS.PREVIOUS,
        "NEXT": StudentInfo.BUTTONS.NEXT,
    },
}


def draw_overlay(image, layout: dict):
    overlay = image.copy()
    for name, area in layout.items():
        if isinstance(area, Location):
            cv2.circle(overlay, (area.x, area.y), 8, (0, 0, 255), 2)
            x, y = area.x + 10, area.y
        else:
            assert isinstance(area, Region)
            cv2.rectangle(
                overlay, (area.x, area.y), (area.right, area.bottom), (0, 255, 0), 1
            )
            x, y = area.x, max(area.y - 3, 10)
        cv2.putText(
            overlay, name, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1
        )
    return overlay


def main():
    device = create_device(Config.settings)
    if not device.connect(Config.ADB_RETRIES):
        raise SystemExit("Could not connect to the device.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    names = "/".join(LAYOUTS)
    while True:
        name = input(f"Screen you are on ({names}, q to quit): ").strip().lower()
        if name == "q":
            break
        if name not in LAYOUTS:
            print(f"Unknown screen '{name}'.")
            continue

        try:
            image = device.capture_screenshot()
        except Exception as e:  # noqa: BLE001
            image = None
            print(f"Capture error: {e}")
        if image is None:
            print("Capture failed, try again.")
            continue
        if image.shape[2] == 4:  # ADB screenshots carry alpha
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        stem = OUT_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{name}"
        cv2.imwrite(f"{stem}.png", image)
        cv2.imwrite(f"{stem}_overlay.png", draw_overlay(image, LAYOUTS[name]))
        print(f"Saved {stem}.png and {stem}_overlay.png")


if __name__ == "__main__":
    main()
