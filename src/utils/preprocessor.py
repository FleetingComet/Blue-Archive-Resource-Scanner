import cv2
import numpy as np
import matplotlib.pyplot as plt

from src.utils.color_util import remove_colors

# def preprocess_image_for_ocr(image, debug=False):
#     """Preprocesses an image for Tesseract OCR with enhanced processing steps."""

#     # Convert to grayscale
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

#     # Initial resize for small images (applied to grayscale)
#     h, w = gray.shape
#     if h < 100 or w < 100:  # Adjusted minimum size threshold
#         gray = cv2.resize(gray, None, fx=2, fy=2,
#                         interpolation=cv2.INTER_CUBIC)

#     # Noise reduction on grayscale image
#     denoised = cv2.fastNlMeansDenoising(gray, None, h=20,
#                                       templateWindowSize=7,
#                                       searchWindowSize=21)

#     # Adaptive thresholding
#     binary = cv2.adaptiveThreshold(denoised, 255,
#                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#                                   cv2.THRESH_BINARY, 11, 4)

#     # Morphological operations
#     kernel = np.ones((2,2), np.uint8)
#     cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
#     cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)

#     # Secondary resize if needed (after processing)
#     final_h, final_w = cleaned.shape
#     if final_h < 300 or final_w < 300:  # Final quality check
#         cleaned = cv2.resize(cleaned, None,
#                            fx=1.5, fy=1.5,
#                            interpolation=cv2.INTER_CUBIC)

#     # Debug visualization
#     if debug:
#         cv2.imshow("1 - Grayscale", gray)
#         cv2.imshow("2 - Denoised", denoised)
#         cv2.imshow("3 - Thresholded", binary)
#         cv2.imshow("4 - Morphological Cleaning", cleaned)
#         cv2.waitKey(0)
#         cv2.destroyAllWindows()

#     return cleaned

# def preprocess_image_for_ocr(image, scale_factor=2, debug=False):
#     """
#     Preprocess the image to enhance OCR accuracy:
#       - Loads the image.
#       - Converts to grayscale.
#       - Upscales the image (if needed).
#       - Applies Gaussian blur.
#       - Uses adaptive thresholding to create a binary image.

#     Args:
#         image_path (str): Path to the image file.
#         scale_factor (int): Factor by which to upscale the image.
#         debug (bool): If True, displays intermediate images.

#     Returns:
#         numpy.ndarray: Preprocessed binary image.
#     """

#     # Convert to grayscale
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

#     # Upscale the image to make small text more legible
#     if scale_factor > 1:
#         gray = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_LINEAR)


#     # Apply Gaussian blur to reduce noise
#     blurred = cv2.GaussianBlur(gray, (3, 3), 0)

#     # Apply adaptive thresholding to get a clean binary image
#     thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#                                cv2.THRESH_BINARY, 15, 3)

#     if debug:
#         cv2.imshow("Grayscale", gray)
#         cv2.imshow("Blurred", blurred)
#         cv2.imshow("Threshold", thresh)
#         cv2.waitKey(0)
#         cv2.destroyAllWindows()

#     return thresh


# def preprocess_image_for_ocr(image):
#     # Convert image to grayscale
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

#     # Improve contrast with histogram equalization
#     equalized = cv2.equalizeHist(gray)

#     # Use adaptive thresholding for better results on uneven lighting
#     adaptive = cv2.adaptiveThreshold(
#         equalized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#         cv2.THRESH_BINARY, 11, 2
#     )

#     # Resize if image is very small to better capture details
#     h, w = adaptive.shape
#     if h < 50 or w < 50:
#         adaptive = cv2.resize(adaptive, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)

#     # Apply a morphological opening to remove small noise while preserving text structure
#     kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
#     morph = cv2.morphologyEx(adaptive, cv2.MORPH_OPEN, kernel, iterations=1)

#     # Apply non-local means denoising for additional noise removal
#     denoised = cv2.fastNlMeansDenoising(morph, h=30)

#     return denoised

# def preprocess_image_for_ocr(image):
#     # Convert to grayscale
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#     _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

#     h, w = binary.shape
#     if h < 50 or w < 50:
#         binary = cv2.resize(binary, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)

#     # Noise removal
#     denoised = cv2.fastNlMeansDenoising(binary, h=30)
#     return denoised


# def preprocess_image_for_ocr(image, debug=False):
#     # Convert to grayscale
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#     _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
#     denoised = cv2.fastNlMeansDenoising(binary, h=30)
#     brightened = cv2.convertScaleAbs(binary, alpha=2, beta=0)
#     inverted = 255 - brightened

#     h, w = binary.shape
#     if h < 50 or w < 50:
#         inverted = cv2.resize(
#             inverted, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR
#         )

#     # Noise removal
#     if debug:
#         titles = ["Original", "Grayscale", "Binarized (Otsu)", "Denoised", "Inverted"]
#         images = [image, gray, binary, denoised, inverted]

#         if debug:
#             for i, v in enumerate(images):
#                 cv2.imshow(titles[i], v)
#             cv2.waitKey(0)
#             cv2.destroyAllWindows()
#     return inverted


def preprocess_image_for_ocr(image, image_type):
    """
    Preprocess an image for OCR based on the specified image type.

    Parameters:
        image (np.array): The input image.
        image_type (str): The type of image. Supported types include:
            - "number_in_circle": For numeric values inside a circle (like bond level or Tier).
            - "skill_level_indicator": For skill level indicators (e.g., "MAX").
            - "level_indicator": For level indicators.
            - "student_name": For text labels.
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

    if image_type == "number_in_circle":  # in bond or gear tier
        gray = cv2.equalizeHist(gray)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # config = "--psm 10 -c tessedit_char_whitelist=0123456789"
        config = "--psm 7 -c tessedit_char_whitelist=0123456789"
        config += " --oem 3 --tessdata-dir ./tessdata -l BlueArchive"

    elif image_type == "skill_level_indicator":  # Level
        hex_colors = ["dceffa", "e0effa", "e7f3fb", "d8dadc", "bcccd8"]
        binary, _ = remove_colors(image, hex_colors)
        config = "--psm 6 -c tessedit_char_whitelist=0123456789MAXmax"
        # config += " --oem 3 --tessdata-dir ./tessdata -l BlueArchive"

    elif image_type == "level_indicator":  # Level
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        config = "--psm 6 -c tessedit_char_whitelist=0123456789MAXmax/"

    elif image_type == "student_name":  # text label
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        config = "--psm 7"
        # config += " --oem 3 --tessdata-dir ./tessdata -l BlueArchive"
    else:
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        config = "--psm 6"
        # config += " --oem 3 --tessdata-dir ./tessdata -l BlueArchive"
    return binary, config
