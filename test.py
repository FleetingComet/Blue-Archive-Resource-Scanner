import time
import mss
import numpy as np
import win32gui
import win32ui
import win32con
from area import Region
from locations.search import StudentSearchPattern
from utils.data.jsonHelper import map_student_data_to_character
from utils.device.window_capture import WindowCapture
import cv2

from utils.device.window_capture_mss import WindowCaptureMSS
from utils.ocr.extract import extract_from_region


# @staticmethod
# def list_window_names():
#     def winEnumHandler(hwnd, ctx):
#         if win32gui.IsWindowVisible(hwnd):
#             print(hex(hwnd), win32gui.GetWindowText(hwnd))
#     win32gui.EnumWindows(winEnumHandler, None)

# list_window_names()


# wc = WindowCapture("Blue Archive")
# time.sleep(0.5)
# img = wc.get_screenshot()
# cv2.imshow("Captured", img)
# cv2.waitKey(0)
def crop_image(image, region: Region):
    """Crop the image to the specified region."""
    return image[region.y : region.bottom, region.x : region.right]


def bring_to_front(window_title):
    hwnd = win32gui.FindWindow(None, window_title)
    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        return hwnd
    else:
        raise Exception(f"Window '{window_title}' not found.")


wc = WindowCaptureMSS("Blue Archive")
# wc = WindowCapture("Blue Archive")
window_title = "Blue Archive"
# hwnd = bring_to_front(window_title)
time.sleep(0.5)
frame = wc.get_screenshot()

# cv2.imshow("MSS", frame)
# cv2.waitKey(0)

# translated = wc.translate_from_base_resolution(StudentSearchPattern.STUDENT_NAME.value)
# print(f"Coordinates: {StudentSearchPattern.STUDENT_NAME.value}")
# print(f"Translated coordinates: {translated}")


# crop = crop_image(frame, translated)
# cv2.imshow("crop", crop)
# cv2.waitKey(0)
def funcname(test):
    cropped = crop_image(wc.get_screenshot(), test)
    cv2.imshow("cropped", cropped)
    cv2.waitKey(0)


# Translate from 1280×720 to actual content
# for region in StudentSearchPattern:
#     translated = wc.translate_from_base_resolution(region.value)
#     print(f"Region: {region.name}, Coordinates: {translated}")
#     funcname(translated)

image = wc.get_screenshot()

student_data = {
    "Name": extract_from_region(
        image,
        wc.translate_from_base_resolution(StudentSearchPattern.STUDENT_NAME.value),
        image_type="name",
    ),
    "Level": extract_from_region(
        image,
        wc.translate_from_base_resolution(StudentSearchPattern.LEVEL.value),
        image_type="level_indicator",
    ),
    "Bond Level": extract_from_region(
        image,
        wc.translate_from_base_resolution(StudentSearchPattern.BOND_LEVEL.value),
        image_type="number_in_circle",
    ),
    "Rarity": extract_from_region(
        image,
        wc.translate_from_base_resolution(StudentSearchPattern.STAR_QUANTITY.value),
        image_type="star",
    ),
    "Gear 1 Tier": extract_from_region(
        image,
        wc.translate_from_base_resolution(StudentSearchPattern.GEAR_1_TIER.value),
        image_type="gear",
    ),
    "Gear 2 Tier": extract_from_region(
        image,
        wc.translate_from_base_resolution(StudentSearchPattern.GEAR_2_TIER.value),
        image_type="gear",
    ),
    "Gear 3 Tier": extract_from_region(
        image,
        wc.translate_from_base_resolution(StudentSearchPattern.GEAR_3_TIER.value),
        image_type="gear",
    ),
    "Gear Bond Tier": extract_from_region(
        image,
        wc.translate_from_base_resolution(StudentSearchPattern.GEAR_BOND_TIER.value),
        image_type="gear",
    ),
    "Unique Equipment Star Quantity": extract_from_region(
        image,
        wc.translate_from_base_resolution(StudentSearchPattern.UNIQUE_EQUIPMENT_STAR_QUANTITY.value),
        image_type="ue_star",
    ),
    "Unique Equipment Level": extract_from_region(
        image,
        wc.translate_from_base_resolution(StudentSearchPattern.UNIQUE_EQUIPMENT_LEVEL.value),
        image_type="ue_level",
    ),
    "Skill EX": extract_from_region(
        image,
        wc.translate_from_base_resolution(StudentSearchPattern.SKILL_EX.value),
        image_type="skill_level_indicator",
    ),
    "Skill Basic": extract_from_region(
        image,
        wc.translate_from_base_resolution(StudentSearchPattern.SKILL_BASIC.value),
        image_type="skill_level_indicator",
    ),
    "Skill Enhanced": extract_from_region(
        image,
        wc.translate_from_base_resolution(StudentSearchPattern.SKILL_ENHANCED.value),
        image_type="skill_level_indicator",
    ),
    "Skill Sub": extract_from_region(
        image,
        wc.translate_from_base_resolution(StudentSearchPattern.SKILL_SUB.value),
        image_type="skill_level_indicator",
    ),
}

name, current_data = map_student_data_to_character(student_data)
print("Character Name:", name)
print("Current Data:", current_data)

# get screen coordinates
# region_on_screen = wc.get_screen_position()

# def get_window_rect(hwnd):
#     left, top, right, bottom = win32gui.GetWindowRect(hwnd)
#     return {
#         "top": top,
#         "left": left,
#         "width": right - left,
#         "height": bottom - top
#     }

# window_title = "Blue Archive"

# hwnd = bring_to_front(window_title)
# time.sleep(0.5)  # Wait for window to come into focus

# with mss.mss() as sct:
#     region = get_window_rect(hwnd)
#     screenshot = np.array(sct.grab(region))[:, :, :3]
#     cv2.imshow("Capture", screenshot)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()
