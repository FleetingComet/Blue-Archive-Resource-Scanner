import cv2
import numpy as np

from src.enums.ExtractionMode import ExtractionMode
from src.utils.ocr.color_util import remove_colors, retain_colors


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
        tuple: (binary, config)
        binary (np.array): The preprocessed binary image.
    """

    if mode == ExtractionMode.GEAR:
        h, w = image.shape[:2]
        image = cv2.resize(image, (w * 5, h * 5), interpolation=cv2.INTER_CUBIC)
        # Tier Color
        hex_colors = [
            "0f88bc",
        ]
        result, _ = retain_colors(image, hex_colors, tolerance=70)

        return result

    h, w = image.shape[:2]
    if h < 50 or w < 50:
        image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)

    # if image.shape[2] == 4:
    #     image = image[:, :, :3]

    # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # h, w = gray.shape[:2]
    # if h < 50 or w < 50:
    #     gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    if image.ndim == 3:
        if image.shape[2] == 4:
            image = image[:, :, :3]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    if mode == ExtractionMode.BOND_LEVEL:  # in bond or somewhere
        # gray = cv2.equalizeHist(gray)
        # _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        binary = gray
        binary = 255 - binary
        return binary

    elif mode == ExtractionMode.SKILL_LEVEL:  # Skill Level
        hex_colors = ["dceffa", "e0effa", "e7f3fb", "d8dadc", "bcccd8"]
        binary, _ = remove_colors(image, hex_colors)

        gray = cv2.cvtColor(binary, cv2.COLOR_BGR2GRAY)
        gray = cv2.convertScaleAbs(gray, alpha=1.3, beta=0)
        _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        binary = cv2.resize(binary, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
        # binary = 255 - binary
        return binary

    elif (
        mode == ExtractionMode.LEVEL or mode == ExtractionMode.NUMBER
    ):  # Level or Number
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    elif (
        mode == ExtractionMode.NAME or mode == ExtractionMode.TEXT
    ):  # single line label
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
        gray = sharpen_image(gray)
        gray = unsharp_mask(gray)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    elif mode == ExtractionMode.MULTI_LINE_NAME:  # multi line
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

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
