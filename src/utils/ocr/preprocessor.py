import cv2
import numpy as np

from src.enums.ExtractionMode import ExtractionMode
from src.utils.ocr.color_util import remove_colors, remove_non_white, retain_colors


def preprocess_image_for_ocr(image, mode: ExtractionMode = None):
    """
    Preprocess an image for OCR based on the specified image type.

    Parameters:
        image (np.array): The input image.
        mode (ExtractionMode): The type of image. Supported types include:
            - "number_in_circle": For numeric values inside a circle (like bond level).
            - "skill_level_indicator": For skill level indicators (e.g., "MAX").
            - "level_indicator" or "number": For level indicators or numbers.
            - "multi_line_name": For multi line text labels (e.g. Names on Equipment and Items).
            - "name" or "text": For text labels.
            - "gear": For gear tiers (e.g., "T9", "T7").
            - Otherwise, default processing is applied.

    Returns:
        binary (np.array): The preprocessed binary image.
    """

    h, w = image.shape[:2]
    if h < 50 or w < 50 and mode != ExtractionMode.GEAR:
        image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    if mode == ExtractionMode.GEAR:
        image = cv2.resize(image, (w * 5, h * 5), interpolation=cv2.INTER_CUBIC)
        # Tier Color
        hex_colors = ["0f88bc"]
        image, _ = retain_colors(image, hex_colors, tolerance=70)
        return image

    elif mode == ExtractionMode.SKILL_LEVEL:
        hex_colors = ["dceffa", "e0effa", "e7f3fb", "d8dadc", "bcccd8"]
        image, _ = remove_colors(image, hex_colors)

    elif mode == ExtractionMode.BOND_LEVEL:
        hex_colors = ["3c4e66"]
        image, _ = retain_colors(image, hex_colors, tolerance=20)

    elif mode == ExtractionMode.UE_LEVEL or mode == ExtractionMode.NAME:
        image = remove_non_white(image)

    # Standardization to Grayscale
    if image.ndim == 3:
        if image.shape[2] == 4:
            image = image[:, :, :3]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    if mode in [ExtractionMode.NAME, ExtractionMode.TEXT]:  # single line label
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
        gray = sharpen_image(gray)
        gray = unsharp_mask(gray)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    elif mode == ExtractionMode.MULTI_LINE_NAME:  # multi line
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    elif mode == ExtractionMode.BOND_LEVEL:  # in bond or somewhere
        binary = 255 - gray
        return binary

    elif mode == ExtractionMode.SKILL_LEVEL:  # Skill Level
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.convertScaleAbs(gray, alpha=1.3, beta=0)
        _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        binary = cv2.resize(binary, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
        # binary = 255 - binary
        return binary

    elif mode in [ExtractionMode.LEVEL, ExtractionMode.NUMBER]:  # Level or Number
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    else:
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return binary


def sharpen_image(image):
    # Define a sharpening kernel
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    # Apply filter
    sharpened = cv2.filter2D(image, -1, kernel)
    return sharpened


def unsharp_mask(image, alpha=1.5, beta=-0.5, gamma=0):
    # Gaussian blur
    blurred = cv2.GaussianBlur(image, (0, 0), sigmaX=3)
    # Weighted sum
    sharp = cv2.addWeighted(image, alpha, blurred, beta, gamma)
    return sharp
