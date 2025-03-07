import os
from pathlib import Path
import cv2


def match_tier(cropped_image) -> str:
    tier_directory = r"assets\images\tier"
    tiers = [os.path.join(tier_directory, tier) for tier in os.listdir(tier_directory)]
    best_match = match_image_using_directory(cropped_image, tiers)
    if not best_match:
        return None
    # return os.path.basename(best_match)
    return Path(best_match).stem


def match_image_using_directory(input_image, reference_image_paths, threshold=0.9):
    """Match the input image against reference images using template matching."""
    best_match_name = None
    current_max_value = -1

    # input_image_gray = cv2.cvtColor(input_image, cv2.IMREAD_GRAYSCALE)
    input_image_gray = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)

    h, w = input_image_gray.shape[:2]
    if h < 50 or w < 50:
        input_image_gray = cv2.resize(
            input_image_gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR
        )

    for reference_path in reference_image_paths:
        reference_image = cv2.imread(reference_path, cv2.IMREAD_GRAYSCALE)

        result = cv2.matchTemplate(
            input_image_gray, reference_image, cv2.TM_CCOEFF_NORMED
        )
        _, max_value, _, _ = cv2.minMaxLoc(result)

        # print(f"Max Value for {reference_path}: {max_value}")

        # Check if this is the best match so far
        if max_value > current_max_value:
            current_max_value = max_value
            best_match_name = reference_path
            if max_value >= 0.99:
                break

    if not current_max_value >= threshold:
        return None

    return best_match_name
