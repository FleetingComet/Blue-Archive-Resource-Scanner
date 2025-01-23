import os
import cv2
import numpy as np
import pytesseract

from locations.search import SearchPattern
from utils.adb_controller import ADBController


def extract_text(image, isTitle: bool = False) -> str:
    """Extract text from preprocessed image"""
    if isTitle:
        config = "--psm 6"  # single word 8, 7 for single line
    else:
        config = "--psm 6 -c tessedit_char_whitelist=0123456789"
    text: str = pytesseract.image_to_string(image, config=config)
    return text.strip()


def preprocess_image_for_ocr(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Increase contrast and sharpen
    # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    # morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    # sharp = cv2.addWeighted(gray, 1.5, morph, -0.5, 0)

    # _, binary = cv2.threshold(sharp, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)

    # test
    # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    # binary = cv2.dilate(binary, kernel, iterations=1)
    # return binary

    # clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    # enhanced = clahe.apply(gray)
    # binary = cv2.adaptiveThreshold(
    #         gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    #     )

    # Noise removal
    denoised = cv2.fastNlMeansDenoising(binary, h=30)

    # kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    # dilated = cv2.dilate(denoised, kernel_dilate, iterations=1)

    return denoised


screenshots_dir = "screenshots"
screenshot_path = os.path.join(screenshots_dir, "latest_screenshot.png")

adb_controller = ADBController()

if not adb_controller.capture_screenshot(screenshot_path):
    print("Failed to capture screenshot.")


image = cv2.imread(screenshot_path, cv2.IMREAD_ANYCOLOR)

# predetermined_region = Region(620, 575, 90, 35) #+10 on y, equipment page
# predetermined_region = Region(1240, 1160, 90, 30) #+10 on y, equipment page
# predetermined_region = Region(980, 1020, 160, 60)  # item page

# predetermined_region = SearchPattern.EQUIPMENT.value
predetermined_region = SearchPattern.EQUIPMENT_NAME.value
# predetermined_region = SearchPattern.EQUIPMENT_TIER.value

cv2.rectangle(
    image,
    (predetermined_region.x, predetermined_region.y),
    (predetermined_region.right, predetermined_region.bottom),
    (255, 0, 0),
    2,
)

# scale_factor = 0.5  # Adjust this as needed to see the image comfortably
# image = cv2.resize(image, None, fx=scale_factor, fy=scale_factor)
cv2.namedWindow("Detected Region", cv2.WINDOW_AUTOSIZE)
cv2.imshow("Detected Region", image)
cv2.waitKey(0)

crop_img = image[
    predetermined_region.y : predetermined_region.bottom,
    predetermined_region.x : predetermined_region.right,
]
# cv2.imshow("cropped", crop_img)
# cv2.waitKey(0)

preprocessed_crop = preprocess_image_for_ocr(crop_img)
text = extract_text(preprocessed_crop, isTitle=True)
# print(f"Image: {screenshot_path} Owned: {text}")
text_formatted = text.replace('\r', '').replace('\n', ' ')
print(f"{text_formatted}")
# with open("test.txt", "w+") as f:
#     f.write(text_formatted)

h1, w1 = image.shape[:2]
h2, w2 = crop_img.shape[:2]
res = np.zeros(shape=(max(h1, h2), w1 + w2, 3), dtype=np.uint8)

res[:h1, :w1] = image
res[:h2, w1 : w1 + w2] = crop_img

cv2.namedWindow("Preprocessed Image", cv2.WINDOW_AUTOSIZE)
cv2.imshow("Preprocessed Image", preprocessed_crop)
cv2.waitKey(0)
cv2.imwrite("preprocessed_crop.png", preprocessed_crop)

cv2.namedWindow("Preprocessed", cv2.WINDOW_AUTOSIZE)
cv2.imshow("Preprocessed", res)
cv2.waitKey(0)
cv2.destroyAllWindows()
