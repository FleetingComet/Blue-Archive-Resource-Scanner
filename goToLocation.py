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
    title = searchTitle()
    time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER)
    if not title:
        return None
    else:
        print(f"title is {title}")


def searchTitle() -> str:
    if screenshot_path is None:
        return None

    image = cv2.imread(screenshot_path)
    title_crop_img = image[
        EntryPointTitles.PAGE.value.y : EntryPointTitles.PAGE.value.bottom,
        EntryPointTitles.PAGE.value.x : EntryPointTitles.PAGE.value.right,
    ]

    preprocessed_crop = preprocess_image_for_ocr(title_crop_img)
    if preprocessed_crop is not None:
        text = extract_text(preprocessed_crop, isName=True)
        text.replace("\r", "").replace("\n", " ")

        if text not in ["Items", "Equipment"]:
            return None
        else:
            return text

    return None


def determineButton(location: str) -> Location:
    # wtf help
    if location == "home":
        region = EntryPointButtons.HOME.value
    elif location == "students":
        region = EntryPointButtons.STUDENTS.value
    elif location == "menu":
        region = EntryPointButtons.MENU_TAB.value
    elif location == "menu_equipment":
        region = EntryPointButtons.MENU_TAB_EQUIPMENT.value
    elif location == "menu_items":
        region = EntryPointButtons.MENU_TAB_ITEMS.value
    else:
        return None
    return region


def goHome(adb_controller: ADBController):
    adb_controller.execute_command(
        f"shell input tap {determineButton('home').x} {determineButton('home').y}"
    )
    time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER)
    return


def goToPage(adb_controller: ADBController, location: str):
    press_MenuTab(adb_controller)
    time.sleep(0.5 * Config.WAIT_TIME_MULTIPLIER)
    adb_controller.execute_command(
        f"shell input tap {determineButton(location).x} {determineButton(location).y}"
    )
    return


def press_MenuTab(adb_controller: ADBController):
    if not adb_controller.capture_screenshot(screenshot_path):
        print("Failed to capture screenshot.")
        return
    if screenshot_path is None:
        return

    image = cv2.imread(screenshot_path)
    title_crop_img = image[
        EntryPointTitles.MENU_TAB.value.y : EntryPointTitles.MENU_TAB.value.bottom,
        EntryPointTitles.MENU_TAB.value.x : EntryPointTitles.MENU_TAB.value.right,
    ]

    preprocessed_crop = preprocess_image_for_ocr(title_crop_img)
    if preprocessed_crop is not None:
        text = extract_text(preprocessed_crop, isName=True)
        text.replace("\r", "").replace("\n", " ")

        if text != "Menu Tab":
            adb_controller.execute_command(
                f"shell input tap {determineButton('menu').x} {determineButton('menu').y}"
            )
        else:
            return
