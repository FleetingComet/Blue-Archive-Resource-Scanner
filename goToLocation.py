import time
import cv2
from area import Location, Region
from config import Config
from src.locations.entrypoint import EntryPointButtons, EntryPointTitles
from src.utils.preprocess_image_for_ocr import preprocess_image_for_ocr
from src.utils.extract_text import extract_text
from src.utils.adb_controller import ADBController

screenshot_path = Config.get_screenshot_path()


def whereAmI(adb_controller: ADBController) -> str:
    if not adb_controller.capture_screenshot(screenshot_path):
        print("Failed to capture screenshot.")
        return None
    return searchTitle()


def searchTitle() -> str:
    if screenshot_path is None:
        return None

    image = cv2.imread(screenshot_path)
    title_crop_img = image[
        EntryPointTitles.PAGE.value.y : EntryPointTitles.PAGE.value.bottom,
        EntryPointTitles.PAGE.value.x : EntryPointTitles.PAGE.value.right,
    ]

    preprocessed_crop = preprocess_image_for_ocr(title_crop_img)
    if preprocessed_crop is None:
        return None

    text = (
        extract_text(preprocessed_crop, isName=True)
        .replace("\r", "")
        .replace("\n", " ")
    )

    return text if text in ["Items", "Equipment"] else None


def determineButton(location: str) -> Location:
    button_mapping = {
        "home": EntryPointButtons.HOME,
        "students": EntryPointButtons.STUDENTS,
        "menu": EntryPointButtons.MENU_TAB,
        "menu_equipment": EntryPointButtons.MENU_TAB_EQUIPMENT,
        "menu_items": EntryPointButtons.MENU_TAB_ITEMS,
    }

    return (
        button_mapping.get(location, None).value if location in button_mapping else None
    )


def goHome(adb_controller: ADBController):
    if button := determineButton("home"):
        adb_controller.execute_command(f"shell input tap {button.x} {button.y}")
        time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER)


def goToPage(adb_controller: ADBController, location: str):
    press_MenuTab(adb_controller)
    time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER)
    if button := determineButton(location):
        adb_controller.execute_command(f"shell input tap {button.x} {button.y}")


def press_MenuTab(adb_controller: ADBController):
    if not adb_controller.capture_screenshot(screenshot_path):
        print("Failed to capture screenshot.")
        return

    image = cv2.imread(screenshot_path)
    title_crop_img = image[
        EntryPointTitles.MENU_TAB.value.y : EntryPointTitles.MENU_TAB.value.bottom,
        EntryPointTitles.MENU_TAB.value.x : EntryPointTitles.MENU_TAB.value.right,
    ]

    preprocessed_crop = preprocess_image_for_ocr(title_crop_img)
    if preprocessed_crop is None:
        return

    text = (
        extract_text(preprocessed_crop, isName=True)
        .replace("\r", "")
        .replace("\n", " ")
    )
    if text != "Menu Tab" and (button := determineButton("menu")):
        adb_controller.execute_command(f"shell input tap {button.x} {button.y}")
