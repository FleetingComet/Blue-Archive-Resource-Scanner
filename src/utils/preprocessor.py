import cv2

from src.utils.color_util import remove_colors


def preprocess_image_for_ocr(image, image_type=None):
    """
    Preprocess an image for OCR based on the specified image type.

    Parameters:
        image (np.array): The input image.
        image_type (str): The type of image. Supported types include:
            - "number_in_circle": For numeric values inside a circle (like bond level).
            - "skill_level_indicator": For skill level indicators (e.g., "MAX").
            - "level_indicator": For level indicators.
            - "name": For text labels.
            - Otherwise, default processing is applied.

    Returns:
        tuple: (binary, config)
            binary (np.array): The preprocessed binary image.
            config (str): Tesseract configuration string.
    """

    h, w = image.shape[:2]
    if h < 50 or w < 50:
        image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)

    if image.shape[2] == 4:
        image = image[:, :, :3]

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]
    if h < 50 or w < 50:
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    if (
        image_type == "number_in_circle" or image_type == "ue_level"
    ):  # in bond or somewhere
        # gray = cv2.equalizeHist(gray)
        # _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        binary = gray
        binary = 255 - binary
        # config = "--psm 10 -c tessedit_char_whitelist=0123456789"
        config = "--psm 7 -c tessedit_char_whitelist=0123456789"
        config += " --oem 3 --tessdata-dir ./tessdata -l BlueArchive"

    elif image_type == "skill_level_indicator":  # Skill Level
        hex_colors = ["dceffa", "e0effa", "e7f3fb", "d8dadc", "bcccd8"]
        binary, _ = remove_colors(image, hex_colors)
        config = "--psm 6 -c tessedit_char_whitelist=0123456789MAXmax"
        # config += " --oem 3 --tessdata-dir ./tessdata -l BlueArchive"

    elif image_type == "level_indicator":  # Level
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        config = "--psm 6 -c tessedit_char_whitelist=0123456789MAXmax/"
    # elif image_type == "ue_level":  # Level
    #     _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    #     config = "--psm 6 -c tessedit_char_whitelist=0123456789MAXmax/"

    elif image_type == "name":  # text label
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        config = "--psm 7"
        # config += " --oem 3 --tessdata-dir ./tessdata -l BlueArchive"
    else:
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        config = "--psm 6 -c tessedit_char_whitelist=0123456789"
        # config += " --oem 3 --tessdata-dir ./tessdata -l BlueArchive"
    return binary, config
